# Copyright (c) 2026 Arista Networks, Inc.
# Use of this source code is governed by the Apache License 2.0
# that can be found in the LICENSE file.
"""Unit tests for Arista Security Advisory 212."""

from __future__ import annotations

from datetime import date
from functools import partial
from typing import TYPE_CHECKING

import pytest

from anta._advisory.eos_versions import AffectedStatus, evaluate_version
from anta._advisory.facts.avt import AvtRole, PathfinderRoleFact
from anta._advisory.facts.bgp_peering import BgpLinkStatePeeringFact
from anta._advisory.facts.eos import EosVersionFact
from anta._advisory.facts.models import ConfigurationState, FactProblemKind, FactSource, FactSourceKind
from anta._advisory.facts.platform import PlatformIdentityFact
from anta._advisory.findings.models import AffectedResult, ErrorResult, NotAffectedResult, VulnerabilityResult
from anta._advisory.remediation import ChangeSoftwareVersion, FixedRelease, KnownFixedReleases, RemediationPlan, SoftwareTarget
from anta._eos.platform import PlatformFamily, PlatformIdentity, PlatformType
from anta._eos.version import EOSVersion, parse_eos_version
from anta.result_manager.models import AntaTestStatus
from anta.tests.advisories.sa_212 import ADVISORY, AFFECTED_VERSION_MATRIX, SA212, _assess_sa212
from tests.units.anta_tests import build_eos_platform, build_eos_version, test  # noqa: F401 - Parameterized advisory harness.
from tests.units.anta_tests.advisories import build_expected_advisory_result

if TYPE_CHECKING:
    from tests.units.anta_tests import AntaUnitTestData

SOURCE = FactSource("unit test", FactSourceKind.DEVICE_METADATA)
EXPECTED_REMEDIATION = RemediationPlan(
    ChangeSoftwareVersion(
        software=SoftwareTarget.EOS,
        current_version=EOSVersion(4, 35, 6, suffix="M"),
        destination=KnownFixedReleases(
            (
                FixedRelease(EOSVersion(4, 37, 0, suffix="F")),
                FixedRelease(EOSVersion(4, 36, 3, suffix="M")),
                FixedRelease(EOSVersion(4, 35, 7, suffix="M")),
                FixedRelease(EOSVersion(4, 34, 9, suffix="M")),
                FixedRelease(EOSVersion(4, 33, 11, suffix="M")),
            )
        ),
    )
)
expected = partial(build_expected_advisory_result, "CVE-2026-120979")


@pytest.mark.parametrize(
    ("version", "affected"),
    [
        ("4.20.0F", True),
        ("4.31.99M", True),
        ("4.32.0F", True),
        ("4.32.99M", True),
        ("4.33.0F", True),
        ("4.33.10M", True),
        ("4.33.10.1M", True),
        ("4.33.11M", False),
        ("4.34.0F", True),
        ("4.34.8M", True),
        ("4.34.8.1M", True),
        ("4.34.9M", False),
        ("4.35.0F", True),
        ("4.35.6M", True),
        ("4.35.6.1M", True),
        ("4.35.7M", False),
        ("4.36.0F", True),
        ("4.36.2F", True),
        ("4.36.2.1F", True),
        ("4.36.3M", False),
        ("4.37.0F", False),
        ("4.38.0F", False),
        ("5.0.0F", False),
    ],
)
def test_source_version_boundaries(version: str, affected: bool) -> None:
    """Encode old trains and each independently stated first fixed release."""
    status = evaluate_version(parse_eos_version(version).unwrap(), AFFECTED_VERSION_MATRIX).affected_status
    assert status is (AffectedStatus.AFFECTED if affected else AffectedStatus.NOT_AFFECTED)


def assess(model: str | None = "CloudEOS", *, role: AvtRole = AvtRole.PATHFINDER, configured: bool = True, version: str = "4.35.6M") -> VulnerabilityResult:
    """Build independent facts for the pure assessment."""
    platform = build_eos_platform(model) if model else None
    identity = PlatformIdentityFact.from_identity(platform).available(SOURCE) if platform else PlatformIdentityFact.unavailable(FactProblemKind.MISSING, SOURCE)
    return _assess_sa212(
        EosVersionFact.from_version(parse_eos_version(version).unwrap()).available(SOURCE),
        identity,
        BgpLinkStatePeeringFact(ConfigurationState.CONFIGURED if configured else ConfigurationState.NOT_CONFIGURED).available(SOURCE),
        PathfinderRoleFact(role).available(SOURCE),
    )


@pytest.mark.parametrize("model", ["AWE-5310", "AWE-7230R", "CloudEOS", "vEOS"])
def test_affected_platforms(model: str) -> None:
    """Appliance and conservatively included virtual identities remain applicable."""
    result = assess(model)
    assert isinstance(result, AffectedResult)
    assert result.vulnerability_id == "CVE-2026-120979"
    assert result.remediation == EXPECTED_REMEDIATION


@pytest.mark.parametrize(
    "family",
    [
        PlatformFamily.SERIES_710,
        PlatformFamily.SERIES_720_D,
        PlatformFamily.SERIES_720_XP,
        PlatformFamily.SERIES_722_XPM,
        PlatformFamily.SERIES_750_X,
        PlatformFamily.SERIES_7010_TX,
        PlatformFamily.SERIES_7020_R,
        PlatformFamily.SERIES_7020_R4,
        PlatformFamily.SERIES_7130,
        PlatformFamily.SERIES_7170,
        PlatformFamily.SERIES_7050_X3,
        PlatformFamily.SERIES_7050_X4,
        PlatformFamily.SERIES_7060_X,
        PlatformFamily.SERIES_7060_X2,
        PlatformFamily.SERIES_7060_X4,
        PlatformFamily.SERIES_7060_X5,
        PlatformFamily.SERIES_7060_X6,
        PlatformFamily.SERIES_7260_X,
        PlatformFamily.SERIES_7260_X3,
        PlatformFamily.SERIES_7280_R,
        PlatformFamily.SERIES_7280_R2,
        PlatformFamily.SERIES_7280_R3,
        PlatformFamily.SERIES_7280_R4,
        PlatformFamily.SERIES_7300_X,
        PlatformFamily.SERIES_7300_X3,
        PlatformFamily.SERIES_7320_X,
        PlatformFamily.SERIES_7358_X4,
        PlatformFamily.SERIES_7368_X4,
        PlatformFamily.SERIES_7388_X5,
        PlatformFamily.SERIES_7500_R,
        PlatformFamily.SERIES_7500_R2,
        PlatformFamily.SERIES_7500_R3,
        PlatformFamily.SERIES_7800_R3,
        PlatformFamily.SERIES_7800_R4,
        PlatformFamily.SERIES_7700_R4,
        PlatformFamily.ZTX_7200,
        PlatformFamily.CEOS_LAB,
        PlatformFamily.VEOS_LAB,
    ],
)
def test_excluded_platforms(family: PlatformFamily) -> None:
    """Each EOS platform exclusion is independent of implementation constants."""
    platform = PlatformIdentityFact(model=family.value, type=PlatformType.FIXED, modules=(), platform_families=frozenset({family})).available(SOURCE)
    result = _assess_sa212(
        EosVersionFact.unavailable(FactProblemKind.MISSING, SOURCE),
        platform,
        BgpLinkStatePeeringFact(ConfigurationState.CONFIGURED).available(SOURCE),
        PathfinderRoleFact(AvtRole.PATHFINDER).available(SOURCE),
    )
    assert isinstance(result, NotAffectedResult)


@pytest.mark.parametrize("role", [AvtRole.EDGE, AvtRole.ZONE_TRANSIT, AvtRole.REGION_TRANSIT, AvtRole.UNKNOWN])
def test_non_pathfinder_is_decisive(role: AvtRole) -> None:
    """A valid negative role bypasses missing unrelated identity."""
    assert isinstance(assess(None, role=role), NotAffectedResult)


def test_absent_peering_is_decisive() -> None:
    """Absent persistent peering bypasses missing unrelated identity."""
    assert isinstance(assess(None, configured=False), NotAffectedResult)


def test_unknown_platform_is_error() -> None:
    """Unknown model cannot prove a source exclusion."""
    assert isinstance(assess("DCS-UNRECOGNIZED"), ErrorResult)


def test_cvx_family_is_conservatively_included() -> None:
    """CVX family classification does not exclude possible CloudEOS exposure."""
    platform = PlatformIdentityFact(model="CVX", type=PlatformType.VIRTUAL, modules=(), platform_families=frozenset({PlatformFamily.CVX})).available(SOURCE)
    result = _assess_sa212(
        EosVersionFact.from_version(EOSVersion(4, 35, 6, suffix="M")).available(SOURCE),
        platform,
        BgpLinkStatePeeringFact(ConfigurationState.CONFIGURED).available(SOURCE),
        PathfinderRoleFact(AvtRole.PATHFINDER).available(SOURCE),
    )
    assert isinstance(result, AffectedResult)


@pytest.mark.parametrize("model", ["vEOS", "CloudEOS"])
def test_included_virtual_identity_preserves_other_gates(model: str) -> None:
    """Platform inclusion does not bypass software, activation, or role gates."""
    assert isinstance(assess(model, version="4.35.7M"), NotAffectedResult)
    assert isinstance(assess(model, configured=False), NotAffectedResult)
    assert isinstance(assess(model, role=AvtRole.EDGE), NotAffectedResult)


def test_all_required_problems_are_preserved() -> None:
    """Unavailable scope and exposure evidence are aggregated together."""
    result = _assess_sa212(
        EosVersionFact.unavailable(FactProblemKind.MISSING, SOURCE),
        PlatformIdentityFact.unavailable(FactProblemKind.MISSING, SOURCE),
        BgpLinkStatePeeringFact.unavailable(FactProblemKind.MISSING, SOURCE),
        PathfinderRoleFact.unavailable(FactProblemKind.COLLECTION_FAILED, SOURCE),
    )
    assert isinstance(result, ErrorResult)
    assert tuple(problem.definition for problem in result.problems) == (EosVersionFact, PlatformIdentityFact, BgpLinkStatePeeringFact, PathfinderRoleFact)


def test_fixed_release_bypasses_unavailable_role_and_platform() -> None:
    """A software fix independently closes the exposure path."""
    result = _assess_sa212(
        EosVersionFact.from_version(EOSVersion(4, 35, 7, suffix="M")).available(SOURCE),
        PlatformIdentityFact.unavailable(FactProblemKind.MISSING, SOURCE),
        BgpLinkStatePeeringFact.unavailable(FactProblemKind.COLLECTION_FAILED, SOURCE),
        PathfinderRoleFact.unavailable(FactProblemKind.COLLECTION_FAILED, SOURCE),
    )
    assert isinstance(result, NotAffectedResult)


def test_absent_peering_bypasses_unavailable_role_and_scope() -> None:
    """Persistent absence decides safety independently of unrelated failures."""
    result = _assess_sa212(
        EosVersionFact.unavailable(FactProblemKind.MISSING, SOURCE),
        PlatformIdentityFact.unavailable(FactProblemKind.MISSING, SOURCE),
        BgpLinkStatePeeringFact(ConfigurationState.NOT_CONFIGURED).available(SOURCE),
        PathfinderRoleFact.unavailable(FactProblemKind.COLLECTION_FAILED, SOURCE),
    )
    assert isinstance(result, NotAffectedResult)


def test_non_pathfinder_bypasses_unavailable_peering_and_scope() -> None:
    """A successful valid unknown role is distinct from unavailable evidence."""
    result = _assess_sa212(
        EosVersionFact.unavailable(FactProblemKind.MISSING, SOURCE),
        PlatformIdentityFact.unavailable(FactProblemKind.MISSING, SOURCE),
        BgpLinkStatePeeringFact.unavailable(FactProblemKind.COLLECTION_FAILED, SOURCE),
        PathfinderRoleFact(AvtRole.UNKNOWN).available(SOURCE),
    )
    assert isinstance(result, NotAffectedResult)


def test_metadata_uses_allocated_identity() -> None:
    """Metadata uses the allocated SA/CVE and approved batch date."""
    assert ADVISORY.sa_number == "0212"
    assert ADVISORY.last_updated == date(2026, 11, 10)
    assert tuple(v.id for v in ADVISORY.vulnerabilities) == ("CVE-2026-120979",)


BGP_CONFIG = "router bgp 65000\n   neighbor 198.51.100.2 remote-as 65001\n   address-family link-state\n      neighbor 198.51.100.2 activate\n"

_DATA: AntaUnitTestData = {
    (SA212, "affected-configured-down-no-consumer"): {
        "version": build_eos_version("4.35.6M"),
        "platform": build_eos_platform("CloudEOS"),
        "eos_data": [
            BGP_CONFIG,
            {
                "role": "pathfinder",
                "routerId": "0.0.0.0",  # noqa: S104
                "vrfs": {},
            },
        ],
        "expected": expected(
            AntaTestStatus.FAILURE,
            "The device is affected because EOS version '4.35.6M' is affected, platform 'CloudEOS' is within the affected platform scope, "
            "the BGP-LS peering configuration is configured, and the Pathfinder role is enabled",
            EXPECTED_REMEDIATION,
        ),
    },
    (SA212, "not-affected-no-bgp-missing-other-inputs"): {
        "version": None,
        "platform": None,
        "eos_data": ["", {}],
        "expected": expected(AntaTestStatus.SUCCESS, "The device is not affected because the BGP-LS peering configuration is not configured", None),
    },
    (SA212, "not-affected-fixed-missing-role-platform"): {
        "version": build_eos_version("4.35.7M"),
        "platform": None,
        "eos_data": [BGP_CONFIG, {}],
        "expected": expected(AntaTestStatus.SUCCESS, "The device is not affected because EOS version '4.35.7M' is outside the affected releases", None),
    },
    (SA212, "not-affected-ceos-missing-role-and-version"): {
        "version": None,
        "platform": build_eos_platform("cEOSLab"),
        "eos_data": [BGP_CONFIG, {}],
        "expected": expected(AntaTestStatus.SUCCESS, "The device is not affected because platform 'cEOSLab' is outside the affected platform scope", None),
    },
    (SA212, "error-missing-role"): {
        "version": build_eos_version("4.35.6M"),
        "platform": build_eos_platform("CloudEOS"),
        "eos_data": [BGP_CONFIG, {"vrfs": {}}],
        "expected": expected(
            AntaTestStatus.ERROR,
            "The test could not determine the Pathfinder role because the 'show adaptive-virtual-topology path' output is incomplete",
            None,
        ),
    },
    (SA212, "error-incomplete-scope-and-peering"): {
        "version": None,
        "platform": None,
        "eos_data": ["router bgp", {"role": "not-a-role"}],
        "expected": expected(
            AntaTestStatus.ERROR,
            "The test could not determine the EOS version because it is missing from device metadata. "
            "The test could not determine the platform identity because it is missing from device metadata. "
            "The test could not determine the BGP-LS peering because the 'show running-config | section router bgp' output is invalid. "
            "The test could not determine the Pathfinder role because the 'show adaptive-virtual-topology path' output is invalid.",
            None,
        ),
    },
}

for _role in ("edge", "zone transit", "region transit", "unknown"):
    _DATA[(SA212, f"not-affected-valid-{_role}")] = {
        "version": None,
        "platform": None,
        "eos_data": [BGP_CONFIG, {"role": _role}],
        "expected": expected(AntaTestStatus.SUCCESS, "The device is not affected because the Pathfinder role is disabled", None),
    }


for _scenario, _config in (
    (
        "dynamic-group-no-runtime-neighbors",
        (
            "router bgp 65000\n"
            "   neighbor DYNAMIC peer group\n"
            "   bgp listen range 198.51.100.0/24 peer-group DYNAMIC\n"
            "   address-family link-state\n"
            "      neighbor DYNAMIC activate\n"
        ),
    ),
    ("unused-activated-group", "router bgp 65000\n   neighbor UNUSED peer group\n   address-family link-state\n      neighbor UNUSED activate\n"),
    (
        "mixed-shutdown-and-enabled",
        BGP_CONFIG.replace("   address-family", "   neighbor SHUT shutdown\n   address-family").replace(
            "      neighbor 198", "      neighbor SHUT activate\n      neighbor 198"
        ),
    ),
):
    _DATA[(SA212, f"affected-{_scenario}")] = {
        "version": build_eos_version("4.35.6M"),
        "platform": build_eos_platform("CloudEOS"),
        "eos_data": [_config, {"role": "pathfinder"}],
        "expected": expected(
            AntaTestStatus.FAILURE,
            "The device is affected because EOS version '4.35.6M' is affected, platform 'CloudEOS' is within the affected platform scope, "
            "the BGP-LS peering configuration is configured, and the Pathfinder role is enabled",
            EXPECTED_REMEDIATION,
        ),
    }

_DATA[(SA212, "not-affected-persistently-shutdown-only-neighbor")] = {
    "version": None,
    "platform": None,
    "eos_data": [BGP_CONFIG.replace("   address-family", "   neighbor 198.51.100.2 shutdown\n   address-family"), {}],
    "expected": expected(AntaTestStatus.SUCCESS, "The device is not affected because the BGP-LS peering configuration is not configured", None),
}

_DATA[(SA212, "affected-raw-veos-identity")] = {
    "version": build_eos_version("4.35.6M"),
    "platform": build_eos_platform("vEOS"),
    "eos_data": [BGP_CONFIG, {"role": "pathfinder"}],
    "expected": expected(
        AntaTestStatus.FAILURE,
        "The device is affected because EOS version '4.35.6M' is affected, platform 'vEOS' is within the affected platform scope, "
        "the BGP-LS peering configuration is configured, and the Pathfinder role is enabled",
        EXPECTED_REMEDIATION,
    ),
}

_DATA[(SA212, "affected-cvx-family-identity")] = {
    "version": build_eos_version("4.35.6M"),
    "platform": PlatformIdentity(model="CVX", type=PlatformType.VIRTUAL, modules=(), platform_families=frozenset({PlatformFamily.CVX})),
    "eos_data": [BGP_CONFIG, {"role": "pathfinder"}],
    "expected": expected(
        AntaTestStatus.FAILURE,
        "The device is affected because EOS version '4.35.6M' is affected, platform 'CVX' is within the affected platform scope, "
        "the BGP-LS peering configuration is configured, and the Pathfinder role is enabled",
        EXPECTED_REMEDIATION,
    ),
}

_DATA[(SA212, "not-affected-explicit-veos-lab")] = {
    "version": None,
    "platform": build_eos_platform("vEOS-lab"),
    "eos_data": [BGP_CONFIG, {}],
    "expected": expected(AntaTestStatus.SUCCESS, "The device is not affected because platform 'vEOS-lab' is outside the affected platform scope", None),
}

for _scenario, _version, _config, _role, _message in (
    ("fixed", "4.35.7M", BGP_CONFIG, "pathfinder", "EOS version '4.35.7M' is outside the affected releases"),
    ("no-activation", "4.35.6M", "router bgp 65000\n", "pathfinder", "the BGP-LS peering configuration is not configured"),
    ("edge", "4.35.6M", BGP_CONFIG, "edge", "the Pathfinder role is disabled"),
):
    _DATA[(SA212, f"not-affected-veos-{_scenario}")] = {
        "version": build_eos_version(_version),
        "platform": build_eos_platform("vEOS"),
        "eos_data": [_config, {"role": _role}],
        "expected": expected(AntaTestStatus.SUCCESS, f"The device is not affected because {_message}", None),
    }


def test_v1_7060xe7_exclusion() -> None:
    """The v1 source explicitly excludes the 7060XE7 series."""
    assert isinstance(assess("DCS-7060XE7"), NotAffectedResult)
