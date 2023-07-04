#!/usr/bin/env python
# coding: utf-8 -*-

"""
Exec CLI helpers
"""

import asyncio
import itertools
import json
import logging
import traceback
from pathlib import Path
from typing import Dict, List, Literal, Optional

from aioeapi import EapiCommandError

from anta.device import AntaDevice
from anta.inventory import AntaInventory
from anta.models import AntaTestCommand
from anta.tools.misc import exc_to_str, tb_to_str

EOS_SCHEDULED_TECH_SUPPORT = "/mnt/flash/schedule/tech-support"

logger = logging.getLogger(__name__)


async def clear_counters_utils(anta_inventory: AntaInventory, tags: Optional[List[str]] = None) -> None:
    """
    Clear counters
    """

    async def clear(dev: AntaDevice) -> None:
        commands = [AntaTestCommand(command="clear counters")]
        if dev.hw_model not in ["cEOSLab", "vEOS-lab"]:
            commands.append(AntaTestCommand(command="clear hardware counter drop"))
        await dev.collect_commands(commands=commands)
        for command in commands:
            if command.output is None:  # TODO - add a failed attribute to AntaTestCommand class
                logger.error(f"Could not clear counters on device {dev.name}")
        logger.info(f"Cleared counters on {dev.name} ({dev.hw_model})")

    logger.info("Connecting to devices...")
    await anta_inventory.connect_inventory()
    devices = anta_inventory.get_inventory(established_only=True, tags=tags).values()
    logger.info("Clearing counters on remote devices...")
    await asyncio.gather(*(clear(device) for device in devices))


async def collect_commands(
    inv: AntaInventory,
    commands: Dict[str, str],
    root_dir: Path,
    tags: Optional[List[str]] = None,
) -> None:
    """
    Collect EOS commands
    """

    async def collect(dev: AntaDevice, command: str, outformat: Literal["json", "text"]) -> None:
        outdir = Path() / root_dir / dev.name / outformat
        outdir.mkdir(parents=True, exist_ok=True)
        c = AntaTestCommand(command=command, ofmt=outformat)
        await dev.collect(c)
        if c.output is None:  # TODO @mtache use c.failed
            logger.error(f"Could not collect commands on device {dev.name}")
            return
        if c.ofmt == "json":
            outfile = outdir / (command + ".json")
            content = json.dumps(c.output, indent=2)
        elif c.ofmt == "text":
            outfile = outdir / (command + ".log")
            content = str(c.output)
        with outfile.open(mode="w", encoding="UTF-8") as f:
            f.write(content)
        logger.info(f"Collected command '{command}' from device {dev.name} ({dev.hw_model})")

    logger.info("Connecting to devices...")
    await inv.connect_inventory()
    devices = inv.get_inventory(established_only=True, tags=tags).values()
    logger.info("Collecting commands from remote devices")
    coros = [collect(device, command, "json") for device, command in itertools.product(devices, commands["json_format"])]
    coros += [collect(device, command, "text") for device, command in itertools.product(devices, commands["text_format"])]
    res = await asyncio.gather(*coros, return_exceptions=True)
    for r in res:
        if isinstance(r, Exception):
            logger.error(f"Error when collecting commands: {r.__class__.__name__}: {r}")
    for r in res:
        if isinstance(r, Exception):
            logger.critical(f"Error when collecting commands - {exc_to_str(r)}")
            logger.debug(tb_to_str(r))


async def collect_scheduled_show_tech(inv: AntaInventory, root_dir: Path, configure: bool, tags: Optional[List[str]] = None, latest: Optional[int] = None) -> None:
    """
    Collect scheduled show-tech on devices
    """

    async def collect(device: AntaDevice) -> None:
        """
        Collect all the tech-support files stored on Arista switches flash and copy them locally
        """
        try:
            # Get the tech-support filename to retrieve
            cmd = f"bash timeout 10 ls -1t {EOS_SCHEDULED_TECH_SUPPORT}"
            if latest:
                cmd += f" | head -{latest}"
            command = AntaTestCommand(command=cmd, ofmt="text")
            await device.collect(command=command)
            if command.output:
                filenames = list(map(lambda f: Path(f"{EOS_SCHEDULED_TECH_SUPPORT}/{f}"), str(command.output).splitlines()))
            else:
                logger.error(f"Unable to get tech-support filenames on {device.name}: verify that {EOS_SCHEDULED_TECH_SUPPORT} is not empty")
                return

            # Create directories
            outdir = Path() / root_dir / f"{device.name.lower()}"
            outdir.mkdir(parents=True, exist_ok=True)

            # Check if 'aaa authorization exec default local' is present in the running-config
            command = AntaTestCommand(command="show running-config | include aaa authorization exec default local", ofmt="text")
            await device.collect(command=command)

            if not command.output:
                logger.debug(f"'aaa authorization exec default local' is not configured on device {device.name}")
                if configure:
                    # TODO - @mtache - add `config` field to `AntaTestCommand` object to handle this use case.
                    commands = [
                        {"cmd": "enable", "input": device._enable_password},  # type: ignore[attr-defined] # pylint: disable=protected-access
                        "configure terminal",
                        "aaa authorization exec default local",
                    ]
                    command = AntaTestCommand(command="show running-config | include aaa authorization exec default local", ofmt="text")
                    logger.debug(f"Configuring 'aaa authorization exec default local' on device {device.name}")
                    await device.session.cli(commands=commands)  # type: ignore[attr-defined]
                    logger.info(f"Configured 'aaa authorization exec default local' on device {device.name}")
                else:
                    logger.error(f"Unable to collect tech-support on {device.name}: configuration 'aaa authorization exec default local' is not present")
                    return
            logger.debug(f"'aaa authorization exec default local' is already configured on device {device.name}")

            await device.copy(sources=filenames, destination=outdir, direction="from")
            logger.info(f"Collected {len(filenames)} scheduled tech-support from {device.name}")

        except EapiCommandError as e:
            logger.error(f"Unable to collect tech-support on {device.name}: {e.errmsg}")
        # In this case we want to catch all exceptions
        except Exception as e:  # pylint: disable=broad-except
            logger.error(f"Unable to collect tech-support on device {device.name}")
            logger.debug(f"Exception raised for device {device.name} - {type(e).__name__}: {str(e)}")
            logger.debug(traceback.format_exc())

    logger.info("Connecting to devices...")
    await inv.connect_inventory()
    devices = inv.get_inventory(established_only=True, tags=tags).values()
    await asyncio.gather(*(collect(device) for device in devices))
