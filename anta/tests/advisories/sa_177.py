# Copyright (c) 2026 Arista Networks, Inc.
# Use of this source code is governed by the Apache License 2.0
# that can be found in the LICENSE file.
# pylint: disable=duplicate-code
"""ANTA test for Arista Security Advisory 177."""

from __future__ import annotations

from datetime import date
from typing import Any, ClassVar

from anta._advisory.base import _PREVIEW_WARNING, _AntaAdvisoryTest
from anta._advisory.eos_versions import VersionRule
from anta._advisory.facts.eos import EosVersionFact
from anta._advisory.facts.models import Fact, FactDefinition, FeatureState, FeatureValue, UnavailableFact
from anta._advisory.facts.network_services import MlagConfiguredFact
from anta._advisory.facts.platform import PlatformIdentityFact
from anta._advisory.facts.routing import PimSparseModeFact
from anta._advisory.findings.assessment import assess_eos_scope, assess_platform_scope
from anta._advisory.findings.models import AffectedResult, ErrorResult, NotAffectedResult, PlatformAssessment, VulnerabilityResult
from anta._advisory.findings.projection import project_vulnerability_result
from anta._advisory.models import _AdvisoryMetadata, _AdvisoryVulnerability, _AdvisoryVulnerabilitySeverity
from anta._advisory.optional_commands import OptionalCommandsMixin
from anta._advisory.remediation import FixedRelease, software_version_plan
from anta._eos.platform import PlatformFamily, PlatformIdentity
from anta._eos.version import EOSVersion
from anta.decorators import preview_test_class

AFFECTED_VERSION_MATRIX: tuple[VersionRule, ...] = (
    VersionRule(major=4, minor=36, patch_lte=1),
    VersionRule(major=4, minor=35, patch_lte=5),
    VersionRule(major=4, minor=34, patch_gte=2, patch_lte=7),
)
FIXED_RELEASES = (
    FixedRelease(EOSVersion(4, 36, 2, suffix="F")),
    FixedRelease(EOSVersion(4, 35, 6, suffix="M")),
    FixedRelease(EOSVersion(4, 34, 8, suffix="M")),
)
AFFECTED_PLATFORM_FAMILIES = frozenset(
    {
        PlatformFamily.SERIES_710,
        PlatformFamily.SERIES_720_D,
        PlatformFamily.SERIES_720_XP,
        PlatformFamily.SERIES_722_XPM,
        PlatformFamily.SERIES_750_X,
        PlatformFamily.SERIES_7010_TX,
        PlatformFamily.SERIES_7020_R,
        PlatformFamily.SERIES_7020_R4,
        PlatformFamily.SERIES_7130,
        PlatformFamily.SERIES_7170,
        PlatformFamily.SERIES_7050_X3,
        PlatformFamily.SERIES_7050_X4,
        PlatformFamily.SERIES_7060_X,
        PlatformFamily.SERIES_7060_X2,
        PlatformFamily.SERIES_7060_X4,
        PlatformFamily.SERIES_7060_X5,
        PlatformFamily.SERIES_7060_X6,
        PlatformFamily.SERIES_7260_X,
        PlatformFamily.SERIES_7260_X3,
        PlatformFamily.SERIES_7280_R,
        PlatformFamily.SERIES_7280_R2,
        PlatformFamily.SERIES_7280_R3,
        PlatformFamily.SERIES_7280_R4,
        PlatformFamily.SERIES_7300_X,
        PlatformFamily.SERIES_7300_X3,
        PlatformFamily.SERIES_7320_X,
        PlatformFamily.SERIES_7358_X4,
        PlatformFamily.SERIES_7388_X5,
        PlatformFamily.SERIES_7500_R,
        PlatformFamily.SERIES_7500_R2,
        PlatformFamily.SERIES_7500_R3,
        PlatformFamily.SERIES_7800_R3,
        PlatformFamily.SERIES_7800_R4,
        PlatformFamily.CEOS_LAB,
        PlatformFamily.VEOS_LAB,
    }
)

ADVISORY = _AdvisoryMetadata(
    sa_number="0177",
    last_updated=date(2026, 9, 9),
    title="Security Advisory 0177",
    vulnerabilities=(
        _AdvisoryVulnerability(
            id="CVE-2026-77190",
            severity=_AdvisoryVulnerabilitySeverity.MEDIUM,
            description="Malformed PIM sparse-mode messages may repeatedly restart the Pimsm agent and cause a sustained denial of service.",
        ),
    ),
    url="https://www.arista.com/en/support/advisories-notices/security-advisory/24733-security-advisory-0177",
    description=(
        "On affected Arista EOS releases and platforms with PIM Sparse Mode and active MLAG, malformed messages may repeatedly restart the "
        "Pimsm agent and cause a sustained denial of service."
    ),
)
VULNERABILITY_ID = ADVISORY.vulnerabilities[0].id


def _assess_sa177(  # noqa: PLR0911
    version: Fact[EOSVersion],
    platform: Fact[PlatformIdentity],
    sparse_mode: Fact[FeatureValue],
    mlag: Fact[FeatureValue],
) -> VulnerabilityResult:
    """Assess EOS, platform, PIM sparse-mode, and configured MLAG exposure."""
    for prerequisite in (sparse_mode, mlag):
        if not isinstance(prerequisite, UnavailableFact) and prerequisite.value.state is not FeatureState.ENABLED:
            return NotAffectedResult(vulnerability_id=VULNERABILITY_ID, decisive=(prerequisite,))

    eos_scope = assess_eos_scope(VULNERABILITY_ID, version, AFFECTED_VERSION_MATRIX)
    if isinstance(eos_scope, NotAffectedResult):
        return eos_scope

    platform_scope = assess_platform_scope(VULNERABILITY_ID, platform, AFFECTED_PLATFORM_FAMILIES)
    if isinstance(platform_scope, NotAffectedResult):
        return platform_scope

    if isinstance(eos_scope, ErrorResult):
        problems = eos_scope.problems + (platform_scope.problems if isinstance(platform_scope, ErrorResult) else ())
        return ErrorResult(vulnerability_id=VULNERABILITY_ID, problems=problems)
    if isinstance(platform_scope, ErrorResult):
        return platform_scope
    platform_assessment: PlatformAssessment = platform_scope

    if isinstance(sparse_mode, UnavailableFact):
        problems = (sparse_mode, mlag) if isinstance(mlag, UnavailableFact) else (sparse_mode,)
        return ErrorResult(vulnerability_id=VULNERABILITY_ID, problems=problems)
    if isinstance(mlag, UnavailableFact):
        return ErrorResult(vulnerability_id=VULNERABILITY_ID, problems=(mlag,))
    return AffectedResult(
        vulnerability_id=VULNERABILITY_ID,
        context=(eos_scope, platform_assessment),
        conditions=(sparse_mode, mlag),
        remediation=software_version_plan(FIXED_RELEASES, current_version=eos_scope.fact.value),
    )


@preview_test_class(warning_message=_PREVIEW_WARNING)
class SA177(OptionalCommandsMixin, _AntaAdvisoryTest):
    """Verify whether the device is impacted by Security Advisory 0177.

    The advisory describes the exposure as requiring active MLAG. This test deliberately uses the complete persistent MLAG configuration instead:
    a configured domain ID, local interface, peer address, and peer link are treated as exposed regardless of the currently reported operational
    state. An inactive peer or domain can become active immediately after evidence collection, so transient inactivity does not establish that the
    device is not affected.

    Expected Results
    ----------------
    * Success: EOS or the platform is outside scope, PIM Sparse Mode is absent, or the complete MLAG configuration is absent.
    * Failure: An affected EOS release and platform have both PIM Sparse Mode and the complete MLAG configuration.
    * Error: Required EOS, platform, PIM Sparse Mode, or MLAG configuration cannot be determined.

    Examples
    --------
    ```yaml
    anta.tests.advisories:
      - SA177:
    ```
    """

    advisory: ClassVar[_AdvisoryMetadata] = ADVISORY
    required_facts: ClassVar[tuple[type[FactDefinition[Any]], ...]] = (
        EosVersionFact,
        PlatformIdentityFact,
        PimSparseModeFact,
        MlagConfiguredFact,
    )
    description = "Verify whether the device is impacted by Security Advisory 0177."
    _atomic_support = True

    @_AntaAdvisoryTest.anta_test
    def test(self) -> None:
        """Derive facts, assess the vulnerability, and project it."""
        finding = _assess_sa177(
            self.fact(EosVersionFact),
            self.fact(PlatformIdentityFact),
            self.fact(PimSparseModeFact),
            self.fact(MlagConfiguredFact),
        )
        atomic = self.result.add(f"Verify {VULNERABILITY_ID}.", vulnerability_ids=(VULNERABILITY_ID,))
        project_vulnerability_result(atomic, finding)
