# Copyright (c) 2026 Arista Networks, Inc.
# Use of this source code is governed by the Apache License 2.0
# that can be found in the LICENSE file.
"""ANTA test for Arista Security Advisory 224."""

from __future__ import annotations

from datetime import date
from typing import ClassVar

from anta._advisory.base import _PREVIEW_WARNING, _AntaAdvisoryTest
from anta._advisory.eos_versions import VersionRule
from anta._advisory.facts.eos import EosVersionFact
from anta._advisory.facts.models import Fact, FactsBase, FeatureState, UnavailableFact, fact_field, facts_dataclass
from anta._advisory.facts.platform import PlatformIdentityFact
from anta._advisory.facts.ptp import PtpGlobalFact
from anta._advisory.findings.assessment import assess_eos_scope, assess_platform_scope
from anta._advisory.findings.models import AffectedResult, ErrorResult, NotAffectedResult, VulnerabilityResult
from anta._advisory.findings.projection import project_vulnerability_result
from anta._advisory.models import _AdvisoryMetadata, _AdvisoryVulnerability, _AdvisoryVulnerabilitySeverity
from anta._advisory.optional_commands import OptionalCommandsMixin
from anta._advisory.remediation import FixedRelease, software_version_plan
from anta._eos.platform import PlatformFamily
from anta._eos.version import EOSVersion
from anta.decorators import preview_test_class

AFFECTED_VERSION_MATRIX: tuple[VersionRule, ...] = (
    VersionRule(major=4, minor=29, patch_gte=2),
    VersionRule(major=4, minor_gte=30, minor_lte=32),
    VersionRule(major=4, minor=33, patch_lte=8),
    VersionRule(major=4, minor=34, patch_lte=1),
)
FIXED_RELEASES = (
    FixedRelease(EOSVersion(4, 37, 0, suffix="F")),
    FixedRelease(EOSVersion(4, 36, 0, suffix="F")),
    FixedRelease(EOSVersion(4, 35, 0, suffix="F")),
    FixedRelease(EOSVersion(4, 34, 2, suffix="F")),
    FixedRelease(EOSVersion(4, 33, 9, suffix="M")),
)
AFFECTED_PLATFORM_FAMILIES = frozenset({PlatformFamily.SERIES_750_X})

ADVISORY = _AdvisoryMetadata(
    sa_number="0224",
    last_updated=date(2026, 11, 10),
    title="Security Advisory 0224",
    vulnerabilities=(
        _AdvisoryVulnerability(
            id="CVE-2026-121370",
            severity=_AdvisoryVulnerabilitySeverity.HIGH,
            description="Traffic received on a PTP-enabled port can cause a denial of service on affected 750X platforms.",
        ),
    ),
    url="https://www.arista.com/en/support/advisories-notices/security-advisory/25046-security-advisory-0224",
    description=(
        "On affected 750X platforms running Arista EOS with PTP configured, an unauthenticated attacker with network access to a "
        "PTP-enabled port can cause a denial of service by sending traffic to the system."
    ),
)
VULNERABILITY_ID = ADVISORY.vulnerabilities[0].id


def _assess_sa224(
    version: Fact[EosVersionFact],
    platform: Fact[PlatformIdentityFact],
    ptp: Fact[PtpGlobalFact],
) -> VulnerabilityResult:
    """Assess affected EOS/platform scope and globally enabled PTP."""
    if not isinstance(ptp, UnavailableFact) and ptp.value.state is FeatureState.DISABLED:
        return NotAffectedResult(vulnerability_id=VULNERABILITY_ID, decisive=(ptp,))

    eos_scope = assess_eos_scope(VULNERABILITY_ID, version, AFFECTED_VERSION_MATRIX)
    if isinstance(eos_scope, NotAffectedResult):
        return eos_scope
    platform_scope = assess_platform_scope(VULNERABILITY_ID, platform, AFFECTED_PLATFORM_FAMILIES)
    if isinstance(platform_scope, NotAffectedResult):
        return platform_scope

    if isinstance(eos_scope, ErrorResult) or isinstance(platform_scope, ErrorResult) or isinstance(ptp, UnavailableFact):
        return ErrorResult(
            vulnerability_id=VULNERABILITY_ID,
            problems=(
                *(eos_scope.problems if isinstance(eos_scope, ErrorResult) else ()),
                *(platform_scope.problems if isinstance(platform_scope, ErrorResult) else ()),
                *((ptp,) if isinstance(ptp, UnavailableFact) else ()),
            ),
        )
    return AffectedResult(
        vulnerability_id=VULNERABILITY_ID,
        context=(eos_scope, platform_scope),
        conditions=(ptp,),
        remediation=software_version_plan(FIXED_RELEASES, current_version=eos_scope.fact.value),
    )


@preview_test_class(warning_message=_PREVIEW_WARNING)
class SA224(OptionalCommandsMixin, _AntaAdvisoryTest):
    """Verify whether the device is impacted by Security Advisory 0224.

    Expected Results
    ----------------
    * Not Affected: EOS or the platform is outside scope, or global PTP is disabled.
    * Affected: An affected 750X platform and EOS release have PTP globally enabled, including when no PTP interfaces are configured.
    * Error: Required EOS, platform, or global PTP state cannot be determined.

    Notes
    -----
    The test does not check whether PTP is enabled on individual interfaces. Global PTP enablement determines the PTP exposure condition;
    port state, master/slave counts, and traffic counters do not gate the assessment. The test does not detect exploitation.

    The operational PTP CPU-queue bandwidth-limiting workaround is not assessed. An in-scope device with global PTP enabled is reported as
    Affected regardless of workaround application. This conservative coverage limit does not imply that the workaround is ineffective or
    unobservable. Software remediation lists the fixed releases.

    PTP state is read from ``show ptp`` revision 2. Explicit disabled mode and the disabled variant containing only an empty interface-summary
    mapping both establish disabled PTP. Every nonempty mode other than ``ptpDisabled`` establishes enabled PTP, including new modes.
    Missing or malformed required output and empty explicit modes produce Error when required;
    unsupported or failed PTP collection also produces Error on an otherwise in-scope device. Disabled PTP, excluded software, or an excluded
    platform can independently establish Not Affected without unrelated unavailable inputs. All required unavailable inputs are retained when
    no decisive exclusion applies.

    Examples
    --------
    ```yaml
    anta.tests.advisories:
      - SA224:
    ```
    """

    @facts_dataclass
    class Facts(FactsBase):
        """Collected facts required to assess the advisory."""

        version: Fact[EosVersionFact] = fact_field(EosVersionFact)
        platform: Fact[PlatformIdentityFact] = fact_field(PlatformIdentityFact)
        ptp: Fact[PtpGlobalFact] = fact_field(PtpGlobalFact)

    advisory: ClassVar[_AdvisoryMetadata] = ADVISORY
    description = "Verify whether the device is impacted by Security Advisory 0224."
    _atomic_support = True

    @_AntaAdvisoryTest.anta_test
    def test(self) -> None:
        """Derive the facts, assess the vulnerability, and project its atomic result."""
        facts = self.Facts.collect(self)
        finding = _assess_sa224(facts.version, facts.platform, facts.ptp)
        atomic = self.result.add(f"Verify {VULNERABILITY_ID}.", vulnerability_ids=(VULNERABILITY_ID,))
        project_vulnerability_result(atomic, finding)
