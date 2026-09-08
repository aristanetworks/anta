# Copyright (c) 2026 Arista Networks, Inc.
# Use of this source code is governed by the Apache License 2.0
# that can be found in the LICENSE file.
"""Fixtures and constants for ANTA security advisory unit tests."""

from __future__ import annotations

from datetime import date, datetime, timezone
from typing import TYPE_CHECKING
from unittest.mock import MagicMock

import pytest

from anta._advisory.models import (
    _AdvisoryMetadata,
    _AdvisoryVulnerability,
    _AdvisoryVulnerabilitySeverity,
)
from anta._runner import AntaRunContext, AntaRunFilters

if TYPE_CHECKING:
    from anta._advisory.reporter.reporting import SecurityAdvisoryReport

ADVISORY = _AdvisoryMetadata(
    sa_number="0001",
    title="Test advisory",
    last_updated=date(2026, 1, 1),
    vulnerabilities=(
        _AdvisoryVulnerability(
            id="CVE-2026-0001",
            severity=_AdvisoryVulnerabilitySeverity.MEDIUM,
            description="Test vulnerability affecting the management API.",
        ),
        _AdvisoryVulnerability(
            id="CVE-2026-0002",
            severity=_AdvisoryVulnerabilitySeverity.HIGH,
            description="Test vulnerability affecting access controls.",
        ),
    ),
    url="https://example.com/advisory",
    description="Test advisory description.",
)

ADVISORY_ANTA_VERSION = "v1.4.0"
ADVISORY_RUN_START_TIME = datetime(2025, 5, 20, 8, 30, 0, tzinfo=timezone.utc)
ADVISORY_RUN_END_TIME = datetime(2025, 5, 20, 8, 35, 30, 500000, tzinfo=timezone.utc)
ADVISORY_RUN_START_TIME_FORMATTED = "2025-05-20 08:30:00.000+00:00"
ADVISORY_RUN_END_TIME_FORMATTED = "2025-05-20 08:35:30.500+00:00"
ADVISORY_RUN_DURATION_FORMATTED = "5 minutes, 30 seconds"
ADVISORY_RUN_FILTERS = AntaRunFilters(tags={"spine"})
ADVISORY_RUN_DEVICES_UNREACHABLE = ["s1-spine2"]
ADVISORY_RUN_DEVICES_FILTERED = ["s1-leaf1", "s1-leaf2"]


@pytest.fixture(autouse=True)
def _advisory_anta_version(monkeypatch: pytest.MonkeyPatch) -> None:
    """Use a fixed ANTA version in advisory report tests."""
    monkeypatch.setattr("anta.__version__", ADVISORY_ANTA_VERSION)


def build_security_advisory_run_context(
    report: SecurityAdvisoryReport,
    *,
    inventory_size: int = 1,
    filters: AntaRunFilters | None = None,
    start_time: datetime = ADVISORY_RUN_START_TIME,
    end_time: datetime = ADVISORY_RUN_END_TIME,
    devices_unreachable_at_setup: list[str] | None = None,
    devices_filtered_at_setup: list[str] | None = None,
) -> AntaRunContext:
    """Build a run context with realistic execution metadata for advisory report tests."""
    inventory = MagicMock()
    inventory.__len__ = MagicMock(return_value=inventory_size)
    return AntaRunContext(
        inventory=inventory,
        catalog=MagicMock(),
        manager=report.source,
        filters=filters or AntaRunFilters(),
        start_time=start_time,
        end_time=end_time,
        devices_unreachable_at_setup=devices_unreachable_at_setup or [],
        devices_filtered_at_setup=devices_filtered_at_setup or [],
    )


def build_fleet_security_advisory_run_context(report: SecurityAdvisoryReport) -> AntaRunContext:
    """Build a run context for multi-advisory fleet report tests."""
    return build_security_advisory_run_context(
        report,
        inventory_size=8,
        filters=ADVISORY_RUN_FILTERS,
        devices_unreachable_at_setup=ADVISORY_RUN_DEVICES_UNREACHABLE,
        devices_filtered_at_setup=ADVISORY_RUN_DEVICES_FILTERED,
    )
