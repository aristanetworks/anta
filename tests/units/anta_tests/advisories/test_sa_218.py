# Copyright (c) 2026 Arista Networks, Inc.
# Use of this source code is governed by the Apache License 2.0
# that can be found in the LICENSE file.
"""Unit tests for Arista Security Advisory 218."""

from __future__ import annotations

from datetime import date
from functools import partial
from typing import cast

import pytest

from anta._advisory.eos_versions import AffectedStatus, evaluate_version
from anta._advisory.facts.eos import EosVersionFact
from anta._advisory.facts.http import EapiEnabledFact, HttpDefaultServicesFact
from anta._advisory.facts.models import FactProblemKind, FactsBase, FactSource, FactSourceKind, FeatureState
from anta._advisory.findings.models import AffectedResult, EosReleaseAssessment, ErrorResult, NotAffectedResult
from anta._advisory.remediation import ChangeSoftwareVersion, FixedRelease, KnownFixedReleases, RemediationPlan, SoftwareTarget
from anta._eos.version import EOSVersion, parse_eos_version
from anta.result_manager.models import AntaTestStatus
from anta.tests.advisories.sa_218 import ADVISORY, AFFECTED_VERSION_MATRIX, FIXED_RELEASES, SA218, _assess_sa218
from tests.units.anta_tests import (
    AntaUnitTestData,
    build_eos_platform,
    build_eos_version,
    test,  # noqa: F401 - Pytest collects this imported test function.
)
from tests.units.anta_tests.advisories import OfflineAntaDevice, build_expected_advisory_result

SOURCE = FactSource("unit-test", FactSourceKind.DEVICE_METADATA)
VERSION = EosVersionFact.from_version(EOSVersion(4, 36, 1, suffix="F")).available(SOURCE)
EAPI = EapiEnabledFact(FeatureState.ENABLED).available(SOURCE)
DEFAULTS = HttpDefaultServicesFact(FeatureState.ENABLED).available(SOURCE)
EXPECTED_FIXED_RELEASES = KnownFixedReleases(
    (
        FixedRelease(EOSVersion(4, 37, 0, suffix="F")),
        FixedRelease(EOSVersion(4, 36, 3, hotfix=2, suffix="M")),
        FixedRelease(EOSVersion(4, 35, 7, hotfix=2, suffix="M")),
        FixedRelease(EOSVersion(4, 34, 9, hotfix=2, suffix="M")),
        FixedRelease(EOSVersion(4, 33, 11, hotfix=2, suffix="M")),
    )
)
REMEDIATION = RemediationPlan(ChangeSoftwareVersion(SoftwareTarget.EOS, EOSVersion(4, 36, 1, suffix="F"), EXPECTED_FIXED_RELEASES))
CONFIG = "management api http-commands\n   default-services\n   no shutdown\n"
COMMAND = "show running-config all | section ^management (api http-commands|http-server)"
expected = partial(build_expected_advisory_result, "CVE-2026-121371")


@pytest.mark.parametrize(
    ("version", "affected"),
    [
        ("4.20.99M", True),
        ("4.31.99M", True),
        ("4.32.0F", True),
        ("4.32.99M", True),
        ("4.32.99.99M", True),
        ("4.33.0F", True),
        ("4.33.10.99M", True),
        ("4.33.11M", True),
        ("4.33.11.1M", True),
        ("4.33.11.2M", False),
        ("4.33.11.3M", False),
        ("4.33.12M", False),
        ("4.34.0F", True),
        ("4.34.8.99M", True),
        ("4.34.9M", True),
        ("4.34.9.1M", True),
        ("4.34.9.2M", False),
        ("4.34.9.3M", False),
        ("4.34.10M", False),
        ("4.35.0F", True),
        ("4.35.6.99M", True),
        ("4.35.7M", True),
        ("4.35.7.1M", True),
        ("4.35.7.2M", False),
        ("4.35.7.3M", False),
        ("4.35.8M", False),
        ("4.36.0F", True),
        ("4.36.2.99M", True),
        ("4.36.3M", True),
        ("4.36.3.1M", True),
        ("4.36.3.2M", False),
        ("4.36.3.3M", False),
        ("4.36.4M", False),
        ("4.37.0F", False),
        ("4.37.0.1F", False),
        ("4.38.0F", False),
        ("5.0.0F", False),
    ],
)
def test_source_software_boundaries(version: str, affected: bool) -> None:
    """Keep base and .1 affected, .2 fixed, and unfixed older trains unbounded."""
    result = evaluate_version(parse_eos_version(version).unwrap(), AFFECTED_VERSION_MATRIX)
    assert result.affected_status is (AffectedStatus.AFFECTED if affected else AffectedStatus.NOT_AFFECTED)


def test_source_fixed_release_labels() -> None:
    """Preserve the exact four-component fixed releases and maturity labels."""
    assert tuple(str(release.version) for release in FIXED_RELEASES) == (
        "4.37.0F",
        "4.36.3.2M",
        "4.35.7.2M",
        "4.34.9.2M",
        "4.33.11.2M",
    )


def test_allocated_metadata() -> None:
    """Keep assigned batch identity separate from unresolved source publication metadata."""
    assert ADVISORY.sa_number == "0218"
    assert ADVISORY.last_updated == date(2026, 11, 10)
    assert tuple(vulnerability.id for vulnerability in ADVISORY.vulnerabilities) == ("CVE-2026-121371",)


def test_affected_assessment_and_fixed_software_remediation() -> None:
    """Configured prerequisite services on affected software establish exposure."""
    result = _assess_sa218(VERSION, EAPI, DEFAULTS)
    assert isinstance(result, AffectedResult)
    assert result.vulnerability_id == "CVE-2026-121371"
    assert result.context[0].fact is VERSION
    assert result.conditions == (EAPI, DEFAULTS)
    assert result.remediation == REMEDIATION


@pytest.mark.parametrize("decisive", ["version", "eapi", "defaults"])
def test_independent_exclusion_ignores_unrelated_unavailable_evidence(decisive: str) -> None:
    """An explicitly absent prerequisite proves safety without unrelated evidence."""
    version = EosVersionFact.unavailable(FactProblemKind.MISSING, SOURCE)
    eapi = EapiEnabledFact.unavailable(FactProblemKind.MISSING, SOURCE)
    defaults = HttpDefaultServicesFact.unavailable(FactProblemKind.MISSING, SOURCE)
    if decisive == "version":
        version = EosVersionFact.from_version(EOSVersion(4, 37, 0, suffix="F")).available(SOURCE)
    elif decisive == "eapi":
        eapi = EapiEnabledFact(FeatureState.DISABLED).available(SOURCE)
    else:
        defaults = HttpDefaultServicesFact(FeatureState.DISABLED).available(SOURCE)
    result = _assess_sa218(version, eapi, defaults)
    assert isinstance(result, NotAffectedResult)
    if decisive == "version":
        assert isinstance(result.decisive[0], EosReleaseAssessment)
        assert result.decisive[0].fact is version
    else:
        assert result.decisive == (eapi if decisive == "eapi" else defaults,)


def test_all_required_unavailable_evidence_is_retained() -> None:
    """No required collection failure is hidden when there is no decisive exclusion."""
    version = EosVersionFact.unavailable(FactProblemKind.MISSING, SOURCE)
    eapi = EapiEnabledFact.unavailable(FactProblemKind.MALFORMED, SOURCE)
    defaults = HttpDefaultServicesFact.unavailable(FactProblemKind.COLLECTION_FAILED, SOURCE)
    result = _assess_sa218(version, eapi, defaults)
    assert isinstance(result, ErrorResult)
    assert result.problems == (version, eapi, defaults)


def test_all_eos_scope_and_command_contract() -> None:
    """All EOS platforms use explicit revision-one API state and scoped full defaults."""
    facts = cast("type[FactsBase]", SA218.__dict__["Facts"])
    assert tuple(facts.definitions()) == ("version", "eapi", "default_services")
    instance = SA218(OfflineAntaDevice("unit-test"))
    assert [(command.command, command.ofmt, command.revision) for command in instance.instance_commands] == [
        ("show management api http-commands", "json", 1),
        (COMMAND, "text", None),
    ]


_DATA: AntaUnitTestData = {
    (SA218, "not-affected-disabled-api-malformed-defaults"): {
        "version": None,
        "eos_data": [{"enabled": False, "httpsServer": {"running": True}}, {}],
        "expected": expected(AntaTestStatus.SUCCESS, "The device is not affected because the eAPI feature is disabled.", None),
    },
    (SA218, "not-affected-disabled-default-services-malformed-api"): {
        "version": None,
        "eos_data": [{}, CONFIG.replace("   default-services", "   no default-services")],
        "expected": expected(AntaTestStatus.SUCCESS, "The device is not affected because the management HTTP server default services is disabled.", None),
    },
    (SA218, "not-affected-fixed-malformed-features"): {
        "version": build_eos_version("4.37.0F"),
        "eos_data": [{}, {}],
        "expected": expected(AntaTestStatus.SUCCESS, "The device is not affected because EOS version '4.37.0F' is outside the affected releases.", None),
    },
    (SA218, "error-missing-api-state"): {
        "version": build_eos_version("4.36.1F"),
        "eos_data": [{}, CONFIG],
        "expected": expected(
            AntaTestStatus.ERROR,
            "The test could not determine the eAPI service state because the 'show management api http-commands' output is incomplete.",
            None,
        ),
    },
    (SA218, "error-default-services-omitted"): {
        "version": build_eos_version("4.36.1F"),
        "eos_data": [{"enabled": True}, "management api http-commands\n   no shutdown\n"],
        "expected": expected(
            AntaTestStatus.ERROR,
            f"The test could not determine the management HTTP default-service state because the '{COMMAND}' output is incomplete.",
            None,
        ),
    },
    (SA218, "error-conflicting-carriers"): {
        "version": build_eos_version("4.36.1F"),
        "eos_data": [{"enabled": True}, CONFIG + "management http-server\n   no default-services\n"],
        "expected": expected(
            AntaTestStatus.ERROR,
            f"The test could not determine the management HTTP default-service state because the '{COMMAND}' output is invalid.",
            None,
        ),
    },
}

for _transport in ("httpServer", "httpsServer", "localHttpServer", "unixSocketServer"):
    _DATA[(SA218, f"affected-{_transport}-not-running")] = {
        "version": build_eos_version("4.36.1F"),
        "eos_data": [{"enabled": True, _transport: {"configured": True, "running": False}, "vrfs": []}, CONFIG],
        "expected": expected(
            AntaTestStatus.FAILURE,
            "The device is affected because EOS version '4.36.1F' is affected, the eAPI feature is enabled, "
            "and the management HTTP server default services is enabled.",
            REMEDIATION,
        ),
    }

for _model in ("cEOSLab", "vEOS-lab", "CVX", "ZTX-7230S-4TX-4S"):
    _DATA[(SA218, f"affected-all-eos-{_model}")] = {
        "version": build_eos_version("4.36.1F"),
        "platform": build_eos_platform(_model),
        "eos_data": [{"enabled": True}, CONFIG.replace("management api http-commands", "management http-server")],
        "expected": expected(
            AntaTestStatus.FAILURE,
            "The device is affected because EOS version '4.36.1F' is affected, the eAPI feature is enabled, "
            "and the management HTTP server default services is enabled.",
            REMEDIATION,
        ),
    }
