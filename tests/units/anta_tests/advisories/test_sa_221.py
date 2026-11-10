# Copyright (c) 2026 Arista Networks, Inc.
# Use of this source code is governed by the Apache License 2.0
# that can be found in the LICENSE file.
# pylint: disable=duplicate-code
"""Unit tests for Arista Security Advisory 221."""

from __future__ import annotations

from datetime import date
from typing import TYPE_CHECKING, Any, Literal, TypeAlias
from unittest.mock import AsyncMock

from anta._advisory.eos_versions import AffectedStatus
from anta._advisory.facts.eos import EosVersionFact
from anta._advisory.facts.models import AvailableFact, ConfigurationState, FactProblemKind, FeatureState
from anta._advisory.facts.routing import RipDhcpMd5InterfaceFact, RipEnabledFact, RipMd5AuthenticationFact
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
from anta.tests.advisories.sa_221 import ADVISORY, AFFECTED_VERSION_MATRIX, SA221, _assess_rip_md5_issue
from tests.units.anta_tests import (
    build_eos_version,
    test,  # noqa: F401 - Pytest collects this imported test function.
)
from tests.units.anta_tests.advisories import OfflineAntaDevice
from tests.units.anta_tests.advisories.fact_builders import SOURCE, assert_version_statuses, eos_version_fact

if TYPE_CHECKING:
    from tests.units.anta_tests import AntaUnitTestData, AtomicResult, UnitTestResult

Status: TypeAlias = Literal[AntaTestStatus.SUCCESS, AntaTestStatus.FAILURE, AntaTestStatus.ERROR]
CRASH_ID = "CVE-2026-121287"
BYPASS_ID = "CVE-2026-121288"
UNASSIGNED_IPV4 = "0.0.0.0"  # noqa: S104 - EOS reports an interface without an IPv4 address as 0.0.0.0/0
RIP_CONFIG_COMMAND = r"show running-config all section ^router\srip"
RIP_AUTHENTICATION_COMMAND = r"show running-config sanitized section ^\s+rip\sauthentication"
EXPECTED_FIXED_RELEASES = (
    FixedRelease(EOSVersion(4, 36, 3, suffix="M")),
    FixedRelease(EOSVersion(4, 35, 7, suffix="M")),
    FixedRelease(EOSVersion(4, 34, 9, suffix="M")),
    FixedRelease(EOSVersion(4, 33, 11, suffix="M")),
)


def expected_remediation(current_version: EOSVersion) -> RemediationPlan:
    """Build the advisory's alternative software and RIP-disablement resolution."""
    return RemediationPlan(
        AnyOf(
            (
                ChangeSoftwareVersion(SoftwareTarget.EOS, current_version, KnownFixedReleases(EXPECTED_FIXED_RELEASES)),
                ConditionalAction("RIP is not required", OperationalAction("Disable RIP in each affected VRF as described in the advisory.")),
            )
        )
    )


# Captured from EOS 4.36.0F with RIP and MD5 authentication configured in a non-default VRF.
RIP_CONFIG = """router rip vrf SA_RIP_TEST
   metric default 1
   distance 120
   timers 30 180 120
   network 198.51.100.0/29
   no shutdown
   no ecmp
   no ip access-group
router rip
   network 192.0.2.0/24
   shutdown
"""
RIP_SHUTDOWN_CONFIG = """router rip
   network 192.0.2.0/24
   shutdown
"""
RIP_DEFAULT_VRF_ONLY_CONFIG = """router rip
   network 192.0.2.0/24
   no shutdown
"""
RIP_OTHER_VRF_CONFIG = """router rip vrf SA_RIP_TEST
   metric default 1
   distance 120
   timers 30 180 120
   network 203.0.113.0/24
   no shutdown
   no ecmp
   no ip access-group
router rip
   metric default 1
   distance 120
   timers 30 180 120
   network 198.51.100.0/29
   no shutdown
   no ecmp
   no ip access-group
"""
RIP_AUTHENTICATION_CONFIG = """interface Vlan3990
   rip authentication algorithm md5 tx key-id 10
   rip authentication algorithm md5 key-id 10 key 7 <removed>
   rip authentication algorithm md5 key-id 11 key 7 <removed>
"""
IP_INTERFACES: dict[str, Any] = {
    "interfaces": {
        "Ethernet1": {
            "name": "Ethernet1",
            "interfaceStatus": "connected",
            "lineProtocolStatus": "up",
            "interfaceAddress": {
                "primaryIp": {"address": UNASSIGNED_IPV4, "maskLen": 0},
                "secondaryIps": {},
                "secondaryIpsOrderedList": [],
                "virtualIp": {"address": UNASSIGNED_IPV4, "maskLen": 0},
                "virtualSecondaryIps": {},
                "virtualSecondaryIpsOrderedList": [],
                "broadcastAddress": "255.255.255.255",
                "dhcp": False,
            },
            "vrf": "default",
        },
        "Management1": {
            "name": "Management1",
            "interfaceStatus": "connected",
            "lineProtocolStatus": "up",
            "interfaceAddress": {
                "primaryIp": {"address": "192.0.2.121", "maskLen": 24},
                "secondaryIps": {},
                "secondaryIpsOrderedList": [],
                "virtualIp": {"address": UNASSIGNED_IPV4, "maskLen": 0},
                "virtualSecondaryIps": {},
                "virtualSecondaryIpsOrderedList": [],
                "broadcastAddress": "255.255.255.255",
                "dhcp": False,
            },
            "vrf": "MGMT",
        },
        "Vlan3990": {
            "name": "Vlan3990",
            "interfaceStatus": "connected",
            "lineProtocolStatus": "up",
            "mtu": 1500,
            "interfaceAddressBrief": {"ipAddr": {"address": "198.51.100.1", "maskLen": 29}},
            "ipv4Routable240": False,
            "ipv4Routable0": False,
            "enabled": True,
            "description": "",
            "interfaceAddress": {
                "primaryIp": {"address": "198.51.100.1", "maskLen": 29},
                "secondaryIps": {},
                "secondaryIpsOrderedList": [],
                "virtualIp": {"address": UNASSIGNED_IPV4, "maskLen": 0},
                "virtualSecondaryIps": {},
                "virtualSecondaryIpsOrderedList": [],
                "broadcastAddress": "255.255.255.255",
                "dhcp": False,
            },
            "proxyArp": False,
            "proxyArpAllowDefault": False,
            "localProxyArp": False,
            "gratuitousArp": False,
            "arpAgingTimeout": 14400,
            "routedAddr": "f4:1d:03:b2:f4:12",
            "isVrrpBackup": False,
            "vrf": "SA_RIP_TEST",
            "urpf": "disable",
            "addresslessForwarding": "isInvalid",
            "v4IntfForwarding": True,
            "directedBroadcastEnabled": False,
            "maxMssIngress": 0,
            "maxMssEgress": 0,
        },
    }
}


def dhcp_interfaces(address: str, mask_length: int) -> dict[str, Any]:
    """Return the captured interfaces with Vlan3990 addressed by DHCP, as rendered by EOS 4.36.0F with and without a lease."""
    vlan = IP_INTERFACES["interfaces"]["Vlan3990"]
    addressing = {**vlan["interfaceAddress"], "primaryIp": {"address": address, "maskLen": mask_length}, "dhcp": True}
    return {"interfaces": {**IP_INTERFACES["interfaces"], "Vlan3990": {**vlan, "interfaceAddress": addressing}}}


def eos_data(
    rip_config: str = RIP_CONFIG,
    authentication_config: str = RIP_AUTHENTICATION_CONFIG,
    interfaces: dict[str, Any] | None = None,
) -> list[dict[str, Any] | str]:
    """Supply output to the RIP fact and to every RIP MD5 exposure and DHCP fact command, in declaration order."""
    ip_interfaces = IP_INTERFACES if interfaces is None else interfaces
    return [rip_config, rip_config, authentication_config, ip_interfaces, rip_config, authentication_config, ip_interfaces]


DHCP_AFFECTED_MESSAGE = (
    "The device is affected because EOS version '{version}' is affected, the RIP feature is enabled, and the RIP DHCP MD5 authentication "
    "interface configuration is configured."
)
NOT_SELECTED_MESSAGE = (
    "The device is not affected because the RIP MD5 authentication is disabled and the RIP DHCP MD5 authentication interface configuration is not configured."
)


def expected_result(status: Status, message: str, remediation: RemediationPlan | None) -> UnitTestResult:
    """Build parent and atomic expectations for two vulnerabilities that share the same outcome."""
    atomic_results: list[AtomicResult] = []
    for vulnerability_id in (CRASH_ID, BYPASS_ID):
        atomic: AtomicResult = {"description": f"Verify {vulnerability_id}.", "result": status, "messages": [message]}
        if remediation is not None:
            atomic["remediation"] = remediation
        atomic_results.append(atomic)
    return {
        "result": status,
        "messages": [message, message],
        "remediations": [remediation] if remediation is not None else [],
        "atomic_results": atomic_results,
    }


_DATA: AntaUnitTestData = {
    (SA221, "failure-md5-interface-in-enabled-vrf-network"): {
        "version": build_eos_version("4.36.2F"),
        "eos_data": eos_data(),
        "expected": expected_result(
            AntaTestStatus.FAILURE,
            "The device is affected because EOS version '4.36.2F' is affected, the RIP feature is enabled, and the RIP MD5 authentication is enabled.",
            expected_remediation(EOSVersion(4, 36, 2, suffix="F")),
        ),
    },
    (SA221, "failure-end-of-support-release"): {
        "version": build_eos_version("4.31.1F"),
        "eos_data": eos_data(),
        "expected": expected_result(
            AntaTestStatus.FAILURE,
            "The device is affected because EOS version '4.31.1F' is affected, the RIP feature is enabled, and the RIP MD5 authentication is enabled.",
            expected_remediation(EOSVersion(4, 31, 1, suffix="F")),
        ),
    },
    (SA221, "failure-dhcp-lease-in-enabled-vrf-network"): {
        "version": build_eos_version("4.36.2F"),
        "eos_data": eos_data(interfaces=dhcp_interfaces("198.51.100.2", 29)),
        "expected": expected_result(
            AntaTestStatus.FAILURE,
            "The device is affected because EOS version '4.36.2F' is affected, the RIP feature is enabled, and the RIP MD5 authentication is enabled.",
            expected_remediation(EOSVersion(4, 36, 2, suffix="F")),
        ),
    },
    (SA221, "failure-dhcp-without-lease"): {
        "version": build_eos_version("4.36.2F"),
        "eos_data": eos_data(interfaces=dhcp_interfaces(UNASSIGNED_IPV4, 0)),
        "expected": expected_result(AntaTestStatus.FAILURE, DHCP_AFFECTED_MESSAGE.format(version="4.36.2F"), expected_remediation(EOSVersion(4, 36, 2, suffix="F"))),
    },
    (SA221, "failure-dhcp-lease-outside-rip-network"): {
        "version": build_eos_version("4.36.2F"),
        "eos_data": eos_data(interfaces=dhcp_interfaces("203.0.113.10", 24)),
        "expected": expected_result(AntaTestStatus.FAILURE, DHCP_AFFECTED_MESSAGE.format(version="4.36.2F"), expected_remediation(EOSVersion(4, 36, 2, suffix="F"))),
    },
    (SA221, "success-dhcp-without-lease-on-fixed-release"): {
        "version": build_eos_version("4.36.3M"),
        "eos_data": eos_data(interfaces=dhcp_interfaces(UNASSIGNED_IPV4, 0)),
        "expected": expected_result(AntaTestStatus.SUCCESS, "The device is not affected because EOS version '4.36.3M' is outside the affected releases.", None),
    },
    (SA221, "success-dhcp-md5-interface-without-rip-in-its-vrf"): {
        "version": build_eos_version("4.36.2F"),
        "eos_data": eos_data(rip_config=RIP_DEFAULT_VRF_ONLY_CONFIG, interfaces=dhcp_interfaces(UNASSIGNED_IPV4, 0)),
        "expected": expected_result(AntaTestStatus.SUCCESS, NOT_SELECTED_MESSAGE, None),
    },
    (SA221, "success-fixed-release"): {
        "version": build_eos_version("4.36.3M"),
        "eos_data": eos_data(),
        "expected": expected_result(AntaTestStatus.SUCCESS, "The device is not affected because EOS version '4.36.3M' is outside the affected releases.", None),
    },
    (SA221, "failure-release-without-published-fix-in-train"): {
        "version": build_eos_version("4.37.0F"),
        "eos_data": eos_data(),
        "expected": expected_result(
            AntaTestStatus.FAILURE,
            "The device is affected because EOS version '4.37.0F' is affected, the RIP feature is enabled, and the RIP MD5 authentication is enabled.",
            expected_remediation(EOSVersion(4, 37, 0, suffix="F")),
        ),
    },
    (SA221, "success-unlisted-later-train"): {
        "version": build_eos_version("4.38.0F"),
        "eos_data": eos_data(interfaces={"interfaces": []}),
        "expected": expected_result(AntaTestStatus.SUCCESS, "The device is not affected because EOS version '4.38.0F' is outside the affected releases.", None),
    },
    (SA221, "success-rip-shutdown-short-circuits-version"): {
        "version": None,
        "eos_data": eos_data(rip_config=RIP_SHUTDOWN_CONFIG),
        "expected": expected_result(AntaTestStatus.SUCCESS, "The device is not affected because the RIP feature is disabled.", None),
    },
    (SA221, "success-rip-not-configured"): {
        "version": build_eos_version("4.36.2F"),
        "eos_data": eos_data(rip_config=""),
        "expected": expected_result(AntaTestStatus.SUCCESS, "The device is not affected because the RIP feature is disabled.", None),
    },
    (SA221, "success-no-md5-authentication"): {
        "version": build_eos_version("4.36.2F"),
        "eos_data": eos_data(authentication_config=""),
        "expected": expected_result(
            AntaTestStatus.SUCCESS,
            "The device is not affected because the RIP MD5 authentication is disabled and the RIP DHCP MD5 authentication interface "
            "configuration is not configured.",
            None,
        ),
    },
    (SA221, "success-md5-interface-only-matched-in-other-vrf"): {
        "version": build_eos_version("4.36.2F"),
        "eos_data": eos_data(rip_config=RIP_OTHER_VRF_CONFIG),
        "expected": expected_result(AntaTestStatus.SUCCESS, NOT_SELECTED_MESSAGE, None),
    },
    (SA221, "error-missing-version"): {
        "version": None,
        "eos_data": eos_data(),
        "expected": expected_result(AntaTestStatus.ERROR, "The test could not determine the EOS version because it is missing from device metadata.", None),
    },
    (SA221, "error-malformed-rip-configuration"): {
        "version": build_eos_version("4.36.2F"),
        "eos_data": eos_data(rip_config="router rip\n   network 192.0.2.0/24\n"),
        "expected": expected_result(
            AntaTestStatus.ERROR,
            f"The test could not determine the RIP feature state because the '{RIP_CONFIG_COMMAND}' output is invalid. "
            f"The test could not determine the RIP MD5 authentication state because the '{RIP_CONFIG_COMMAND}' output is invalid. "
            f"The test could not determine the RIP DHCP MD5 authentication interface configuration state because the '{RIP_CONFIG_COMMAND}' "
            "output is invalid.",
            None,
        ),
    },
    (SA221, "error-malformed-authentication-configuration"): {
        "version": build_eos_version("4.36.2F"),
        "eos_data": eos_data(authentication_config="interface Vlan3990\n   description rip authentication\n"),
        "expected": expected_result(
            AntaTestStatus.ERROR,
            f"The test could not determine the RIP MD5 authentication state because the '{RIP_AUTHENTICATION_COMMAND}' output is invalid. "
            "The test could not determine the RIP DHCP MD5 authentication interface configuration state because the "
            f"'{RIP_AUTHENTICATION_COMMAND}' output is invalid.",
            None,
        ),
    },
    (SA221, "error-incomplete-interface-addressing"): {
        "version": build_eos_version("4.36.2F"),
        "eos_data": eos_data(interfaces={"interfaces": {"Vlan3990": {"name": "Vlan3990", "vrf": "SA_RIP_TEST"}}}),
        "expected": expected_result(
            AntaTestStatus.ERROR,
            "The test could not determine the RIP MD5 authentication state because the 'show ip interface' output is incomplete. "
            "The test could not determine the RIP DHCP MD5 authentication interface configuration state because the 'show ip interface' "
            "output is incomplete.",
            None,
        ),
    },
}


def rip_fact(state: FeatureState) -> AvailableFact[RipEnabledFact]:
    """Build normalized RIP administrative state for direct assessment tests."""
    return RipEnabledFact(state).available(SOURCE)


def md5_fact(state: FeatureState) -> AvailableFact[RipMd5AuthenticationFact]:
    """Build normalized RIP MD5 interface exposure for direct assessment tests."""
    return RipMd5AuthenticationFact(state).available(SOURCE)


def dhcp_fact(state: ConfigurationState) -> AvailableFact[RipDhcpMd5InterfaceFact]:
    """Build normalized DHCP MD5 interface configuration for direct assessment tests."""
    return RipDhcpMd5InterfaceFact(state).available(SOURCE)


NO_DHCP = dhcp_fact(ConfigurationState.NOT_CONFIGURED)


def test_advisory_metadata() -> None:
    """Verify advisory identifiers, tracker URL, and approved revision date."""
    assert ADVISORY.sa_number == "0221"
    assert ADVISORY.title == "Security Advisory 0221"
    assert ADVISORY.url == "https://www.arista.com/en/support/advisories-notices/security-advisory/25043-security-advisory-0221"
    assert ADVISORY.last_updated == date(2026, 11, 10)
    assert SA221.description == "Verify whether the device is impacted by Security Advisory 0221."
    assert tuple((item.id, item.severity) for item in ADVISORY.vulnerabilities) == (
        (CRASH_ID, _AdvisoryVulnerabilitySeverity.HIGH),
        (BYPASS_ID, _AdvisoryVulnerabilitySeverity.HIGH),
    )


def test_sa221_commands_are_derived_from_required_facts() -> None:
    """Collect the RIP configuration once per fact, followed by authentication and interface addressing."""
    commands = [(command.command, command.ofmt, command.revision) for command in SA221.commands if isinstance(command, AntaCommand)]

    assert len(SA221.commands) == len(commands)
    assert commands == [
        (RIP_CONFIG_COMMAND, "text", None),
        (RIP_CONFIG_COMMAND, "text", None),
        (RIP_AUTHENTICATION_COMMAND, "text", None),
        ("show ip interface", "json", 2),
        (RIP_CONFIG_COMMAND, "text", None),
        (RIP_AUTHENTICATION_COMMAND, "text", None),
        ("show ip interface", "json", 2),
    ]


def test_sa221_version_boundaries() -> None:
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


def test_sa221_assessment_states() -> None:
    """Produce every reachable state for both vulnerabilities from their shared exposure."""
    enabled_rip = rip_fact(FeatureState.ENABLED)
    enabled_md5 = md5_fact(FeatureState.ENABLED)
    disabled_md5 = md5_fact(FeatureState.DISABLED)
    dhcp = dhcp_fact(ConfigurationState.CONFIGURED)
    for vulnerability_id in (CRASH_ID, BYPASS_ID):
        affected = _assess_rip_md5_issue(vulnerability_id, eos_version_fact("4.33.10M"), enabled_rip, enabled_md5, NO_DHCP)
        assert isinstance(affected, AffectedResult)
        assert affected.vulnerability_id == vulnerability_id
        assert affected.conditions == (enabled_rip, enabled_md5)
        assert affected.context[0].relation is VersionRelation.AFFECTED
        assert affected.remediation == expected_remediation(EOSVersion(4, 33, 10, suffix="M"))
        assert isinstance(_assess_rip_md5_issue(vulnerability_id, eos_version_fact("4.33.10M"), enabled_rip, enabled_md5, dhcp), AffectedResult)

        dhcp_affected = _assess_rip_md5_issue(vulnerability_id, eos_version_fact("4.33.10M"), enabled_rip, disabled_md5, dhcp)
        assert isinstance(dhcp_affected, AffectedResult)
        assert dhcp_affected.vulnerability_id == vulnerability_id
        assert dhcp_affected.conditions == (enabled_rip, dhcp)
        assert dhcp_affected.context[0].relation is VersionRelation.AFFECTED
        assert dhcp_affected.remediation == expected_remediation(EOSVersion(4, 33, 10, suffix="M"))

        for md5, dhcp_configuration in ((enabled_md5, NO_DHCP), (disabled_md5, dhcp)):
            fixed = _assess_rip_md5_issue(vulnerability_id, eos_version_fact("4.33.11M"), enabled_rip, md5, dhcp_configuration)
            assert isinstance(fixed, NotAffectedResult)
            assert isinstance(fixed.decisive[0], EosReleaseAssessment)
            assert fixed.decisive[0].relation is VersionRelation.OUTSIDE_SCOPE

        disabled_rip = rip_fact(FeatureState.DISABLED)
        assert _assess_rip_md5_issue(vulnerability_id, eos_version_fact("4.33.10M"), disabled_rip, enabled_md5, dhcp) == NotAffectedResult(
            vulnerability_id=vulnerability_id, decisive=(disabled_rip,)
        )
        assert _assess_rip_md5_issue(vulnerability_id, eos_version_fact("4.33.10M"), enabled_rip, disabled_md5, NO_DHCP) == NotAffectedResult(
            vulnerability_id=vulnerability_id, decisive=(disabled_md5, NO_DHCP)
        )


def test_sa221_decisive_absence_ignores_unavailable_inputs() -> None:
    """Close the exposure from any absent prerequisite without requiring unrelated unavailable facts."""
    missing_version = EosVersionFact.unavailable(FactProblemKind.MISSING, SOURCE)
    malformed_rip = RipEnabledFact.unavailable(FactProblemKind.MALFORMED, SOURCE)
    malformed_md5 = RipMd5AuthenticationFact.unavailable(FactProblemKind.MALFORMED, SOURCE)
    malformed_dhcp = RipDhcpMd5InterfaceFact.unavailable(FactProblemKind.MALFORMED, SOURCE)

    assert isinstance(_assess_rip_md5_issue(CRASH_ID, missing_version, rip_fact(FeatureState.DISABLED), malformed_md5, malformed_dhcp), NotAffectedResult)
    assert isinstance(_assess_rip_md5_issue(CRASH_ID, missing_version, malformed_rip, md5_fact(FeatureState.DISABLED), NO_DHCP), NotAffectedResult)
    assert isinstance(_assess_rip_md5_issue(CRASH_ID, eos_version_fact("4.38.0F"), malformed_rip, malformed_md5, malformed_dhcp), NotAffectedResult)


def test_sa221_confirmed_exposure_does_not_require_dhcp_state() -> None:
    """Confirm exposure from a matched MD5 interface address even when DHCP addressing cannot be determined."""
    malformed_dhcp = RipDhcpMd5InterfaceFact.unavailable(FactProblemKind.MALFORMED, SOURCE)

    finding = _assess_rip_md5_issue(BYPASS_ID, eos_version_fact("4.36.2F"), rip_fact(FeatureState.ENABLED), md5_fact(FeatureState.ENABLED), malformed_dhcp)

    assert isinstance(finding, AffectedResult)


def test_sa221_dhcp_exposure_does_not_require_md5_address_state() -> None:
    """Confirm exposure from DHCP addressing even when the MD5 interface address match cannot be determined."""
    malformed_md5 = RipMd5AuthenticationFact.unavailable(FactProblemKind.MALFORMED, SOURCE)
    dhcp = dhcp_fact(ConfigurationState.CONFIGURED)
    enabled_rip = rip_fact(FeatureState.ENABLED)

    finding = _assess_rip_md5_issue(CRASH_ID, eos_version_fact("4.36.2F"), enabled_rip, malformed_md5, dhcp)

    assert isinstance(finding, AffectedResult)
    assert finding.conditions == (enabled_rip, dhcp)


def test_sa221_unmatched_md5_interface_requires_dhcp_state() -> None:
    """Do not prove safety from an unmatched MD5 interface address while its DHCP addressing is unknown."""
    missing_dhcp = RipDhcpMd5InterfaceFact.unavailable(FactProblemKind.MISSING, SOURCE)

    finding = _assess_rip_md5_issue(CRASH_ID, eos_version_fact("4.36.2F"), rip_fact(FeatureState.ENABLED), md5_fact(FeatureState.DISABLED), missing_dhcp)

    assert finding == ErrorResult(vulnerability_id=CRASH_ID, problems=(missing_dhcp,))


def test_sa221_aggregates_every_unavailable_required_fact() -> None:
    """Report every unavailable fact required on the evaluated path, including the EOS version."""
    missing_version = EosVersionFact.unavailable(FactProblemKind.MISSING, SOURCE)
    malformed_rip = RipEnabledFact.unavailable(FactProblemKind.MALFORMED, SOURCE)
    malformed_md5 = RipMd5AuthenticationFact.unavailable(FactProblemKind.MALFORMED, SOURCE)
    malformed_dhcp = RipDhcpMd5InterfaceFact.unavailable(FactProblemKind.MALFORMED, SOURCE)

    assert _assess_rip_md5_issue(BYPASS_ID, missing_version, malformed_rip, malformed_md5, malformed_dhcp) == ErrorResult(
        vulnerability_id=BYPASS_ID, problems=(missing_version, malformed_rip, malformed_md5, malformed_dhcp)
    )
    assert _assess_rip_md5_issue(BYPASS_ID, missing_version, rip_fact(FeatureState.ENABLED), malformed_md5, NO_DHCP) == ErrorResult(
        vulnerability_id=BYPASS_ID, problems=(missing_version, malformed_md5)
    )
    assert _assess_rip_md5_issue(BYPASS_ID, eos_version_fact("4.36.2F"), malformed_rip, md5_fact(FeatureState.ENABLED), malformed_dhcp) == ErrorResult(
        vulnerability_id=BYPASS_ID, problems=(malformed_rip,)
    )


async def test_sa221_fixed_release_excludes_failed_rip_collection() -> None:
    """A failed RIP, authentication, or interface command cannot hide an independently fixed release."""
    device = OfflineAntaDevice("unit-test")
    device.version = build_eos_version("4.36.3M")
    await device.refresh()
    instance = SA221(device=device, eos_data=eos_data())
    for command in instance.instance_commands:
        command.output = None
        command.errors = ["permission denied"]
    instance.collect = AsyncMock()

    await instance.test()

    assert instance.result.result is AntaTestStatus.SUCCESS
    assert [atomic.messages for atomic in instance.result.atomic_results] == [
        ["The device is not affected because EOS version '4.36.3M' is outside the affected releases."]
    ] * 2


async def test_sa221_failed_authentication_collection_is_structured_error() -> None:
    """Attribute a failed RIP authentication collection to the exposure facts on an affected release."""
    device = OfflineAntaDevice("unit-test")
    device.version = build_eos_version("4.36.2F")
    await device.refresh()
    instance = SA221(device=device, eos_data=eos_data())
    for command in instance.instance_commands:
        if command.command == RIP_AUTHENTICATION_COMMAND:
            command.output = None
            command.errors = ["permission denied"]
    instance.collect = AsyncMock()

    await instance.test()

    assert instance.result.result is AntaTestStatus.ERROR
    assert [atomic.messages for atomic in instance.result.atomic_results] == [
        [
            (
                f"The test could not determine the RIP MD5 authentication state because '{RIP_AUTHENTICATION_COMMAND}' could not be collected. "
                f"The test could not determine the RIP DHCP MD5 authentication interface configuration state because '{RIP_AUTHENTICATION_COMMAND}' "
                "could not be collected."
            )
        ]
    ] * 2
