# Copyright (c) 2023-2026 Arista Networks, Inc.
# Use of this source code is governed by the Apache License 2.0
# that can be found in the LICENSE file.
"""Arista bug database analysis engine.

Provides the ``BugDatabase`` class that orchestrates downloading/loading the
AlertBase-CVP.json database, resolving device tags, and matching bugs against
an ANTA inventory.
"""

from __future__ import annotations

import asyncio
import logging
from typing import TYPE_CHECKING

from anta.bugdb.matcher import match_bugs
from anta.bugdb.models import AlertBaseDatabase, DeviceBugReport
from anta.bugdb.tags import build_implication_graph, compile_query_rules, resolve_all_tags
from anta.bugdb.version import EOSVersion
from anta.models import AntaCommand

if TYPE_CHECKING:
    from anta.bugdb.aql import AqlNode
    from anta.device import AntaDevice
    from anta.inventory import AntaInventory

logger = logging.getLogger(__name__)


class BugDatabase:
    """High-level interface for bug database analysis.

    Orchestrates tag resolution, version comparison, and bug matching
    across an ANTA inventory.

    Parameters
    ----------
    db
        Parsed AlertBase database.
    """

    def __init__(self, db: AlertBaseDatabase) -> None:
        self._db = db
        self._eos_bugs = [b for b in db.bugs if b.product == "eos"]
        self._implication_graph = build_implication_graph(db.tag_implication)
        self._compiled_rules = compile_query_rules(list(db.query_rules_rev) + list(db.query_rules))
        logger.info(
            "Bug database loaded: %d EOS bugs, %d tag implications, %d AQL rules compiled",
            len(self._eos_bugs),
            len(db.tag_implication),
            len(self._compiled_rules),
        )

    @property
    def bug_count(self) -> int:
        """Number of EOS bugs in the database."""
        return len(self._eos_bugs)

    @property
    def compiled_rules(self) -> dict[str, tuple[AqlNode, list[str]]]:
        """Compiled AQL rules for tag resolution."""
        return self._compiled_rules

    async def analyze_device(
        self,
        device: AntaDevice,
        *,
        min_severity: str | None = None,
    ) -> DeviceBugReport:
        """Run full bug analysis for a single device.

        Parameters
        ----------
        device
            The ANTA device to analyze.
        min_severity
            Optional minimum severity filter.

        Returns
        -------
        DeviceBugReport
            Report containing all matching bugs for the device.
        """
        # Get EOS version from device
        eos_version_str = await self._get_device_version(device)
        if eos_version_str is None:
            logger.warning("Could not determine EOS version for %s, skipping", device.name)
            return DeviceBugReport(
                device_name=device.name,
                hw_model=device.hw_model or "unknown",
                eos_version="unknown",
            )

        try:
            device_version = EOSVersion(eos_version_str)
        except ValueError:
            logger.warning("Cannot parse EOS version '%s' for %s", eos_version_str, device.name)
            return DeviceBugReport(
                device_name=device.name,
                hw_model=device.hw_model or "unknown",
                eos_version=eos_version_str,
            )

        # Resolve all tags
        tags = await resolve_all_tags(device, self._implication_graph, self._compiled_rules)

        # Match bugs
        matches = match_bugs(self._eos_bugs, device_version, tags, min_severity=min_severity)

        return DeviceBugReport(
            device_name=device.name,
            hw_model=device.hw_model or "unknown",
            eos_version=eos_version_str,
            resolved_tags=tags,
            matching_bugs=matches,
        )

    async def analyze_inventory(
        self,
        inventory: AntaInventory,
        *,
        tags: set[str] | None = None,
        devices: tuple[str, ...] | None = None,
        min_severity: str | None = None,
    ) -> list[DeviceBugReport]:
        """Run bug analysis for all devices in an inventory.

        Parameters
        ----------
        inventory
            The ANTA inventory to analyze.
        tags
            Optional inventory tag filter.
        devices
            Optional device name filter.
        min_severity
            Optional minimum severity filter.

        Returns
        -------
        list[DeviceBugReport]
            Reports for all analyzed devices, sorted by device name.
        """
        # Connect inventory
        await inventory.connect_inventory()
        selected = inventory.get_inventory(tags=tags, established_only=True)

        # Filter by device names if specified
        device_list = list(selected.values())
        if devices:
            device_set = set(devices)
            device_list = [d for d in device_list if d.name in device_set]

        if not device_list:
            logger.warning("No established devices found in inventory")
            return []

        logger.info("Analyzing %d devices for %d EOS bugs", len(device_list), len(self._eos_bugs))

        # Analyze all devices concurrently
        reports = await asyncio.gather(
            *(self.analyze_device(d, min_severity=min_severity) for d in device_list),
        )

        return sorted(reports, key=lambda r: r.device_name)

    async def _get_device_version(self, device: AntaDevice) -> str | None:
        """Get the EOS version string from a device via show version."""
        cmd = AntaCommand(command="show version", revision=1)
        await device.collect_commands([cmd])
        if cmd.collected:
            return cmd.json_output.get("version")
        return None
