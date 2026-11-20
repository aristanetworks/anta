# Copyright (c) 2023-2026 Arista Networks, Inc.
# Use of this source code is governed by the Apache License 2.0
# that can be found in the LICENSE file.
"""Tests for anta.bugdb (BugDatabase class)."""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from anta.bugdb import BugDatabase
from anta.bugdb.models import AlertBaseDatabase, DeviceBugReport


def _make_bug(
    bug_id: int = 1,
    severity: str = "sev2",
    product: str = "eos",
    introduced: list[str] | None = None,
    fixed: list[str] | None = None,
) -> dict:
    """Create a raw bug dict for AlertBaseDatabase parsing."""
    return {
        "bugId": bug_id,
        "severity": severity,
        "alertSummary": f"Bug {bug_id}",
        "product": product,
        "versionIntroduced": introduced or ["4.20.0"],
        "versionFixed": fixed or ["4.25.0"],
    }


def _make_db(
    bugs: list[dict] | None = None,
    tag_implication: list[list[str]] | None = None,
) -> AlertBaseDatabase:
    """Create a minimal AlertBaseDatabase."""
    return AlertBaseDatabase.model_validate(
        {
            "bugs": bugs or [],
            "tagImplication": tag_implication or [],
            "queryRules": [],
            "queryRulesRev": [],
        }
    )


def _make_device(name: str = "device1", version: str | None = "4.22.0F", hw_model: str = "DCS-7050") -> MagicMock:
    """Create a mock AntaDevice."""
    device = MagicMock()
    device.name = name
    device.version = version
    device.hw_model = hw_model
    device.collect_commands = AsyncMock()
    return device


class TestBugDatabase:
    """Tests for the BugDatabase class."""

    def test_init_separates_products(self) -> None:
        """Test that __init__ separates EOS and TerminAttr bugs."""
        db = _make_db(
            bugs=[
                _make_bug(1, product="eos"),
                _make_bug(2, product="eos"),
                _make_bug(3, product="terminattr", introduced=["TerminAttr-v1.20.0"], fixed=["TerminAttr-v1.25.0"]),
            ]
        )
        bug_db = BugDatabase(db)
        assert bug_db.bug_count == 2
        assert bug_db.terminattr_bug_count == 1

    def test_init_no_terminattr(self) -> None:
        """Test init when no TerminAttr bugs exist."""
        db = _make_db(bugs=[_make_bug(1)])
        bug_db = BugDatabase(db)
        assert bug_db.bug_count == 1
        assert bug_db.terminattr_bug_count == 0


class TestAnalyzeDevice:
    """Tests for BugDatabase.analyze_device."""

    @pytest.mark.asyncio
    async def test_no_version(self) -> None:
        """Test analyze_device with no EOS version returns unknown."""
        db = _make_db(bugs=[_make_bug(1)])
        bug_db = BugDatabase(db)
        device = _make_device(version=None)
        report = await bug_db.analyze_device(device)
        assert report.eos_version == "unknown"
        assert not report.matching_bugs

    @pytest.mark.asyncio
    async def test_unparsable_version(self) -> None:
        """Test analyze_device with unparsable EOS version."""
        db = _make_db(bugs=[_make_bug(1)])
        bug_db = BugDatabase(db)
        device = _make_device(version="not-a-version")
        report = await bug_db.analyze_device(device)
        assert report.eos_version == "not-a-version"
        assert not report.matching_bugs

    @pytest.mark.asyncio
    async def test_matching_eos_bug(self) -> None:
        """Test analyze_device matches an EOS bug by version."""
        db = _make_db(bugs=[_make_bug(1, introduced=["4.20.0"], fixed=["4.25.0"])])
        bug_db = BugDatabase(db)
        device = _make_device(version="4.22.0F")
        with patch("anta.bugdb.resolve_all_tags", new_callable=AsyncMock, return_value=set()):
            report = await bug_db.analyze_device(device)
        assert len(report.matching_bugs) == 1
        assert report.matching_bugs[0].bug.bug_id == 1

    @pytest.mark.asyncio
    async def test_no_matching_bugs(self) -> None:
        """Test analyze_device when device version is not affected."""
        db = _make_db(bugs=[_make_bug(1, introduced=["4.20.0"], fixed=["4.21.0"])])
        bug_db = BugDatabase(db)
        device = _make_device(version="4.22.0F")
        with patch("anta.bugdb.resolve_all_tags", new_callable=AsyncMock, return_value=set()):
            report = await bug_db.analyze_device(device)
        assert not report.matching_bugs

    @pytest.mark.asyncio
    async def test_terminattr_matching(self) -> None:
        """Test analyze_device matches TerminAttr bugs."""
        db = _make_db(
            bugs=[
                _make_bug(1, product="eos", introduced=["4.20.0"], fixed=["4.25.0"]),
                _make_bug(2, product="terminattr", introduced=["TerminAttr-v1.20.0"], fixed=["TerminAttr-v1.30.0"]),
            ]
        )
        bug_db = BugDatabase(db)
        device = _make_device(version="4.22.0F")

        async def mock_collect(cmds: list) -> None:
            cmds[0].output = {"details": {"packages": {"TerminAttr-core": {"version": "v1.25.0"}}}}

        device.collect_commands = AsyncMock(side_effect=mock_collect)

        with patch("anta.bugdb.resolve_all_tags", new_callable=AsyncMock, return_value=set()):
            report = await bug_db.analyze_device(device)

        assert report.terminattr_version == "v1.25.0"
        assert len(report.matching_bugs) == 2

    @pytest.mark.asyncio
    async def test_terminattr_version_fetch_failure(self) -> None:
        """Test analyze_device gracefully handles TerminAttr version fetch failure."""
        db = _make_db(
            bugs=[
                _make_bug(1, product="terminattr", introduced=["TerminAttr-v1.20.0"], fixed=["TerminAttr-v1.30.0"]),
            ]
        )
        bug_db = BugDatabase(db)
        device = _make_device(version="4.22.0F")

        # Command fails (collected stays False)
        device.collect_commands = AsyncMock()

        with patch("anta.bugdb.resolve_all_tags", new_callable=AsyncMock, return_value=set()):
            report = await bug_db.analyze_device(device)

        assert report.terminattr_version == ""
        # Only EOS matching runs, TA bugs not matched
        assert not report.matching_bugs

    @pytest.mark.asyncio
    async def test_terminattr_version_unparsable(self) -> None:
        """Test analyze_device handles unparsable TerminAttr version."""
        db = _make_db(
            bugs=[
                _make_bug(1, product="terminattr", introduced=["TerminAttr-v1.20.0"], fixed=["TerminAttr-v1.30.0"]),
            ]
        )
        bug_db = BugDatabase(db)
        device = _make_device(version="4.22.0F")

        async def mock_collect(cmds: list) -> None:
            cmds[0].output = {"details": {"packages": {"TerminAttr-core": {"version": "bad-version"}}}}

        device.collect_commands = AsyncMock(side_effect=mock_collect)

        with patch("anta.bugdb.resolve_all_tags", new_callable=AsyncMock, return_value=set()):
            report = await bug_db.analyze_device(device)

        assert report.terminattr_version == "bad-version"
        assert not report.matching_bugs

    @pytest.mark.asyncio
    async def test_terminattr_missing_package(self) -> None:
        """Test analyze_device when TerminAttr-core package is missing from show version detail."""
        db = _make_db(
            bugs=[
                _make_bug(1, product="terminattr", introduced=["TerminAttr-v1.20.0"], fixed=["TerminAttr-v1.30.0"]),
            ]
        )
        bug_db = BugDatabase(db)
        device = _make_device(version="4.22.0F")

        async def mock_collect(cmds: list) -> None:
            cmds[0].output = {"details": {"packages": {}}}

        device.collect_commands = AsyncMock(side_effect=mock_collect)

        with patch("anta.bugdb.resolve_all_tags", new_callable=AsyncMock, return_value=set()):
            report = await bug_db.analyze_device(device)

        assert report.terminattr_version == ""
        assert not report.matching_bugs


class TestAnalyzeInventory:
    """Tests for BugDatabase.analyze_inventory."""

    @pytest.mark.asyncio
    async def test_no_established_devices(self) -> None:
        """Test analyze_inventory with no established devices."""
        db = _make_db(bugs=[_make_bug(1)])
        bug_db = BugDatabase(db)
        inventory = MagicMock()
        inventory.connect_inventory = AsyncMock()
        inventory.get_inventory.return_value = {}

        reports = await bug_db.analyze_inventory(inventory)
        assert reports == []

    @pytest.mark.asyncio
    async def test_single_device(self) -> None:
        """Test analyze_inventory with a single device."""
        db = _make_db(bugs=[_make_bug(1, introduced=["4.20.0"], fixed=["4.25.0"])])
        bug_db = BugDatabase(db)

        device = _make_device()
        inventory = MagicMock()
        inventory.connect_inventory = AsyncMock()
        inventory.get_inventory.return_value = {"device1": device}

        with patch("anta.bugdb.resolve_all_tags", new_callable=AsyncMock, return_value=set()):
            reports = await bug_db.analyze_inventory(inventory)

        assert len(reports) == 1
        assert reports[0].device_name == "device1"
        assert len(reports[0].matching_bugs) == 1

    @pytest.mark.asyncio
    async def test_device_filter(self) -> None:
        """Test analyze_inventory filters by device name."""
        db = _make_db(bugs=[_make_bug(1, introduced=["4.20.0"], fixed=["4.25.0"])])
        bug_db = BugDatabase(db)

        device1 = _make_device(name="dev1")
        device2 = _make_device(name="dev2")
        inventory = MagicMock()
        inventory.connect_inventory = AsyncMock()
        inventory.get_inventory.return_value = {"dev1": device1, "dev2": device2}

        with patch("anta.bugdb.resolve_all_tags", new_callable=AsyncMock, return_value=set()):
            reports = await bug_db.analyze_inventory(inventory, devices=("dev1",))

        assert len(reports) == 1
        assert reports[0].device_name == "dev1"

    @pytest.mark.asyncio
    async def test_per_device_failure_isolation(self) -> None:
        """Test that a per-device exception doesn't fail the whole inventory."""
        db = _make_db(bugs=[_make_bug(1, introduced=["4.20.0"], fixed=["4.25.0"])])
        bug_db = BugDatabase(db)

        device1 = _make_device(name="dev1")
        device2 = _make_device(name="dev2")
        inventory = MagicMock()
        inventory.connect_inventory = AsyncMock()
        inventory.get_inventory.return_value = {"dev1": device1, "dev2": device2}

        def mock_analyze(device: MagicMock, **_kwargs: object) -> DeviceBugReport:
            if device.name == "dev1":
                msg = "Connection failed"
                raise RuntimeError(msg)
            return DeviceBugReport(device_name=device.name, hw_model="DCS-7050", eos_version="4.22.0F")

        with (
            patch("anta.bugdb.resolve_all_tags", new_callable=AsyncMock, return_value=set()),
            patch.object(bug_db, "analyze_device", side_effect=mock_analyze),
        ):
            reports = await bug_db.analyze_inventory(inventory)

        assert len(reports) == 2
        dev1_report = next(r for r in reports if r.device_name == "dev1")
        assert dev1_report.eos_version == "unknown"
        dev2_report = next(r for r in reports if r.device_name == "dev2")
        assert dev2_report.device_name == "dev2"

    @pytest.mark.asyncio
    async def test_results_sorted_by_name(self) -> None:
        """Test that results are sorted by device name."""
        db = _make_db(bugs=[])
        bug_db = BugDatabase(db)

        device_z = _make_device(name="z-switch")
        device_a = _make_device(name="a-switch")
        inventory = MagicMock()
        inventory.connect_inventory = AsyncMock()
        inventory.get_inventory.return_value = {"z": device_z, "a": device_a}

        with patch("anta.bugdb.resolve_all_tags", new_callable=AsyncMock, return_value=set()):
            reports = await bug_db.analyze_inventory(inventory)

        assert [r.device_name for r in reports] == ["a-switch", "z-switch"]

    @pytest.mark.asyncio
    async def test_terminattr_summary_logged(self) -> None:
        """Test that log includes TerminAttr bug count when present."""
        db = _make_db(
            bugs=[
                _make_bug(1, product="eos"),
                _make_bug(2, product="terminattr", introduced=["TerminAttr-v1.20.0"], fixed=["TerminAttr-v1.30.0"]),
            ]
        )
        bug_db = BugDatabase(db)

        device = _make_device()
        inventory = MagicMock()
        inventory.connect_inventory = AsyncMock()
        inventory.get_inventory.return_value = {"device1": device}

        with (
            patch("anta.bugdb.resolve_all_tags", new_callable=AsyncMock, return_value=set()),
            patch("anta.bugdb.logger") as mock_logger,
        ):
            await bug_db.analyze_inventory(inventory)

        mock_logger.info.assert_called_once()
        log_msg = mock_logger.info.call_args[0][0] % mock_logger.info.call_args[0][1:]
        assert "1 EOS bugs" in log_msg
        assert "1 TerminAttr bugs" in log_msg
