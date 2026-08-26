# Copyright (c) 2026 Arista Networks, Inc.
# Use of this source code is governed by the Apache License 2.0
# that can be found in the LICENSE file.
"""Unit tests for security advisory reporting helpers."""

from __future__ import annotations

import pytest

from anta._advisory.reporting import validate_advisory_results
from anta.result_manager.models import TestResult as AntaTestResult
from anta.result_manager.models import TestResultMetadata as AntaTestResultMetadata
from tests.units._advisory.conftest import ADVISORY


def test_validate_advisory_results() -> None:
    """Verify advisory results are returned with their typed metadata."""
    result = AntaTestResult(
        name="leaf1",
        test="VerifyAdvisory",
        categories=["advisories"],
        description="Verify an advisory.",
        metadata=AntaTestResultMetadata(security_advisory=ADVISORY),
    )

    assert validate_advisory_results([result]) == [(result, ADVISORY)]


def test_validate_advisory_results_rejects_empty_results() -> None:
    """Verify an advisory report cannot be generated without results."""
    with pytest.raises(ValueError, match="at least one test result"):
        validate_advisory_results([])


def test_validate_advisory_results_rejects_mixed_results() -> None:
    """Verify ordinary results cannot be included in an advisory report."""
    result = AntaTestResult(name="leaf1", test="VerifyNTP", categories=["ntp"], description="Verify NTP.")

    with pytest.raises(ValueError, match="leaf1/VerifyNTP"):
        validate_advisory_results([result])
