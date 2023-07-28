#!/usr/bin/env python
# coding: utf-8 -*-

"""
Exec CLI helpers
"""

import asyncio
import itertools
import json
import logging
from pathlib import Path
from typing import Dict, List, Literal, Optional

from aioeapi import EapiCommandError

from anta.device import AntaDevice, AsyncEOSDevice
from anta.inventory import AntaInventory
from anta.models import AntaCommand
from anta.tools.misc import anta_log_exception, exc_to_str

EOS_SCHEDULED_TECH_SUPPORT = "/mnt/flash/schedule/tech-support"

logger = logging.getLogger(__name__)


async def clear_counters_utils(anta_inventory: AntaInventory, tags: Optional[List[str]] = None) -> None:
    """
    Clear counters
    """

    async def clear(dev: AntaDevice) -> None:
        commands = [AntaCommand(command="clear counters")]
        if dev.hw_model not in ["cEOSLab", "vEOS-lab"]:
            commands.append(AntaCommand(command="clear hardware counter drop"))
        await dev.collect_commands(commands=commands)
        for command in commands:
            if not command.collected:
                logger.error(f"Could not clear counters on device {dev.name}: {command.failed}")
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
        c = AntaCommand(command=command, ofmt=outformat)
        await dev.collect(c)
        if not c.collected and c.failed is not None:
            logger.error(f"Could not collect commands on device {dev.name}: {exc_to_str(c.failed)}")
            return
        if c.ofmt == "json":
            outfile = outdir / f"{command}.json"
            content = json.dumps(c.json_output, indent=2)
        elif c.ofmt == "text":
            outfile = outdir / f"{command}.log"
            content = c.text_output
        with outfile.open(mode="w", encoding="UTF-8") as f:
            f.write(content)
        logger.info(f"Collected command '{command}' from device {dev.name} ({dev.hw_model})")

    logger.info("Connecting to devices...")
    await inv.connect_inventory()
    devices = inv.get_inventory(established_only=True, tags=tags).values()
    logger.info("Collecting commands from remote devices")
    coros = []
    if "json_format" in commands:
        coros += [collect(device, command, "json") for device, command in itertools.product(devices, commands["json_format"])]
    if "text_format" in commands:
        coros += [collect(device, command, "text") for device, command in itertools.product(devices, commands["text_format"])]
    res = await asyncio.gather(*coros, return_exceptions=True)
    for r in res:
        if isinstance(r, Exception):
            message = "Error when collecting commands"
            anta_log_exception(r, message, logger)


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
            command = AntaCommand(command=cmd, ofmt="text")
            await device.collect(command=command)
            if command.collected and command.text_output:
                filenames = list(map(lambda f: Path(f"{EOS_SCHEDULED_TECH_SUPPORT}/{f}"), command.text_output.splitlines()))
            else:
                logger.error(f"Unable to get tech-support filenames on {device.name}: verify that {EOS_SCHEDULED_TECH_SUPPORT} is not empty")
                return

            # Create directories
            outdir = Path() / root_dir / f"{device.name.lower()}"
            outdir.mkdir(parents=True, exist_ok=True)

            # Check if 'aaa authorization exec default local' is present in the running-config
            command = AntaCommand(command="show running-config | include aaa authorization exec default local", ofmt="text")
            await device.collect(command=command)

            if command.collected and not command.text_output:
                logger.debug(f"'aaa authorization exec default local' is not configured on device {device.name}")
                if configure:
                    # Otherwise mypy complains about enable
                    assert isinstance(device, AsyncEOSDevice)
                    # TODO - @mtache - add `config` field to `AntaCommand` object to handle this use case.
                    commands = []
                    if device.enable and device._enable_password is not None:  # type: ignore[attr-defined] # pylint: disable=protected-access
                        commands.append({"cmd": "enable", "input": device._enable_password})  # type: ignore[attr-defined] # pylint: disable=protected-access
                    elif device.enable:
                        commands.append({"cmd": "enable"})
                    commands.extend(
                        [
                            {"cmd": "configure terminal"},
                            {"cmd": "aaa authorization exec default local"},
                        ]
                    )
                    logger.warning(f"Configuring 'aaa authorization exec default local' on device {device.name}")
                    command = AntaCommand(command="show running-config | include aaa authorization exec default local", ofmt="text")
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
            message = f"Unable to collect tech-support on device {device.name}"
            anta_log_exception(e, message, logger)

    logger.info("Connecting to devices...")
    await inv.connect_inventory()
    devices = inv.get_inventory(established_only=True, tags=tags).values()
    await asyncio.gather(*(collect(device) for device in devices))
