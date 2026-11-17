# Copyright (c) 2026 Arista Networks, Inc.
# Use of this source code is governed by the Apache License 2.0
# that can be found in the LICENSE file.
# pylint: disable=duplicate-code
"""ANTA test for Arista Security Advisory 210."""

from __future__ import annotations

from datetime import date
from typing import ClassVar

from anta._advisory.base import _PREVIEW_WARNING, _AntaAdvisoryTest
from anta._advisory.eos_versions import VersionRule
from anta._advisory.facts.bgp import BgpPathSelectionActivationFact
from anta._advisory.facts.eos import EosVersionFact
from anta._advisory.facts.models import ConfigurationState, Fact, FactsBase, UnavailableFact, fact_field, facts_dataclass
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
    VersionRule(major=4, minor_lt=33),
)
FIXED_RELEASES = (
    FixedRelease(EOSVersion(4, 37, 0, suffix="F")),
    FixedRelease(EOSVersion(4, 36, 3, suffix="M")),
    FixedRelease(EOSVersion(4, 35, 7, suffix="M")),
    FixedRelease(EOSVersion(4, 34, 9, suffix="M")),
    FixedRelease(EOSVersion(4, 33, 11, suffix="M")),
)
ADVISORY = _AdvisoryMetadata(
    sa_number="0210",
    last_updated=date(2026, 11, 10),
    title="Security Advisory 0210",
    vulnerabilities=(
        _AdvisoryVulnerability(
            id="CVE-2026-121293",
            severity=_AdvisoryVulnerabilitySeverity.MEDIUM,
            description="A crafted BGP message over a session with the path-selection address family may terminate the BGP process.",
        ),
    ),
    url="https://www.arista.com/en/support/advisories-notices/security-advisory/25032-security-advisory-0210",
    description="Affected EOS releases with the BGP path-selection address family activated may suffer BGP process restarts from a controlled peer.",
)
VULNERABILITY_ID = ADVISORY.vulnerabilities[0].id


def _assess_sa210(version: Fact[EosVersionFact], path_selection: Fact[BgpPathSelectionActivationFact]) -> VulnerabilityResult:
    """Assess affected EOS and configured path-selection activation."""
    if not isinstance(path_selection, UnavailableFact) and path_selection.value.state is ConfigurationState.NOT_CONFIGURED:
        return NotAffectedResult(vulnerability_id=VULNERABILITY_ID, decisive=(path_selection,))
    release = assess_eos_version(version, AFFECTED_VERSION_MATRIX)
    if isinstance(release, EosReleaseAssessment) and release.relation is VersionRelation.OUTSIDE_SCOPE:
        return NotAffectedResult(vulnerability_id=VULNERABILITY_ID, decisive=(release,))
    problems = tuple(fact for fact in (release, path_selection) if isinstance(fact, UnavailableFact))
    if problems:
        return ErrorResult(vulnerability_id=VULNERABILITY_ID, problems=problems)
    assert isinstance(release, EosReleaseAssessment)  # noqa: S101
    assert not isinstance(path_selection, UnavailableFact)  # noqa: S101
    return AffectedResult(
        vulnerability_id=VULNERABILITY_ID,
        context=(release,),
        conditions=(path_selection,),
        remediation=software_version_plan(FIXED_RELEASES, current_version=release.fact.value),
    )


@preview_test_class(warning_message=_PREVIEW_WARNING)
class SA210(OptionalCommandsMixin, _AntaAdvisoryTest):
    """Verify whether the device is impacted by Security Advisory 0210.

    Expected Results
    ----------------
    * Not Affected: EOS is outside scope, or no neighbor or peer group is activated in the BGP path-selection address family.
    * Affected: An affected EOS release has a neighbor or peer group activated in the BGP path-selection address family.
    * Error: Required software or BGP configuration evidence is unavailable.

    Notes
    -----
    All EOS platforms are in scope. The advisory describes exposure through an established session with the path-selection address family
    negotiated. The test instead checks the BGP running configuration for any `neighbor <name> activate` under
    `address-family path-selection`, because a configured peer that is down or not yet negotiated can establish the
    address family at any time. Neighbor and session state, peer-group membership, and neighbor, VRF, or BGP shutdown are not evaluated.
    The routing protocol model is not a prerequisite. The advisory provides no mitigation, so remediation recommends fixed software.

    Examples
    --------
    ```yaml
    anta.tests.advisories:
      - SA210:
    ```
    """

    @facts_dataclass
    class Facts(FactsBase):
        """Collected facts required to assess the advisory."""

        version: Fact[EosVersionFact] = fact_field(EosVersionFact)
        path_selection: Fact[BgpPathSelectionActivationFact] = fact_field(BgpPathSelectionActivationFact)

    advisory: ClassVar[_AdvisoryMetadata] = ADVISORY
    description = "Verify whether the device is impacted by Security Advisory 0210."
    _atomic_support = True

    @_AntaAdvisoryTest.anta_test
    def test(self) -> None:
        """Collect declared facts and project the independent vulnerability result."""
        facts = self.Facts.collect(self)
        finding = _assess_sa210(facts.version, facts.path_selection)
        atomic = self.result.add(f"Verify {VULNERABILITY_ID}.", vulnerability_ids=(VULNERABILITY_ID,))
        project_vulnerability_result(atomic, finding)
