# Copyright (c) 2026 Arista Networks, Inc.
# Use of this source code is governed by the Apache License 2.0
# that can be found in the LICENSE file.
# pylint: disable=duplicate-code
"""ANTA test for Arista Security Advisory 213."""

from __future__ import annotations

from datetime import date
from typing import ClassVar

from anta._advisory.base import _PREVIEW_WARNING, _AntaAdvisoryTest
from anta._advisory.eos_versions import VersionRule
from anta._advisory.facts.bgp import BgpSrTeActivationFact, MultiAgentRoutingFact
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
from anta._advisory.remediation import FixedRelease, software_version_plan
from anta._eos.version import EOSVersion
from anta.decorators import preview_test_class

AFFECTED_VERSION_MATRIX: tuple[VersionRule, ...] = (
    VersionRule(major=4, minor=36, patch_lt=3),
    VersionRule(major=4, minor=35, patch_lt=7),
    VersionRule(major=4, minor=34, patch_lt=9),
    VersionRule(major=4, minor=33, patch_lt=11),
    VersionRule(major=4, minor_gte=23, minor_lte=32),
    VersionRule(major=4, minor=22, patch_gte=1),
)
FIXED_RELEASES = (
    FixedRelease(EOSVersion(4, 37, 0, suffix="F")),
    FixedRelease(EOSVersion(4, 36, 3, suffix="M")),
    FixedRelease(EOSVersion(4, 35, 7, suffix="M")),
    FixedRelease(EOSVersion(4, 34, 9, suffix="M")),
    FixedRelease(EOSVersion(4, 33, 11, suffix="M")),
)
ADVISORY = _AdvisoryMetadata(
    sa_number="0213",
    last_updated=date(2026, 11, 10),
    title="Security Advisory 0213",
    vulnerabilities=(
        _AdvisoryVulnerability(
            id="CVE-2026-121286",
            severity=_AdvisoryVulnerabilitySeverity.MEDIUM,
            description="Crafted BGP packets from a peer with an SR-TE address family may restart the BGP process.",
        ),
    ),
    url="https://www.arista.com/en/support/advisories-notices/security-advisory/25035-security-advisory-0213",
    description="Affected EOS releases with a BGP SR-TE address family activated and the multi-agent routing protocol model may suffer BGP restarts.",
)
VULNERABILITY_ID = ADVISORY.vulnerabilities[0].id


def _assess_sa213(version: Fact[EosVersionFact], sr_te: Fact[BgpSrTeActivationFact], multi_agent: Fact[MultiAgentRoutingFact]) -> VulnerabilityResult:
    """Assess affected EOS, IPv4 or IPv6 SR-TE activation, and a configured or operating multi-agent model."""
    if not isinstance(sr_te, UnavailableFact) and sr_te.value.state is ConfigurationState.NOT_CONFIGURED:
        return NotAffectedResult(vulnerability_id=VULNERABILITY_ID, decisive=(sr_te,))
    if not isinstance(multi_agent, UnavailableFact) and multi_agent.value.state is FeatureState.DISABLED:
        return NotAffectedResult(vulnerability_id=VULNERABILITY_ID, decisive=(multi_agent,))
    release = assess_eos_version(version, AFFECTED_VERSION_MATRIX)
    if isinstance(release, EosReleaseAssessment) and release.relation is VersionRelation.OUTSIDE_SCOPE:
        return NotAffectedResult(vulnerability_id=VULNERABILITY_ID, decisive=(release,))
    problems = tuple(fact for fact in (release, sr_te, multi_agent) if isinstance(fact, UnavailableFact))
    if problems:
        return ErrorResult(vulnerability_id=VULNERABILITY_ID, problems=problems)
    assert isinstance(release, EosReleaseAssessment)  # noqa: S101
    assert not isinstance(sr_te, UnavailableFact)  # noqa: S101
    assert not isinstance(multi_agent, UnavailableFact)  # noqa: S101
    return AffectedResult(
        vulnerability_id=VULNERABILITY_ID,
        context=(release,),
        conditions=(sr_te, multi_agent),
        remediation=software_version_plan(FIXED_RELEASES, current_version=release.fact.value),
    )


@preview_test_class(warning_message=_PREVIEW_WARNING)
class SA213(OptionalCommandsMixin, _AntaAdvisoryTest):
    """Verify whether the device is impacted by Security Advisory 0213.

    Expected Results
    ----------------
    * Not Affected: EOS is outside scope, no neighbor or peer group is activated in the BGP IPv4 or IPv6 SR-TE address family, or both the
      configured and operating routing protocol models are ribd.
    * Affected: An affected EOS release has a neighbor or peer group activated in the BGP IPv4 or IPv6 SR-TE address family, and the
      multi-agent routing protocol model configured or operating.
    * Error: Required software, BGP configuration, or routing-model evidence is unavailable or inconsistent.

    Notes
    -----
    All EOS platforms are in scope. Either SR-TE address family is sufficient; ordinary unicast and other address families do not count.
    The advisory requires an established neighbor in an SR-TE address family. The test instead checks the BGP running configuration for any
    `neighbor <name> activate` under `address-family ipv4 sr-te` or `address-family ipv6 sr-te`, globally or in a VRF, because a configured
    neighbor that is down or not yet negotiated can establish the address family at any time. Neighbor and session state, peer-group
    membership, and neighbor, VRF, or BGP shutdown are not evaluated.

    The routing-model prerequisite is satisfied when either the configured or the operating model is multi-agent, so a model change that
    awaits a reload does not establish safety in either direction. Without a multi-agent model, an unrecognized or missing value
    produces Error. The advisory only directs customers to contact support for mitigation guidance, so remediation recommends fixed
    software.

    Examples
    --------
    ```yaml
    anta.tests.advisories:
      - SA213:
    ```
    """

    @facts_dataclass
    class Facts(FactsBase):
        """Collected facts required to assess the advisory."""

        version: Fact[EosVersionFact] = fact_field(EosVersionFact)
        sr_te: Fact[BgpSrTeActivationFact] = fact_field(BgpSrTeActivationFact)
        multi_agent: Fact[MultiAgentRoutingFact] = fact_field(MultiAgentRoutingFact)

    advisory: ClassVar[_AdvisoryMetadata] = ADVISORY
    description = "Verify whether the device is impacted by Security Advisory 0213."
    _atomic_support = True

    @_AntaAdvisoryTest.anta_test
    def test(self) -> None:
        """Collect declared facts and project the independent vulnerability result."""
        facts = self.Facts.collect(self)
        finding = _assess_sa213(facts.version, facts.sr_te, facts.multi_agent)
        atomic = self.result.add(f"Verify {VULNERABILITY_ID}.", vulnerability_ids=(VULNERABILITY_ID,))
        project_vulnerability_result(atomic, finding)
