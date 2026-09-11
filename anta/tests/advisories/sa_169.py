# Copyright (c) 2026 Arista Networks, Inc.
# Use of this source code is governed by the Apache License 2.0
# that can be found in the LICENSE file.
"""ANTA test for Arista Security Advisory 169."""

from __future__ import annotations

from datetime import date
from typing import Any, ClassVar, cast

from anta._advisory.base import _PREVIEW_WARNING, _AntaAdvisoryTest
from anta._advisory.eos_versions import VersionRule
from anta._advisory.facts.eos import EosVersionFact
from anta._advisory.facts.management import GnsiAuthzFact, GnsiMultipleTransportsFact, GnsiTransportFact
from anta._advisory.facts.models import AvailableFact, Fact, FactDefinition, FeatureState, FeatureValue, UnavailableFact
from anta._advisory.findings.assessment import assess_eos_scope
from anta._advisory.findings.models import (
    AffectedResult,
    EosReleaseAssessment,
    ErrorResult,
    InconclusiveResult,
    NotAffectedResult,
    Unobservable,
    UnobservableKind,
    VulnerabilityResult,
)
from anta._advisory.findings.projection import project_vulnerability_result
from anta._advisory.models import _AdvisoryMetadata, _AdvisoryVulnerability, _AdvisoryVulnerabilitySeverity
from anta._advisory.optional_commands import OptionalCommandsMixin
from anta._advisory.remediation import FixedRelease, software_version_plan
from anta._eos.version import EOSVersion
from anta.decorators import preview_test_class

AFFECTED_VERSION_MATRIX: tuple[VersionRule, ...] = (
    VersionRule(major=4, minor=36, patch_eq=0),
    VersionRule(major=4, minor=35, patch_lte=5),
    VersionRule(major=4, minor=34, patch_lte=6),
    VersionRule(major=4, minor=34, patch_eq=7, hotfix_eq=0),
    VersionRule(major=4, minor=33, patch_lte=8),
    VersionRule(major=4, minor=32, patch_lte=11),
    VersionRule(major=4, minor=31, patch_lte=10),
)
FIXED_RELEASES = (
    FixedRelease(EOSVersion(4, 36, 1, suffix="F")),
    FixedRelease(EOSVersion(4, 35, 6, suffix="M")),
    FixedRelease(EOSVersion(4, 34, 7, suffix="M", hotfix=1)),
    FixedRelease(EOSVersion(4, 33, 9, suffix="M")),
)

# TODO(sa169-policy): Replace the conservative historical-state conclusion when
# a regular structured EOS command exposes the active persisted gNSI Authz policy and rotation state.
ADVISORY = _AdvisoryMetadata(
    sa_number="0169",
    last_updated=date(2026, 9, 9),
    title="Security Advisory 0169",
    vulnerabilities=(
        _AdvisoryVulnerability(
            id="CVE-2026-73463",
            severity=_AdvisoryVulnerabilitySeverity.MEDIUM,
            description="A gNSI Authz policy rotation may silently retain a stale authorization policy.",
        ),
    ),
    url="https://www.arista.com/en/support/advisories-notices/security-advisory/24725-security-advisory-0169",
    description=(
        "On affected EOS releases, a race involving multiple gNSI transports may cause an Authz policy rotation to fail silently and retain "
        "access revoked by the new policy."
    ),
)
VULNERABILITY_ID = ADVISORY.vulnerabilities[0].id


def _assess_sa169(
    version: Fact[EOSVersion],
    transport: Fact[FeatureValue],
    multiple_transports: Fact[FeatureValue],
    authz: Fact[FeatureValue],
) -> VulnerabilityResult:
    """Assess EOS scope, current transport cardinality, and historical stale-policy risk."""
    for fact in (transport, authz):
        if not isinstance(fact, UnavailableFact) and fact.value.state is not FeatureState.ENABLED:
            return NotAffectedResult(vulnerability_id=VULNERABILITY_ID, decisive=(fact,))
    eos_release = assess_eos_scope(VULNERABILITY_ID, version, AFFECTED_VERSION_MATRIX)
    if not isinstance(eos_release, EosReleaseAssessment):
        return eos_release
    problems = tuple(fact for fact in (transport, multiple_transports, authz) if isinstance(fact, UnavailableFact))
    if problems:
        return ErrorResult(vulnerability_id=VULNERABILITY_ID, problems=problems)
    available_transport = cast("AvailableFact[FeatureValue]", transport)
    available_authz = cast("AvailableFact[FeatureValue]", authz)
    available_multiple = cast("AvailableFact[FeatureValue]", multiple_transports)
    remediation = software_version_plan(FIXED_RELEASES, current_version=eos_release.fact.value)
    if available_multiple.value.state is FeatureState.ENABLED:
        return AffectedResult(
            vulnerability_id=VULNERABILITY_ID,
            context=(eos_release,),
            conditions=(available_transport, available_authz, available_multiple),
            remediation=remediation,
        )
    return InconclusiveResult(
        vulnerability_id=VULNERABILITY_ID,
        indications=(eos_release, available_transport, available_authz),
        unresolved=(Unobservable(UnobservableKind.HISTORICAL_STATE, "whether a secondary transport caused the active Authz policy to become stale"),),
        remediation=remediation,
    )


@preview_test_class(warning_message=_PREVIEW_WARNING)
class SA169(OptionalCommandsMixin, _AntaAdvisoryTest):
    """Verify whether the device is impacted by Security Advisory 0169.

    Expected Results
    ----------------
    * Success: EOS is outside scope, gNSI has no enabled transport, or Authz is disabled.
    * Failure: Affected EOS has gNSI Authz and multiple transports enabled.
    * Inconclusive: Affected EOS has gNSI Authz and one transport enabled, but a removed secondary transport may have left stale policy state.
    * Error: Required EOS or gNSI state cannot be determined.

    Examples
    --------
    ```yaml
    anta.tests.advisories:
      - SA169:
    ```
    """

    advisory: ClassVar[_AdvisoryMetadata] = ADVISORY
    required_facts: ClassVar[tuple[type[FactDefinition[Any]], ...]] = (
        EosVersionFact,
        GnsiTransportFact,
        GnsiMultipleTransportsFact,
        GnsiAuthzFact,
    )
    description = "Verify whether the device is impacted by Security Advisory 0169."
    _atomic_support = True

    @_AntaAdvisoryTest.anta_test
    def test(self) -> None:
        """Derive facts, assess the vulnerability, and project it."""
        finding = _assess_sa169(
            self.fact(EosVersionFact),
            self.fact(GnsiTransportFact),
            self.fact(GnsiMultipleTransportsFact),
            self.fact(GnsiAuthzFact),
        )
        atomic = self.result.add(f"Verify {VULNERABILITY_ID}.", vulnerability_ids=(VULNERABILITY_ID,))
        project_vulnerability_result(atomic, finding)
