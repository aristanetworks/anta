# Copyright (c) 2026 Arista Networks, Inc.
# Use of this source code is governed by the Apache License 2.0
# that can be found in the LICENSE file.
"""ANTA test for Arista Security Advisory 161."""

from __future__ import annotations

from datetime import date
from typing import Any, ClassVar, cast

from anta._advisory.base import _PREVIEW_WARNING, _AntaAdvisoryTest
from anta._advisory.eos_versions import VersionRule
from anta._advisory.facts.eos import EosVersionFact
from anta._advisory.facts.models import AvailableFact, Fact, FactDefinition, FeatureState, FeatureValue, UnavailableFact
from anta._advisory.facts.network_services import MlagDualPrimaryErrdisableFact
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
    VersionRule(major=4, minor=36, patch_lte=1),
    VersionRule(major=4, minor=35, patch_lte=5),
    VersionRule(major=4, minor=34, patch_lte=7),
    VersionRule(major=4, minor=33, patch_lte=9),
    VersionRule(major=4, minor_lt=33),
)
FIXED_RELEASES = (
    FixedRelease(EOSVersion(4, 36, 2, suffix="F")),
    FixedRelease(EOSVersion(4, 35, 6, suffix="M")),
    FixedRelease(EOSVersion(4, 34, 8, suffix="M")),
    FixedRelease(EOSVersion(4, 33, 10, suffix="M")),
)
ADVISORY = _AdvisoryMetadata(
    sa_number="0161",
    last_updated=date(2026, 9, 9),
    title="Security Advisory 0161",
    vulnerabilities=(
        _AdvisoryVulnerability(
            id="CVE-2026-73450",
            severity=_AdvisoryVulnerabilitySeverity.MEDIUM,
            description="Forged MLAG dual-primary heartbeat packets may errdisable interfaces and interrupt traffic.",
        ),
    ),
    url="https://www.arista.com/en/support/advisories-notices/security-advisory/24717-security-advisory-0161",
    description="On affected EOS releases with MLAG dual-primary heartbeat and errdisable-all configured, forged heartbeat packets may interrupt traffic.",
)
VULNERABILITY_ID = ADVISORY.vulnerabilities[0].id


def _assess_sa161(version: Fact[EOSVersion], local_mlag: Fact[FeatureValue]) -> VulnerabilityResult:
    """Assess EOS scope and the stable local MLAG configuration."""
    if not isinstance(local_mlag, UnavailableFact) and local_mlag.value.state is not FeatureState.ENABLED:
        return NotAffectedResult(vulnerability_id=VULNERABILITY_ID, decisive=(local_mlag,))
    eos_release = assess_eos_scope(VULNERABILITY_ID, version, AFFECTED_VERSION_MATRIX)
    if not isinstance(eos_release, EosReleaseAssessment):
        return eos_release
    if isinstance(local_mlag, UnavailableFact):
        return ErrorResult(vulnerability_id=VULNERABILITY_ID, problems=(local_mlag,))
    return AffectedResult(
        vulnerability_id=VULNERABILITY_ID,
        conditions=(cast("AvailableFact[FeatureValue]", local_mlag),),
        context=(eos_release,),
        remediation=software_version_plan(FIXED_RELEASES, current_version=eos_release.fact.value),
    )


@preview_test_class(warning_message=_PREVIEW_WARNING)
class SA161(OptionalCommandsMixin, _AntaAdvisoryTest):
    """Verify whether the device is impacted by Security Advisory 0161.

    Expected Results
    ----------------
    * Success: EOS is outside scope or the local vulnerable MLAG dual-primary configuration is absent.
    * Failure: An affected EOS release has MLAG dual-primary heartbeat configured with the errdisable-all action.
    * Error: Required EOS or local MLAG state cannot be determined.

    Transient MLAG, peer-link, heartbeat, and dual-primary operational states do not remove exposure from a device with the vulnerable configuration.

    Examples
    --------
    ```yaml
    anta.tests.advisories:
      - SA161:
    ```
    """

    advisory: ClassVar[_AdvisoryMetadata] = ADVISORY
    required_facts: ClassVar[tuple[type[FactDefinition[Any]], ...]] = (EosVersionFact, MlagDualPrimaryErrdisableFact)
    description = "Verify whether the device is impacted by Security Advisory 0161."
    _atomic_support = True

    @_AntaAdvisoryTest.anta_test
    def test(self) -> None:
        """Derive facts, assess the vulnerability, and project it."""
        finding = _assess_sa161(self.fact(EosVersionFact), self.fact(MlagDualPrimaryErrdisableFact))
        atomic = self.result.add(f"Verify {VULNERABILITY_ID}.", vulnerability_ids=(VULNERABILITY_ID,))
        project_vulnerability_result(atomic, finding)
