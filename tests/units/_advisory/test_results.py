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
from anta._advisory.facts.eos import EosVersionFact
from anta._advisory.facts.models import FactSource, FactSourceKind
from anta._advisory.findings.models import AffectedEosRelease, AffectedResult, EosReleaseAssessment, NotAffectedResult, VersionRelation
from anta._advisory.remediation import software_version_plan
from anta._advisory.reporter.reporting import validate_advisory_results
from anta._advisory.results import (
    _AdvisoryAtomicTestResult,
    _get_advisory_metadata,
    _get_atomic_vulnerability_id,
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


def test_advisory_test_starts_without_atomic_results(device: AntaDevice) -> None:
    """Create vulnerability atomics lazily when assessment or lifecycle outcomes exist."""
    result = FakeAdvisoryTest(device=device, eos_data=[{"version": "4.36.1F"}]).result

    assert not result.atomic_results


def test_advisory_result_survives_result_manager_operations(device: AntaDevice) -> None:
    """Preserve advisory result identity and metadata through result manager operations."""
    advisory_result = FakeAdvisoryTest(device=device, eos_data=[{"version": "4.36.1F"}]).result
    atomic = advisory_result.add("Issue", vulnerability_id="CVE-2026-0001")
    eos = EosVersionFact.available(EOSVersion(4, 36, 1, suffix="F"), FactSource("device metadata", FactSourceKind.DEVICE_METADATA))
    finding = NotAffectedResult(vulnerability_id="CVE-2026-0001", decisive=(EosReleaseAssessment(eos, VersionRelation.OUTSIDE_SCOPE),))
    atomic.set_finding(finding)
    ordinary_result = AntaTestResult(name="ordinary", test="VerifyNTP", categories=["ntp"], description="Verify NTP.")
    manager = ResultManager()
    manager.add(ordinary_result)
    manager.add(advisory_result)

    assert manager.results[1] is advisory_result
    assert _get_advisory_metadata(manager.results[1]) is ADVISORY
    atomic_result = advisory_result.atomic_results[0]
    assert isinstance(atomic_result, _AdvisoryAtomicTestResult)
    assert atomic_result.finding is finding
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
        assert "finding" not in dumped_result
        assert "remediation" not in dumped_result
        assert "remediation_guidance" not in dumped_result


def test_advisory_atomic_result_with_vulnerability_association(device: AntaDevice) -> None:
    """Associate an atomic result with one advisory vulnerability."""
    result = FakeAdvisoryTest(device=device, eos_data=[{"version": "4.36.1F"}]).result

    atomic_result = result.add("Vulnerability-specific check", vulnerability_id="CVE-2026-0002")

    assert _get_atomic_vulnerability_id(atomic_result) == "CVE-2026-0002"
    assert atomic_result.finding is None


def test_advisory_atomic_result_retains_one_finding(device: AntaDevice) -> None:
    """Retain the exact finding object once and expose findings from the parent in insertion order."""
    result = FakeAdvisoryTest(device=device, eos_data=[{"version": "4.36.1F"}]).result
    eos = EosVersionFact.available(EOSVersion(4, 36, 1, suffix="F"), FactSource("device metadata", FactSourceKind.DEVICE_METADATA))
    first = NotAffectedResult(vulnerability_id="CVE-2026-0001", decisive=(EosReleaseAssessment(eos, VersionRelation.OUTSIDE_SCOPE),))
    second = NotAffectedResult(vulnerability_id="CVE-2026-0002", decisive=(EosReleaseAssessment(eos, VersionRelation.OUTSIDE_SCOPE),))
    first_atomic = result.add("First", vulnerability_id=first.vulnerability_id)
    second_atomic = result.add("Second", vulnerability_id=second.vulnerability_id)

    first_atomic.set_finding(first)
    second_atomic.set_finding(second)

    assert first_atomic.finding is first
    assert result.findings == (first, second)
    with pytest.raises(ValueError, match="only retain one"):
        first_atomic.set_finding(first)


def test_advisory_atomic_result_derives_remediation_from_finding(device: AntaDevice) -> None:
    """Expose remediation as a derived property without copying it onto the atomic result."""
    result = FakeAdvisoryTest(device=device, eos_data=[{"version": "4.36.1F"}]).result
    eos = EosVersionFact.available(EOSVersion(4, 36, 1, suffix="F"), FactSource("device metadata", FactSourceKind.DEVICE_METADATA))
    assessment = AffectedEosRelease(eos)
    remediation = software_version_plan((), current_version=eos.value)
    finding = AffectedResult(vulnerability_id="CVE-2026-0001", conditions=(assessment,), remediation=remediation)
    atomic = result.add("Affected", vulnerability_id=finding.vulnerability_id)

    assert atomic.remediation is None
    atomic.set_finding(finding)

    assert atomic.remediation is remediation


def test_advisory_parent_failure_is_a_reportable_lifecycle_result(device: AntaDevice) -> None:
    """Preserve parent-only failures produced by core command handling."""
    result = FakeAdvisoryTest(device=device, eos_data=[{"version": "4.36.1F"}]).result

    result.is_failure("Failure without a structured finding.")

    assert result.result is AntaTestStatus.FAILURE
    assert result.messages == ["Failure without a structured finding."]
    assert not result.atomic_results
    assert validate_advisory_results([result]) == [(result, ADVISORY)]


@pytest.mark.parametrize("status", [AntaTestStatus.FAILURE, AntaTestStatus.ERROR, AntaTestStatus.SKIPPED])
def test_lifecycle_status_does_not_create_assessment_atomics(device: AntaDevice, status: AntaTestStatus) -> None:
    """Keep lifecycle outcomes on the parent result for expansion by reporting."""
    result = FakeAdvisoryTest(device=device, eos_data=[{"version": "4.36.1F"}]).result
    result.advisory = ADVISORY.model_copy(update={"vulnerabilities": ()})

    result._set_status(status, "Lifecycle message.")

    assert result.result is status
    assert result.messages == ["Lifecycle message."]
    assert not result.atomic_results


def test_advisory_atomic_result_rejects_unknown_vulnerability_association(device: AntaDevice) -> None:
    """Reject invalid atomic-to-vulnerability associations."""
    result = FakeAdvisoryTest(device=device, eos_data=[{"version": "4.36.1F"}]).result

    with pytest.raises(ValueError, match="Unknown vulnerability ID"):
        result.add("Invalid vulnerability association", vulnerability_id="CVE-2026-9999")


def test_advisory_result_copy_and_pickle(device: AntaDevice) -> None:
    """Preserve advisory metadata, vulnerability associations, and parent links across copies and pickle."""
    result = FakeAdvisoryTest(device=device, eos_data=[{"version": "4.36.1F"}]).result
    atomic = result.add("Vulnerability-specific check", vulnerability_id="CVE-2026-0001")
    eos = EosVersionFact.available(EOSVersion(4, 36, 1, suffix="F"), FactSource("device metadata", FactSourceKind.DEVICE_METADATA))
    finding = NotAffectedResult(vulnerability_id="CVE-2026-0001", decisive=(EosReleaseAssessment(eos, VersionRelation.OUTSIDE_SCOPE),))
    atomic.set_finding(finding)

    deep_copy = copy.deepcopy(result)
    assert _get_advisory_metadata(deep_copy) == ADVISORY
    deep_copy_atomic = deep_copy.atomic_results[0]
    assert isinstance(deep_copy_atomic, _AdvisoryAtomicTestResult)
    assert _get_atomic_vulnerability_id(deep_copy_atomic) == "CVE-2026-0001"
    assert deep_copy_atomic.finding == finding
    assert _get_advisory_metadata(deep_copy_atomic.parent) == ADVISORY

    for restored in (result.model_copy(deep=False), pickle.loads(pickle.dumps(result))):  # noqa: S301
        assert restored is not result
        assert _get_advisory_metadata(restored) == ADVISORY
        assert _get_atomic_vulnerability_id(restored.atomic_results[0]) == "CVE-2026-0001"

    restored_from_pickle = pickle.loads(pickle.dumps(result))  # noqa: S301
    assert restored_from_pickle.atomic_results[0].parent is restored_from_pickle


def test_advisory_result_class_is_private_to_advisory_tests() -> None:
    """Keep ordinary tests on the core TestResult class."""
    assert _AntaAdvisoryTest._create_result is not AntaTest._create_result
    assert AntaTestResult.__private_attributes__ == {}
