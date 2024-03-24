# Copyright (c) 2023-2024 Arista Networks, Inc.
# Use of this source code is governed by the Apache License 2.0
# that can be found in the LICENSE file.

"""Exec CLI helpers."""

from __future__ import annotations

import asyncio
import itertools
import json
import logging
import re
from pathlib import Path
from typing import TYPE_CHECKING, Any, Literal

from aioeapi import EapiCommandError
from click.exceptions import UsageError
from httpx import ConnectError, HTTPError

from anta.device import AntaDevice, AsyncEOSDevice
from anta.models import AntaCommand
from anta.platform_utils import SUPPORT_HARDWARE_COUNTERS_SERIES, find_series_by_model
from anta.tools.get_item import get_item

if TYPE_CHECKING:
    from anta.inventory import AntaInventory

EOS_SCHEDULED_TECH_SUPPORT = "/mnt/flash/schedule/tech-support"
INVALID_CHAR = "`~!@#$/"
logger = logging.getLogger(__name__)


async def clear_counters_utils(anta_inventory: AntaInventory, tags: list[str] | None = None) -> None:
    """Clear counters on the devices in the inventory.

    If the device is part of a series that supports hardware counters, the hardware counters are also cleared.

    Arguments:
    ----------
      anta_inventory (AntaInventory): The ANTA inventory object containing the devices to connect to.
      tags (list[str] | None): A list of tags to filter the devices to connect to.

    """
    # Commands to clear counters. Can be used later to add more commands if needed.
    clear_counters_commands: list[dict[str, Any]] = [
        {
            "command": "clear counters",
            "is_cleared": False,
            "restricted_series": None,
        },
        {
            "command": "clear hardware counter drop",
            "is_cleared": False,
            "restricted_series": SUPPORT_HARDWARE_COUNTERS_SERIES,
        },
    ]

    async def clear(device: AntaDevice) -> None:
        if not isinstance(device.hw_model, str):
            logger.error("Could not clear counters on device %s because its hardware model is not set or invalid.", device.name)
            return

        model_series = find_series_by_model(device.hw_model)
        commands = [
            AntaCommand(command=command["command"])
            for command in clear_counters_commands
            if not command["restricted_series"] or model_series in command["restricted_series"]
        ]

        await device.collect_commands(commands=commands)

        for command in commands:
            if device.supports(command, log=False) and not command.collected:
                logger.error("Could not '%s' on device %s: %s", command.command, device.name, command.errors)
            else:
                get_item(clear_counters_commands, "command", command.command)["is_cleared"] = True

        # Log if any counters have been cleared
        if any(cmd["is_cleared"] for cmd in clear_counters_commands):
            logger.info("Cleared counters on %s (%s)", device.name, device.hw_model)

    logger.info("Connecting to devices...")
    await anta_inventory.connect_inventory()
    devices = anta_inventory.get_inventory(established_only=True, tags=tags).values()
    logger.info("Clearing counters on remote devices...")
    await asyncio.gather(*(clear(device) for device in devices))


async def collect_commands(
    inv: AntaInventory,
    commands: dict[str, str],
    root_dir: Path,
    tags: list[str] | None = None,
) -> None:
    """Collect EOS commands."""

    async def collect(dev: AntaDevice, command: str, outformat: Literal["json", "text"]) -> None:
        outdir = Path() / root_dir / dev.name / outformat
        outdir.mkdir(parents=True, exist_ok=True)
        safe_command = re.sub(r"(/|\|$)", "_", command)
        c = AntaCommand(command=command, ofmt=outformat)
        await dev.collect(c)
        if not c.collected:
            logger.error("Could not collect commands on device %s: %s", dev.name, c.errors)
            return
        if c.ofmt == "json":
            outfile = outdir / f"{safe_command}.json"
            content = json.dumps(c.json_output, indent=2)
        elif c.ofmt == "text":
            outfile = outdir / f"{safe_command}.log"
            content = c.text_output
        with outfile.open(mode="w", encoding="UTF-8") as f:
            f.write(content)
        logger.info("Collected command '%s' from device %s (%s)", command, dev.name, dev.hw_model)

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
            logger.error("Error when collecting commands: %s", str(r))


async def collect_scheduled_show_tech(inv: AntaInventory, root_dir: Path, *, configure: bool, tags: list[str] | None = None, latest: int | None = None) -> None:
    """Collect scheduled show-tech on devices."""

    async def collect(device: AntaDevice) -> None:
        """Collect all the tech-support files stored on Arista switches flash and copy them locally."""
        try:
            # Get the tech-support filename to retrieve
            cmd = f"bash timeout 10 ls -1t {EOS_SCHEDULED_TECH_SUPPORT}"
            if latest:
                cmd += f" | head -{latest}"
            command = AntaCommand(command=cmd, ofmt="text")
            await device.collect(command=command)
            if command.collected and command.text_output:
                filenames = [Path(f"{EOS_SCHEDULED_TECH_SUPPORT}/{f}") for f in command.text_output.splitlines()]
            else:
                logger.error("Unable to get tech-support filenames on %s: verify that %s is not empty", device.name, EOS_SCHEDULED_TECH_SUPPORT)
                return

            # Create directories
            outdir = Path() / root_dir / f"{device.name.lower()}"
            outdir.mkdir(parents=True, exist_ok=True)

            # Check if 'aaa authorization exec default local' is present in the running-config
            command = AntaCommand(command="show running-config | include aaa authorization exec default", ofmt="text")
            await device.collect(command=command)

            if command.collected and not command.text_output:
                logger.debug("'aaa authorization exec default local' is not configured on device %s", device.name)
                if configure:
                    commands = []
                    # TODO: @mtache - add `config` field to `AntaCommand` object to handle this use case.
                    # Otherwise mypy complains about enable as it is only implemented for AsyncEOSDevice
                    # TODO: Should enable be also included in AntaDevice?
                    if not isinstance(device, AsyncEOSDevice):
                        msg = "anta exec collect-tech-support is only supported with AsyncEOSDevice for now."
                        raise UsageError(msg)
                    if device.enable and device._enable_password is not None:  # pylint: disable=protected-access
                        commands.append({"cmd": "enable", "input": device._enable_password})  # pylint: disable=protected-access
                    elif device.enable:
                        commands.append({"cmd": "enable"})
                    commands.extend(
                        [
                            {"cmd": "configure terminal"},
                            {"cmd": "aaa authorization exec default local"},
                        ],
                    )
                    logger.warning("Configuring 'aaa authorization exec default local' on device %s", device.name)
                    command = AntaCommand(command="show running-config | include aaa authorization exec default local", ofmt="text")
                    await device._session.cli(commands=commands)  # pylint: disable=protected-access
                    logger.info("Configured 'aaa authorization exec default local' on device %s", device.name)
                else:
                    logger.error("Unable to collect tech-support on %s: configuration 'aaa authorization exec default local' is not present", device.name)
                    return
            logger.debug("'aaa authorization exec default local' is already configured on device %s", device.name)

            await device.copy(sources=filenames, destination=outdir, direction="from")
            logger.info("Collected %s scheduled tech-support from %s", len(filenames), device.name)

        except (EapiCommandError, HTTPError, ConnectError) as e:
            logger.error("Unable to collect tech-support on %s: %s", device.name, str(e))

    logger.info("Connecting to devices...")
    await inv.connect_inventory()
    devices = inv.get_inventory(established_only=True, tags=tags).values()
    await asyncio.gather(*(collect(device) for device in devices))
