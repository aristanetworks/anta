# Copyright (c) 2026 Arista Networks, Inc.
# Use of this source code is governed by the Apache License 2.0
# that can be found in the LICENSE file.
"""ANTA test for Arista Security Advisory 221."""

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
from anta._advisory.facts.routing import RipDhcpMd5InterfaceFact, RipEnabledFact, RipMd5AuthenticationFact
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
ADVISORY = _AdvisoryMetadata(
    sa_number="0221",
    last_updated=date(2026, 11, 10),
    title="Security Advisory 0221",
    vulnerabilities=(
        _AdvisoryVulnerability(
            id="CVE-2026-121287",
            severity=_AdvisoryVulnerabilitySeverity.HIGH,
            description=(
                "Crafted RIPv2 packets sent to an interface using RIPv2 MD5 authentication may crash the Rip agent without valid credentials "
                "and may allow arbitrary code execution."
            ),
        ),
        _AdvisoryVulnerability(
            id="CVE-2026-121288",
            severity=_AdvisoryVulnerabilitySeverity.HIGH,
            description="An unauthenticated adjacent attacker may bypass RIPv2 MD5 authentication and inject unauthorized routes.",
        ),
    ),
    url="https://www.arista.com/en/support/advisories-notices/security-advisory/25043-security-advisory-0221",
    description=(
        "Two vulnerabilities in RIPv2 MD5 authentication may allow an unauthenticated adjacent attacker to crash the Rip agent, potentially "
        "execute arbitrary code, or inject unauthorized routes that redirect or disrupt traffic."
    ),
)
CRASH_ID, BYPASS_ID = (vulnerability.id for vulnerability in ADVISORY.vulnerabilities)


def _assess_rip_md5_issue(
    vulnerability_id: str,
    version: Fact[EosVersionFact],
    rip: Fact[RipEnabledFact],
    md5_authentication: Fact[RipMd5AuthenticationFact],
    dhcp_md5_interface: Fact[RipDhcpMd5InterfaceFact],
) -> VulnerabilityResult:
    """Assess one SA221 issue from EOS scope, enabled RIP, and MD5 authentication on a RIP interface.

    Both issues share the same published version scope and exposure, but they remain distinct vulnerabilities. A DHCP-addressed MD5
    interface in the VRF of an enabled RIP instance is exposed regardless of its current lease.
    """
    if not isinstance(rip, UnavailableFact) and rip.value.state is not FeatureState.ENABLED:
        return NotAffectedResult(vulnerability_id=vulnerability_id, decisive=(rip,))
    matched = not isinstance(md5_authentication, UnavailableFact) and md5_authentication.value.state is FeatureState.ENABLED
    dhcp = not isinstance(dhcp_md5_interface, UnavailableFact) and dhcp_md5_interface.value.state is ConfigurationState.CONFIGURED
    if (
        not matched
        and not isinstance(md5_authentication, UnavailableFact)
        and not isinstance(dhcp_md5_interface, UnavailableFact)
        and dhcp_md5_interface.value.state is ConfigurationState.NOT_CONFIGURED
    ):
        return NotAffectedResult(vulnerability_id=vulnerability_id, decisive=(md5_authentication, dhcp_md5_interface))
    eos_release = assess_eos_version(version, AFFECTED_VERSION_MATRIX)
    if isinstance(eos_release, EosReleaseAssessment) and eos_release.relation is VersionRelation.OUTSIDE_SCOPE:
        return NotAffectedResult(vulnerability_id=vulnerability_id, decisive=(eos_release,))
    exposure: tuple[Fact[RipMd5AuthenticationFact] | Fact[RipDhcpMd5InterfaceFact], ...]
    if matched:
        exposure = (md5_authentication,)
    elif dhcp:
        exposure = (dhcp_md5_interface,)
    else:
        exposure = (md5_authentication, dhcp_md5_interface)
    problems = tuple(fact for fact in (eos_release, rip, *exposure) if isinstance(fact, UnavailableFact))
    if problems:
        return ErrorResult(vulnerability_id=vulnerability_id, problems=problems)
    eos_release = cast("EosReleaseAssessment", eos_release)
    return AffectedResult(
        vulnerability_id=vulnerability_id,
        context=(eos_release,),
        conditions=(
            cast("AvailableFact[RipEnabledFact]", rip),
            cast("AvailableFact[RipMd5AuthenticationFact] | AvailableFact[RipDhcpMd5InterfaceFact]", exposure[0]),
        ),
        remediation=RemediationPlan(AnyOf((software_version_action(FIXED_RELEASES, current_version=eos_release.fact.value), DISABLE_RIP))),
    )


@preview_test_class(warning_message=_PREVIEW_WARNING)
class SA221(_AntaAdvisoryTest):
    """Verify whether the device is impacted by Security Advisory 0221.

    Expected Results
    ----------------
    * Not Affected: The EOS version is outside the affected releases, no RIP instance is enabled, or no interface with RIP MD5
      authentication has an address within a network of an enabled RIP instance in its VRF and none in such a VRF uses DHCP.
    * Affected: On an affected EOS release, an enabled RIP instance has a network that contains the address of an interface with RIP MD5
      authentication in the same VRF, or an interface with RIP MD5 authentication uses DHCP in the VRF of an enabled RIP instance.
    * Error: The required EOS version, RIP configuration, RIP authentication configuration, or interface addressing cannot be determined.

    Notes
    -----
    Both vulnerabilities share the same exposure: RIP running with MD5 authentication on an interface. Each is reported separately.

    Exposure is assessed from persistent configuration rather than RIP neighbor state, so an interface that is down or currently has no
    RIP neighbor is still assessed. Every RIP MD5 authentication statement counts, including a key definition without a transmit key and a
    transmit key with ``rx-disabled``.

    An interface with RIP MD5 authentication that uses DHCP in the VRF of an enabled RIP instance is affected regardless of its current
    lease. The lease can change without a configuration change, so a missing lease or a lease outside the RIP networks does not make the
    device safe.

    Examples
    --------
    ```yaml
    anta.tests.advisories:
      - SA221:
    ```
    """

    @facts_dataclass
    class Facts(FactsBase):
        """Collected facts required to assess the advisory."""

        version: Fact[EosVersionFact] = fact_field(EosVersionFact)
        rip: Fact[RipEnabledFact] = fact_field(RipEnabledFact)
        md5_authentication: Fact[RipMd5AuthenticationFact] = fact_field(RipMd5AuthenticationFact)
        dhcp_md5_interface: Fact[RipDhcpMd5InterfaceFact] = fact_field(RipDhcpMd5InterfaceFact)

    advisory: ClassVar[_AdvisoryMetadata] = ADVISORY
    description = "Verify whether the device is impacted by Security Advisory 0221."
    _atomic_support = True

    @_AntaAdvisoryTest.anta_test
    def test(self) -> None:
        """Derive facts, assess both vulnerabilities, and project them."""
        facts = self.Facts.collect(self)
        for vulnerability_id in (CRASH_ID, BYPASS_ID):
            finding = _assess_rip_md5_issue(vulnerability_id, facts.version, facts.rip, facts.md5_authentication, facts.dhcp_md5_interface)
            atomic = self.result.add(f"Verify {vulnerability_id}.", vulnerability_ids=(vulnerability_id,))
            project_vulnerability_result(atomic, finding)
