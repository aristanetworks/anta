# Copyright (c) 2026 Arista Networks, Inc.
# Use of this source code is governed by the Apache License 2.0
# that can be found in the LICENSE file.
"""ANTA test for Arista Security Advisory 157."""

from __future__ import annotations

from datetime import date
from typing import Any, ClassVar, cast

from anta._advisory.base import _PREVIEW_WARNING, _AntaAdvisoryTest
from anta._advisory.eos_versions import AffectedStatus, VersionRule, evaluate_version
from anta._advisory.facts.eos import EosVersionFact
from anta._advisory.facts.models import AvailableFact, Fact, FactDefinition, FeatureState, FeatureValue, UnavailableFact
from anta._advisory.facts.network_services import VrrpAntiReplayFact, VrrpFact, VrrpV2IpAhFact
from anta._advisory.findings.assessment import assess_eos_scope
from anta._advisory.findings.models import (
    AffectedFeatureState,
    AffectedResult,
    EosReleaseAssessment,
    ErrorResult,
    NotAffectedResult,
    VersionRelation,
    VulnerabilityResult,
)
from anta._advisory.findings.projection import project_vulnerability_result
from anta._advisory.models import _AdvisoryMetadata, _AdvisoryVulnerability, _AdvisoryVulnerabilitySeverity
from anta._advisory.remediation import (
    AnyOf,
    ApplyConfiguration,
    ConditionalAction,
    FixedRelease,
    OperationalAction,
    RemediationPlan,
    Sequence,
    software_version_action,
    software_version_plan,
)
from anta._eos.version import EOSVersion
from anta.decorators import preview_test_class

# pylint: disable=duplicate-code
AFFECTED_VERSION_MATRIX: tuple[VersionRule, ...] = (
    VersionRule(major=4, minor=36, patch_lte=1),
    VersionRule(major=4, minor=35, patch_lte=5),
    VersionRule(major=4, minor=34, patch_lte=7),
    VersionRule(major=4, minor=33, patch_lte=9),
    VersionRule(major=4, minor_lt=33),
)
CONDITIONAL_FIXED_VERSION_MATRIX: tuple[VersionRule, ...] = (
    VersionRule(major=4, minor=36, patch_gte=2),
    VersionRule(major=4, minor=35, patch_gte=6),
    VersionRule(major=4, minor=34, patch_gte=8),
    VersionRule(major=4, minor=33, patch_gte=10),
    VersionRule(major=4, minor_gt=36),
)
FIXED_RELEASES = (
    FixedRelease(EOSVersion(4, 36, 2, suffix="F")),
    FixedRelease(EOSVersion(4, 35, 6, suffix="M")),
    FixedRelease(EOSVersion(4, 34, 8, suffix="M")),
    FixedRelease(EOSVersion(4, 33, 10, suffix="M")),
)
# pylint: enable=duplicate-code
ANTI_REPLAY_CONFIGURATION = ApplyConfiguration(("vrrp ipv4 authentication anti-replay",))
ADVISORY = _AdvisoryMetadata(
    sa_number="0157",
    last_updated=date(2026, 9, 9),
    title="Security Advisory 0157",
    vulnerabilities=(
        _AdvisoryVulnerability(
            id="CVE-2026-73444",
            severity=_AdvisoryVulnerabilitySeverity.MEDIUM,
            description="VRRPv2 IP-AH authentication may be bypassed by an adjacent attacker.",
        ),
        _AdvisoryVulnerability(
            id="CVE-2026-73443",
            severity=_AdvisoryVulnerabilitySeverity.MEDIUM,
            description="VRRPv2 IP-AH advertisements may be captured and replayed indefinitely.",
        ),
        _AdvisoryVulnerability(
            id="CVE-2026-73442",
            severity=_AdvisoryVulnerabilitySeverity.LOW,
            description="Peer VRRP authentication credentials may be written to agent trace logs.",
        ),
    ),
    url="https://www.arista.com/en/support/advisories-notices/security-advisory/24713-security-advisory-0157",
    description="On affected EOS releases, VRRP authentication may be bypassed, replayed, or exposed in logs depending on configuration.",
)
BYPASS_ID, REPLAY_ID, LOGGING_ID = (vulnerability.id for vulnerability in ADVISORY.vulnerabilities)


def _logging_remediation_plan(current_version: EOSVersion) -> RemediationPlan:
    """Return the alternative software resolution or conditional VRRP mitigation."""
    return RemediationPlan(
        AnyOf(
            (
                software_version_action(FIXED_RELEASES, current_version=current_version),
                ConditionalAction(
                    "VRRP is not operationally required",
                    OperationalAction("Disable VRRP as described in the advisory."),
                ),
            )
        )
    )


def _assess_bypass(version: Fact[EOSVersion], ip_ah: Fact[FeatureValue]) -> VulnerabilityResult:
    """Assess the VRRPv2 IP-AH authentication-bypass issue."""
    if not isinstance(ip_ah, UnavailableFact) and ip_ah.value.state is not FeatureState.ENABLED:
        return NotAffectedResult(vulnerability_id=BYPASS_ID, decisive=(ip_ah,))
    eos_release = assess_eos_scope(BYPASS_ID, version, AFFECTED_VERSION_MATRIX)
    if not isinstance(eos_release, EosReleaseAssessment):
        return eos_release
    if isinstance(ip_ah, UnavailableFact):
        return ErrorResult(vulnerability_id=BYPASS_ID, problems=(ip_ah,))
    return AffectedResult(
        vulnerability_id=BYPASS_ID,
        conditions=(cast("AvailableFact[FeatureValue]", ip_ah),),
        context=(eos_release,),
        remediation=software_version_plan(FIXED_RELEASES, current_version=eos_release.fact.value),
    )


def _replay_version_relation(version: AvailableFact[EOSVersion]) -> VersionRelation:
    """Classify releases requiring an update, the post-update setting, or neither."""
    if evaluate_version(version.value, AFFECTED_VERSION_MATRIX).affected_status is AffectedStatus.AFFECTED:
        return VersionRelation.AFFECTED
    if evaluate_version(version.value, CONDITIONAL_FIXED_VERSION_MATRIX).affected_status is AffectedStatus.AFFECTED:
        return VersionRelation.CONDITIONAL_FIXED
    return VersionRelation.OUTSIDE_SCOPE


def _assess_replay(  # noqa: PLR0911  # pylint: disable=too-many-return-statements
    version: Fact[EOSVersion], ip_ah: Fact[FeatureValue], anti_replay: Fact[FeatureValue]
) -> VulnerabilityResult:
    """Require both fixed software and explicitly enabled VRRP replay protection."""
    if not isinstance(ip_ah, UnavailableFact) and ip_ah.value.state is not FeatureState.ENABLED:
        return NotAffectedResult(vulnerability_id=REPLAY_ID, decisive=(ip_ah,))
    if isinstance(version, UnavailableFact):
        return ErrorResult(vulnerability_id=REPLAY_ID, problems=(version,))
    relation = _replay_version_relation(version)
    release = EosReleaseAssessment(version, relation)
    if relation is VersionRelation.OUTSIDE_SCOPE:
        return NotAffectedResult(vulnerability_id=REPLAY_ID, decisive=(release,))
    if relation is VersionRelation.CONDITIONAL_FIXED:
        if isinstance(anti_replay, UnavailableFact):
            return ErrorResult(vulnerability_id=REPLAY_ID, problems=(anti_replay,))
        if anti_replay.value.state is FeatureState.ENABLED:
            return NotAffectedResult(vulnerability_id=REPLAY_ID, decisive=(release, anti_replay))
        if isinstance(ip_ah, UnavailableFact):
            return ErrorResult(vulnerability_id=REPLAY_ID, problems=(ip_ah,))
        return AffectedResult(
            vulnerability_id=REPLAY_ID,
            conditions=(ip_ah, AffectedFeatureState(anti_replay.definition, anti_replay.value, anti_replay.source)),
            context=(release,),
            remediation=RemediationPlan(ANTI_REPLAY_CONFIGURATION),
        )
    if isinstance(ip_ah, UnavailableFact):
        return ErrorResult(vulnerability_id=REPLAY_ID, problems=(ip_ah,))
    plan = RemediationPlan(Sequence((software_version_action(FIXED_RELEASES, current_version=version.value), ANTI_REPLAY_CONFIGURATION)))
    return AffectedResult(vulnerability_id=REPLAY_ID, conditions=(ip_ah,), context=(release,), remediation=plan)


def _assess_logging(version: Fact[EOSVersion], vrrp: Fact[FeatureValue]) -> VulnerabilityResult:
    """Assess the VRRP credential-logging issue."""
    if not isinstance(vrrp, UnavailableFact) and vrrp.value.state is not FeatureState.ENABLED:
        return NotAffectedResult(vulnerability_id=LOGGING_ID, decisive=(vrrp,))
    eos_release = assess_eos_scope(LOGGING_ID, version, AFFECTED_VERSION_MATRIX)
    if not isinstance(eos_release, EosReleaseAssessment):
        return eos_release
    if isinstance(vrrp, UnavailableFact):
        return ErrorResult(vulnerability_id=LOGGING_ID, problems=(vrrp,))
    return AffectedResult(
        vulnerability_id=LOGGING_ID,
        conditions=(cast("AvailableFact[FeatureValue]", vrrp),),
        context=(eos_release,),
        remediation=_logging_remediation_plan(eos_release.fact.value),
    )


@preview_test_class(warning_message=_PREVIEW_WARNING)
class SA157(_AntaAdvisoryTest):
    """Verify whether the device is impacted by Security Advisory 0157.

    Expected Results
    ----------------
    * Success: EOS is outside scope or the configuration prerequisite for an issue is absent; replay also requires anti-replay after updating.
    * Failure: An affected release has the issue's VRRP prerequisite, or a conditionally fixed release lacks anti-replay for the replay issue.
    * Error: Required EOS or VRRP state cannot be determined.

    Replay protection is disabled by default after updating, so CVE-2026-73443 requires both fixed software and the global anti-replay setting.
    Assessment uses persistent VRRP configuration rather than transient operational state. CVE-2026-73444 and CVE-2026-73443 require VRRPv2
    with IP-AH authentication, while CVE-2026-73442 applies when either VRRPv2 or VRRPv3 is configured.

    Examples
    --------
    ```yaml
    anta.tests.advisories:
      - SA157:
    ```
    """

    advisory: ClassVar[_AdvisoryMetadata] = ADVISORY
    required_facts: ClassVar[tuple[type[FactDefinition[Any]], ...]] = (EosVersionFact, VrrpFact, VrrpV2IpAhFact, VrrpAntiReplayFact)
    description = "Verify whether the device is impacted by Security Advisory 0157."
    _atomic_support = True

    @_AntaAdvisoryTest.anta_test
    def test(self) -> None:
        """Derive facts, assess all three vulnerabilities, and project them."""
        version = self.fact(EosVersionFact)
        vrrp = self.fact(VrrpFact)
        ip_ah = self.fact(VrrpV2IpAhFact)
        anti_replay = self.fact(VrrpAntiReplayFact)
        for vulnerability_id, finding in (
            (BYPASS_ID, _assess_bypass(version, ip_ah)),
            (REPLAY_ID, _assess_replay(version, ip_ah, anti_replay)),
            (LOGGING_ID, _assess_logging(version, vrrp)),
        ):
            atomic = self.result.add(f"Verify {vulnerability_id}.", vulnerability_ids=(vulnerability_id,))
            project_vulnerability_result(atomic, finding)
