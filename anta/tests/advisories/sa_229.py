# Copyright (c) 2026 Arista Networks, Inc.
# Use of this source code is governed by the Apache License 2.0
# that can be found in the LICENSE file.
"""ANTA test for Arista Security Advisory 229."""

from __future__ import annotations

from datetime import date
from typing import ClassVar

from anta._advisory.base import _PREVIEW_WARNING, _AntaAdvisoryTest
from anta._advisory.eos_versions import VersionRule
from anta._advisory.facts.eos import EosVersionFact
from anta._advisory.facts.management_queues import ManagementSingleQueueBootFact
from anta._advisory.facts.models import Fact, FactProblemKind, FactsBase, FeatureState, UnavailableFact, fact_field, facts_dataclass
from anta._advisory.facts.platform import PlatformIdentityFact
from anta._advisory.findings.assessment import assess_eos_scope, assess_platform_scope
from anta._advisory.findings.models import (
    AffectedEosRelease,
    AffectedResult,
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
from anta._eos.platform import PlatformFamily
from anta.decorators import preview_test_class

# ADR-0003 keeps affected trains open-ended until the advisory publishes a fix.
AFFECTED_VERSION_MATRIX: tuple[VersionRule, ...] = (
    VersionRule(major=4, minor=21, patch_gte=3),
    VersionRule(major=4, minor_gte=22, minor_lte=37),
)
FIXED_RELEASES: tuple[FixedRelease, ...] = ()
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
        PlatformFamily.SERIES_7368_X4,
        PlatformFamily.SERIES_7388_X5,
        PlatformFamily.SERIES_7500_R,
        PlatformFamily.SERIES_7500_R2,
        PlatformFamily.SERIES_7500_R3,
        PlatformFamily.SERIES_7800_R3,
        PlatformFamily.SERIES_7800_R4,
        PlatformFamily.SERIES_7700_R4,
        PlatformFamily.ZTX_7200,
        PlatformFamily.CEOS_LAB,
        PlatformFamily.VEOS_LAB,
        PlatformFamily.CVX,
    }
)

ADVISORY = _AdvisoryMetadata(
    sa_number="0229",
    last_updated=date(2026, 11, 24),
    title="Security Advisory 0229",
    vulnerabilities=(
        _AdvisoryVulnerability(
            id="CVE-2026-99288",
            severity=_AdvisoryVulnerabilitySeverity.HIGH,
            description="IPv4 TCP traffic can cause a Linux kernel panic and device restart (NoisyTCP).",
        ),
    ),
    url="https://www.arista.com/en/support/advisories-notices/security-advisory/25220-security-advisory-0229",
    description="An unauthenticated attacker sending IPv4 traffic to a reachable TCP port can cause a kernel panic on affected EOS devices.",
)
VULNERABILITY_ID = "CVE-2026-99288"


def _assess_sa229(
    version: Fact[EosVersionFact],
    platform: Fact[PlatformIdentityFact],
    boot: Fact[ManagementSingleQueueBootFact],
) -> VulnerabilityResult:
    """Assess EOS exposure without treating traffic or interface state as prerequisites."""
    eos_scope = assess_eos_scope(VULNERABILITY_ID, version, AFFECTED_VERSION_MATRIX)
    if isinstance(eos_scope, NotAffectedResult):
        return eos_scope
    platform_scope = assess_platform_scope(VULNERABILITY_ID, platform, AFFECTED_PLATFORM_FAMILIES)
    if isinstance(platform_scope, NotAffectedResult):
        return platform_scope
    if not isinstance(boot, UnavailableFact) and boot.value.state is FeatureState.UNSUPPORTED:
        boot = ManagementSingleQueueBootFact.unavailable(FactProblemKind.UNSUPPORTED, boot.source)
    problems = (
        *(eos_scope.problems if isinstance(eos_scope, ErrorResult) else ()),
        *(platform_scope.problems if isinstance(platform_scope, ErrorResult) else ()),
        *((boot,) if isinstance(boot, UnavailableFact) else ()),
    )
    if isinstance(eos_scope, ErrorResult) or isinstance(platform_scope, ErrorResult) or isinstance(boot, UnavailableFact):
        return ErrorResult(
            vulnerability_id=VULNERABILITY_ID,
            problems=problems,
        )
    if boot.value.state is FeatureState.ENABLED:
        return InconclusiveResult(
            vulnerability_id=VULNERABILITY_ID,
            indications=(eos_scope, platform_scope, boot),
            unresolved=(
                Unobservable(UnobservableKind.DEVICE_STATE_NOT_EXPOSED, "effective receive-channel coverage within the supported non-Bash observation contract"),
            ),
            remediation=software_version_plan(FIXED_RELEASES, current_version=eos_scope.fact.value),
        )
    return AffectedResult(
        vulnerability_id=VULNERABILITY_ID,
        conditions=(AffectedEosRelease(eos_scope.fact),),
        context=(platform_scope,),
        remediation=software_version_plan(FIXED_RELEASES, current_version=eos_scope.fact.value),
    )


@preview_test_class(warning_message=_PREVIEW_WARNING)
class SA229(OptionalCommandsMixin, _AntaAdvisoryTest):
    """Verify whether the device is impacted by Security Advisory 0229 (NoisyTCP).

    Expected Results
    ----------------
    * Not Affected: EOS or the platform is outside scope, including EOS before 4.21.3F and CloudEOS or AWE platforms.
    * Affected: EOS and the platform are in scope, with no enabled advisory boot control recognized.
    * Inconclusive: EOS and the platform are in scope and the advisory boot control is enabled, but its effective coverage is not verified.
    * Error: Required EOS, platform, or event-handler observations cannot be collected or interpreted reliably.

    Notes
    -----
    EOS exposure requires no configurable feature prerequisite. Assessment uses software and platform identity;
    idle services, down interfaces, TCP reachability, and absence of crash indicators do not establish safety.
    The test assesses exposure and does not detect exploitation. Non-EOS products covered by the advisory are outside its scope.

    The only test-specific collected command is structured ``show event-handler``. The test never executes Bash, invokes ``ethtool``,
    enumerates namespaces, or changes device configuration. This deliberately limited observation contract supports ANTA
    accounts without shell access or permission to execute arbitrary Bash commands.

    An enabled on-boot handler is recognized by an exact match to the advisory's canonical action text, regardless of its name. That text is
    compared as data and is never executed. Equivalent arbitrary Bash programs are not interpreted. A complete matching
    handler can be recognized despite unrelated malformed handler records.

    Presence of the boot control does not prove that its action succeeded or that every relevant interface currently uses
    one receive channel. Effective queue state is outside this test's non-Bash observation contract, so a recognized enabled
    control produces Inconclusive, not Mitigated. Inconclusive projects to ANTA Failure and requires operator verification.
    A denied, unsupported, missing, or malformed required ``show event-handler`` observation produces Error; it is never
    converted to Inconclusive. The test does not infer mitigation from action counters or transient interface state.

    Revision 1.2 publishes no fixed EOS releases or hotfix. Following the advisory software-version policy, affected trains from
    4.21 through 4.37 remain open-ended until fixed releases are published, while preserving the 4.21.3F introduction boundary.
    Later patches and hotfixes in those trains are conservatively reported as Affected even when they exceed the listed maxima.
    This policy does not establish that every later release contains the vulnerability. Remediation recommends a fixed release
    when one is published; consult the advisory for the current workaround and its management-interface disruption warning.

    Examples
    --------
    ```yaml
    anta.tests.advisories:
      - SA229:
    ```
    """

    @facts_dataclass
    class Facts(FactsBase):
        """Software, platform, and read-only boot-control observations."""

        version: Fact[EosVersionFact] = fact_field(EosVersionFact)
        platform: Fact[PlatformIdentityFact] = fact_field(PlatformIdentityFact)
        boot: Fact[ManagementSingleQueueBootFact] = fact_field(ManagementSingleQueueBootFact)

    advisory: ClassVar[_AdvisoryMetadata] = ADVISORY
    description = "Verify whether the device is impacted by Security Advisory 0229."
    _atomic_support = True

    @_AntaAdvisoryTest.anta_test
    def test(self) -> None:
        """Collect metadata facts, assess exposure, and project the single CVE result."""
        facts = self.Facts.collect(self)
        finding = _assess_sa229(facts.version, facts.platform, facts.boot)
        atomic = self.result.add(f"Verify {VULNERABILITY_ID}.", vulnerability_ids=(VULNERABILITY_ID,))
        project_vulnerability_result(atomic, finding)
