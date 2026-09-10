# Copyright (c) 2026 Arista Networks, Inc.
# Use of this source code is governed by the Apache License 2.0
# that can be found in the LICENSE file.
"""ANTA test for Arista Security Advisory 162."""

from __future__ import annotations

from datetime import date
from typing import Any, ClassVar, cast

from anta._advisory.base import _PREVIEW_WARNING, _AntaAdvisoryTest
from anta._advisory.eos_versions import VersionRule
from anta._advisory.facts.eos import EosVersionFact
from anta._advisory.facts.management import GnsiCertzFact, GnsiTransportFact
from anta._advisory.facts.models import AvailableFact, Fact, FactDefinition, FeatureState, FeatureValue, UnavailableFact
from anta._advisory.findings.assessment import assess_eos_scope
from anta._advisory.findings.models import (
    AffectedResult,
    EosReleaseAssessment,
    ErrorResult,
    InconclusiveResult,
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
    VersionRule(major=4, minor=34, patch_lt=7),
    VersionRule(major=4, minor=34, patch_eq=7, hotfix_eq=0),
    VersionRule(major=4, minor=33, patch_lte=8),
    VersionRule(major=4, minor=32),
    VersionRule(major=4, minor=31),
    VersionRule(major=4, minor=30, patch_gte=2),
)
FIXED_RELEASES = (
    FixedRelease(EOSVersion(4, 36, 1, suffix="F")),
    FixedRelease(EOSVersion(4, 35, 6, suffix="M")),
    FixedRelease(EOSVersion(4, 34, 7, suffix="M", hotfix=1)),
    FixedRelease(EOSVersion(4, 33, 9, suffix="M")),
)

ADVISORY = _AdvisoryMetadata(
    sa_number="0162",
    last_updated=date(2026, 9, 9),
    title="Security Advisory 0162",
    vulnerabilities=(
        _AdvisoryVulnerability(
            id="CVE-2026-73447",
            severity=_AdvisoryVulnerabilitySeverity.CRITICAL,
            description="gNSI Certz and Bootz command injection permitting authenticated privilege escalation.",
        ),
    ),
    url="https://www.arista.com/en/support/advisories-notices/security-advisory/24718-security-advisory-0162",
    description=(
        "A vulnerability in the gRPC Network Security Interface (gNSI) Certz service on Arista EOS-based products allows an authenticated "
        "user to escalate its privilege to execute arbitrary OS commands via a crafted Certz Rotate request. The Bootz service is also affected."
    ),
)
VULNERABILITY_ID = ADVISORY.vulnerabilities[0].id


def _assess_sa162(
    version: Fact[EOSVersion],
    transport: Fact[FeatureValue],
    certz: Fact[FeatureValue],
) -> VulnerabilityResult:
    """Assess the Certz and historical Bootz exposure from normalized facts."""
    eos_release = assess_eos_scope(VULNERABILITY_ID, version, AFFECTED_VERSION_MATRIX)
    if not isinstance(eos_release, EosReleaseAssessment):
        return eos_release

    version_context = eos_release
    transport_disabled = not isinstance(transport, UnavailableFact) and transport.value.state is not FeatureState.ENABLED
    certz_disabled = not isinstance(certz, UnavailableFact) and certz.value.state is not FeatureState.ENABLED
    if transport_disabled or certz_disabled:
        return InconclusiveResult(
            vulnerability_id=VULNERABILITY_ID,
            indications=(version_context,),
            unresolved=(
                Unobservable(
                    UnobservableKind.HISTORICAL_STATE,
                    "initial Bootz CertzProfile certificate contents",
                ),
            ),
            remediation=software_version_plan(FIXED_RELEASES, current_version=version_context.fact.value),
        )

    problems = tuple(fact for fact in (transport, certz) if isinstance(fact, UnavailableFact))
    if problems:
        return ErrorResult(vulnerability_id=VULNERABILITY_ID, problems=problems)

    available_transport = cast("AvailableFact[FeatureValue]", transport)
    available_certz = cast("AvailableFact[FeatureValue]", certz)
    return AffectedResult(
        vulnerability_id=VULNERABILITY_ID,
        context=(version_context,),
        conditions=(available_transport, available_certz),
        remediation=software_version_plan(FIXED_RELEASES, current_version=version_context.fact.value),
    )


@preview_test_class(warning_message=_PREVIEW_WARNING)
class SA162(OptionalCommandsMixin, _AntaAdvisoryTest):
    """Verify whether the device is impacted by Security Advisory 0162.

    Expected Results
    ----------------
    * Success: The test will pass if the EOS version is outside the affected releases.
    * Failure: The test will fail if an affected EOS version has an enabled gNSI transport and Certz service.
    * Inconclusive: The test is inconclusive when the Certz path is closed but Bootz certificate use during initial provisioning is unknown.
    * Error: The test will error if EOS or current Certz-path state needed for the assessment cannot be determined.

    Examples
    --------
    ```yaml
    anta.tests.advisories:
      - SA162:
    ```
    """

    advisory: ClassVar[_AdvisoryMetadata] = ADVISORY
    required_facts: ClassVar[tuple[type[FactDefinition[Any]], ...]] = (EosVersionFact, GnsiTransportFact, GnsiCertzFact)
    description = "Verify whether the device is impacted by Security Advisory 0162."
    _atomic_support = True

    @_AntaAdvisoryTest.anta_test
    def test(self) -> None:
        """Derive the declared facts, assess the vulnerability, and project it."""
        finding = _assess_sa162(
            self.fact(EosVersionFact),
            self.fact(GnsiTransportFact),
            self.fact(GnsiCertzFact),
        )
        atomic_result = self.result.add(
            f"Verify {VULNERABILITY_ID}.",
            vulnerability_ids=(VULNERABILITY_ID,),
        )
        project_vulnerability_result(atomic_result, finding)
