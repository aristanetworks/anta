#!/usr/bin/env python
# coding: utf-8 -*-

"""
Exec CLI helpers
"""

import asyncio
import itertools
import logging
import traceback
from pathlib import Path
from typing import Dict, List, Literal

import asyncssh
from aioeapi import EapiCommandError

from anta.inventory import AntaInventory
from anta.inventory.models import InventoryDevice

EOS_SCHEDULED_TECH_SUPPORT = "/mnt/flash/schedule/tech-support"

logger = logging.getLogger(__name__)


async def clear_counters_utils(anta_inventory: AntaInventory, enable_pass: str, tags: List[str]) -> None:
    """
    clear counters
    """

    async def clear(dev: InventoryDevice) -> None:
        commands = [{"cmd": "enable", "input": enable_pass}, "clear counters"]
        if dev.hw_model not in ["cEOSLab", "vEOS-lab"]:
            commands.append("clear hardware counter drop")
        try:
            await dev.session.cli(commands=commands)
            logger.info(f"Cleared counters on {dev.name} ({dev.hw_model})")
        # In this case we want to catch all exceptions
        except Exception as e:  # pylint: disable=broad-except
            logger.error(f"Could not clear counters on device {dev.name}")
            logger.debug(f"Exception raised for device {dev.name} - {type(e).__name__}: {str(e)}")
            logger.debug(traceback.format_exc())

    logger.info("Connecting to devices...")
    await anta_inventory.connect_inventory()
    devices = anta_inventory.get_inventory(established_only=True, tags=tags)
    logger.info("Clearing counters on remote devices...")
    await asyncio.gather(*(clear(device) for device in devices))


async def collect_commands(
    inv: AntaInventory,
    enable_pass: str,
    commands: Dict[str, str],
    root_dir: str,
    tags: List[str],
) -> None:
    """
    Collect EOS commands
    """

    async def collect(dev: InventoryDevice, command: str, outformat: Literal["json", "text"]) -> None:
        try:
            outdir = Path() / root_dir / dev.name / outformat
            outdir.mkdir(parents=True, exist_ok=True)
            outfile = outdir / command
            if enable_pass is not None:
                result = await dev.session.cli(
                    commands=[{"cmd": "enable", "input": enable_pass}, command],
                    ofmt=outformat,
                )
            else:
                result = await dev.session.cli(
                    commands=["", command],
                    ofmt=outformat,
                )
            with outfile.open(mode="w", encoding="UTF-8") as f:
                f.write(str(result[1]))
            logger.info(f"Collected command '{command}' from device {dev.name} ({dev.hw_model})")
        except EapiCommandError as e:
            logger.error(f"Command failed on {dev.name}: {e.errmsg}")
        # In this case we want to catch all exceptions
        except Exception as e:  # pylint: disable=broad-except
            logger.error(f"Could not collect commands on device {dev.name}")
            logger.debug(f"Exception raised for device {dev.name} - {type(e).__name__}: {str(e)}")
            logger.debug(traceback.format_exc())

    logger.info("Connecting to devices...")
    await inv.connect_inventory()
    devices = inv.get_inventory(established_only=True, tags=tags)
    logger.info("Collecting commands from remote devices")
    coros = [collect(device, command, "json") for device, command in itertools.product(devices, commands["json_format"])]
    coros += [collect(device, command, "text") for device, command in itertools.product(devices, commands["text_format"])]
    res = await asyncio.gather(*coros, return_exceptions=True)
    for r in res:
        if isinstance(r, Exception):
            logger.error(f"Error when running tests: {r.__class__.__name__}: {r}")


async def collect_scheduled_show_tech(  # pylint: disable=too-many-arguments
    inv: AntaInventory,
    enable_pass: str,
    root_dir: str,
    tags: List[str],
    ssh_port: int,
    insecure: bool,
    latest: int,
    configure: bool,
) -> None:
    """
    Collect scheduled show-tech on devices
    """

    async def collect(device: InventoryDevice) -> None:
        """
        Collect all the tech-support files stored on Arista switches flash and copy them locally
        """
        try:
            # Get the tech-support filename to retrieve
            command = f"bash timeout 10 ls -1t {EOS_SCHEDULED_TECH_SUPPORT}"
            if latest:
                command += f" | head -{latest}"
            commands = [{"cmd": "enable", "input": enable_pass}, command]
            logger.debug(f"Sending '{command}' to device {device.name}")
            res = await device.session.cli(commands=commands, ofmt="text")
            if res[1]:
                filenames = list(map(lambda f: f"{EOS_SCHEDULED_TECH_SUPPORT}/{f}", res[1].splitlines()))
            else:
                logger.error(f"Unable to get tech-support filenames on {device.name}: verify that {EOS_SCHEDULED_TECH_SUPPORT} is not empty")
                return

            # Create directories
            outdir = Path() / root_dir / f"{device.name.lower()}"
            outdir.mkdir(parents=True, exist_ok=True)

            # Check if 'aaa authorization exec default local' is present in the running-config
            commands = [
                {"cmd": "enable", "input": enable_pass},
                "show running-config | include aaa authorization exec default local",
            ]
            logger.debug(f"Sending 'show running-config | include aaa authorization exec default local' to device {device.name}")
            res = await device.session.cli(commands=commands, ofmt="text")

            if not res[1]:
                logger.debug(f"'aaa authorization exec default local' is not configured on device {device.name}")
                if configure:
                    commands = [
                        {"cmd": "enable", "input": enable_pass},
                        "configure terminal",
                        "aaa authorization exec default local",
                    ]
                    logger.debug(f"Configuring 'aaa authorization exec default local' on device {device.name}")
                    await device.session.cli(commands=commands)
                    logger.info(f"Configured 'aaa authorization exec default local' on device {device.name}")
                else:
                    logger.error(f"Unable to collect tech-support on {device.name}: configuration 'aaa authorization exec default local' is not present")
                    return
            logger.debug(f"'aaa authorization exec default local' is already configured on device {device.name}")

            ssh_params = {
                "host": device.host,
                "port": ssh_port,
                "username": device.username,
                "password": device.password,
            }
            if insecure:
                ssh_params.update({"known_hosts": None})

            async with asyncssh.connect(**ssh_params) as conn:
                coros = []
                for file in filenames:
                    logger.info(f"Copying '{file}' from device {device.name} to '{outdir}' locally")
                    coros.append(asyncssh.scp((conn, file), outdir))
                await asyncio.gather(*coros)
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
    devices = inv.get_inventory(established_only=True, tags=tags)
    await asyncio.gather(*(collect(device) for device in devices))
