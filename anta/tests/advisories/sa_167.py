# Copyright (c) 2026 Arista Networks, Inc.
# Use of this source code is governed by the Apache License 2.0
# that can be found in the LICENSE file.
"""ANTA test for Arista Security Advisory 167."""

from __future__ import annotations

from datetime import date
from typing import Any, ClassVar

from anta._advisory.base import _PREVIEW_WARNING, _AntaAdvisoryTest
from anta._advisory.eos_versions import VersionRule
from anta._advisory.facts.eos import EosVersionFact
from anta._advisory.facts.management import GnsiAuthzFact, GnsiTransportFact
from anta._advisory.facts.models import Fact, FactDefinition, FeatureState, FeatureValue, UnavailableFact
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
    VersionRule(major=4, minor=34, patch_lte=7),
    VersionRule(major=4, minor=33, patch_lte=8),
    VersionRule(major=4, minor=32),
    VersionRule(major=4, minor=31),
)
FIXED_RELEASES = (
    FixedRelease(EOSVersion(4, 36, 1, suffix="F")),
    FixedRelease(EOSVersion(4, 35, 6, suffix="M")),
    FixedRelease(EOSVersion(4, 34, 8, suffix="M")),
    FixedRelease(EOSVersion(4, 33, 9, suffix="M")),
)

ADVISORY = _AdvisoryMetadata(
    sa_number="0167",
    last_updated=date(2026, 9, 9),
    title="Security Advisory 0167",
    vulnerabilities=(
        _AdvisoryVulnerability(
            id="CVE-2026-73445",
            severity=_AdvisoryVulnerabilitySeverity.MEDIUM,
            description="gNSI Authz Rotate RPC may activate an unintended policy from an ongoing stream.",
        ),
    ),
    url="https://www.arista.com/en/support/advisories-notices/security-advisory/24723-security-advisory-0167",
    description=(
        "On affected platforms running Arista EOS, an issue with the gRPC Network Security Interface (gNSI) Authz Rotate RPC may cause an "
        "incorrect Authz policy which was uploaded in the ongoing RPC stream to become active. This does not affect Bootz."
    ),
)
VULNERABILITY_ID = ADVISORY.vulnerabilities[0].id


def _assess_sa167(
    version: Fact[EOSVersion],
    transport: Fact[FeatureValue],
    authz: Fact[FeatureValue],
) -> VulnerabilityResult:
    """Assess Authz Rotate exposure from normalized current state."""
    eos_release = assess_eos_scope(VULNERABILITY_ID, version, AFFECTED_VERSION_MATRIX)
    if not isinstance(eos_release, EosReleaseAssessment):
        return eos_release

    if isinstance(transport, UnavailableFact):
        return ErrorResult(vulnerability_id=VULNERABILITY_ID, problems=(transport,))
    if transport.value.state is not FeatureState.ENABLED:
        return NotAffectedResult(vulnerability_id=VULNERABILITY_ID, decisive=(transport,))

    if isinstance(authz, UnavailableFact):
        return ErrorResult(vulnerability_id=VULNERABILITY_ID, problems=(authz,))
    if authz.value.state is not FeatureState.ENABLED:
        return NotAffectedResult(vulnerability_id=VULNERABILITY_ID, decisive=(authz,))

    return AffectedResult(
        vulnerability_id=VULNERABILITY_ID,
        context=(eos_release,),
        conditions=(transport, authz),
        remediation=software_version_plan(FIXED_RELEASES, current_version=eos_release.fact.value),
    )


@preview_test_class(warning_message=_PREVIEW_WARNING)
class SA167(OptionalCommandsMixin, _AntaAdvisoryTest):
    """Verify whether the device is impacted by Security Advisory 0167.

    Expected Results
    ----------------
    * Success: The test will pass if the EOS version is outside the affected releases, no gNSI transport is enabled, or Authz is disabled.
    * Failure: The test will fail if affected EOS has an enabled gNSI transport and Authz service.
    * Error: The test will error if required EOS version, transport, or Authz state cannot be determined.

    Examples
    --------
    ```yaml
    anta.tests.advisories:
      - SA167:
    ```
    """

    advisory: ClassVar[_AdvisoryMetadata] = ADVISORY
    required_facts: ClassVar[tuple[type[FactDefinition[Any]], ...]] = (EosVersionFact, GnsiTransportFact, GnsiAuthzFact)
    description = "Verify whether the device is impacted by Security Advisory 0167."
    _atomic_support = True

    @_AntaAdvisoryTest.anta_test
    def test(self) -> None:
        """Derive the declared facts, assess the vulnerability, and project it."""
        finding = _assess_sa167(
            self.fact(EosVersionFact),
            self.fact(GnsiTransportFact),
            self.fact(GnsiAuthzFact),
        )
        atomic_result = self.result.add(f"Verify {VULNERABILITY_ID}.", vulnerability_ids=(VULNERABILITY_ID,))
        project_vulnerability_result(atomic_result, finding)
