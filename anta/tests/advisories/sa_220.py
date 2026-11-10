# Copyright (c) 2026 Arista Networks, Inc.
# Use of this source code is governed by the Apache License 2.0
# that can be found in the LICENSE file.
"""ANTA test for Arista Security Advisory 220."""

from __future__ import annotations

from datetime import date
from typing import ClassVar, cast

from anta._advisory.base import _PREVIEW_WARNING, _AntaAdvisoryTest
from anta._advisory.eos_versions import VersionRule
from anta._advisory.facts.eos import EosVersionFact
from anta._advisory.facts.models import (
    AvailableFact,
    ConfigurationState,
    Fact,
    FactsBase,
    FeatureState,
    UnavailableFact,
    fact_field,
    facts_dataclass,
)
from anta._advisory.facts.routing import RipDhcpManagementInterfaceFact, RipEnabledFact, RipManagementInterfaceFact
from anta._advisory.findings.assessment import assess_eos_version
from anta._advisory.findings.models import (
    AffectedResult,
    EosReleaseAssessment,
    ErrorResult,
    NotAffectedResult,
    VersionRelation,
    VulnerabilityResult,
)
from anta._advisory.findings.projection import project_vulnerability_result
from anta._advisory.models import _AdvisoryMetadata, _AdvisoryVulnerability, _AdvisoryVulnerabilitySeverity
from anta._advisory.optional_commands import OptionalCommandsMixin
from anta._advisory.remediation import (
    AnyOf,
    ConditionalAction,
    FixedRelease,
    OperationalAction,
    RemediationPlan,
    software_version_action,
)
from anta._eos.version import EOSVersion
from anta.decorators import preview_test_class

# pylint: disable=duplicate-code  # Advisory version metadata stays local even when identical.
AFFECTED_VERSION_MATRIX: tuple[VersionRule, ...] = (
    VersionRule(major=4, minor=37),
    VersionRule(major=4, minor=36, patch_lte=2),
    VersionRule(major=4, minor=35, patch_lte=6),
    VersionRule(major=4, minor=34, patch_lte=8),
    VersionRule(major=4, minor=33, patch_lte=10),
    VersionRule(major=4, minor_lt=33),
)
FIXED_RELEASES = (
    FixedRelease(EOSVersion(4, 36, 3, suffix="M")),
    FixedRelease(EOSVersion(4, 35, 7, suffix="M")),
    FixedRelease(EOSVersion(4, 34, 9, suffix="M")),
    FixedRelease(EOSVersion(4, 33, 11, suffix="M")),
)
DISABLE_RIP = ConditionalAction("RIP is not required", OperationalAction("Disable RIP in each affected VRF as described in the advisory."))
EXCLUDE_MANAGEMENT_SUBNET = ConditionalAction(
    "RIP is required on data interfaces",
    OperationalAction("Ensure that no RIP network prefix matches a management interface subnet in the same VRF, as described in the advisory."),
)
ADVISORY = _AdvisoryMetadata(
    sa_number="0220",
    last_updated=date(2026, 11, 10),
    title="Security Advisory 0220",
    vulnerabilities=(
        _AdvisoryVulnerability(
            id="CVE-2026-121367",
            severity=_AdvisoryVulnerabilitySeverity.CRITICAL,
            description=("RIPv2 may be silently enabled on management interfaces, allowing an unauthenticated adjacent attacker to install routes."),
        ),
    ),
    url="https://www.arista.com/en/support/advisories-notices/security-advisory/25042-security-advisory-0220",
    description=(
        "On affected EOS platforms with RIPv2 configured, RIPv2 may be silently enabled on management interfaces. An unauthenticated "
        "adjacent attacker may inject routes to redirect traffic, blackhole traffic, or disrupt network reachability."
    ),
)
VULNERABILITY_ID = ADVISORY.vulnerabilities[0].id


def _assess_management_rip(
    version: Fact[EosVersionFact],
    rip: Fact[RipEnabledFact],
    management_interface: Fact[RipManagementInterfaceFact],
    dhcp_management_interface: Fact[RipDhcpManagementInterfaceFact],
) -> VulnerabilityResult:
    """Assess EOS scope, enabled RIP, and an enabled RIP network matching a management interface in the same VRF.

    A DHCP-addressed management interface in the VRF of an enabled RIP instance is exposed regardless of its current lease.
    """
    if not isinstance(rip, UnavailableFact) and rip.value.state is not FeatureState.ENABLED:
        return NotAffectedResult(vulnerability_id=VULNERABILITY_ID, decisive=(rip,))
    matched = not isinstance(management_interface, UnavailableFact) and management_interface.value.state is FeatureState.ENABLED
    dhcp = not isinstance(dhcp_management_interface, UnavailableFact) and dhcp_management_interface.value.state is ConfigurationState.CONFIGURED
    if (
        not matched
        and not isinstance(management_interface, UnavailableFact)
        and not isinstance(dhcp_management_interface, UnavailableFact)
        and dhcp_management_interface.value.state is ConfigurationState.NOT_CONFIGURED
    ):
        return NotAffectedResult(vulnerability_id=VULNERABILITY_ID, decisive=(management_interface, dhcp_management_interface))
    eos_release = assess_eos_version(version, AFFECTED_VERSION_MATRIX)
    if isinstance(eos_release, EosReleaseAssessment) and eos_release.relation is VersionRelation.OUTSIDE_SCOPE:
        return NotAffectedResult(vulnerability_id=VULNERABILITY_ID, decisive=(eos_release,))
    exposure: tuple[Fact[RipManagementInterfaceFact] | Fact[RipDhcpManagementInterfaceFact], ...]
    if matched:
        exposure = (management_interface,)
    elif dhcp:
        exposure = (dhcp_management_interface,)
    else:
        exposure = (management_interface, dhcp_management_interface)
    problems = tuple(fact for fact in (eos_release, rip, *exposure) if isinstance(fact, UnavailableFact))
    if problems:
        return ErrorResult(vulnerability_id=VULNERABILITY_ID, problems=problems)
    eos_release = cast("EosReleaseAssessment", eos_release)
    software = software_version_action(FIXED_RELEASES, current_version=eos_release.fact.value)
    return AffectedResult(
        vulnerability_id=VULNERABILITY_ID,
        context=(eos_release,),
        conditions=(
            cast("AvailableFact[RipEnabledFact]", rip),
            cast("AvailableFact[RipManagementInterfaceFact] | AvailableFact[RipDhcpManagementInterfaceFact]", exposure[0]),
        ),
        remediation=RemediationPlan(AnyOf((software, DISABLE_RIP, EXCLUDE_MANAGEMENT_SUBNET))),
    )


@preview_test_class(warning_message=_PREVIEW_WARNING)
class SA220(OptionalCommandsMixin, _AntaAdvisoryTest):
    """Verify whether the device is impacted by Security Advisory 0220.

    Expected Results
    ----------------
    * Not Affected: The EOS version is outside the affected releases, no RIP instance is enabled, or no enabled RIP instance has a network
      that contains the address of a management interface in its VRF and no management interface in such a VRF uses DHCP.
    * Affected: On an affected EOS release, an enabled RIP instance has a network that contains the address of a management interface in
      the same VRF, or a management interface uses DHCP in the VRF of an enabled RIP instance.
    * Error: The required EOS version, RIP configuration, or interface addressing cannot be determined.

    Notes
    -----
    RIP processing on a management interface does not appear in the configuration, so the test correlates the networks of each enabled
    RIP instance with the primary and secondary addresses of interfaces whose names start with ``Management``. A network matches when it
    contains the interface address, including a supernet or a narrower prefix.

    A management interface that uses DHCP in the VRF of an enabled RIP instance is affected regardless of its current lease. The lease
    can change without a configuration change, so a missing lease or a lease outside the RIP networks does not make the device safe.

    Examples
    --------
    ```yaml
    anta.tests.advisories:
      - SA220:
    ```
    """

    @facts_dataclass
    class Facts(FactsBase):
        """Collected facts required to assess the advisory."""

        version: Fact[EosVersionFact] = fact_field(EosVersionFact)
        rip: Fact[RipEnabledFact] = fact_field(RipEnabledFact)
        management_interface: Fact[RipManagementInterfaceFact] = fact_field(RipManagementInterfaceFact)
        dhcp_management_interface: Fact[RipDhcpManagementInterfaceFact] = fact_field(RipDhcpManagementInterfaceFact)

    advisory: ClassVar[_AdvisoryMetadata] = ADVISORY
    description = "Verify whether the device is impacted by Security Advisory 0220."
    _atomic_support = True

    @_AntaAdvisoryTest.anta_test
    def test(self) -> None:
        """Derive facts, assess the vulnerability, and project it."""
        facts = self.Facts.collect(self)
        finding = _assess_management_rip(facts.version, facts.rip, facts.management_interface, facts.dhcp_management_interface)
        atomic_result = self.result.add(f"Verify {VULNERABILITY_ID}.", vulnerability_ids=(VULNERABILITY_ID,))
        project_vulnerability_result(atomic_result, finding)
