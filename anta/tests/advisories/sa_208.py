# Copyright (c) 2026 Arista Networks, Inc.
# Use of this source code is governed by the Apache License 2.0
# that can be found in the LICENSE file.
# pylint: disable=duplicate-code
"""ANTA test for Arista Security Advisory 208."""

from __future__ import annotations

from datetime import date
from typing import ClassVar

from anta._advisory.base import _PREVIEW_WARNING, _AntaAdvisoryTest
from anta._advisory.eos_versions import VersionRule
from anta._advisory.facts.bgp import BgpInstanceFact, MultiAgentRoutingFact
from anta._advisory.facts.eos import EosVersionFact
from anta._advisory.facts.models import Fact, FactsBase, FeatureState, UnavailableFact, fact_field, facts_dataclass
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
    VersionRule(major=4, minor_gte=26, minor_lte=32),
    VersionRule(major=4, minor=25, patch_gte=1),
)
FIXED_RELEASES = (
    FixedRelease(EOSVersion(4, 37, 0, suffix="F")),
    FixedRelease(EOSVersion(4, 36, 3, suffix="M")),
    FixedRelease(EOSVersion(4, 35, 7, suffix="M")),
    FixedRelease(EOSVersion(4, 34, 9, suffix="M")),
    FixedRelease(EOSVersion(4, 33, 11, suffix="M")),
)
ADVISORY = _AdvisoryMetadata(
    sa_number="0208",
    last_updated=date(2026, 11, 10),
    title="Security Advisory 0208",
    vulnerabilities=(
        _AdvisoryVulnerability(
            id="CVE-2026-121289",
            severity=_AdvisoryVulnerabilitySeverity.CRITICAL,
            description="A crafted packet may crash the BGP agent and could allow arbitrary code execution.",
        ),
    ),
    url="https://www.arista.com/en/support/advisories-notices/security-advisory/25030-security-advisory-0208",
    description="Affected EOS releases running BGP with the multi-agent routing protocol model may suffer BGP agent crashes from crafted packets.",
)
VULNERABILITY_ID = ADVISORY.vulnerabilities[0].id


def _assess_sa208(
    version: Fact[EosVersionFact],
    bgp: Fact[BgpInstanceFact],
    multi_agent: Fact[MultiAgentRoutingFact],
) -> VulnerabilityResult:
    """Assess affected EOS, a BGP instance, and a configured or operating multi-agent model."""
    if not isinstance(bgp, UnavailableFact) and bgp.value.state is FeatureState.DISABLED:
        return NotAffectedResult(vulnerability_id=VULNERABILITY_ID, decisive=(bgp,))
    if not isinstance(multi_agent, UnavailableFact) and multi_agent.value.state is FeatureState.DISABLED:
        return NotAffectedResult(vulnerability_id=VULNERABILITY_ID, decisive=(multi_agent,))
    release = assess_eos_version(version, AFFECTED_VERSION_MATRIX)
    if isinstance(release, EosReleaseAssessment) and release.relation is VersionRelation.OUTSIDE_SCOPE:
        return NotAffectedResult(vulnerability_id=VULNERABILITY_ID, decisive=(release,))
    problems = tuple(fact for fact in (release, bgp, multi_agent) if isinstance(fact, UnavailableFact))
    if problems:
        return ErrorResult(vulnerability_id=VULNERABILITY_ID, problems=problems)
    assert isinstance(release, EosReleaseAssessment)  # noqa: S101
    assert not isinstance(bgp, UnavailableFact)  # noqa: S101
    assert not isinstance(multi_agent, UnavailableFact)  # noqa: S101
    return AffectedResult(
        vulnerability_id=VULNERABILITY_ID,
        context=(release,),
        conditions=(bgp, multi_agent),
        remediation=software_version_plan(FIXED_RELEASES, current_version=release.fact.value),
    )


@preview_test_class(warning_message=_PREVIEW_WARNING)
class SA208(OptionalCommandsMixin, _AntaAdvisoryTest):
    """Verify whether the device is impacted by Security Advisory 0208.

    Expected Results
    ----------------
    * Not Affected: EOS is outside scope, no BGP instance is present, or both the configured and operating routing protocol models are ribd.
    * Affected: An affected EOS release has a BGP instance and either routing protocol model is multi-agent.
    * Error: Required software, BGP instance, or routing-model evidence is unavailable or inconsistent.

    Notes
    -----
    All EOS platforms are in scope. The advisory describes the vulnerable code as active with an established BGP session. The test instead
    counts any reported BGP instance, including one with zero or idle peers, because a configured peer can establish a session at any time.
    Empty output, only disabled VRFs, or the exact EOS `BGP inactive` response establishes no active BGP instance. This includes BGP
    shutdown or missing-router-ID states.

    The routing-model prerequisite is satisfied when either the configured or the operating model is multi-agent, so a model change that
    awaits a reload does not establish safety in either direction. Without a multi-agent model, an unrecognized or missing value produces Error.

    The test does not verify that attribute discard is effective on every existing session or that TCP-AO covers every exposure.
    These controls therefore do not change its Affected result. Configured attribute discard alone cannot prove enforcement because
    it requires a session restart. Remediation recommends fixed software.

    Examples
    --------
    ```yaml
    anta.tests.advisories:
      - SA208:
    ```
    """

    @facts_dataclass
    class Facts(FactsBase):
        """Collected facts required to assess the advisory."""

        version: Fact[EosVersionFact] = fact_field(EosVersionFact)
        bgp: Fact[BgpInstanceFact] = fact_field(BgpInstanceFact)
        multi_agent: Fact[MultiAgentRoutingFact] = fact_field(MultiAgentRoutingFact)

    advisory: ClassVar[_AdvisoryMetadata] = ADVISORY
    description = "Verify whether the device is impacted by Security Advisory 0208."
    _atomic_support = True

    @_AntaAdvisoryTest.anta_test
    def test(self) -> None:
        """Collect declared facts and project the independent vulnerability result."""
        facts = self.Facts.collect(self)
        finding = _assess_sa208(facts.version, facts.bgp, facts.multi_agent)
        atomic = self.result.add(f"Verify {VULNERABILITY_ID}.", vulnerability_ids=(VULNERABILITY_ID,))
        project_vulnerability_result(atomic, finding)
