# Copyright (c) 2026 Arista Networks, Inc.
# Use of this source code is governed by the Apache License 2.0
# that can be found in the LICENSE file.
"""ANTA test for Arista Security Advisory 151."""

from __future__ import annotations

from datetime import date
from typing import Any, ClassVar

from anta._advisory.base import _PREVIEW_WARNING, _AntaAdvisoryTest
from anta._advisory.eos_versions import VersionRule
from anta._advisory.facts.acl import SharedSviIngressAclFact
from anta._advisory.facts.eos import EosVersionFact
from anta._advisory.facts.models import ConfigurationState, ConfigurationValue, Fact, FactDefinition, UnavailableFact
from anta._advisory.facts.platform import PlatformIdentityFact
from anta._advisory.findings.assessment import assess_eos_scope, assess_platform_scope
from anta._advisory.findings.models import (
    AffectedResult,
    EosReleaseAssessment,
    ErrorResult,
    NotAffectedResult,
    PlatformAssessment,
    VulnerabilityResult,
)
from anta._advisory.findings.projection import project_vulnerability_result
from anta._advisory.models import _AdvisoryMetadata, _AdvisoryVulnerability, _AdvisoryVulnerabilitySeverity
from anta._advisory.optional_commands import OptionalCommandsMixin
from anta._advisory.remediation import FixedRelease, software_version_plan
from anta._eos.platform import PlatformFamily, PlatformIdentity
from anta._eos.version import EOSVersion
from anta.decorators import preview_test_class

AFFECTED_VERSION_MATRIX: tuple[VersionRule, ...] = (
    VersionRule(major=4, minor=36, patch_eq=0),
    VersionRule(major=4, minor=35, patch_lte=4),
    VersionRule(major=4, minor=34, patch_lte=6),
    VersionRule(major=4, minor=33, patch_lte=8),
    VersionRule(major=4, minor=32, patch_lte=11),
    VersionRule(major=4, minor=31, patch_gte=1, patch_lte=10),
)
AFFECTED_PLATFORM_FAMILIES = frozenset({PlatformFamily.SERIES_750})
FIXED_RELEASES = (
    FixedRelease(EOSVersion(4, 36, 1, suffix="F")),
    FixedRelease(EOSVersion(4, 35, 5, suffix="M")),
    FixedRelease(EOSVersion(4, 34, 7, suffix="M")),
    FixedRelease(EOSVersion(4, 33, 9, suffix="M")),
)

# TODO(sa151-mitigation): Replace the historical-state conclusion if EOS exposes whether every
# shared SVI ingress ACL was reapplied after the latest secondary-switch-card restart or insertion.
ADVISORY = _AdvisoryMetadata(
    sa_number="0151",
    last_updated=date(2026, 9, 9),
    title="Security Advisory 0151",
    vulnerabilities=(
        _AdvisoryVulnerability(
            id="CVE-2026-73451",
            severity=_AdvisoryVulnerabilitySeverity.MEDIUM,
            description="A shared SVI ingress ACL may stop functioning after a secondary switch-card event.",
        ),
    ),
    url="https://www.arista.com/en/support/advisories-notices/security-advisory/24707-security-advisory-0151",
    description=(
        "On affected 755 and 758 Series platforms, restarting or inserting a secondary switch card may cause shared IPv4 or IPv6 SVI "
        "ingress ACLs to stop functioning."
    ),
)
VULNERABILITY_ID = ADVISORY.vulnerabilities[0].id


def _assess_sa151(version: Fact[EOSVersion], platform: Fact[PlatformIdentity], acl: Fact[ConfigurationValue]) -> VulnerabilityResult:
    """Assess EOS, platform, and shared SVI ACL exposure."""
    if not isinstance(acl, UnavailableFact) and acl.value.state is ConfigurationState.NOT_CONFIGURED:
        return NotAffectedResult(vulnerability_id=VULNERABILITY_ID, decisive=(acl,))
    eos_release = assess_eos_scope(VULNERABILITY_ID, version, AFFECTED_VERSION_MATRIX)
    if not isinstance(eos_release, EosReleaseAssessment):
        return eos_release
    platform_scope = assess_platform_scope(VULNERABILITY_ID, platform, AFFECTED_PLATFORM_FAMILIES)
    if not isinstance(platform_scope, PlatformAssessment):
        return platform_scope
    if isinstance(acl, UnavailableFact):
        return ErrorResult(vulnerability_id=VULNERABILITY_ID, problems=(acl,))
    return AffectedResult(
        vulnerability_id=VULNERABILITY_ID,
        context=(eos_release, platform_scope),
        conditions=(acl,),
        remediation=software_version_plan(FIXED_RELEASES, current_version=eos_release.fact.value),
    )


@preview_test_class(warning_message=_PREVIEW_WARNING)
class SA151(OptionalCommandsMixin, _AntaAdvisoryTest):
    """Verify whether the device is impacted by Security Advisory 0151.

    Expected Results
    ----------------
    * Success: EOS or platform is outside scope, or no shared SVI ingress ACL is configured.
    * Failure: Affected EOS and platform have a shared SVI ingress ACL configured.
    * Error: Required EOS, platform, or shared SVI ingress ACL state cannot be determined.

    Examples
    --------
    ```yaml
    anta.tests.advisories:
      - SA151:
    ```
    """

    advisory: ClassVar[_AdvisoryMetadata] = ADVISORY
    required_facts: ClassVar[tuple[type[FactDefinition[Any]], ...]] = (EosVersionFact, PlatformIdentityFact, SharedSviIngressAclFact)
    description = "Verify whether the device is impacted by Security Advisory 0151."
    _atomic_support = True

    @_AntaAdvisoryTest.anta_test
    def test(self) -> None:
        """Derive facts, assess the vulnerability, and project it."""
        finding = _assess_sa151(self.fact(EosVersionFact), self.fact(PlatformIdentityFact), self.fact(SharedSviIngressAclFact))
        atomic = self.result.add(f"Verify {VULNERABILITY_ID}.", vulnerability_ids=(VULNERABILITY_ID,))
        project_vulnerability_result(atomic, finding)
