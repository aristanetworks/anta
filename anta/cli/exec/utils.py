# Copyright (c) 2023-2025 Arista Networks, Inc.
# Use of this source code is governed by the Apache License 2.0
# that can be found in the LICENSE file.

"""Exec CLI helpers."""

from __future__ import annotations

import asyncio
import itertools
import json
import logging
from pathlib import Path
from typing import TYPE_CHECKING, Any, Literal

from asyncssh.misc import HostKeyNotVerifiable
from click.exceptions import UsageError
from httpx import ConnectError, HTTPError

from anta.device import AntaDevice, AsyncEOSDevice
from anta.models import AntaCommand
from anta.tools import safe_command
from asynceapi import EapiCommandError

if TYPE_CHECKING:
    from collections.abc import Coroutine

    from anta.inventory import AntaInventory
    from asynceapi._types import EapiComplexCommand, EapiSimpleCommand

EOS_SCHEDULED_TECH_SUPPORT = "/mnt/flash/schedule/tech-support"
INVALID_CHAR = "`~!@#$/"
logger = logging.getLogger(__name__)


async def clear_counters(anta_inventory: AntaInventory, tags: set[str] | None = None) -> None:
    """Clear counters."""

    async def clear(dev: AntaDevice) -> None:
        commands = [AntaCommand(command="clear counters")]
        if dev.hw_model not in ["cEOSLab", "vEOS-lab"]:
            commands.append(AntaCommand(command="clear hardware counter drop"))
        await dev.collect_commands(commands=commands)
        for command in commands:
            if not command.collected:
                logger.error("Could not clear counters on device %s: %s", dev.name, command.errors)
        logger.info("Cleared counters on %s (%s)", dev.name, dev.hw_model)

    logger.info("Connecting to devices...")
    await anta_inventory.connect_inventory()
    devices = anta_inventory.get_inventory(established_only=True, tags=tags).devices
    logger.info("Clearing counters on remote devices...")
    _ = await asyncio.gather(*(clear(device) for device in devices))


async def collect_commands(
    inv: AntaInventory,
    commands: dict[str, list[str]],
    root_dir: Path,
    tags: set[str] | None = None,
) -> None:
    """Collect EOS commands."""

    async def collect(dev: AntaDevice, command: str, outformat: Literal["json", "text"]) -> None:
        outdir = Path() / root_dir / dev.name / outformat
        outdir.mkdir(parents=True, exist_ok=True)
        c = AntaCommand(command=command, ofmt=outformat)
        await dev.collect(c)
        if not c.collected:
            logger.error("Could not collect commands on device %s: %s", dev.name, c.errors)
            return
        if c.ofmt == "json":
            outfile = outdir / f"{safe_command(command)}.json"
            content = json.dumps(c.json_output, indent=2)
        elif c.ofmt == "text":
            outfile = outdir / f"{safe_command(command)}.log"
            content = c.text_output
        else:
            logger.error("Command outformat is not in ['json', 'text'] for command '%s'", command)
            return
        with outfile.open(mode="w", encoding="UTF-8") as f:
            _ = f.write(content)
        logger.info("Collected command '%s' from device %s (%s)", command, dev.name, dev.hw_model)

    logger.info("Connecting to devices...")
    await inv.connect_inventory()
    devices = inv.get_inventory(established_only=True, tags=tags).devices
    if not devices:
        logger.info("No online device found. Exiting")
        return
    logger.info("Collecting commands from remote devices")
    coros: list[Coroutine[Any, Any, None]] = []
    if "json_format" in commands:
        coros += [collect(device, command, "json") for device, command in itertools.product(devices, commands["json_format"])]
    if "text_format" in commands:
        coros += [collect(device, command, "text") for device, command in itertools.product(devices, commands["text_format"])]
    res = await asyncio.gather(*coros, return_exceptions=True)
    for r in res:
        if isinstance(r, Exception):
            logger.error("Error when collecting commands: %s", str(r))


async def collect_show_tech(inv: AntaInventory, root_dir: Path, *, configure: bool, tags: set[str] | None = None, latest: int | None = None) -> None:  # noqa: C901
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
            if not (command.collected and command.text_output):
                logger.error("Unable to get tech-support filenames on %s: verify that %s is not empty", device.name, EOS_SCHEDULED_TECH_SUPPORT)
                return

            filenames = [Path(f"{EOS_SCHEDULED_TECH_SUPPORT}/{f}") for f in command.text_output.splitlines()]

            # Create directories
            outdir = Path() / root_dir / f"{device.name.lower()}"
            outdir.mkdir(parents=True, exist_ok=True)

            # Check if 'aaa authorization exec default local' is present in the running-config
            command = AntaCommand(command="show running-config | include aaa authorization exec default", ofmt="text")
            await device.collect(command=command)

            if command.collected and not command.text_output:
                logger.debug("'aaa authorization exec default local' is not configured on device %s", device.name)
                if not configure:
                    logger.error("Unable to collect tech-support on %s: configuration 'aaa authorization exec default local' is not present", device.name)
                    return

                # TODO: ANTA 2.0.0
                msg = (
                    "[DEPRECATED] Using '--configure' for collecting show-techs is deprecated and will be removed in ANTA 2.0.0. "
                    "Please add the required configuration on your devices before running this command from ANTA."
                )
                logger.warning(msg)

                # TODO: @mtache - add `config` field to `AntaCommand` object to handle this use case.
                # Otherwise mypy complains about enable as it is only implemented for AsyncEOSDevice
                # TODO: Should enable be also included in AntaDevice?
                if not isinstance(device, AsyncEOSDevice):
                    msg = "anta exec collect-tech-support is only supported with AsyncEOSDevice for now."
                    raise UsageError(msg)
                commands: list[EapiSimpleCommand | EapiComplexCommand] = []
                if device.enable and device._enable_password is not None:
                    commands.append({"cmd": "enable", "input": device._enable_password})
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
                await device._session.cli(commands=commands)
                logger.info("Configured 'aaa authorization exec default local' on device %s", device.name)

            logger.debug("'aaa authorization exec default local' is already configured on device %s", device.name)

            await device.copy(sources=filenames, destination=outdir, direction="from")
            logger.info("Collected %s scheduled tech-support from %s", len(filenames), device.name)

        except HostKeyNotVerifiable:
            logger.error(
                "Unable to collect tech-support on %s. The host SSH key could not be verified. Make sure it is part of the `known_hosts` file on your machine.",
                device.name,
            )
        except (EapiCommandError, HTTPError, ConnectError) as e:
            logger.error("Unable to collect tech-support on %s: %s", device.name, str(e))

    logger.info("Connecting to devices...")
    await inv.connect_inventory()
    devices = inv.get_inventory(established_only=True, tags=tags).devices
    await asyncio.gather(*(collect(device) for device in devices))
