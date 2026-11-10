# Copyright (c) 2026 Arista Networks, Inc.
# Use of this source code is governed by the Apache License 2.0
# that can be found in the LICENSE file.
# pylint: disable=duplicate-code
"""ANTA test for Arista Security Advisory 209."""

from __future__ import annotations

from datetime import date
from typing import ClassVar

from anta._advisory.base import _PREVIEW_WARNING, _AntaAdvisoryTest
from anta._advisory.eos_versions import VersionRule
from anta._advisory.facts.bgp import BgpListenPort, BgpNonDefaultListenPortFact, MultiAgentRoutingFact
from anta._advisory.facts.eos import EosVersionFact
from anta._advisory.facts.models import ConfigurationState, Fact, FactsBase, FeatureState, UnavailableFact, fact_field, facts_dataclass
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
from anta._advisory.remediation import AnyOf, ConditionalAction, FixedRelease, OperationalAction, RemediationPlan, software_version_action
from anta._eos.version import EOSVersion
from anta.decorators import preview_test_class

AFFECTED_VERSION_MATRIX: tuple[VersionRule, ...] = (
    VersionRule(major=4, minor=36, patch_lt=3),
    VersionRule(major=4, minor=35, patch_lt=7),
    VersionRule(major=4, minor=34, patch_lt=9),
    VersionRule(major=4, minor=33, patch_lt=11),
    VersionRule(major=4, minor_lt=33),
)
FIXED_RELEASES = (
    FixedRelease(EOSVersion(4, 37, 0, suffix="F")),
    FixedRelease(EOSVersion(4, 36, 3, suffix="M")),
    FixedRelease(EOSVersion(4, 35, 7, suffix="M")),
    FixedRelease(EOSVersion(4, 34, 9, suffix="M")),
    FixedRelease(EOSVersion(4, 33, 11, suffix="M")),
)
DEFAULT_PORT_CONDITION = "removing the non-default BGP listen port is operationally feasible"
ADVISORY = _AdvisoryMetadata(
    sa_number="0209",
    last_updated=date(2026, 11, 10),
    title="Security Advisory 0209",
    vulnerabilities=(
        _AdvisoryVulnerability(
            id="CVE-2026-121290",
            severity=_AdvisoryVulnerabilitySeverity.HIGH,
            description="A non-default BGP listen port disables the default protective ACL rules against unexpected BGP peering attempts.",
        ),
    ),
    url="https://www.arista.com/en/support/advisories-notices/security-advisory/25031-security-advisory-0209",
    description="Affected EOS releases with a non-default BGP listen port and the multi-agent routing protocol model lack default BGP ACL protection.",
)
VULNERABILITY_ID = ADVISORY.vulnerabilities[0].id


def _restore_default_port(ports: tuple[BgpListenPort, ...], *, complete: bool) -> OperationalAction:
    """Remove the listen port from each VRF reporting a non-default port, without implying a partial inventory is complete."""
    vrfs = ", ".join(dict.fromkeys(port.vrf for port in ports))
    if complete:
        return OperationalAction(f"Remove 'bgp transport listen-port' from the BGP configuration of VRFs: {vrfs}.")
    return OperationalAction(f"Remove 'bgp transport listen-port' from the BGP configuration of every VRF using a non-default port, including: {vrfs}.")


def _assess_sa209(
    version: Fact[EosVersionFact],
    listen_port: Fact[BgpNonDefaultListenPortFact],
    multi_agent: Fact[MultiAgentRoutingFact],
) -> VulnerabilityResult:
    """Assess affected EOS, a reported non-default listen port, and a configured or operating multi-agent model."""
    if not isinstance(listen_port, UnavailableFact) and listen_port.value.state is ConfigurationState.NOT_CONFIGURED:
        return NotAffectedResult(vulnerability_id=VULNERABILITY_ID, decisive=(listen_port,))
    if not isinstance(multi_agent, UnavailableFact) and multi_agent.value.state is FeatureState.DISABLED:
        return NotAffectedResult(vulnerability_id=VULNERABILITY_ID, decisive=(multi_agent,))
    release = assess_eos_version(version, AFFECTED_VERSION_MATRIX)
    if isinstance(release, EosReleaseAssessment) and release.relation is VersionRelation.OUTSIDE_SCOPE:
        return NotAffectedResult(vulnerability_id=VULNERABILITY_ID, decisive=(release,))
    problems = tuple(fact for fact in (release, listen_port, multi_agent) if isinstance(fact, UnavailableFact))
    if problems:
        return ErrorResult(vulnerability_id=VULNERABILITY_ID, problems=problems)
    assert isinstance(release, EosReleaseAssessment)  # noqa: S101
    assert not isinstance(listen_port, UnavailableFact)  # noqa: S101
    assert not isinstance(multi_agent, UnavailableFact)  # noqa: S101
    software = software_version_action(FIXED_RELEASES, current_version=release.fact.value)
    configuration = ConditionalAction(DEFAULT_PORT_CONDITION, _restore_default_port(listen_port.value.ports, complete=listen_port.value.problem is None))
    return AffectedResult(
        vulnerability_id=VULNERABILITY_ID,
        context=(release,),
        conditions=(listen_port, multi_agent),
        remediation=RemediationPlan(AnyOf((software, configuration))),
    )


@preview_test_class(warning_message=_PREVIEW_WARNING)
class SA209(OptionalCommandsMixin, _AntaAdvisoryTest):
    """Verify whether the device is impacted by Security Advisory 0209.

    Expected Results
    ----------------
    * Not Affected: EOS is outside scope, BGP is not running or every running VRF reports TCP 179 as its IPv4 and IPv6 listen port, or
      both the configured and operating routing protocol models are ribd.
    * Affected: An affected EOS release reports a BGP listen port other than TCP 179 in any VRF, and the multi-agent routing protocol model
      is configured or operating.
    * Error: Required software, BGP listen port, or routing-model evidence is unavailable or inconsistent.

    Notes
    -----
    All EOS platforms are in scope. Listen ports are read from the `bgpIpv4ListenPort` and `bgpIpv6ListenPort` values of every VRF in
    `show bgp instance vrf all`. Any valid non-default port establishes exposure even when another VRF or address family is unreadable;
    without one, a missing or malformed value produces Error rather than Not Affected. EOS reports only VRFs
    where BGP is running: the `BGP inactive` response, or an empty VRF list such as with a missing router ID, establishes that no
    listen port exists. A global BGP `shutdown` removes only the default VRF from the output, so a non-default port in a named VRF
    remains Affected.

    The routing-model prerequisite is satisfied when either the configured or the operating model is multi-agent, so a model change that
    awaits a reload does not establish safety in either direction. Without a multi-agent model, an unrecognized or missing value
    produces Error.

    The advisory's custom control-plane ACL alternative depends on operator-specific expected peers and TTL values that the device cannot
    validate, so ACL configuration never produces Mitigated or Inconclusive. Remediation recommends fixed software or, where operationally
    feasible, removing the non-default listen port from each VRF that reports one. When another VRF or address family is unreadable,
    the listed VRFs may be incomplete, so the removal applies to every VRF using a non-default port; fixed software remains complete.

    Examples
    --------
    ```yaml
    anta.tests.advisories:
      - SA209:
    ```
    """

    @facts_dataclass
    class Facts(FactsBase):
        """Collected facts required to assess the advisory."""

        version: Fact[EosVersionFact] = fact_field(EosVersionFact)
        listen_port: Fact[BgpNonDefaultListenPortFact] = fact_field(BgpNonDefaultListenPortFact)
        multi_agent: Fact[MultiAgentRoutingFact] = fact_field(MultiAgentRoutingFact)

    advisory: ClassVar[_AdvisoryMetadata] = ADVISORY
    description = "Verify whether the device is impacted by Security Advisory 0209."
    _atomic_support = True

    @_AntaAdvisoryTest.anta_test
    def test(self) -> None:
        """Collect declared facts and project the independent vulnerability result."""
        facts = self.Facts.collect(self)
        finding = _assess_sa209(facts.version, facts.listen_port, facts.multi_agent)
        atomic = self.result.add(f"Verify {VULNERABILITY_ID}.", vulnerability_ids=(VULNERABILITY_ID,))
        project_vulnerability_result(atomic, finding)
