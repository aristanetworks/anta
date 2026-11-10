# Copyright (c) 2026 Arista Networks, Inc.
# Use of this source code is governed by the Apache License 2.0
# that can be found in the LICENSE file.
"""Unit tests for Arista Security Advisory 211."""

from __future__ import annotations

from copy import deepcopy
from datetime import date
from functools import partial
from typing import TYPE_CHECKING

import pytest

from anta._advisory.eos_versions import AffectedStatus, evaluate_version
from anta._advisory.facts.bgp_link_state import BgpLinkStateDpsConsumerFact
from anta._advisory.facts.eos import EosVersionFact
from anta._advisory.facts.models import ConfigurationState, FactProblemKind, FactSource, FactSourceKind
from anta._advisory.findings.models import AffectedResult, ErrorResult, NotAffectedResult
from anta._advisory.remediation import ChangeSoftwareVersion, FixedRelease, KnownFixedReleases, RemediationPlan, SoftwareTarget
from anta._eos.version import EOSVersion, parse_eos_version
from anta.result_manager.models import AntaTestStatus
from anta.tests.advisories.sa_211 import ADVISORY, AFFECTED_VERSION_MATRIX, SA211, _assess_sa211
from tests.units._advisory.facts.test_bgp_link_state import CONFIG, INSTANCE
from tests.units.anta_tests import build_eos_version, test  # noqa: F401 - Parameterized advisory harness.
from tests.units.anta_tests.advisories import build_expected_advisory_result

if TYPE_CHECKING:
    from tests.units.anta_tests import AntaUnitTestData

SOURCE = FactSource("unit test", FactSourceKind.DEVICE_METADATA)
EXPECTED_REMEDIATION = RemediationPlan(
    ChangeSoftwareVersion(
        software=SoftwareTarget.EOS,
        current_version=EOSVersion(4, 35, 0, suffix="F"),
        destination=KnownFixedReleases(
            (
                FixedRelease(EOSVersion(4, 33, 11, suffix="M")),
                FixedRelease(EOSVersion(4, 34, 9, suffix="M")),
                FixedRelease(EOSVersion(4, 35, 7, suffix="M")),
                FixedRelease(EOSVersion(4, 36, 3, suffix="M")),
                FixedRelease(EOSVersion(4, 37, 0, suffix="F")),
            )
        ),
    )
)
expected = partial(build_expected_advisory_result, "CVE-2026-120978")
_DATA: AntaUnitTestData = {
    (SA211, "configured-down-peer-no-pathfinder-or-auth-without-platform-gate"): {
        "version": build_eos_version("4.35.0F"),
        "platform": None,
        "eos_data": [CONFIG, INSTANCE],
        "expected": expected(
            AntaTestStatus.FAILURE,
            "The device is affected because EOS version '4.35.0F' is affected and the BGP-LS DPS consumer peering configuration is configured",
            EXPECTED_REMEDIATION,
        ),
    },
    (SA211, "no-bgp-without-version-or-operational-evidence"): {
        "version": None,
        "platform": None,
        "eos_data": ["", {}],
        "expected": expected(AntaTestStatus.SUCCESS, "The device is not affected because the BGP-LS DPS consumer peering configuration is not configured", None),
    },
    (SA211, "fixed-with-invalid-roles"): {
        "version": build_eos_version("4.35.7M"),
        "platform": None,
        "eos_data": [CONFIG, {}],
        "expected": expected(AntaTestStatus.SUCCESS, "The device is not affected because EOS version '4.35.7M' is outside the affected releases", None),
    },
    (SA211, "missing-role-instance"): {
        "version": build_eos_version("4.35.0F"),
        "platform": None,
        "eos_data": [CONFIG, {}],
        "expected": expected(
            AntaTestStatus.ERROR, "The test could not determine the BGP-LS DPS consumer peering because the 'show bgp instance vrf all' output is incomplete", None
        ),
    },
    (SA211, "all-required-unavailable-facts-aggregated"): {
        "version": None,
        "platform": None,
        "eos_data": [CONFIG, {}],
        "expected": expected(
            AntaTestStatus.ERROR,
            "The test could not determine the EOS version because it is missing from device metadata. "
            "The test could not determine the BGP-LS DPS consumer peering because the 'show bgp instance vrf all' output is incomplete.",
            None,
        ),
    },
}

_NO_CONSUMER = deepcopy(INSTANCE)
_NO_CONSUMER["vrfs"]["default"]["afiSafiConfig"]["linkState"]["bgpLsProtoRoles"] = []
_DATA[(SA211, "no-consumer-is-decisive-without-software")] = {
    "version": None,
    "platform": None,
    "eos_data": [CONFIG.replace("      path-selection role consumer propagator\n", ""), _NO_CONSUMER],
    "expected": expected(AntaTestStatus.SUCCESS, "The device is not affected because the BGP-LS DPS consumer peering configuration is not configured", None),
}

for _name, _config in {
    "qualified-consumer-with-malformed-sibling-config": CONFIG + "   vrf RED\n      neighbor Q shutdown extra\n",
    "qualified-consumer-with-missing-sibling-role": CONFIG + "   vrf RED\n      address-family link-state\n         neighbor Q activate\n",
    "unused-activated-group": CONFIG.replace("   neighbor 192.0.2.212 peer group BGP_LS_PEERS\n", ""),
    "dynamic-listener-without-runtime-peer": CONFIG.replace(
        "   neighbor 192.0.2.212 peer group BGP_LS_PEERS\n", "   bgp listen range 198.51.100.0/24 peer-group BGP_LS_PEERS remote-as 65212\n"
    ),
}.items():
    _DATA[(SA211, _name)] = {
        "version": build_eos_version("4.35.0F"),
        "platform": None,
        "eos_data": [_config, INSTANCE],
        "expected": expected(
            AntaTestStatus.FAILURE,
            "The device is affected because EOS version '4.35.0F' is affected and the BGP-LS DPS consumer peering configuration is configured",
            EXPECTED_REMEDIATION,
        ),
    }

_DATA[(SA211, "confirmed-persistent-shutdown-without-software-or-role")] = {
    "version": None,
    "platform": None,
    "eos_data": [CONFIG.replace("   router-id", "   shutdown\n   router-id"), {}],
    "expected": expected(AntaTestStatus.SUCCESS, "The device is not affected because the BGP-LS DPS consumer peering configuration is not configured", None),
}


@pytest.mark.parametrize(
    ("version", "affected"),
    [
        ("4.0.0F", True),
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
        ("4.37.99M", False),
        ("4.38.0F", False),
        ("5.0.0F", False),
    ],
)
def test_source_boundaries(version: str, affected: bool) -> None:
    """Encode every named fix, older unbounded trains, and hotfix edges."""
    status = evaluate_version(parse_eos_version(version).unwrap(), AFFECTED_VERSION_MATRIX).affected_status
    assert status is (AffectedStatus.AFFECTED if affected else AffectedStatus.NOT_AFFECTED)


def test_required_problems_are_aggregated() -> None:
    """Retain software and exposure problems rather than version-only failure."""
    finding = _assess_sa211(
        EosVersionFact.unavailable(FactProblemKind.MISSING, SOURCE),
        BgpLinkStateDpsConsumerFact.unavailable(FactProblemKind.MALFORMED, SOURCE),
    )
    assert isinstance(finding, ErrorResult)
    assert tuple(problem.definition for problem in finding.problems) == (EosVersionFact, BgpLinkStateDpsConsumerFact)


def test_decisive_absence_short_circuits_missing_software() -> None:
    """Complete absence evidence independently decides the result."""
    finding = _assess_sa211(
        EosVersionFact.unavailable(FactProblemKind.MISSING, SOURCE),
        BgpLinkStateDpsConsumerFact(ConfigurationState.NOT_CONFIGURED).available(SOURCE),
    )
    assert isinstance(finding, NotAffectedResult)


def test_affected_result_has_independent_remediation_and_single_cve() -> None:
    """Assess one vulnerability with source-defined fixed releases."""
    finding = _assess_sa211(
        EosVersionFact.from_version(EOSVersion(4, 35, 0, suffix="F")).available(SOURCE),
        BgpLinkStateDpsConsumerFact(ConfigurationState.CONFIGURED).available(SOURCE),
    )
    assert isinstance(finding, AffectedResult)
    assert finding.vulnerability_id == "CVE-2026-120978"
    assert finding.remediation == EXPECTED_REMEDIATION


def test_fixed_release_is_decisive_without_exposure_evidence() -> None:
    """A named software fix independently closes the exposure."""
    finding = _assess_sa211(
        EosVersionFact.from_version(EOSVersion(4, 36, 3, suffix="M")).available(SOURCE),
        BgpLinkStateDpsConsumerFact.unavailable(FactProblemKind.COLLECTION_FAILED, SOURCE),
    )
    assert isinstance(finding, NotAffectedResult)


def test_allocated_metadata() -> None:
    """Use the assigned SA/CVE identity and approved batch date."""
    assert ADVISORY.sa_number == "0211"
    assert ADVISORY.last_updated == date(2026, 11, 10)
    assert tuple(v.id for v in ADVISORY.vulnerabilities) == ("CVE-2026-120978",)
