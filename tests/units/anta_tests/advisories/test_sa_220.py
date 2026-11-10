# Copyright (c) 2026 Arista Networks, Inc.
# Use of this source code is governed by the Apache License 2.0
# that can be found in the LICENSE file.
# pylint: disable=duplicate-code
"""Unit tests for Arista Security Advisory 220."""

from __future__ import annotations

from datetime import date
from functools import partial
from typing import TYPE_CHECKING, Any

from anta._advisory.eos_versions import AffectedStatus
from anta._advisory.facts.eos import EosVersionFact
from anta._advisory.facts.models import AvailableFact, ConfigurationState, FactProblemKind, FeatureState
from anta._advisory.facts.routing import RipDhcpManagementInterfaceFact, RipEnabledFact, RipManagementInterfaceFact
from anta._advisory.findings.models import (
    AffectedResult,
    EosReleaseAssessment,
    ErrorResult,
    NotAffectedResult,
    VersionRelation,
)
from anta._advisory.models import _AdvisoryVulnerabilitySeverity
from anta._advisory.remediation import (
    AnyOf,
    ChangeSoftwareVersion,
    ConditionalAction,
    FixedRelease,
    KnownFixedReleases,
    OperationalAction,
    RemediationPlan,
    SoftwareTarget,
)
from anta._eos.version import EOSVersion
from anta.models import AntaCommand
from anta.result_manager.models import AntaTestStatus
from anta.tests.advisories.sa_220 import ADVISORY, AFFECTED_VERSION_MATRIX, SA220, _assess_management_rip
from tests.units.anta_tests import (
    build_eos_version,
    test,  # noqa: F401 - Pytest collects this imported test function.
)
from tests.units.anta_tests.advisories import build_expected_advisory_result
from tests.units.anta_tests.advisories.fact_builders import SOURCE, assert_version_statuses, eos_version_fact

if TYPE_CHECKING:
    from tests.units.anta_tests import AntaUnitTestData

VULNERABILITY_ID = "CVE-2026-121367"
RIP_CONFIG_COMMAND = r"show running-config all section ^router\srip"
UNASSIGNED_IPV4 = "0.0.0.0"  # noqa: S104 - EOS reports an interface without an IPv4 address as 0.0.0.0/0
EXPECTED_FIXED_RELEASES = (
    FixedRelease(EOSVersion(4, 36, 3, suffix="M")),
    FixedRelease(EOSVersion(4, 35, 7, suffix="M")),
    FixedRelease(EOSVersion(4, 34, 9, suffix="M")),
    FixedRelease(EOSVersion(4, 33, 11, suffix="M")),
)
expected_result = partial(build_expected_advisory_result, VULNERABILITY_ID)


def expected_remediation(current_version: EOSVersion) -> RemediationPlan:
    """Build the advisory's alternative software, RIP-disablement, and network-scoping resolution."""
    return RemediationPlan(
        AnyOf(
            (
                ChangeSoftwareVersion(SoftwareTarget.EOS, current_version, KnownFixedReleases(EXPECTED_FIXED_RELEASES)),
                ConditionalAction("RIP is not required", OperationalAction("Disable RIP in each affected VRF as described in the advisory.")),
                ConditionalAction(
                    "RIP is required on data interfaces",
                    OperationalAction("Ensure that no RIP network prefix matches a management interface subnet in the same VRF, as described in the advisory."),
                ),
            )
        )
    )


# Shaped after EOS 4.36.0F output with RIP enabled in the management VRF; addresses use documentation ranges.
RIP_MGMT_CONFIG = """router rip vrf MGMT
   metric default 1
   distance 120
   timers 30 180 120
   network 192.0.2.0/24
   no shutdown
   no ecmp
   no ip access-group
"""
RIP_DATA_ONLY_CONFIG = """router rip vrf SA_RIP_TEST
   metric default 1
   distance 120
   timers 30 180 120
   network 198.51.100.0/29
   no shutdown
   no ecmp
   no ip access-group
"""
RIP_DEFAULT_VRF_CONFIG = """router rip
   metric default 1
   distance 120
   timers 30 180 120
   network 192.0.2.0/24
   no shutdown
   no ecmp
   no ip access-group
"""
RIP_SHUTDOWN_CONFIG = """router rip vrf MGMT
   network 192.0.2.0/24
   shutdown
"""


def interface_addressing(address: str, mask_length: int, *, dhcp: bool = False) -> dict[str, Any]:
    """Return the structured IPv4 addressing of one interface as rendered by EOS 4.36.0F."""
    return {
        "primaryIp": {"address": address, "maskLen": mask_length},
        "secondaryIps": {},
        "secondaryIpsOrderedList": [],
        "virtualIp": {"address": UNASSIGNED_IPV4, "maskLen": 0},
        "virtualSecondaryIps": {},
        "virtualSecondaryIpsOrderedList": [],
        "broadcastAddress": "255.255.255.255",
        "dhcp": dhcp,
    }


MANAGEMENT1: dict[str, Any] = {
    "name": "Management1",
    "interfaceStatus": "connected",
    "lineProtocolStatus": "up",
    "mtu": 1500,
    "interfaceAddressBrief": {"ipAddr": {"address": "192.0.2.122", "maskLen": 24}},
    "ipv4Routable240": False,
    "ipv4Routable0": False,
    "enabled": True,
    "description": "OOB_MANAGEMENT",
    "interfaceAddress": interface_addressing("192.0.2.122", 24),
    "proxyArp": False,
    "proxyArpAllowDefault": False,
    "localProxyArp": False,
    "gratuitousArp": False,
    "arpAgingTimeout": 14400,
    "isVrrpBackup": False,
    "vrf": "MGMT",
    "urpf": "disable",
    "addresslessForwarding": "isInvalid",
    "v4IntfForwarding": True,
    "directedBroadcastEnabled": False,
    "maxMssIngress": 0,
    "maxMssEgress": 0,
}
IP_INTERFACES: dict[str, Any] = {
    "interfaces": {
        "Ethernet1": {"name": "Ethernet1", "interfaceAddress": interface_addressing(UNASSIGNED_IPV4, 0), "vrf": "default"},
        "Management1": MANAGEMENT1,
        "Vlan3990": {"name": "Vlan3990", "interfaceAddress": interface_addressing("198.51.100.1", 29), "vrf": "SA_RIP_TEST"},
    }
}


def dhcp_management_interfaces(address: str, mask_length: int) -> dict[str, Any]:
    """Return the captured interfaces with Management1 addressed by DHCP, with or without a current lease."""
    return {
        "interfaces": {
            **IP_INTERFACES["interfaces"],
            "Management1": {**MANAGEMENT1, "interfaceAddress": interface_addressing(address, mask_length, dhcp=True)},
        }
    }


def eos_data(rip_config: str = RIP_MGMT_CONFIG, interfaces: dict[str, Any] | None = None) -> list[dict[str, Any] | str]:
    """Supply output to the RIP fact and to every RIP management interface and DHCP fact command, in declaration order."""
    ip_interfaces = IP_INTERFACES if interfaces is None else interfaces
    return [rip_config, rip_config, ip_interfaces, rip_config, ip_interfaces]


AFFECTED_MESSAGE = "The device is affected because EOS version '{version}' is affected, the RIP feature is enabled, and the RIP management interface is enabled."
DHCP_AFFECTED_MESSAGE = (
    "The device is affected because EOS version '{version}' is affected, the RIP feature is enabled, and the RIP DHCP management interface "
    "configuration is configured."
)
NOT_SELECTED_MESSAGE = (
    "The device is not affected because the RIP management interface is disabled and the RIP DHCP management interface configuration is not configured."
)

_DATA: AntaUnitTestData = {
    (SA220, "failure-management-address-in-enabled-rip-network"): {
        "version": build_eos_version("4.36.2F"),
        "eos_data": eos_data(),
        "expected": expected_result(AntaTestStatus.FAILURE, AFFECTED_MESSAGE.format(version="4.36.2F"), expected_remediation(EOSVersion(4, 36, 2, suffix="F"))),
    },
    (SA220, "failure-release-without-published-fix-in-train"): {
        "version": build_eos_version("4.37.0F"),
        "eos_data": eos_data(),
        "expected": expected_result(AntaTestStatus.FAILURE, AFFECTED_MESSAGE.format(version="4.37.0F"), expected_remediation(EOSVersion(4, 37, 0, suffix="F"))),
    },
    (SA220, "failure-later-release-in-unfixed-train"): {
        "version": build_eos_version("4.37.1F"),
        "eos_data": eos_data(),
        "expected": expected_result(AntaTestStatus.FAILURE, AFFECTED_MESSAGE.format(version="4.37.1F"), expected_remediation(EOSVersion(4, 37, 1, suffix="F"))),
    },
    (SA220, "failure-default-vrf-management"): {
        "version": build_eos_version("4.33.10M"),
        "eos_data": eos_data(RIP_DEFAULT_VRF_CONFIG, {"interfaces": {"Management1": {**MANAGEMENT1, "vrf": "default"}}}),
        "expected": expected_result(AntaTestStatus.FAILURE, AFFECTED_MESSAGE.format(version="4.33.10M"), expected_remediation(EOSVersion(4, 33, 10, suffix="M"))),
    },
    (SA220, "failure-dhcp-lease-in-enabled-rip-network"): {
        "version": build_eos_version("4.36.2F"),
        "eos_data": eos_data(interfaces=dhcp_management_interfaces("192.0.2.122", 24)),
        "expected": expected_result(AntaTestStatus.FAILURE, AFFECTED_MESSAGE.format(version="4.36.2F"), expected_remediation(EOSVersion(4, 36, 2, suffix="F"))),
    },
    (SA220, "failure-dhcp-without-lease"): {
        "version": build_eos_version("4.36.2F"),
        "eos_data": eos_data(interfaces=dhcp_management_interfaces(UNASSIGNED_IPV4, 0)),
        "expected": expected_result(AntaTestStatus.FAILURE, DHCP_AFFECTED_MESSAGE.format(version="4.36.2F"), expected_remediation(EOSVersion(4, 36, 2, suffix="F"))),
    },
    (SA220, "failure-dhcp-lease-outside-rip-network"): {
        "version": build_eos_version("4.36.2F"),
        "eos_data": eos_data(interfaces=dhcp_management_interfaces("203.0.113.10", 24)),
        "expected": expected_result(AntaTestStatus.FAILURE, DHCP_AFFECTED_MESSAGE.format(version="4.36.2F"), expected_remediation(EOSVersion(4, 36, 2, suffix="F"))),
    },
    (SA220, "success-dhcp-without-lease-on-fixed-release"): {
        "version": build_eos_version("4.36.3M"),
        "eos_data": eos_data(interfaces=dhcp_management_interfaces(UNASSIGNED_IPV4, 0)),
        "expected": expected_result(AntaTestStatus.SUCCESS, "The device is not affected because EOS version '4.36.3M' is outside the affected releases.", None),
    },
    (SA220, "success-fixed-release"): {
        "version": build_eos_version("4.36.3M"),
        "eos_data": eos_data(),
        "expected": expected_result(AntaTestStatus.SUCCESS, "The device is not affected because EOS version '4.36.3M' is outside the affected releases.", None),
    },
    (SA220, "success-unlisted-later-train"): {
        "version": build_eos_version("4.38.0F"),
        "eos_data": eos_data(interfaces={"interfaces": []}),
        "expected": expected_result(AntaTestStatus.SUCCESS, "The device is not affected because EOS version '4.38.0F' is outside the affected releases.", None),
    },
    (SA220, "success-rip-shutdown-short-circuits-version"): {
        "version": None,
        "eos_data": eos_data(RIP_SHUTDOWN_CONFIG),
        "expected": expected_result(AntaTestStatus.SUCCESS, "The device is not affected because the RIP feature is disabled.", None),
    },
    (SA220, "success-rip-not-configured"): {
        "version": build_eos_version("4.36.2F"),
        "eos_data": eos_data(""),
        "expected": expected_result(AntaTestStatus.SUCCESS, "The device is not affected because the RIP feature is disabled.", None),
    },
    (SA220, "success-rip-network-selects-only-data-interface"): {
        "version": build_eos_version("4.36.2F"),
        "eos_data": eos_data(RIP_DATA_ONLY_CONFIG),
        "expected": expected_result(AntaTestStatus.SUCCESS, NOT_SELECTED_MESSAGE, None),
    },
    (SA220, "success-matching-network-in-other-vrf"): {
        "version": build_eos_version("4.36.2F"),
        "eos_data": eos_data(RIP_DEFAULT_VRF_CONFIG),
        "expected": expected_result(AntaTestStatus.SUCCESS, NOT_SELECTED_MESSAGE, None),
    },
    (SA220, "success-dhcp-management-without-rip-in-its-vrf"): {
        "version": build_eos_version("4.36.2F"),
        "eos_data": eos_data(RIP_DATA_ONLY_CONFIG, dhcp_management_interfaces(UNASSIGNED_IPV4, 0)),
        "expected": expected_result(AntaTestStatus.SUCCESS, NOT_SELECTED_MESSAGE, None),
    },
    (SA220, "error-missing-version"): {
        "version": None,
        "eos_data": eos_data(),
        "expected": expected_result(AntaTestStatus.ERROR, "The test could not determine the EOS version because it is missing from device metadata.", None),
    },
    (SA220, "error-malformed-rip-configuration"): {
        "version": build_eos_version("4.36.2F"),
        "eos_data": eos_data("router rip vrf MGMT\n   network 192.0.2.0/24\n"),
        "expected": expected_result(
            AntaTestStatus.ERROR,
            f"The test could not determine the RIP feature state because the '{RIP_CONFIG_COMMAND}' output is invalid. "
            f"The test could not determine the RIP management interface state because the '{RIP_CONFIG_COMMAND}' output is invalid. "
            f"The test could not determine the RIP DHCP management interface configuration state because the '{RIP_CONFIG_COMMAND}' output is invalid.",
            None,
        ),
    },
    (SA220, "error-incomplete-management-addressing"): {
        "version": build_eos_version("4.36.2F"),
        "eos_data": eos_data(interfaces={"interfaces": {"Management1": {"name": "Management1", "vrf": "MGMT"}}}),
        "expected": expected_result(
            AntaTestStatus.ERROR,
            "The test could not determine the RIP management interface state because the 'show ip interface' output is incomplete. "
            "The test could not determine the RIP DHCP management interface configuration state because the 'show ip interface' output is incomplete.",
            None,
        ),
    },
    (SA220, "error-missing-version-and-dhcp-state"): {
        "version": None,
        "eos_data": eos_data(
            RIP_DATA_ONLY_CONFIG.replace("SA_RIP_TEST", "MGMT").replace("198.51.100.0/29", "198.51.100.0/24"),
            {"interfaces": {"Management1": {**MANAGEMENT1, "interfaceAddress": {**MANAGEMENT1["interfaceAddress"], "dhcp": None}}}},
        ),
        "expected": expected_result(
            AntaTestStatus.ERROR,
            "The test could not determine the EOS version because it is missing from device metadata. "
            "The test could not determine the RIP DHCP management interface configuration state because the 'show ip interface' output is incomplete.",
            None,
        ),
    },
}


def rip_fact(state: FeatureState) -> AvailableFact[RipEnabledFact]:
    """Build normalized RIP administrative state for direct assessment tests."""
    return RipEnabledFact(state).available(SOURCE)


def management_fact(state: FeatureState) -> AvailableFact[RipManagementInterfaceFact]:
    """Build normalized RIP management interface exposure for direct assessment tests."""
    return RipManagementInterfaceFact(state).available(SOURCE)


def dhcp_fact(state: ConfigurationState) -> AvailableFact[RipDhcpManagementInterfaceFact]:
    """Build normalized DHCP management interface configuration for direct assessment tests."""
    return RipDhcpManagementInterfaceFact(state).available(SOURCE)


NO_DHCP = dhcp_fact(ConfigurationState.NOT_CONFIGURED)


def test_advisory_metadata() -> None:
    """Verify advisory identifiers, tracker URL, and approved revision date."""
    assert ADVISORY.sa_number == "0220"
    assert ADVISORY.title == "Security Advisory 0220"
    assert ADVISORY.url == "https://www.arista.com/en/support/advisories-notices/security-advisory/25042-security-advisory-0220"
    assert ADVISORY.last_updated == date(2026, 11, 10)
    assert SA220.description == "Verify whether the device is impacted by Security Advisory 0220."
    assert tuple((item.id, item.severity) for item in ADVISORY.vulnerabilities) == ((VULNERABILITY_ID, _AdvisoryVulnerabilitySeverity.CRITICAL),)


def test_sa220_commands_are_derived_from_required_facts() -> None:
    """Collect the RIP configuration once per fact, each exposure fact followed by structured interface addressing."""
    commands = [(command.command, command.ofmt, command.revision) for command in SA220.commands if isinstance(command, AntaCommand)]

    assert len(SA220.commands) == len(commands)
    assert commands == [
        (RIP_CONFIG_COMMAND, "text", None),
        (RIP_CONFIG_COMMAND, "text", None),
        ("show ip interface", "json", 2),
        (RIP_CONFIG_COMMAND, "text", None),
        ("show ip interface", "json", 2),
    ]


def test_sa220_version_boundaries() -> None:
    """Cover every published affected and fixed boundary, keeping the 4.37 train without a published fix affected."""
    assert_version_statuses(
        AFFECTED_VERSION_MATRIX,
        (
            ("4.38.0F", AffectedStatus.NOT_AFFECTED),
            ("4.37.99M", AffectedStatus.AFFECTED),
            ("4.37.1F", AffectedStatus.AFFECTED),
            ("4.37.0F", AffectedStatus.AFFECTED),
            ("4.37.0.1F", AffectedStatus.AFFECTED),
            ("4.36.0F", AffectedStatus.AFFECTED),
            ("4.36.2F", AffectedStatus.AFFECTED),
            ("4.36.2.1F", AffectedStatus.AFFECTED),
            ("4.36.3M", AffectedStatus.NOT_AFFECTED),
            ("4.35.6M", AffectedStatus.AFFECTED),
            ("4.35.6.99M", AffectedStatus.AFFECTED),
            ("4.35.7M", AffectedStatus.NOT_AFFECTED),
            ("4.34.8M", AffectedStatus.AFFECTED),
            ("4.34.8.1M", AffectedStatus.AFFECTED),
            ("4.34.9M", AffectedStatus.NOT_AFFECTED),
            ("4.33.10M", AffectedStatus.AFFECTED),
            ("4.33.10.1M", AffectedStatus.AFFECTED),
            ("4.33.11M", AffectedStatus.NOT_AFFECTED),
            ("4.32.0F", AffectedStatus.AFFECTED),
            ("4.32.99M", AffectedStatus.AFFECTED),
            ("4.31.5M", AffectedStatus.AFFECTED),
            ("4.22.1F", AffectedStatus.AFFECTED),
        ),
    )


def test_sa220_assessment_states() -> None:
    """Produce every reachable state from EOS scope, enabled RIP, management interface exposure, and DHCP addressing."""
    enabled_rip = rip_fact(FeatureState.ENABLED)
    exposed = management_fact(FeatureState.ENABLED)
    not_exposed = management_fact(FeatureState.DISABLED)
    dhcp = dhcp_fact(ConfigurationState.CONFIGURED)

    affected = _assess_management_rip(eos_version_fact("4.37.0F"), enabled_rip, exposed, NO_DHCP)
    assert isinstance(affected, AffectedResult)
    assert affected.vulnerability_id == VULNERABILITY_ID
    assert affected.conditions == (enabled_rip, exposed)
    assert affected.context[0].relation is VersionRelation.AFFECTED
    assert affected.remediation == expected_remediation(EOSVersion(4, 37, 0, suffix="F"))
    assert isinstance(_assess_management_rip(eos_version_fact("4.37.0F"), enabled_rip, exposed, dhcp), AffectedResult)

    dhcp_affected = _assess_management_rip(eos_version_fact("4.36.2F"), enabled_rip, not_exposed, dhcp)
    assert isinstance(dhcp_affected, AffectedResult)
    assert dhcp_affected.conditions == (enabled_rip, dhcp)
    assert dhcp_affected.context[0].relation is VersionRelation.AFFECTED
    assert dhcp_affected.remediation == expected_remediation(EOSVersion(4, 36, 2, suffix="F"))

    for management, dhcp_configuration in ((exposed, NO_DHCP), (not_exposed, dhcp)):
        fixed = _assess_management_rip(eos_version_fact("4.33.11M"), enabled_rip, management, dhcp_configuration)
        assert isinstance(fixed, NotAffectedResult)
        assert isinstance(fixed.decisive[0], EosReleaseAssessment)
        assert fixed.decisive[0].relation is VersionRelation.OUTSIDE_SCOPE

    disabled_rip = rip_fact(FeatureState.DISABLED)
    assert _assess_management_rip(eos_version_fact("4.33.10M"), disabled_rip, exposed, dhcp) == NotAffectedResult(
        vulnerability_id=VULNERABILITY_ID, decisive=(disabled_rip,)
    )
    assert _assess_management_rip(eos_version_fact("4.33.10M"), enabled_rip, not_exposed, NO_DHCP) == NotAffectedResult(
        vulnerability_id=VULNERABILITY_ID, decisive=(not_exposed, NO_DHCP)
    )


def test_sa220_decisive_absence_ignores_unavailable_inputs() -> None:
    """Close the exposure from any absent prerequisite without requiring unrelated unavailable facts."""
    missing_version = EosVersionFact.unavailable(FactProblemKind.MISSING, SOURCE)
    malformed_rip = RipEnabledFact.unavailable(FactProblemKind.MALFORMED, SOURCE)
    malformed_management = RipManagementInterfaceFact.unavailable(FactProblemKind.MALFORMED, SOURCE)
    malformed_dhcp = RipDhcpManagementInterfaceFact.unavailable(FactProblemKind.MALFORMED, SOURCE)

    assert isinstance(_assess_management_rip(missing_version, rip_fact(FeatureState.DISABLED), malformed_management, malformed_dhcp), NotAffectedResult)
    assert isinstance(_assess_management_rip(missing_version, malformed_rip, management_fact(FeatureState.DISABLED), NO_DHCP), NotAffectedResult)
    assert isinstance(_assess_management_rip(eos_version_fact("4.38.0F"), malformed_rip, malformed_management, malformed_dhcp), NotAffectedResult)


def test_sa220_confirmed_exposure_does_not_require_dhcp_state() -> None:
    """Confirm exposure from a matched management address even when DHCP addressing cannot be determined."""
    malformed_dhcp = RipDhcpManagementInterfaceFact.unavailable(FactProblemKind.MALFORMED, SOURCE)

    finding = _assess_management_rip(eos_version_fact("4.36.2F"), rip_fact(FeatureState.ENABLED), management_fact(FeatureState.ENABLED), malformed_dhcp)

    assert isinstance(finding, AffectedResult)


def test_sa220_dhcp_exposure_does_not_require_management_address_state() -> None:
    """Confirm exposure from DHCP addressing even when the management address match cannot be determined."""
    malformed_management = RipManagementInterfaceFact.unavailable(FactProblemKind.MALFORMED, SOURCE)
    dhcp = dhcp_fact(ConfigurationState.CONFIGURED)
    enabled_rip = rip_fact(FeatureState.ENABLED)

    finding = _assess_management_rip(eos_version_fact("4.36.2F"), enabled_rip, malformed_management, dhcp)

    assert isinstance(finding, AffectedResult)
    assert finding.conditions == (enabled_rip, dhcp)


def test_sa220_unmatched_management_interface_requires_dhcp_state() -> None:
    """Do not prove safety from an unmatched management address while its DHCP addressing is unknown."""
    missing_dhcp = RipDhcpManagementInterfaceFact.unavailable(FactProblemKind.MISSING, SOURCE)

    finding = _assess_management_rip(eos_version_fact("4.36.2F"), rip_fact(FeatureState.ENABLED), management_fact(FeatureState.DISABLED), missing_dhcp)

    assert finding == ErrorResult(vulnerability_id=VULNERABILITY_ID, problems=(missing_dhcp,))


def test_sa220_aggregates_every_unavailable_required_fact() -> None:
    """Report every unavailable fact required on the evaluated path, including the EOS version."""
    missing_version = EosVersionFact.unavailable(FactProblemKind.MISSING, SOURCE)
    malformed_rip = RipEnabledFact.unavailable(FactProblemKind.MALFORMED, SOURCE)
    malformed_management = RipManagementInterfaceFact.unavailable(FactProblemKind.MALFORMED, SOURCE)
    malformed_dhcp = RipDhcpManagementInterfaceFact.unavailable(FactProblemKind.MALFORMED, SOURCE)

    assert _assess_management_rip(missing_version, malformed_rip, malformed_management, malformed_dhcp) == ErrorResult(
        vulnerability_id=VULNERABILITY_ID, problems=(missing_version, malformed_rip, malformed_management, malformed_dhcp)
    )
    assert _assess_management_rip(missing_version, rip_fact(FeatureState.ENABLED), malformed_management, NO_DHCP) == ErrorResult(
        vulnerability_id=VULNERABILITY_ID, problems=(missing_version, malformed_management)
    )
    assert _assess_management_rip(eos_version_fact("4.36.2F"), malformed_rip, management_fact(FeatureState.ENABLED), malformed_dhcp) == ErrorResult(
        vulnerability_id=VULNERABILITY_ID, problems=(malformed_rip,)
    )
