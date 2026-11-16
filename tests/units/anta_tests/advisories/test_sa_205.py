# Copyright (c) 2026 Arista Networks, Inc.
# Use of this source code is governed by the Apache License 2.0
# that can be found in the LICENSE file.
"""Unit tests for Arista Security Advisory 205."""

from __future__ import annotations

from datetime import date
from functools import partial
from typing import TYPE_CHECKING

import pytest

from anta._advisory.eos_versions import AffectedStatus, evaluate_version
from anta._advisory.facts.certificates import EstCaCertificateAutoUpdateFact
from anta._advisory.facts.eos import EosVersionFact
from anta._advisory.facts.models import FactProblemKind, FactSource, FactSourceKind, FeatureState
from anta._advisory.findings.models import AffectedResult, ErrorResult, NotAffectedResult
from anta._advisory.remediation import ChangeSoftwareVersion, FixedRelease, KnownFixedReleases, RemediationPlan, SoftwareTarget
from anta._eos.version import EOSVersion, parse_eos_version
from anta.result_manager.models import AntaTestStatus
from anta.tests.advisories import get_catalog
from anta.tests.advisories.sa_205 import ADVISORY, AFFECTED_VERSION_MATRIX, SA205, _assess_sa205
from tests.units.anta_tests import build_eos_platform, build_eos_version, test  # noqa: F401 - Parameterized advisory harness.
from tests.units.anta_tests.advisories import build_expected_advisory_result

if TYPE_CHECKING:
    from tests.units.anta_tests import AntaUnitTestData

SOURCE = FactSource("unit test", FactSourceKind.DEVICE_METADATA)
EXPECTED_REMEDIATION = RemediationPlan(
    ChangeSoftwareVersion(
        software=SoftwareTarget.EOS,
        current_version=EOSVersion(4, 36, 1, suffix="F"),
        destination=KnownFixedReleases((FixedRelease(EOSVersion(4, 37, 0, suffix="F")), FixedRelease(EOSVersion(4, 36, 2, suffix="F")))),
    )
)
expected = partial(build_expected_advisory_result, "CVE-2026-120975")
ENABLED = {"profiles": {"EST1": {"currentState": "Valid", "caCertificates": "enabled", "lastCaRetrieved": 0.0, "managedProfiles": []}}}
DISABLED = {"profiles": {"MANUAL": {"currentState": "Invalid", "caCertificates": "disabled", "managedProfiles": []}}}
AFFECTED_MESSAGE = (
    "The device is affected because EOS version '4.36.1F' is affected and the automatic certificate management EST CA certificate auto-update is enabled"
)
DISABLED_MESSAGE = "The device is not affected because the automatic certificate management EST CA certificate auto-update is disabled"


@pytest.mark.parametrize(
    ("version", "affected"),
    [
        ("4.20.0F", False),
        ("4.35.9M", False),
        ("4.36.0F", False),
        ("4.36.1F", True),
        ("4.36.1.1F", True),
        ("4.36.1.99F", True),
        ("4.36.2F", False),
        ("4.36.2.1F", False),
        ("4.36.3M", False),
        ("4.37.0F", False),
        ("4.37.1F", False),
        ("4.38.0F", False),
        ("5.0.0F", False),
    ],
)
def test_source_version_boundaries(version: str, affected: bool) -> None:
    """Keep the single affected release distinct from earlier and fixed trains."""
    status = evaluate_version(parse_eos_version(version).unwrap(), AFFECTED_VERSION_MATRIX).affected_status
    assert status is (AffectedStatus.AFFECTED if affected else AffectedStatus.NOT_AFFECTED)


def test_affected_and_software_remediation() -> None:
    """Known configured retrieval produces the exact source-backed software targets."""
    result = _assess_sa205(
        EosVersionFact.from_version(EOSVersion(4, 36, 1, suffix="F")).available(SOURCE),
        EstCaCertificateAutoUpdateFact(FeatureState.ENABLED).available(SOURCE),
    )
    assert isinstance(result, AffectedResult)
    assert result.vulnerability_id == "CVE-2026-120975"
    assert result.remediation == EXPECTED_REMEDIATION


def test_disabled_retrieval_bypasses_missing_version() -> None:
    """Decisively absent retrieval closes the exposure path independently of version."""
    result = _assess_sa205(
        EosVersionFact.unavailable(FactProblemKind.MISSING, SOURCE),
        EstCaCertificateAutoUpdateFact(FeatureState.DISABLED).available(SOURCE),
    )
    assert isinstance(result, NotAffectedResult)


@pytest.mark.parametrize("version", ["4.36.0F", "4.36.2F", "4.37.0F"])
def test_fixed_or_outside_release_bypasses_unavailable_retrieval(version: str) -> None:
    """Independent software safety does not depend on unrelated command availability."""
    result = _assess_sa205(
        EosVersionFact.from_version(parse_eos_version(version).unwrap()).available(SOURCE),
        EstCaCertificateAutoUpdateFact.unavailable(FactProblemKind.COLLECTION_FAILED, SOURCE),
    )
    assert isinstance(result, NotAffectedResult)


def test_all_required_unavailable_inputs_are_preserved() -> None:
    """Required version and retrieval problems are reported together."""
    result = _assess_sa205(
        EosVersionFact.unavailable(FactProblemKind.MISSING, SOURCE),
        EstCaCertificateAutoUpdateFact.unavailable(FactProblemKind.MALFORMED, SOURCE),
    )
    assert isinstance(result, ErrorResult)
    assert tuple(problem.definition for problem in result.problems) == (EosVersionFact, EstCaCertificateAutoUpdateFact)


def test_known_enabled_does_not_bypass_missing_software_scope() -> None:
    """A positive setting still requires the independent release prerequisite."""
    result = _assess_sa205(
        EosVersionFact.unavailable(FactProblemKind.MISSING, SOURCE),
        EstCaCertificateAutoUpdateFact(FeatureState.ENABLED).available(SOURCE),
    )
    assert isinstance(result, ErrorResult)
    assert tuple(problem.definition for problem in result.problems) == (EosVersionFact,)


def test_metadata_and_registry() -> None:
    """Register the allocated numeric identity and approved batch date."""
    assert ADVISORY.sa_number == "0205"
    assert ADVISORY.last_updated == date(2026, 11, 10)
    assert tuple(v.id for v in ADVISORY.vulnerabilities) == ("CVE-2026-120975",)
    assert any(entry.test is SA205 for entry in get_catalog().tests)


_DATA: AntaUnitTestData = {
    (SA205, "affected-with-no-managed-profiles"): {
        "version": build_eos_version("4.36.1F"),
        "platform": None,
        "eos_data": [ENABLED],
        "expected": expected(AntaTestStatus.FAILURE, AFFECTED_MESSAGE, EXPECTED_REMEDIATION),
    },
    (SA205, "not-affected-disabled-invalid-protocol"): {
        "version": None,
        "platform": None,
        "eos_data": [DISABLED],
        "expected": expected(AntaTestStatus.SUCCESS, DISABLED_MESSAGE, None),
    },
    (SA205, "not-affected-no-est-protocols"): {
        "version": None,
        "platform": None,
        "eos_data": [{"profiles": {}}],
        "expected": expected(AntaTestStatus.SUCCESS, DISABLED_MESSAGE, None),
    },
    (SA205, "not-affected-fixed-with-invalid-command-data"): {
        "version": build_eos_version("4.37.0F"),
        "platform": None,
        "eos_data": [{}],
        "expected": expected(AntaTestStatus.SUCCESS, "The device is not affected because EOS version '4.37.0F' is outside the affected releases", None),
    },
    (SA205, "error-no-enabled-witness-and-missing-setting"): {
        "version": build_eos_version("4.36.1F"),
        "platform": None,
        "eos_data": [{"profiles": {"MANUAL": {"caCertificates": "disabled"}, "INCOMPLETE": {}}}],
        "expected": expected(
            AntaTestStatus.ERROR,
            "The test could not determine the EST CA certificate auto-update because the "
            "'show management security auto-certificate protocol est detail' output is incomplete",
            None,
        ),
    },
    (SA205, "error-all-required-inputs-unavailable"): {
        "version": None,
        "platform": None,
        "eos_data": [{"profiles": []}],
        "expected": expected(
            AntaTestStatus.ERROR,
            "The test could not determine the EOS version because it is missing from device metadata. "
            "The test could not determine the EST CA certificate auto-update because the "
            "'show management security auto-certificate protocol est detail' output is invalid.",
            None,
        ),
    },
}

for _reverse in (False, True):
    for _bad_entry in ({}, [], {"caCertificates": "unknown"}):
        _entries = [("ENABLED", {"caCertificates": "enabled"}), ("BAD", _bad_entry)]
        if _reverse:
            _entries.reverse()
        _DATA[(SA205, f"affected-known-enabled-mixed-{_reverse}-{_bad_entry}")] = {
            "version": build_eos_version("4.36.1F"),
            "platform": None,
            "eos_data": [{"profiles": dict(_entries)}],
            "expected": expected(AntaTestStatus.FAILURE, AFFECTED_MESSAGE, EXPECTED_REMEDIATION),
        }

for _state in ("Invalid", "Enrolling", "Valid"):
    _DATA[(SA205, f"affected-independent-of-profile-state-{_state}")] = {
        "version": build_eos_version("4.36.1F"),
        "platform": None,
        "eos_data": [
            {
                "profiles": {
                    "EST1": {
                        "currentState": _state,
                        "caCertificates": "enabled",
                        "lastCaRetrieved": 0.0,
                        "managedProfiles": [{"certProfile": "CERT1", "certProfileState": _state}],
                    }
                }
            }
        ],
        "expected": expected(AntaTestStatus.FAILURE, AFFECTED_MESSAGE, EXPECTED_REMEDIATION),
    }

for _reverse in (False, True):
    _entries = [("ENABLED", {"caCertificates": "enabled"}), ("", {})]
    if _reverse:
        _entries.reverse()
    _DATA[(SA205, f"affected-known-named-witness-malformed-sibling-name-{_reverse}")] = {
        "version": build_eos_version("4.36.1F"),
        "platform": None,
        "eos_data": [{"profiles": dict(_entries)}],
        "expected": expected(AntaTestStatus.FAILURE, AFFECTED_MESSAGE, EXPECTED_REMEDIATION),
    }

for _model in ("vEOS-lab", "cEOSLab", "CloudEOS", "CVX", "ZTX-7230S-4TX-4S", "DCS-7050SX3-48YC8"):
    _DATA[(SA205, f"affected-all-eos-{_model}")] = {
        "version": build_eos_version("4.36.1F"),
        "platform": build_eos_platform(_model),
        "eos_data": [ENABLED],
        "expected": expected(AntaTestStatus.FAILURE, AFFECTED_MESSAGE, EXPECTED_REMEDIATION),
    }
