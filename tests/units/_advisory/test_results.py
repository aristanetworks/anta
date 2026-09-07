# Copyright (c) 2026 Arista Networks, Inc.
# Use of this source code is governed by the Apache License 2.0
# that can be found in the LICENSE file.
"""Unit tests for private security advisory result models."""

from __future__ import annotations

import copy
import json
import pickle
from typing import TYPE_CHECKING

import pytest

from anta._advisory.base import _AntaAdvisoryTest
from anta._advisory.remediation import FixedRelease, RemediationGuidance, software_version_plan
from anta._advisory.results import (
    _AdvisoryAtomicTestResult,
    _get_advisory_metadata,
    _get_atomic_vulnerability_ids,
)
from anta._eos.version import EOSVersion
from anta.models import AntaTest
from anta.result_manager import ResultManager
from anta.result_manager.models import AntaTestStatus
from anta.result_manager.models import TestResult as AntaTestResult
from tests.units._advisory.conftest import ADVISORY
from tests.units._advisory.test_base import FakeAdvisoryTest

if TYPE_CHECKING:
    from anta.device import AntaDevice


def test_advisory_result_survives_result_manager_operations(device: AntaDevice) -> None:
    """Preserve advisory result identity and metadata through result manager operations."""
    advisory_result = FakeAdvisoryTest(device=device, eos_data=[{"version": "4.36.1F"}]).result
    remediation = software_version_plan((FixedRelease(EOSVersion(4, 36, 3, suffix="F")),), current_version=EOSVersion(4, 35, 1, suffix="F"))
    advisory_result.add("Issue", vulnerability_ids=("CVE-2026-0001",), remediation=remediation)
    ordinary_result = AntaTestResult(name="ordinary", test="VerifyNTP", categories=["ntp"], description="Verify NTP.")
    manager = ResultManager()
    manager.add(ordinary_result)
    manager.add(advisory_result)

    assert manager.results[1] is advisory_result
    assert _get_advisory_metadata(manager.results[1]) is ADVISORY
    atomic_result = advisory_result.atomic_results[0]
    assert isinstance(atomic_result, _AdvisoryAtomicTestResult)
    assert atomic_result.remediation == remediation
    manager.sort(["name"])
    sorted_advisory_result = next(result for result in manager.results if _get_advisory_metadata(result) is not None)
    assert sorted_advisory_result is advisory_result
    for derived_manager in (
        manager.filter(set()),
        ResultManager.merge_results([manager]),
    ):
        derived_advisory_result = next(result for result in derived_manager.results if _get_advisory_metadata(result) is not None)
        assert derived_advisory_result is advisory_result
        assert _get_advisory_metadata(derived_advisory_result) is ADVISORY
    for dumped_result in json.loads(manager.json):
        assert "advisory" not in dumped_result
        assert "metadata" not in dumped_result
        assert "remediation" not in dumped_result
        assert "remediation_guidance" not in dumped_result


def test_advisory_atomic_result_without_vulnerability_association(device: AntaDevice) -> None:
    """Treat omitted vulnerability IDs as an advisory-wide atomic result."""
    result = FakeAdvisoryTest(device=device, eos_data=[{"version": "4.36.1F"}]).result

    atomic_result = result.add("Advisory-wide check", status=AntaTestStatus.SUCCESS)

    assert isinstance(atomic_result, _AdvisoryAtomicTestResult)
    assert atomic_result.parent is result
    assert _get_atomic_vulnerability_ids(atomic_result) is None
    assert atomic_result.remediation is None
    assert not atomic_result.remediation_guidance
    assert result.result is AntaTestStatus.SUCCESS


def test_advisory_atomic_result_with_vulnerability_association(device: AntaDevice) -> None:
    """Associate an atomic result with a deterministic subset of advisory vulnerabilities."""
    result = FakeAdvisoryTest(device=device, eos_data=[{"version": "4.36.1F"}]).result

    atomic_result = result.add(
        "Vulnerability-specific check",
        vulnerability_ids=("CVE-2026-0002", "CVE-2026-0001"),
        remediation=software_version_plan((FixedRelease(EOSVersion(4, 36, 3, suffix="F")),), current_version=EOSVersion(4, 35, 1, suffix="F")),
        remediation_guidance=frozenset({RemediationGuidance.NEW_RELEASES}),
    )

    assert _get_atomic_vulnerability_ids(atomic_result) == ("CVE-2026-0001", "CVE-2026-0002")
    assert atomic_result.remediation == software_version_plan((FixedRelease(EOSVersion(4, 36, 3, suffix="F")),), current_version=EOSVersion(4, 35, 1, suffix="F"))
    assert atomic_result.remediation_guidance == frozenset({RemediationGuidance.NEW_RELEASES})


@pytest.mark.parametrize(
    ("vulnerability_ids", "message"),
    [
        pytest.param((), "at least one vulnerability ID", id="empty"),
        pytest.param(("CVE-2026-0001", "CVE-2026-0001"), "duplicate vulnerability IDs", id="duplicate"),
        pytest.param(("CVE-2026-9999",), "Unknown vulnerability IDs", id="unknown"),
    ],
)
def test_advisory_atomic_result_rejects_invalid_vulnerability_association(device: AntaDevice, vulnerability_ids: tuple[str, ...], message: str) -> None:
    """Reject invalid atomic-to-vulnerability associations."""
    result = FakeAdvisoryTest(device=device, eos_data=[{"version": "4.36.1F"}]).result

    with pytest.raises(ValueError, match=message):
        result.add("Invalid vulnerability association", vulnerability_ids=vulnerability_ids)


def test_advisory_result_copy_and_pickle(device: AntaDevice) -> None:
    """Preserve advisory metadata, vulnerability associations, and parent links across copies and pickle."""
    result = FakeAdvisoryTest(device=device, eos_data=[{"version": "4.36.1F"}]).result
    result.add("Vulnerability-specific check", vulnerability_ids=("CVE-2026-0001",))

    deep_copy = copy.deepcopy(result)
    assert _get_advisory_metadata(deep_copy) == ADVISORY
    assert _get_atomic_vulnerability_ids(deep_copy.atomic_results[0]) == ("CVE-2026-0001",)
    assert _get_advisory_metadata(deep_copy.atomic_results[0].parent) == ADVISORY

    for restored in (result.model_copy(deep=False), pickle.loads(pickle.dumps(result))):  # noqa: S301
        assert restored is not result
        assert _get_advisory_metadata(restored) == ADVISORY
        assert _get_atomic_vulnerability_ids(restored.atomic_results[0]) == ("CVE-2026-0001",)

    restored_from_pickle = pickle.loads(pickle.dumps(result))  # noqa: S301
    assert restored_from_pickle.atomic_results[0].parent is restored_from_pickle


def test_advisory_result_class_is_private_to_advisory_tests() -> None:
    """Keep ordinary tests on the core TestResult class."""
    assert _AntaAdvisoryTest._create_result is not AntaTest._create_result
    assert AntaTestResult.__private_attributes__ == {}
