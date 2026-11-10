# Copyright (c) 2026 Arista Networks, Inc.
# Use of this source code is governed by the Apache License 2.0
# that can be found in the LICENSE file.
# pylint: disable=duplicate-code  # Keep advisory-specific scope constants local to each test.
"""ANTA test for Arista Security Advisory 201, revision 1.3."""

from __future__ import annotations

import re
from datetime import date
from typing import ClassVar

from anta._advisory.base import _PREVIEW_WARNING, _AntaAdvisoryTest
from anta._advisory.eos_versions import VersionRule
from anta._advisory.facts.eos import EosVersionFact
from anta._advisory.facts.models import Fact, FactProblemKind, FactsBase, UnavailableFact, fact_field, facts_dataclass
from anta._advisory.facts.software import TerminAttrVersionFact
from anta._advisory.findings.assessment import assess_eos_version
from anta._advisory.findings.models import (
    AffectedComponentVersion,
    AffectedEosRelease,
    AffectedResult,
    ComponentVersionAssessment,
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
    AllOf,
    FixedRelease,
    OperationalAction,
    RemediationNode,
    RemediationPlan,
    SoftwareTarget,
    software_version_action,
)
from anta._advisory.version import SemanticVersion
from anta._eos.version import EOSVersion
from anta.decorators import preview_test_class

AFFECTED_VERSION_MATRIX: tuple[VersionRule, ...] = (
    VersionRule(major=4, minor=36, patch_lt=3),
    VersionRule(major=4, minor=36, patch_eq=3, hotfix_lt=2),
    VersionRule(major=4, minor=35, patch_lt=7),
    VersionRule(major=4, minor=35, patch_eq=7, hotfix_lt=2),
    VersionRule(major=4, minor=34, patch_lt=9),
    VersionRule(major=4, minor=34, patch_eq=9, hotfix_lt=2),
    VersionRule(major=4, minor=33, patch_lt=11),
    VersionRule(major=4, minor=33, patch_eq=11, hotfix_lt=2),
    VersionRule(major=4, minor=32),
    VersionRule(major=4, minor=31),
    VersionRule(major=4, minor=30),
    VersionRule(major=4, minor=29),
    # ADR-0003: no fixed release is published for this train.
    VersionRule(major=4, minor=28),
    VersionRule(major=4, minor_lt=28),
)
FIXED_RELEASES: tuple[FixedRelease, ...] = (
    FixedRelease(EOSVersion(4, 37, 0, suffix="F")),
    FixedRelease(EOSVersion(4, 36, 3, hotfix=2, suffix="M")),
    FixedRelease(EOSVersion(4, 35, 7, hotfix=2, suffix="M")),
    FixedRelease(EOSVersion(4, 34, 9, hotfix=2, suffix="M")),
    FixedRelease(EOSVersion(4, 33, 11, hotfix=2, suffix="M")),
)
# Each key is a v1.x minor release. None means every patch is affected;
# otherwise the last affected patch is inclusive. Unlisted minors are outside scope.
TERMINATTR_LAST_AFFECTED_PATCH: dict[int, int | None] = {
    46: 2,
    45: None,
    44: None,
    43: 10,
    42: None,
    41: None,
    40: 14,
    39: None,
    38: None,
    37: 14,
    36: None,
    35: None,
    34: 14,
    33: None,
    32: None,
    31: 17,
    30: None,
    29: None,
    28: None,
    27: None,
    26: None,
    25: None,
    24: None,
    23: None,
    22: None,
    21: None,
    20: None,
    19: None,
    18: None,
    17: None,
    16: None,
    15: None,
    14: None,
    13: None,
    12: None,
    11: None,
    10: None,
    9: None,
    8: None,
    7: None,
    6: None,
    5: None,
    4: None,
    3: None,
    2: None,
    1: None,
    0: None,
}
TERMINATTR_FIXED_RELEASES = (
    FixedRelease(SemanticVersion(1, 46, 3, prefix="v")),
    FixedRelease(SemanticVersion(1, 43, 11, prefix="v")),
    FixedRelease(SemanticVersion(1, 40, 15, prefix="v")),
    FixedRelease(SemanticVersion(1, 37, 15, prefix="v")),
    FixedRelease(SemanticVersion(1, 34, 15, prefix="v")),
    FixedRelease(SemanticVersion(1, 31, 18, prefix="v")),
)
TERMINATTR_EOS_COMPATIBILITY = {
    SemanticVersion(1, 46, 3): (EOSVersion(4, 30, 0, suffix="F"), EOSVersion(4, 36, 3, suffix="M")),
    SemanticVersion(1, 43, 11): (EOSVersion(4, 30, 0, suffix="F"), EOSVersion(4, 35, 7, suffix="M")),
    SemanticVersion(1, 40, 15): (EOSVersion(4, 29, 0, suffix="F"), EOSVersion(4, 34, 8, suffix="M")),
    SemanticVersion(1, 37, 15): (EOSVersion(4, 28, 0, suffix="F"), EOSVersion(4, 33, 10, suffix="M")),
    SemanticVersion(1, 34, 15): (EOSVersion(4, 27, 0, suffix="F"), EOSVersion(4, 32, 11, suffix="M")),
    SemanticVersion(1, 31, 18): (None, EOSVersion(4, 31, 10, suffix="M")),
}
ADVISORY = _AdvisoryMetadata(
    sa_number="0201",
    last_updated=date(2026, 11, 4),
    title="Security Advisory 0201",
    vulnerabilities=(
        _AdvisoryVulnerability(
            id="CVE-2026-111943",
            # Arista's provisional CVSS 4 estimate is 9.2; the CVE owner has not published a score.
            severity=_AdvisoryVulnerabilitySeverity.CRITICAL,
            description="Compromised eMudhra intermediate CA certificates permit man-in-the-middle attacks against outbound TLS clients.",
        ),
    ),
    url="https://www.arista.com/en/support/advisories-notices/security-advisory/24847-security-advisory-0201",
    description="Affected EOS trust stores and TerminAttr clients may trust compromised CA certificates when verifying outbound TLS connections.",
)
VULNERABILITY_ID = ADVISORY.vulnerabilities[0].id


def _parse_terminattr_version(value: str) -> SemanticVersion | None:
    """Parse the numeric release, accepting TerminAttr's underscore build labels."""
    match = re.fullmatch(r"v([0-9]+)\.([0-9]+)\.([0-9]+)(?:_[A-Za-z0-9][A-Za-z0-9_.-]*)?", value)
    return SemanticVersion(*(int(part) for part in match.groups()), prefix="v") if match else None


def _terminattr_version_assessment(fact: Fact[TerminAttrVersionFact]) -> ComponentVersionAssessment | UnavailableFact[TerminAttrVersionFact]:
    """Interpret all component trains in the affected-software list independently of EOS."""
    if isinstance(fact, UnavailableFact):
        return fact
    version = _parse_terminattr_version(fact.value.version)
    if version is None:
        return TerminAttrVersionFact.unavailable(FactProblemKind.INVALID, fact.source)
    if version.major == 1:
        last_patch = TERMINATTR_LAST_AFFECTED_PATCH.get(version.minor)
        # A build label does not establish that the corresponding final release's
        # fix is present. In particular, _devel precedes the same numeric final tag.
        affected = version.minor in TERMINATTR_LAST_AFFECTED_PATCH and (
            last_patch is None or version.patch <= last_patch or (version.patch == last_patch + 1 and "_" in fact.value.version)
        )
    else:
        affected = version.major < 1
    return ComponentVersionAssessment(fact, VersionRelation.AFFECTED if affected else VersionRelation.OUTSIDE_SCOPE)


def _compatible_terminattr_fixes(version: EOSVersion) -> tuple[FixedRelease, ...]:
    """Select only the component releases explicitly supported on the observed EOS."""
    return tuple(
        release
        for release in TERMINATTR_FIXED_RELEASES
        if isinstance(release.version, SemanticVersion)
        and (bounds := TERMINATTR_EOS_COMPATIBILITY[release.version])
        and (bounds[0] is None or bounds[0] <= version)
        and version <= bounds[1]
    )


def _remediation(
    eos: EosReleaseAssessment | UnavailableFact[EosVersionFact],
    component: ComponentVersionAssessment | UnavailableFact[TerminAttrVersionFact],
) -> RemediationPlan:
    """Recommend fixed software, keeping component compatibility tied to the target EOS."""
    actions: list[RemediationNode] = []
    eos_affected = isinstance(eos, EosReleaseAssessment) and eos.relation is VersionRelation.AFFECTED
    if isinstance(eos, EosReleaseAssessment) and eos_affected:
        actions.append(software_version_action(FIXED_RELEASES, current_version=eos.fact.value))
    elif isinstance(eos, UnavailableFact):
        actions.append(OperationalAction("Verify EOS is outside the affected versions; upgrade it if needed."))

    if isinstance(component, ComponentVersionAssessment) and component.relation is VersionRelation.AFFECTED:
        if isinstance(eos, EosReleaseAssessment) and not eos_affected:
            version = _parse_terminattr_version(component.fact.value.version)
            assert version is not None  # noqa: S101
            fixes = _compatible_terminattr_fixes(eos.fact.value)
            component_action = (
                software_version_action(fixes, current_version=version, software=SoftwareTarget.TERMINATTR)
                if fixes
                else OperationalAction(
                    f"Upgrade TerminAttr to a fixed release supported on EOS {eos.fact.value}; confirm compatibility with Arista before selecting the release."
                )
            )
        else:
            component_action = OperationalAction(
                "Upgrade TerminAttr to a fixed release supported on the target EOS release; confirm compatibility with Arista before selecting the release."
            )
        actions.append(component_action)
    elif eos_affected:
        actions.append(OperationalAction("Verify TerminAttr is outside the affected versions and supported on the target EOS release; upgrade it if needed."))
    assert actions  # noqa: S101
    return RemediationPlan(actions[0] if len(actions) == 1 else AllOf(tuple(actions)))


def _assess_sa201(version: Fact[EosVersionFact], terminattr: Fact[TerminAttrVersionFact]) -> VulnerabilityResult:
    """Assess both versions; return not affected only when both are outside scope."""
    eos = assess_eos_version(version, AFFECTED_VERSION_MATRIX)
    component = _terminattr_version_assessment(terminattr)
    conditions: list[AffectedEosRelease | AffectedComponentVersion] = []
    context: list[EosReleaseAssessment | ComponentVersionAssessment] = []
    if isinstance(eos, EosReleaseAssessment):
        if eos.relation is VersionRelation.AFFECTED:
            conditions.append(AffectedEosRelease(eos.fact))
        else:
            context.append(eos)
    if isinstance(component, ComponentVersionAssessment):
        if component.relation is VersionRelation.AFFECTED:
            conditions.append(AffectedComponentVersion(component.fact))
        else:
            context.append(component)
    if conditions:
        return AffectedResult(
            vulnerability_id=VULNERABILITY_ID,
            context=tuple(context),
            conditions=tuple(conditions),
            remediation=_remediation(eos, component),
        )
    problems = tuple(fact for fact in (eos, component) if isinstance(fact, UnavailableFact))
    if problems:
        return ErrorResult(vulnerability_id=VULNERABILITY_ID, problems=problems)
    assert isinstance(eos, EosReleaseAssessment)  # noqa: S101
    assert isinstance(component, ComponentVersionAssessment)  # noqa: S101
    return NotAffectedResult(vulnerability_id=VULNERABILITY_ID, decisive=(eos, component))


@preview_test_class(warning_message=_PREVIEW_WARNING)
class SA201(OptionalCommandsMixin, _AntaAdvisoryTest):
    """Assess EOS and TerminAttr software versions against Security Advisory 0201.

    Expected Results
    ----------------
    * Not Affected: Both EOS and TerminAttr versions are outside the affected releases.
    * Affected: Either EOS or TerminAttr is an affected version.
    * Error: A version needed to determine the result is unavailable or invalid.

    Notes
    -----
    EOS and TerminAttr are assessed independently. Either affected version is sufficient for Affected, even if the other version cannot be
    collected. Both versions must be established as outside the affected releases for Not Affected. Unknown custom-program behavior does
    not soften an affected EOS result.

    This test assesses software versions and recommends upgrading affected software. Revision 1.3 removes the explicit-CA "non impacted"
    examples and recommends a fixed TerminAttr release. The advisory retains a CA condition in its exposure discussion; this version-based
    assessment does not use client configuration to exempt affected software. Explicit CA paths, disabled clients, destinations, and runtime
    sessions do not change the result. No trust-store workaround is assessed or recommended by this test.

    TerminAttr package versions with underscore build labels retain their original spelling in findings. Numeric release components determine
    the affected train and patch; a build at the first fixed patch is conservatively affected until it is the final release. For example,
    ``v1.46.3_devel`` does not establish the fix published in final ``v1.46.3``.

    EOS and TerminAttr upgrades must be compatible. When EOS must also change, select TerminAttr for the target EOS release rather than the
    currently installed EOS. All EOS platforms, including CVX, are assessed without platform-family exclusions. Other Arista products covered
    by the advisory are outside this test.

    Examples
    --------
    ```yaml
    anta.tests.advisories:
      - SA201:
    ```
    """

    @facts_dataclass
    class Facts(FactsBase):
        """Collected facts required to assess the advisory."""

        version: Fact[EosVersionFact] = fact_field(EosVersionFact)
        terminattr: Fact[TerminAttrVersionFact] = fact_field(TerminAttrVersionFact)

    advisory: ClassVar[_AdvisoryMetadata] = ADVISORY
    description = "Verify whether the device is impacted by Security Advisory 0201."
    _atomic_support = True

    @_AntaAdvisoryTest.anta_test
    def test(self) -> None:
        """Collect declared facts, assess the vulnerability, and project its atomic result."""
        facts = self.Facts.collect(self)
        finding = _assess_sa201(facts.version, facts.terminattr)
        atomic = self.result.add(f"Verify {VULNERABILITY_ID}.", vulnerability_ids=(VULNERABILITY_ID,))
        project_vulnerability_result(atomic, finding)
