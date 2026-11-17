# Copyright (c) 2026 Arista Networks, Inc.
# Use of this source code is governed by the Apache License 2.0
# that can be found in the LICENSE file.
"""Unit tests for Arista Security Advisory 219."""

from __future__ import annotations

from functools import partial
from typing import TYPE_CHECKING
from unittest.mock import patch

import pytest

from anta._advisory.eos_versions import AffectedStatus, evaluate_version
from anta._advisory.facts.eos import EosVersionFact
from anta._advisory.facts.ip_security import IpsecKeyControllerFact, IpsecSaAntiReplayFact
from anta._advisory.facts.models import Fact, FactProblemKind, FactSource, FactSourceKind, FeatureState
from anta._advisory.facts.platform import PlatformIdentityFact
from anta._advisory.findings.models import AffectedResult, ErrorResult, NotAffectedResult
from anta._advisory.remediation import FixedRelease, software_version_plan
from anta._advisory.results import _AdvisoryAtomicTestResult
from anta._eos.version import EOSVersion, parse_eos_version
from anta.result_manager.models import AntaTestStatus
from anta.tests.advisories.sa_219 import ADVISORY, AFFECTED_VERSION_MATRIX, SA219, _assess_sa219
from tests.units.anta_tests import build_eos_platform, build_eos_version, test  # noqa: F401 - Imported test collects _DATA.
from tests.units.anta_tests.advisories import OfflineAntaDevice, build_expected_advisory_result

if TYPE_CHECKING:
    from anta.models import AntaCommand
    from tests.units.anta_tests import AntaUnitTestData

SOURCE = FactSource("unit test", FactSourceKind.DEVICE_METADATA)
CONTROLLER = {"keyController": {"dhGroup": "modp4096", "encryptAlgo": "unknownEncr", "hashAlgo": "unknownIntegrity", "firstKeyAddTime": 0.0}}
POLICIES = {"ipsecSecurityAssociations": {"BLAH": {"replayWindowSize": 16384}}}
EXPECTED_FIXED = (
    FixedRelease(EOSVersion(4, 28, 14, suffix="M")),
    FixedRelease(EOSVersion(4, 33, 9, suffix="M")),
    FixedRelease(EOSVersion(4, 34, 8, suffix="M")),
    FixedRelease(EOSVersion(4, 35, 6, suffix="M")),
    FixedRelease(EOSVersion(4, 36, 2, suffix="F")),
    FixedRelease(EOSVersion(4, 37, 0, suffix="F")),
)
EXPECTED_REMEDIATION = software_version_plan(EXPECTED_FIXED, current_version=EOSVersion(4, 35, 0, suffix="F"))
expected = partial(build_expected_advisory_result, "CVE-2026-120974")

_DATA: AntaUnitTestData = {
    (SA219, "affected-controller-without-profile-or-live-tunnels"): {
        "version": build_eos_version("4.35.0F"),
        "platform": build_eos_platform("CloudEOS"),
        "eos_data": [CONTROLLER, POLICIES],
        "expected": expected(
            AntaTestStatus.FAILURE,
            "The device is affected because EOS version '4.35.0F' is affected, platform 'CloudEOS' is within the affected platform scope, "
            "the IPsec key controller is enabled, and the IPsec SA policy anti-replay detection is enabled",
            EXPECTED_REMEDIATION,
        ),
    },
    (SA219, "affected-ambiguous-veos"): {
        "version": build_eos_version("4.35.0F"),
        "platform": build_eos_platform("vEOS"),
        "eos_data": [CONTROLLER, POLICIES],
        "expected": expected(
            AntaTestStatus.FAILURE,
            "The device is affected because EOS version '4.35.0F' is affected, platform 'vEOS' is within the affected platform scope, "
            "the IPsec key controller is enabled, and the IPsec SA policy anti-replay detection is enabled",
            EXPECTED_REMEDIATION,
        ),
    },
    (SA219, "unused-enabled-policy-deliberately-counts"): {
        "version": build_eos_version("4.35.0F"),
        "platform": build_eos_platform("CloudEOS"),
        "eos_data": [CONTROLLER, {"ipsecSecurityAssociations": {"BLAH": {"replayWindowSize": 0}, "unused": {"replayWindowSize": 16384}}}],
        "expected": expected(
            AntaTestStatus.FAILURE,
            "The device is affected because EOS version '4.35.0F' is affected, platform 'CloudEOS' is within the affected platform scope, "
            "the IPsec key controller is enabled, and the IPsec SA policy anti-replay detection is enabled",
            EXPECTED_REMEDIATION,
        ),
    },
    (SA219, "no-controller-ignores-unavailable-policy-and-metadata"): {
        "version": None,
        "platform": None,
        "eos_data": [{}, {}],
        "expected": expected(AntaTestStatus.SUCCESS, "The device is not affected because the IPsec key controller is disabled", None),
    },
    (SA219, "all-policies-disabled-ignores-unavailable-controller-and-metadata"): {
        "version": None,
        "platform": None,
        "eos_data": [{"keyController": None}, {"ipsecSecurityAssociations": {"BLAH": {"replayWindowSize": 0}}}],
        "expected": expected(AntaTestStatus.SUCCESS, "The device is not affected because the IPsec SA policy anti-replay detection is disabled", None),
    },
    (SA219, "no-policies"): {
        "version": None,
        "platform": None,
        "eos_data": [CONTROLLER, {"ipsecSecurityAssociations": {}}],
        "expected": expected(AntaTestStatus.SUCCESS, "The device is not affected because the IPsec SA policy anti-replay detection is disabled", None),
    },
    (SA219, "fixed-exceptional-428-train"): {
        "version": build_eos_version("4.28.14M"),
        "platform": None,
        "eos_data": [{"keyController": None}, {}],
        "expected": expected(AntaTestStatus.SUCCESS, "The device is not affected because EOS version '4.28.14M' is outside the affected releases", None),
    },
    (SA219, "excluded-ceos-lab"): {
        "version": None,
        "platform": build_eos_platform("cEOSLab"),
        "eos_data": [{"keyController": None}, {}],
        "expected": expected(AntaTestStatus.SUCCESS, "The device is not affected because platform 'cEOSLab' is outside the affected platform scope", None),
    },
    (SA219, "missing-policy-window"): {
        "version": build_eos_version("4.35.0F"),
        "platform": build_eos_platform("CloudEOS"),
        "eos_data": [CONTROLLER, {"ipsecSecurityAssociations": {"BLAH": {}}}],
        "expected": expected(
            AntaTestStatus.ERROR,
            "The test could not determine the IPsec SA policy anti-replay detection state because the 'show ip security security-association' output is incomplete.",
            None,
        ),
    },
    (SA219, "witness-survives-malformed-policy"): {
        "version": build_eos_version("4.35.0F"),
        "platform": build_eos_platform("CloudEOS"),
        "eos_data": [CONTROLLER, {"ipsecSecurityAssociations": {"broken": {}, "BLAH": {"replayWindowSize": 1}}}],
        "expected": expected(
            AntaTestStatus.FAILURE,
            "The device is affected because EOS version '4.35.0F' is affected, platform 'CloudEOS' is within the affected platform scope, "
            "the IPsec key controller is enabled, and the IPsec SA policy anti-replay detection is enabled",
            EXPECTED_REMEDIATION,
        ),
    },
}


def version_fact(version: str | None) -> Fact[EosVersionFact]:
    """Create normalized or missing version metadata."""
    if version is None:
        return EosVersionFact.unavailable(FactProblemKind.MISSING, SOURCE)
    return EosVersionFact.from_version(parse_eos_version(version).unwrap()).available(SOURCE)


def platform_fact(model: str | None) -> Fact[PlatformIdentityFact]:
    """Create normalized or missing platform metadata."""
    if model is None:
        return PlatformIdentityFact.unavailable(FactProblemKind.MISSING, SOURCE)
    identity = build_eos_platform(model)
    assert identity is not None
    return PlatformIdentityFact.from_identity(identity).available(SOURCE)


@pytest.mark.parametrize(
    ("version", "affected"),
    [
        ("4.26.99M", False),
        ("4.27.0F", True),
        ("4.27.99M", True),
        ("4.28.13M", True),
        ("4.28.13.99M", True),
        ("4.28.14M", False),
        ("4.28.14.1M", False),
        ("4.28.15M", False),
        ("4.29.0F", True),
        ("4.29.99M", True),
        ("4.30.0F", True),
        ("4.30.99M", True),
        ("4.31.0F", True),
        ("4.31.99M", True),
        ("4.32.0F", True),
        ("4.32.99M", True),
        ("4.33.8M", True),
        ("4.33.8.99M", True),
        ("4.33.9M", False),
        ("4.33.9.1M", False),
        ("4.34.7M", True),
        ("4.34.7.99M", True),
        ("4.34.8M", False),
        ("4.34.8.1M", False),
        ("4.35.5M", True),
        ("4.35.5.99M", True),
        ("4.35.6M", False),
        ("4.35.6.1M", False),
        ("4.36.1F", True),
        ("4.36.1.99F", True),
        ("4.36.2F", False),
        ("4.36.2.1F", False),
        ("4.37.0F", False),
        ("4.38.0F", False),
        ("5.0.0F", False),
    ],
)
def test_source_version_boundaries(version: str, affected: bool) -> None:
    """Keep the sparse old-train fix and every stated source boundary explicit."""
    result = evaluate_version(parse_eos_version(version).unwrap(), AFFECTED_VERSION_MATRIX)
    assert result.affected_status is (AffectedStatus.AFFECTED if affected else AffectedStatus.NOT_AFFECTED)


@pytest.mark.parametrize(
    ("model", "affected"),
    [
        ("CloudEOS", True),
        ("vEOS", True),
        ("AWE-5310", True),
        ("AWE-7250R", True),
        ("vEOS-lab", False),
        ("cEOSLab", False),
        ("DCS-7050SX3-48YC8", False),
        ("DCS-7280CR3-32P4", False),
    ],
)
def test_platform_scope(model: str, affected: bool) -> None:
    """Include ambiguous vEOS while respecting explicit lab and physical exclusions."""
    finding = _assess_sa219(
        version_fact("4.35.0F"),
        platform_fact(model),
        IpsecKeyControllerFact(FeatureState.ENABLED).available(SOURCE),
        IpsecSaAntiReplayFact(FeatureState.ENABLED).available(SOURCE),
    )
    assert isinstance(finding, AffectedResult if affected else NotAffectedResult)


def test_all_required_unavailable_inputs_are_preserved() -> None:
    """An unavailable scope must not hide unavailable feature evidence."""
    finding = _assess_sa219(
        version_fact(None),
        platform_fact(None),
        IpsecKeyControllerFact.unavailable(FactProblemKind.MALFORMED, SOURCE),
        IpsecSaAntiReplayFact.unavailable(FactProblemKind.MISSING, SOURCE),
    )
    assert isinstance(finding, ErrorResult)
    assert tuple(problem.definition for problem in finding.problems) == (EosVersionFact, PlatformIdentityFact, IpsecKeyControllerFact, IpsecSaAntiReplayFact)


def test_unknown_platform_is_error() -> None:
    """Do not classify an unrecognized platform as excluded."""
    finding = _assess_sa219(
        version_fact("4.35.0F"),
        platform_fact("unrecognized"),
        IpsecKeyControllerFact(FeatureState.ENABLED).available(SOURCE),
        IpsecSaAntiReplayFact(FeatureState.ENABLED).available(SOURCE),
    )
    assert isinstance(finding, ErrorResult)


def test_advisory_metadata() -> None:
    """Keep approved identifiers and date independent of source placeholders."""
    assert ADVISORY.sa_number == "0219"
    assert str(ADVISORY.last_updated) == "2026-11-10"
    assert ADVISORY.vulnerabilities[0].id == "CVE-2026-120974"


@pytest.mark.parametrize("failed_command", ["show ip security key controller local", "show ip security security-association"])
@pytest.mark.parametrize("error", ["permission denied", "This command is not supported on this hardware platform"])
@pytest.mark.parametrize("scope", ["affected", "fixed", "excluded"])
async def test_collection_failure_preserves_atomic_assessment(failed_command: str, error: str, scope: str) -> None:
    """Interpret real collection failures after independently decisive exclusions."""
    device = OfflineAntaDevice("unit-test")
    device.version = build_eos_version("4.35.6M" if scope == "fixed" else "4.35.0F")
    device.platform = build_eos_platform("cEOSLab" if scope == "excluded" else "CloudEOS")
    await device.refresh()

    async def collect(command: AntaCommand, *, collection_id: str | None = None) -> None:  # noqa: ARG001
        if command.command == failed_command:
            command.errors = [error]
            command.output = None
        else:
            command.output = CONTROLLER if command.command.endswith("local") else POLICIES

    instance = SA219(device=device)
    with patch.object(device, "_collect", new=collect):
        await instance.test()

    assert len(instance.result.atomic_results) == 1
    atomic = instance.result.atomic_results[0]
    assert isinstance(atomic, _AdvisoryAtomicTestResult)
    assert atomic.vulnerability_ids == ("CVE-2026-120974",)
    assert atomic.remediation is None
    if scope == "fixed":
        message = "The device is not affected because EOS version '4.35.6M' is outside the affected releases."
    elif scope == "excluded":
        message = "The device is not affected because platform 'cEOSLab' is outside the affected platform scope."
    else:
        label = "IPsec key controller state" if failed_command.endswith("local") else "IPsec SA policy anti-replay detection state"
        reason = "is not supported" if error != "permission denied" else "could not be collected"
        message = f"The test could not determine the {label} because '{failed_command}' {reason}."
    assert atomic.messages == [message]
    assert atomic.result is (AntaTestStatus.ERROR if scope == "affected" else AntaTestStatus.SUCCESS)
    assert instance.result.result is atomic.result
