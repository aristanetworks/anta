# Copyright (c) 2026 Arista Networks, Inc.
# Use of this source code is governed by the Apache License 2.0
# that can be found in the LICENSE file.
"""ANTA test for Arista Security Advisory 164."""

from __future__ import annotations

from datetime import date
from typing import Any, ClassVar, cast

from anta._advisory.base import _PREVIEW_WARNING, _AntaAdvisoryTest
from anta._advisory.eos_versions import VersionRule
from anta._advisory.facts.eos import EosVersionFact
from anta._advisory.facts.management import GnmiTransportFact, GnsiPathzFact, GnsiPathzPolicyOverlapFact
from anta._advisory.facts.models import AvailableFact, Fact, FactDefinition, FeatureState, FeatureValue, UnavailableFact
from anta._advisory.findings.assessment import assess_eos_scope
from anta._advisory.findings.models import (
    AffectedResult,
    EosReleaseAssessment,
    ErrorResult,
    NotAffectedResult,
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
    VersionRule(major=4, minor=33, patch_gte=2, patch_lte=8),
)
FIXED_RELEASES = (
    FixedRelease(EOSVersion(4, 36, 1, suffix="F")),
    FixedRelease(EOSVersion(4, 35, 6, suffix="M")),
    FixedRelease(EOSVersion(4, 34, 7, suffix="M")),
    FixedRelease(EOSVersion(4, 33, 9, suffix="M")),
)

ADVISORY = _AdvisoryMetadata(
    sa_number="0164",
    last_updated=date(2026, 9, 9),
    title="Security Advisory 0164",
    vulnerabilities=(
        _AdvisoryVulnerability(
            id="CVE-2026-73439",
            severity=_AdvisoryVulnerabilitySeverity.HIGH,
            description="gNMI Pathz may incorrectly combine user and group permissions for the same path.",
        ),
    ),
    url="https://www.arista.com/en/support/advisories-notices/security-advisory/24720-security-advisory-0164",
    description=(
        "On affected platforms running Arista EOS, a running gNMI server may fail to correctly enforce a gNSI Pathz policy containing a "
        "group rule and a user rule for the same path, allowing an authenticated user unauthorized access to restricted gNMI paths."
    ),
)
VULNERABILITY_ID = ADVISORY.vulnerabilities[0].id


def _assess_sa164(
    version: Fact[EOSVersion],
    gnmi_transport: Fact[FeatureValue],
    pathz: Fact[FeatureValue],
    policy_overlap: Fact[FeatureValue],
) -> VulnerabilityResult:
    """Assess the observable Pathz prerequisites and persisted policy shape."""
    eos_release = assess_eos_scope(VULNERABILITY_ID, version, AFFECTED_VERSION_MATRIX)
    if not isinstance(eos_release, EosReleaseAssessment):
        return eos_release

    if not isinstance(pathz, UnavailableFact) and pathz.value.state is not FeatureState.ENABLED:
        return NotAffectedResult(vulnerability_id=VULNERABILITY_ID, decisive=(pathz,))
    if not isinstance(gnmi_transport, UnavailableFact) and gnmi_transport.value.state is not FeatureState.ENABLED:
        return NotAffectedResult(vulnerability_id=VULNERABILITY_ID, decisive=(gnmi_transport,))

    problems = tuple(fact for fact in (gnmi_transport, pathz, policy_overlap) if isinstance(fact, UnavailableFact))
    if problems:
        return ErrorResult(vulnerability_id=VULNERABILITY_ID, problems=problems)

    overlap = cast("AvailableFact[FeatureValue]", policy_overlap)
    if overlap.value.state is not FeatureState.ENABLED:
        return NotAffectedResult(vulnerability_id=VULNERABILITY_ID, decisive=(overlap,))

    return AffectedResult(
        vulnerability_id=VULNERABILITY_ID,
        context=(eos_release,),
        conditions=(
            cast("AvailableFact[FeatureValue]", gnmi_transport),
            cast("AvailableFact[FeatureValue]", pathz),
            overlap,
        ),
        remediation=software_version_plan(FIXED_RELEASES, current_version=eos_release.fact.value),
    )


@preview_test_class(warning_message=_PREVIEW_WARNING)
class SA164(OptionalCommandsMixin, _AntaAdvisoryTest):
    """Verify whether the device is impacted by Security Advisory 0164.

    Expected Results
    ----------------
    * Success: The test will pass if EOS is outside scope, gNMI or Pathz is disabled, or the Pathz policy has no user/group path overlap.
    * Failure: The test will fail if affected EOS has gNMI and Pathz enabled with user and group rules for the same path.
    * Error: The test will error if required EOS, gNMI, Pathz, or persisted policy state cannot be determined.

    Examples
    --------
    ```yaml
    anta.tests.advisories:
      - SA164:
    ```
    """

    advisory: ClassVar[_AdvisoryMetadata] = ADVISORY
    required_facts: ClassVar[tuple[type[FactDefinition[Any]], ...]] = (
        EosVersionFact,
        GnmiTransportFact,
        GnsiPathzFact,
        GnsiPathzPolicyOverlapFact,
    )
    description = "Verify whether the device is impacted by Security Advisory 0164."
    _atomic_support = True

    @_AntaAdvisoryTest.anta_test
    def test(self) -> None:
        """Derive the declared facts, assess the vulnerability, and project it."""
        finding = _assess_sa164(
            self.fact(EosVersionFact),
            self.fact(GnmiTransportFact),
            self.fact(GnsiPathzFact),
            self.fact(GnsiPathzPolicyOverlapFact),
        )
        atomic_result = self.result.add(f"Verify {VULNERABILITY_ID}.", vulnerability_ids=(VULNERABILITY_ID,))
        project_vulnerability_result(atomic_result, finding)
