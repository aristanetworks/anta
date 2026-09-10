# Copyright (c) 2026 Arista Networks, Inc.
# Use of this source code is governed by the Apache License 2.0
# that can be found in the LICENSE file.
"""Unit tests for Arista Security Advisory 168."""

from __future__ import annotations

from functools import partial
from typing import TYPE_CHECKING

from anta._advisory.eos_versions import AffectedStatus
from anta._advisory.facts.eos import EosVersionFact
from anta._advisory.facts.management import GnmiTransportFact, NetconfTransportFact, RestconfTransportFact
from anta._advisory.facts.models import AvailableFact, FeatureName, FeatureState, FeatureValue
from anta._advisory.findings.models import AffectedResult, ErrorResult, NotAffectedResult
from anta._advisory.remediation import (
    AllOf,
    ChangeSoftwareVersion,
    ConditionalAction,
    FixedRelease,
    KnownFixedReleases,
    OperationalAction,
    RemediationPlan,
    SoftwareTarget,
)
from anta._eos.version import EOSVersion
from anta.result_manager.models import AntaTestStatus
from anta.tests.advisories.sa_168 import ADVISORY, AFFECTED_VERSION_MATRIX, SA168, _assess_sa168
from tests.units.anta_tests import build_eos_version, test
from tests.units.anta_tests.advisories import build_expected_advisory_result
from tests.units.anta_tests.advisories.fact_builders import assert_version_statuses, available_fact, eos_version_fact, unavailable_fact

if TYPE_CHECKING:
    from tests.units.anta_tests import AntaUnitTestData

FIXED_RELEASES = (FixedRelease(EOSVersion(4, 36, 2, suffix="F")),)
REMEDIATION = RemediationPlan(
    AllOf(
        (
            ChangeSoftwareVersion(SoftwareTarget.EOS, EOSVersion(4, 36, 1, suffix="F"), KnownFixedReleases(FIXED_RELEASES)),
            ConditionalAction(
                "sensitive information was logged",
                OperationalAction("Clean up affected local and remote logs, including rotated logs, as described in the advisory."),
            ),
            ConditionalAction(
                "logged information contained secrets",
                OperationalAction("Rotate exposed or compromised secrets as described in the advisory."),
            ),
        )
    )
)
expected_result = partial(build_expected_advisory_result, ADVISORY.vulnerabilities[0].id)


def service_fact(
    definition: type[GnmiTransportFact | RestconfTransportFact | NetconfTransportFact], feature: FeatureName, state: FeatureState
) -> AvailableFact[FeatureValue]:
    """Build one normalized OpenConfig service fact."""
    return available_fact(definition, FeatureValue(feature, state))


def test_sa168_assessment_contract() -> None:
    """Preserve OR semantics and only error when no service proves exposure."""
    gnmi_disabled = service_fact(GnmiTransportFact, FeatureName.GNMI, FeatureState.DISABLED)
    rest_disabled = service_fact(RestconfTransportFact, FeatureName.RESTCONF, FeatureState.DISABLED)
    netconf_disabled = service_fact(NetconfTransportFact, FeatureName.NETCONF, FeatureState.DISABLED)
    gnmi_enabled = service_fact(GnmiTransportFact, FeatureName.GNMI, FeatureState.ENABLED)
    rest_missing = unavailable_fact(RestconfTransportFact)
    assert isinstance(_assess_sa168(unavailable_fact(EosVersionFact), (gnmi_disabled, rest_disabled, netconf_disabled)), NotAffectedResult)
    affected = _assess_sa168(eos_version_fact("4.36.1F"), (gnmi_enabled, rest_missing, netconf_disabled))
    assert isinstance(affected, AffectedResult)
    assert affected.remediation == REMEDIATION
    assert isinstance(_assess_sa168(eos_version_fact("4.36.2F"), (gnmi_enabled, rest_missing, netconf_disabled)), NotAffectedResult)
    assert isinstance(_assess_sa168(eos_version_fact("4.36.1F"), (gnmi_disabled, rest_missing, netconf_disabled)), ErrorResult)


def test_sa168_version_boundaries() -> None:
    """Cover the sole fixed train and all affected prior EOS trains."""
    assert_version_statuses(
        AFFECTED_VERSION_MATRIX,
        (
            ("4.36.1F", AffectedStatus.AFFECTED),
            ("4.36.2F", AffectedStatus.NOT_AFFECTED),
            ("4.35.99M", AffectedStatus.AFFECTED),
            ("4.34.99M", AffectedStatus.AFFECTED),
            ("4.0.0F", AffectedStatus.AFFECTED),
            ("4.37.0F", AffectedStatus.NOT_AFFECTED),
        ),
    )


_DATA: AntaUnitTestData = {
    (SA168, "failure-gnmi-enabled"): {
        "version": build_eos_version("4.36.1F"),
        "eos_data": [{"enabled": True}, {"enabled": False}, {"enabled": False}],
        "expected": expected_result(AntaTestStatus.FAILURE, "gNMI feature is enabled", REMEDIATION),
    },
    (SA168, "failure-restconf-enabled"): {
        "version": build_eos_version("4.36.1F"),
        "eos_data": [{"enabled": False}, {"enabled": True}, {"enabled": False}],
        "expected": expected_result(AntaTestStatus.FAILURE, "RESTCONF feature is enabled", REMEDIATION),
    },
    (SA168, "failure-netconf-enabled"): {
        "version": build_eos_version("4.36.1F"),
        "eos_data": [{"enabled": False}, {"enabled": False}, {"enabled": True}],
        "expected": expected_result(AntaTestStatus.FAILURE, "NETCONF feature is enabled", REMEDIATION),
    },
    (SA168, "success-all-services-disabled"): {
        "version": None,
        "eos_data": [{"enabled": False}, {"enabled": False}, {"enabled": False}],
        "expected": expected_result(AntaTestStatus.SUCCESS, "gNMI feature is disabled", None),
    },
    (SA168, "success-fixed-version"): {
        "version": build_eos_version("4.36.2F"),
        "eos_data": [{"enabled": True}, {"enabled": False}, {"enabled": False}],
        "expected": expected_result(AntaTestStatus.SUCCESS, "outside the affected releases", None),
    },
    (SA168, "error-no-exposure-and-malformed-gnmi"): {
        "version": build_eos_version("4.36.1F"),
        "eos_data": [{}, {"enabled": False}, {"enabled": False}],
        "expected": expected_result(AntaTestStatus.ERROR, "gNMI transport state", None),
    },
}
