# Copyright (c) 2026 Arista Networks, Inc.
# Use of this source code is governed by the Apache License 2.0
# that can be found in the LICENSE file.
"""Independent source-boundary and end-to-end tests for SA-0201 revision 1.1."""

# The expected remediation stays independent from the production command literal.
# pylint: disable=duplicate-code

from __future__ import annotations

from datetime import date
from functools import partial
from typing import TYPE_CHECKING
from unittest.mock import AsyncMock

import pytest

from anta._advisory.eos_versions import AffectedStatus, evaluate_version
from anta._advisory.facts.eos import EosVersionFact
from anta._advisory.facts.models import AvailableFact, Fact, FactProblemKind, FactSource, FactSourceKind, FeatureState
from anta._advisory.facts.platform import PlatformIdentityFact
from anta._advisory.facts.software import TerminAttrVersionFact
from anta._advisory.facts.terminattr import TerminAttrDefaultCaTlsFact, TerminAttrTlsConnection
from anta._advisory.findings.models import AffectedResult, ComponentVersionAssessment, ErrorResult, InconclusiveResult, NotAffectedResult, VersionRelation
from anta._advisory.models import _AdvisoryVulnerabilitySeverity
from anta._advisory.remediation import (
    AnyOf,
    ApplyConfiguration,
    ChangeSoftwareVersion,
    ConditionalAction,
    FixedRelease,
    KnownFixedReleases,
    NextPublishedFixedRelease,
    RemediationPlan,
    RunCommand,
    Sequence,
    SoftwareTarget,
)
from anta._advisory.results import _AdvisoryAtomicTestResult, _get_atomic_vulnerability_ids
from anta._advisory.status import AdvisoryStatus
from anta._advisory.version import SemanticVersion
from anta._eos.platform import PlatformFamily, PlatformType
from anta._eos.version import EOSVersion, parse_eos_version
from anta.models import AntaCommand
from anta.result_manager.models import AntaTestStatus
from anta.tests.advisories.sa_201 import (
    ADVISORY,
    AFFECTED_VERSION_MATRIX,
    FIXED_RELEASES,
    SA201,
    _assess_sa201,
    _compatible_terminattr_fixes,
    _terminattr_version_assessment,
)
from tests.units.anta_tests import build_eos_platform, build_eos_version, test
from tests.units.anta_tests.advisories import OfflineAntaDevice, build_expected_advisory_result

if TYPE_CHECKING:
    from tests.units.anta_tests import AntaUnitTest, AntaUnitTestData

SOURCE = FactSource("device metadata", FactSourceKind.DEVICE_METADATA)
CONFIG_SOURCE = FactSource("show running-configuration | section TerminAttr", FactSourceKind.COMMAND)
PACKAGE_SOURCE = FactSource("show version detail", FactSourceKind.COMMAND)
CONFIG = (
    "daemon TerminAttr\n"
    "   exec /usr/bin/TerminAttr -cvaddr=apiserver.arista.io:443 -cvcompression=gzip -cvvrf=management "
    "-taillogs -cvauth=token-secure,/mnt/flash/token.json\n"
    "   no shutdown\n"
)
CUSTOM_CA_CONFIG = CONFIG.replace("/mnt/flash/token.json", "/mnt/flash/token.json,/mnt/flash/ca.pem")
PACKAGE: dict[str, object] = {"details": {"packages": {"TerminAttr-core": {"version": "v1.46.2", "release": "1"}}}}
FIXED_PACKAGE: dict[str, object] = {"details": {"packages": {"TerminAttr-core": {"version": "v1.46.3", "release": "1"}}}}

# This fixture independently transcribes the published mitigation, rather than
# importing the implementation's commands or building expectations from them.
EXPECTED_CA_CONFIGURATION = (
    "event-handler sa_0201_fix",
    "trigger on-boot",
    "trigger on-config disabled",
    "action bash",
    "d=/etc/pki/ca-trust/source/blocklist; [ -d $d ] || d=/etc/pki/ca-trust/source/blacklist",
    "trust extract --overwrite --format=pem-bundle \\",
    "  --filter='pkcs11:object=Comodo%20AAA%20Services%20root;type=cert' \\",
    "  $d/Comodo_AAA_Services_root.pem &&",
    "openssl x509 -in $d/Comodo_AAA_Services_root.pem \\",
    "  -out $d/Comodo_AAA_Services_root.pem \\",
    "  -trustout -addreject anyExtendedKeyUsage &&",
    "trust extract --overwrite --format=pem-bundle \\",
    "  --filter='pkcs11:object=emSign%20ECC%20Root%20CA%20-%20G3;type=cert' \\",
    "  $d/emSign_ECC_Root_CA_-_G3.pem &&",
    "openssl x509 -in $d/emSign_ECC_Root_CA_-_G3.pem \\",
    "  -out $d/emSign_ECC_Root_CA_-_G3.pem \\",
    "  -trustout -addreject anyExtendedKeyUsage &&",
    "update-ca-trust &&",
    "kill -9 $(pidof TerminAttr)",
    "EOF",
    "exit",
)
EXPECTED_CONDITION = "custom scripts or programs use the default EOS trust store for outbound TLS"
EXPECTED_EOS_ACTION = ChangeSoftwareVersion(SoftwareTarget.EOS, EOSVersion(4, 36, 3, suffix="M"), NextPublishedFixedRelease())
EXPECTED_EOS_PLAN = RemediationPlan(EXPECTED_EOS_ACTION)
EXPECTED_COMBINED_PLAN = RemediationPlan(
    AnyOf(
        (
            EXPECTED_EOS_ACTION,
            Sequence(
                (
                    ChangeSoftwareVersion(
                        SoftwareTarget.TERMINATTR,
                        SemanticVersion(1, 46, 2, prefix="v"),
                        KnownFixedReleases((FixedRelease(SemanticVersion(1, 46, 3, prefix="v")),)),
                    ),
                    ConditionalAction(EXPECTED_CONDITION, ApplyConfiguration(EXPECTED_CA_CONFIGURATION)),
                    ConditionalAction(EXPECTED_CONDITION, RunCommand(("reload",))),
                )
            ),
        )
    )
)
EXPECTED_COMPONENT_ONLY_PLAN = RemediationPlan(ChangeSoftwareVersion(SoftwareTarget.TERMINATTR, SemanticVersion(1, 46, 2, prefix="v"), NextPublishedFixedRelease()))
expected_result = partial(build_expected_advisory_result, "CVE-2026-111943")
CUSTOM_UNRESOLVED = "custom programs' outbound TLS behavior and trust-store selection is device state not exposed."
INCONCLUSIVE_PREFIX = "The assessment is inconclusive and the device may be affected. Indications: "
EOS_AND_PLATFORM = "EOS version '4.36.3M' is affected and platform 'cEOSLab' is within the affected platform scope"

_DATA: AntaUnitTestData = {
    (SA201, "affected-cvaas-default-ca"): {
        "version": build_eos_version("4.36.3M"),
        "platform": build_eos_platform("cEOSLab"),
        "eos_data": [CONFIG, PACKAGE],
        "expected": expected_result(
            AntaTestStatus.FAILURE,
            "The device is affected because EOS version '4.36.3M' is affected, platform 'cEOSLab' is within the affected platform scope, "
            "TerminAttr 'v1.46.2' is affected, and the TerminAttr TLS client using the default CA trust store is enabled.",
            EXPECTED_COMBINED_PLAN,
        ),
    },
    (SA201, "component-upgrade-leaves-custom-programs-unresolved"): {
        "version": build_eos_version("4.36.3M"),
        "platform": build_eos_platform("cEOSLab"),
        "eos_data": [CONFIG, FIXED_PACKAGE],
        "expected": expected_result(
            AntaTestStatus.FAILURE,
            INCONCLUSIVE_PREFIX + "EOS version '4.36.3M' is affected, platform 'cEOSLab' is within the affected platform scope, "
            "and TerminAttr 'v1.46.3' is outside the affected releases. Unresolved: " + CUSTOM_UNRESOLVED,
            EXPECTED_EOS_PLAN,
        ),
    },
    (SA201, "explicit-ca-leaves-custom-programs-unresolved"): {
        "version": build_eos_version("4.36.3M"),
        "platform": build_eos_platform("cEOSLab"),
        "eos_data": [CUSTOM_CA_CONFIG, {}],
        "expected": expected_result(AntaTestStatus.FAILURE, INCONCLUSIVE_PREFIX + EOS_AND_PLATFORM + ". Unresolved: " + CUSTOM_UNRESOLVED, EXPECTED_EOS_PLAN),
    },
    (SA201, "absent-terminattr-does-not-prove-custom-program-absence"): {
        "version": build_eos_version("4.36.3M"),
        "platform": build_eos_platform("cEOSLab"),
        "eos_data": ["", {}],
        "expected": expected_result(AntaTestStatus.FAILURE, INCONCLUSIVE_PREFIX + EOS_AND_PLATFORM + ". Unresolved: " + CUSTOM_UNRESOLVED, EXPECTED_EOS_PLAN),
    },
    (SA201, "component-remains-affected-outside-eos-list"): {
        "version": build_eos_version("4.36.4M"),
        "platform": build_eos_platform("cEOSLab"),
        "eos_data": [CONFIG, PACKAGE],
        "expected": expected_result(
            AntaTestStatus.FAILURE,
            "The device is affected because EOS version '4.36.4M' is outside the affected releases, platform 'cEOSLab' is within the affected platform "
            "scope, TerminAttr 'v1.46.2' is affected, and the TerminAttr TLS client using the default CA trust store is enabled.",
            EXPECTED_COMPONENT_ONLY_PLAN,
        ),
    },
    (SA201, "both-versions-outside-list-ignore-malformed-unneeded-config"): {
        "version": build_eos_version("4.36.4M"),
        "eos_data": ["malformed", FIXED_PACKAGE],
        "expected": expected_result(
            AntaTestStatus.SUCCESS,
            "The device is not affected because EOS version '4.36.4M' is outside the affected releases and TerminAttr 'v1.46.3' is outside the affected releases.",
            None,
        ),
    },
    (SA201, "eos-outside-and-client-absent"): {
        "version": build_eos_version("4.36.4M"),
        "eos_data": ["", {}],
        "expected": expected_result(
            AntaTestStatus.SUCCESS,
            "The device is not affected because EOS version '4.36.4M' is outside the affected releases "
            "and the TerminAttr TLS client using the default CA trust store is disabled.",
            None,
        ),
    },
    (SA201, "eos-outside-and-explicit-ca"): {
        "version": build_eos_version("4.36.4M"),
        "eos_data": [CUSTOM_CA_CONFIG, {}],
        "expected": expected_result(
            AntaTestStatus.SUCCESS,
            "The device is not affected because EOS version '4.36.4M' is outside the affected releases "
            "and the TerminAttr TLS client using the default CA trust store is disabled.",
            None,
        ),
    },
    (SA201, "unknown-destination-is-not-assumed-cvaas"): {
        "version": build_eos_version("4.36.4M"),
        "platform": build_eos_platform("cEOSLab"),
        "eos_data": [CONFIG.replace("apiserver.arista.io", "cloud.example"), PACKAGE],
        "expected": expected_result(
            AntaTestStatus.FAILURE,
            INCONCLUSIVE_PREFIX + "EOS version '4.36.4M' is outside the affected releases, platform 'cEOSLab' is within the affected platform scope, "
            "TerminAttr 'v1.46.2' is affected, and the TerminAttr TLS client using the default CA trust store is enabled. "
            "Unresolved: whether the configured default-CA TLS destination is CVaaS is external state.",
            EXPECTED_COMPONENT_ONLY_PLAN,
        ),
    },
    (SA201, "ambiguous-veos-is-not-a-safe-cvx-exclusion"): {
        "version": build_eos_version("4.36.3M"),
        "platform": build_eos_platform("vEOS"),
        "eos_data": ["", {}],
        "expected": expected_result(
            AntaTestStatus.FAILURE,
            INCONCLUSIVE_PREFIX + "EOS version '4.36.3M' is affected. Unresolved: CloudVision eXchange versus CloudEOS identity is incomplete platform "
            "identity and " + CUSTOM_UNRESOLVED,
            EXPECTED_EOS_PLAN,
        ),
    },
    (SA201, "invalid-configuration-retains-command-source"): {
        "version": build_eos_version("4.36.3M"),
        "platform": build_eos_platform("cEOSLab"),
        "eos_data": ["invalid", PACKAGE],
        "expected": expected_result(
            AntaTestStatus.ERROR,
            "The test could not determine the TerminAttr default-CA TLS client configuration because "
            "the 'show running-configuration | section TerminAttr' output is invalid.",
            None,
        ),
    },
    (SA201, "missing-component-retains-package-command-source"): {
        "version": build_eos_version("4.36.3M"),
        "platform": build_eos_platform("cEOSLab"),
        "eos_data": [CONFIG, {}],
        "expected": expected_result(
            AntaTestStatus.ERROR,
            "The test could not determine the TerminAttr version because the 'show version detail' output is incomplete.",
            None,
        ),
    },
}


def version_fact(version: str | None = "4.36.3M") -> Fact[EosVersionFact]:
    """Construct EOS metadata independently of collection."""
    if version is None:
        return EosVersionFact.unavailable(FactProblemKind.MISSING, SOURCE)
    return EosVersionFact.from_version(parse_eos_version(version).unwrap()).available(SOURCE)


def platform_fact(family: PlatformFamily = PlatformFamily.CEOS_LAB) -> AvailableFact[PlatformIdentityFact]:
    """Construct a semantic platform identity independently of the platform parser."""
    return PlatformIdentityFact("test-platform", PlatformType.VIRTUAL, (), frozenset({family})).available(SOURCE)


def tls_fact(*, ca_file: str | None = None, address: str = "apiserver.arista.io:443") -> AvailableFact[TerminAttrDefaultCaTlsFact]:
    """Construct an enabled TLS client or an explicitly scoped CA selection."""
    state = FeatureState.ENABLED if ca_file is None else FeatureState.DISABLED
    return TerminAttrDefaultCaTlsFact(state, (TerminAttrTlsConnection("default", (address,), ca_file),)).available(CONFIG_SOURCE)


@pytest.mark.parametrize(
    ("version", "affected"),
    [
        ("4.1.0F", True),
        ("4.27.99M", True),
        ("4.28.0F", True),
        ("4.28.14M", True),
        ("4.28.14.1M", True),
        ("4.28.15M", False),
        ("4.29.0F", True),
        ("4.29.99M", True),
        ("4.30.0F", True),
        ("4.30.99M", True),
        ("4.31.0F", True),
        ("4.31.99M", True),
        ("4.32.0F", True),
        ("4.32.99M", True),
        ("4.33.0F", True),
        ("4.33.11M", True),
        ("4.33.11.1M", True),
        ("4.33.12M", False),
        ("4.34.0F", True),
        ("4.34.9M", True),
        ("4.34.9.1M", True),
        ("4.34.10M", False),
        ("4.35.0F", True),
        ("4.35.7M", True),
        ("4.35.7.1M", True),
        ("4.35.8M", False),
        ("4.36.0F", True),
        ("4.36.3M", True),
        ("4.36.3.1M", True),
        ("4.36.4M", False),
        ("4.37.0F", False),
        ("5.0.0F", False),
    ],
)
def test_eos_source_boundaries(version: str, affected: bool) -> None:
    """Check every affected EOS train without inventing unpublished fixed releases."""
    expected = AffectedStatus.AFFECTED if affected else AffectedStatus.NOT_AFFECTED
    assert evaluate_version(parse_eos_version(version).unwrap(), AFFECTED_VERSION_MATRIX).affected_status is expected
    assert not FIXED_RELEASES


@pytest.mark.parametrize(
    ("version", "affected"),
    [
        ("v0.99.99", True),
        ("v1.0.0", True),
        ("v1.30.99", True),
        ("v1.31.0", True),
        ("v1.31.17", True),
        ("v1.31.18", False),
        ("v1.32.99", True),
        ("v1.33.99", True),
        ("v1.34.0", True),
        ("v1.34.14", True),
        ("v1.34.15", False),
        ("v1.35.99", True),
        ("v1.36.99", True),
        ("v1.37.0", True),
        ("v1.37.14", True),
        ("v1.37.15", False),
        ("v1.38.99", True),
        ("v1.39.99", True),
        ("v1.40.0", True),
        ("v1.40.14", True),
        ("v1.40.15", False),
        ("v1.41.99", True),
        ("v1.42.99", True),
        ("v1.43.0", True),
        ("v1.43.10", True),
        ("v1.43.11", False),
        ("v1.44.99", True),
        ("v1.45.99", True),
        ("v1.46.0", True),
        ("v1.46.2", True),
        ("v1.46.3", False),
        ("v1.47.0", False),
        ("v2.0.0", False),
    ],
)
def test_component_source_boundaries(version: str, affected: bool) -> None:
    """Check every component train, including scope boundaries without a published release recommendation."""
    result = _terminattr_version_assessment(TerminAttrVersionFact(version).available(PACKAGE_SOURCE))
    assert isinstance(result, ComponentVersionAssessment)
    assert result.relation is (VersionRelation.AFFECTED if affected else VersionRelation.OUTSIDE_SCOPE)


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
        PlatformFamily.SERIES_7700_R4,
        PlatformFamily.SERIES_7800_R3,
        PlatformFamily.SERIES_7800_R4,
        PlatformFamily.AWE_5000,
        PlatformFamily.AWE_7200_R,
        PlatformFamily.ZTX_7200,
        PlatformFamily.CLOUDEOS,
        PlatformFamily.CEOS_LAB,
        PlatformFamily.VEOS_LAB,
    ],
)
def test_all_listed_eos_families(family: PlatformFamily) -> None:
    """Every source-listed EOS family retains its independently established TerminAttr exposure."""
    result = _assess_sa201(version_fact(), platform_fact(family), tls_fact(), TerminAttrVersionFact("v1.46.2").available(PACKAGE_SOURCE))
    assert isinstance(result, AffectedResult)


@pytest.mark.parametrize(
    ("version", "expected"),
    [
        ("4.26.9M", ("v1.31.18",)),
        ("4.27.0F", ("v1.34.15", "v1.31.18")),
        ("4.29.99M", ("v1.34.15", "v1.31.18")),
        ("4.30.0F", ("v1.46.3", "v1.43.11", "v1.34.15", "v1.31.18")),
        ("4.31.10M", ("v1.46.3", "v1.43.11", "v1.34.15", "v1.31.18")),
        ("4.31.11M", ("v1.46.3", "v1.43.11", "v1.34.15")),
        ("4.32.11M", ("v1.46.3", "v1.43.11", "v1.34.15")),
        ("4.32.12M", ("v1.46.3", "v1.43.11")),
        ("4.35.7M", ("v1.46.3", "v1.43.11")),
        ("4.35.8M", ("v1.46.3",)),
        ("4.36.3M", ("v1.46.3",)),
        ("4.36.4M", ()),
        ("4.37.0F", ()),
    ],
)
def test_component_fix_eos_compatibility(version: str, expected: tuple[str, ...]) -> None:
    """Never suggest an independently fixed TerminAttr release outside its source-supported EOS interval."""
    assert tuple(str(release.version) for release in _compatible_terminattr_fixes(parse_eos_version(version).unwrap())) == expected


def test_all_required_unavailable_facts_are_retained() -> None:
    """One missing prerequisite must not hide the other needed observations."""
    platform = PlatformIdentityFact.unavailable(FactProblemKind.MISSING, SOURCE)
    tls = TerminAttrDefaultCaTlsFact.unavailable(FactProblemKind.MALFORMED, CONFIG_SOURCE)
    component = TerminAttrVersionFact.unavailable(FactProblemKind.MISSING, PACKAGE_SOURCE)
    result = _assess_sa201(version_fact(None), platform, tls, component)
    assert isinstance(result, ErrorResult)
    assert result.problems == (version_fact(None), platform, tls, component)


@pytest.mark.parametrize("version", ["1.46.2", "v1.46", "v1.46.2-dev", "invalid"])
def test_invalid_required_component_version_is_error(version: str) -> None:
    """Unexpected package versions must not silently leave the affected range."""
    result = _assess_sa201(version_fact(), platform_fact(), tls_fact(), TerminAttrVersionFact(version).available(PACKAGE_SOURCE))
    assert isinstance(result, ErrorResult)
    assert result.problems[0].problem is FactProblemKind.INVALID


def test_disabled_component_ignores_unneeded_package_and_retains_eos_uncertainty() -> None:
    """Explicit CA selection removes the package dependency but cannot prove custom-program safety."""
    missing = TerminAttrVersionFact.unavailable(FactProblemKind.MISSING, PACKAGE_SOURCE)
    result = _assess_sa201(version_fact(), platform_fact(), tls_fact(ca_file="ca.pem"), missing)
    assert isinstance(result, InconclusiveResult)
    assert len(result.unresolved) == 1
    assert result.remediation == EXPECTED_EOS_PLAN


def test_unknown_platform_is_an_error() -> None:
    """An unrecognized platform cannot prove either an affected family or an exclusion."""
    unknown = PlatformIdentityFact("unknown", PlatformType.UNKNOWN, (), frozenset()).available(SOURCE)
    result = _assess_sa201(version_fact(), unknown, tls_fact(), TerminAttrVersionFact("v1.46.2").available(PACKAGE_SOURCE))
    assert isinstance(result, ErrorResult)


def test_unlisted_family_short_circuits_unavailable_inputs() -> None:
    """A source-excluded family can decide scope without unrelated unavailable inputs."""
    result = _assess_sa201(
        version_fact(None),
        platform_fact(PlatformFamily.SERIES_7150),
        TerminAttrDefaultCaTlsFact.unavailable(FactProblemKind.MISSING, CONFIG_SOURCE),
        TerminAttrVersionFact.unavailable(FactProblemKind.MISSING, PACKAGE_SOURCE),
    )
    assert isinstance(result, NotAffectedResult)


def test_two_independent_unobservable_properties_are_retained() -> None:
    """An unidentified cloud destination must not hide independent custom-program exposure."""
    result = _assess_sa201(version_fact(), platform_fact(), tls_fact(address="cloud.example:443"), TerminAttrVersionFact("v1.46.2").available(PACKAGE_SOURCE))
    assert isinstance(result, InconclusiveResult)
    assert len(result.unresolved) == 2


@pytest.mark.parametrize(
    ("cloud_ca", "other_ca", "result_type"),
    [
        (None, "private-ca.pem", AffectedResult),
        ("cloud-ca.pem", None, InconclusiveResult),
        ("cloud-ca.pem", "private-ca.pem", NotAffectedResult),
        (None, None, AffectedResult),
    ],
)
def test_cluster_ca_coverage_is_not_transferred(
    cloud_ca: str | None,
    other_ca: str | None,
    result_type: type[AffectedResult | InconclusiveResult | NotAffectedResult],
) -> None:
    """A CA on one cluster cannot close another cluster's independently exposed TLS path."""
    state = FeatureState.ENABLED if cloud_ca is None or other_ca is None else FeatureState.DISABLED
    tls = TerminAttrDefaultCaTlsFact(
        state,
        (
            TerminAttrTlsConnection("cloud", ("apiserver.arista.io:443",), cloud_ca),
            TerminAttrTlsConnection("other", ("onprem.example:443",), other_ca),
        ),
    ).available(CONFIG_SOURCE)
    result = _assess_sa201(version_fact("4.36.4M"), platform_fact(), tls, TerminAttrVersionFact("v1.46.2").available(PACKAGE_SOURCE))
    assert isinstance(result, result_type)


@pytest.mark.parametrize("case", list(_DATA.values()), ids=[name for _, name in _DATA])
async def test_exact_end_to_end_finding(case: AntaUnitTest) -> None:
    """Verify exact reporter prose, structured remediation, and single-CVE atomic attribution."""
    device = OfflineAntaDevice("test")
    device.version = case.get("version")
    device.platform = case.get("platform")
    await device.refresh()
    instance = SA201(device=device, eos_data=case["eos_data"])
    await instance.test()

    assert instance.result.result is case["expected"]["result"]
    expected_messages = case["expected"].get("messages", [])
    assert instance.result.messages == [f"Verify CVE-2026-111943. - {message}" for message in expected_messages]
    assert len(instance.result.atomic_results) == 1
    atomic = instance.result.atomic_results[0]
    assert isinstance(atomic, _AdvisoryAtomicTestResult)
    assert _get_atomic_vulnerability_ids(atomic) == ("CVE-2026-111943",)
    assert atomic.messages == expected_messages
    expected_atomics = case["expected"].get("atomic_results", [])
    assert len(expected_atomics) == 1
    assert atomic.remediation == expected_atomics[0].get("remediation")
    assert atomic.advisory_status in {AdvisoryStatus.AFFECTED, AdvisoryStatus.INCONCLUSIVE, AdvisoryStatus.NOT_AFFECTED, AdvisoryStatus.ERROR}


async def test_unsupported_configuration_does_not_pass() -> None:
    """An unsupported optional command is a sourced advisory error when the component requires it."""
    device = OfflineAntaDevice("test")
    device.version = parse_eos_version("4.36.3M").unwrap()
    device.platform = build_eos_platform("cEOSLab")
    await device.refresh()
    instance = SA201(device=device, eos_data=[CONFIG, PACKAGE])
    instance.instance_commands[0].output = None
    instance.instance_commands[0].errors = ["This command is not supported on this hardware platform"]
    instance.collect = AsyncMock()
    await instance.test()

    assert instance.result.result is AntaTestStatus.ERROR
    assert instance.result.messages == [
        (
            "Verify CVE-2026-111943. - The test could not determine the TerminAttr default-CA TLS client configuration because "
            "'show running-configuration | section TerminAttr' is not supported."
        )
    ]
    assert len(instance.result.atomic_results) == 1
    assert _get_atomic_vulnerability_ids(instance.result.atomic_results[0]) == ("CVE-2026-111943",)


@pytest.mark.parametrize(
    ("version", "configuration", "package", "failed_command", "semantic_status"),
    [
        ("4.36.4M", CONFIG, FIXED_PACKAGE, 0, AdvisoryStatus.NOT_AFFECTED),
        ("4.36.4M", "", PACKAGE, 1, AdvisoryStatus.NOT_AFFECTED),
        ("4.36.3M", CUSTOM_CA_CONFIG, PACKAGE, 1, AdvisoryStatus.INCONCLUSIVE),
        ("4.36.3M", CONFIG, PACKAGE, 0, AdvisoryStatus.ERROR),
        ("4.36.3M", CONFIG, PACKAGE, 1, AdvisoryStatus.ERROR),
    ],
)
async def test_deferred_collection_failure_reaches_assessment(
    version: str,
    configuration: str,
    package: dict[str, object],
    failed_command: int,
    semantic_status: AdvisoryStatus,
) -> None:
    """Ignore only failures on paths independently closed by decisive available evidence."""
    device = OfflineAntaDevice("test")
    device.version = parse_eos_version(version).unwrap()
    device.platform = build_eos_platform("cEOSLab")
    await device.refresh()
    instance = SA201(device=device, eos_data=[configuration, package])
    instance.instance_commands[failed_command].output = None
    instance.instance_commands[failed_command].errors = ["Permission denied"]
    instance.collect = AsyncMock()
    await instance.test()

    assert len(instance.result.atomic_results) == 1
    atomic = instance.result.atomic_results[0]
    assert isinstance(atomic, _AdvisoryAtomicTestResult)
    assert atomic.advisory_status is semantic_status
    if semantic_status is AdvisoryStatus.ERROR:
        label, command = (
            ("TerminAttr default-CA TLS client configuration", "show running-configuration | section TerminAttr")
            if failed_command == 0
            else ("TerminAttr version", "show version detail")
        )
        assert atomic.messages == [f"The test could not determine the {label} because '{command}' could not be collected."]
        assert atomic.remediation is None


def test_source_metadata_and_command_contract() -> None:
    """Keep revision, provisional severity estimate, publication identity, and fact-owned commands aligned."""
    assert ADVISORY.sa_number == "0201"
    assert ADVISORY.last_updated == date(2026, 10, 26)
    assert tuple(vulnerability.id for vulnerability in ADVISORY.vulnerabilities) == ("CVE-2026-111943",)
    assert ADVISORY.vulnerabilities[0].severity is _AdvisoryVulnerabilitySeverity.CRITICAL
    assert len(SA201.commands) == 2
    assert [(command.command, command.ofmt) for command in SA201.commands if isinstance(command, AntaCommand)] == [
        ("show running-configuration | section TerminAttr", "text"),
        ("show version detail", "json"),
    ]
