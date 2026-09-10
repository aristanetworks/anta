# Copyright (c) 2026 Arista Networks, Inc.
# Use of this source code is governed by the Apache License 2.0
# that can be found in the LICENSE file.
"""ANTA test for Arista Security Advisory 156."""

from __future__ import annotations

from datetime import date
from typing import Any, ClassVar

from anta._advisory.base import _PREVIEW_WARNING, _AntaAdvisoryTest
from anta._advisory.eos_versions import AffectedStatus, VersionRule, evaluate_version
from anta._advisory.facts.eos import EosVersionFact
from anta._advisory.facts.models import AvailableFact, Fact, FactDefinition, FeatureState, FeatureValue, MitigationState, MitigationValue, UnavailableFact
from anta._advisory.facts.network_services import (
    DhcpRelayActiveFact,
    DhcpRelayScope,
    DhcpRelayScopeFact,
    DhcpReplySourceValidationFact,
    IpAddressFamily,
    IpLockingCoverage,
    IpLockingCoverageFact,
    IpLockingMitigationFact,
    IpLockingScope,
)
from anta._advisory.findings.models import (
    AffectedFeatureState,
    AffectedResult,
    EosReleaseAssessment,
    ErrorResult,
    MitigatedCondition,
    MitigatedResult,
    NotAffectedResult,
    VersionRelation,
    VulnerabilityResult,
)
from anta._advisory.findings.projection import project_vulnerability_result
from anta._advisory.models import _AdvisoryMetadata, _AdvisoryVulnerability, _AdvisoryVulnerabilitySeverity
from anta._advisory.optional_commands import OptionalCommandsMixin
from anta._advisory.remediation import ApplyConfiguration, FixedRelease, RemediationPlan, Sequence, software_version_action
from anta._eos.version import EOSVersion
from anta.decorators import preview_test_class

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
VALIDATION_CONFIGURATION = ApplyConfiguration(("dhcp relay", "reply source-address validation"))
ADVISORY = _AdvisoryMetadata(
    sa_number="0156",
    last_updated=date(2026, 9, 9),
    title="Security Advisory 0156",
    vulnerabilities=(
        _AdvisoryVulnerability(
            id="CVE-2026-73437",
            severity=_AdvisoryVulnerabilitySeverity.CRITICAL,
            description="DHCP relay may forward replies from sources that are not configured helper addresses.",
        ),
    ),
    url="https://www.arista.com/en/support/advisories-notices/security-advisory/24712-security-advisory-0156",
    description="On affected EOS releases with DHCP relay active, unvalidated replies may provide clients with malicious network configuration.",
)
VULNERABILITY_ID = ADVISORY.vulnerabilities[0].id


def _version_relation(version: AvailableFact[EOSVersion]) -> VersionRelation:
    """Classify vulnerable, conditionally fixed, and outside-scope releases."""
    if evaluate_version(version.value, AFFECTED_VERSION_MATRIX).affected_status is AffectedStatus.AFFECTED:
        return VersionRelation.AFFECTED
    if evaluate_version(version.value, CONDITIONAL_FIXED_VERSION_MATRIX).affected_status is AffectedStatus.AFFECTED:
        return VersionRelation.CONDITIONAL_FIXED
    return VersionRelation.OUTSIDE_SCOPE


def _scope_families(scopes: tuple[IpLockingScope, ...], name: str) -> frozenset[IpAddressFamily]:
    """Return enforcement-disabled families for one case-insensitive scope name."""
    normalized_name = name.casefold()
    return next((scope.families for scope in scopes if scope.name.casefold() == normalized_name), frozenset())


def _vlan_name(interface: str) -> str | None:
    """Return the numeric VLAN scope name for an EOS VLAN interface."""
    prefix = "vlan"
    if not interface.casefold().startswith(prefix) or not (vlan := interface[len(prefix) :]).isdigit():
        return None
    return str(int(vlan))


def _ip_locking_covers_relay(relay: DhcpRelayScope, coverage: IpLockingCoverage) -> bool:
    """Return whether enforcement-disabled IP locking covers every relay path."""
    if not relay.interfaces:
        return False
    for relay_interface in relay.interfaces:
        covered_families = _scope_families(coverage.interfaces, relay_interface.name)
        if (vlan := _vlan_name(relay_interface.name)) is not None:
            covered_families |= _scope_families(coverage.vlans, vlan)
        if not relay_interface.families <= covered_families:
            return False
    return True


def _remediation(version: AvailableFact[EOSVersion], relation: VersionRelation) -> RemediationPlan:
    """Build the remaining source-defined resolution for one affected device."""
    if relation is VersionRelation.CONDITIONAL_FIXED:
        return RemediationPlan(VALIDATION_CONFIGURATION)
    return RemediationPlan(Sequence((software_version_action(FIXED_RELEASES, current_version=version.value), VALIDATION_CONFIGURATION)))


def _assess_sa156(  # noqa: C901, PLR0911  # pylint: disable=too-many-return-statements
    version: Fact[EOSVersion],
    relay: Fact[FeatureValue],
    validation: Fact[FeatureValue],
    ip_locking: Fact[MitigationValue],
    relay_scope: Fact[DhcpRelayScope],
    ip_locking_coverage: Fact[IpLockingCoverage],
) -> VulnerabilityResult:
    """Require the complete resolution or source-defined operational IP-locking coverage."""
    if not isinstance(relay, UnavailableFact) and relay.value.state is not FeatureState.ENABLED:
        return NotAffectedResult(vulnerability_id=VULNERABILITY_ID, decisive=(relay,))
    if isinstance(version, UnavailableFact):
        return ErrorResult(vulnerability_id=VULNERABILITY_ID, problems=(version,))
    relation = _version_relation(version)
    release = EosReleaseAssessment(version, relation)
    if relation is VersionRelation.OUTSIDE_SCOPE:
        return NotAffectedResult(vulnerability_id=VULNERABILITY_ID, decisive=(release,))
    if relation is VersionRelation.CONDITIONAL_FIXED and not isinstance(validation, UnavailableFact) and validation.value.state is FeatureState.ENABLED:
        return NotAffectedResult(vulnerability_id=VULNERABILITY_ID, decisive=(release, validation))
    if isinstance(relay, UnavailableFact):
        return ErrorResult(vulnerability_id=VULNERABILITY_ID, problems=(relay,))

    if isinstance(ip_locking, UnavailableFact):
        problems = (validation, ip_locking) if relation is VersionRelation.CONDITIONAL_FIXED and isinstance(validation, UnavailableFact) else (ip_locking,)
        return ErrorResult(vulnerability_id=VULNERABILITY_ID, problems=problems)
    if ip_locking.value.state is MitigationState.EFFECTIVE:
        if isinstance(relay_scope, UnavailableFact):
            problems = (validation, relay_scope) if relation is VersionRelation.CONDITIONAL_FIXED and isinstance(validation, UnavailableFact) else (relay_scope,)
            return ErrorResult(vulnerability_id=VULNERABILITY_ID, problems=problems)
        if isinstance(ip_locking_coverage, UnavailableFact):
            problems = (
                (validation, ip_locking_coverage)
                if relation is VersionRelation.CONDITIONAL_FIXED and isinstance(validation, UnavailableFact)
                else (ip_locking_coverage,)
            )
            return ErrorResult(vulnerability_id=VULNERABILITY_ID, problems=problems)
        if _ip_locking_covers_relay(relay_scope.value, ip_locking_coverage.value):
            return MitigatedResult(
                vulnerability_id=VULNERABILITY_ID,
                mitigated_conditions=(MitigatedCondition(relay, (ip_locking,)),),
                context=(release,),
                remediation=_remediation(version, relation),
            )

    if relation is VersionRelation.CONDITIONAL_FIXED:
        if isinstance(validation, AvailableFact):
            return AffectedResult(
                vulnerability_id=VULNERABILITY_ID,
                conditions=(relay, AffectedFeatureState(validation.definition, validation.value, validation.source)),
                context=(release,),
                remediation=_remediation(version, relation),
            )
        return ErrorResult(vulnerability_id=VULNERABILITY_ID, problems=(validation,))
    return AffectedResult(
        vulnerability_id=VULNERABILITY_ID,
        conditions=(relay,),
        context=(release,),
        remediation=_remediation(version, relation),
    )


@preview_test_class(warning_message=_PREVIEW_WARNING)
class SA156(OptionalCommandsMixin, _AntaAdvisoryTest):
    """Verify whether the device is impacted by Security Advisory 0156.

    Expected Results
    ----------------
    * Success: DHCP relay is inactive, EOS is outside scope, or a conditionally fixed release has reply validation enabled.
    * Failure: Active DHCP relay is neither fully resolved nor covered by operational enforcement-disabled IP locking.
    * Mitigated: Enforcement-disabled IP locking operationally covers every active relay interface and address family.
    * Error: Required EOS, DHCP relay, reply-validation, or IP-locking scope cannot be determined.

    A software update alone is insufficient. The advisory requires reply source-address validation on every fixed release.
    Its alternative IP-locking mitigation is accepted only from operational state whose interface or VLAN and IPv4/IPv6
    coverage can be correlated with every active DHCP relay path. Unsupported IP locking proves that mitigation is absent.

    Examples
    --------
    ```yaml
    anta.tests.advisories:
      - SA156:
    ```
    """

    advisory: ClassVar[_AdvisoryMetadata] = ADVISORY
    required_facts: ClassVar[tuple[type[FactDefinition[Any]], ...]] = (
        EosVersionFact,
        DhcpRelayActiveFact,
        DhcpReplySourceValidationFact,
        IpLockingMitigationFact,
        DhcpRelayScopeFact,
        IpLockingCoverageFact,
    )
    description = "Verify whether the device is impacted by Security Advisory 0156."
    _atomic_support = True

    @_AntaAdvisoryTest.anta_test
    def test(self) -> None:
        """Derive facts, assess the vulnerability, and project it."""
        finding = _assess_sa156(
            self.fact(EosVersionFact),
            self.fact(DhcpRelayActiveFact),
            self.fact(DhcpReplySourceValidationFact),
            self.fact(IpLockingMitigationFact),
            self.fact(DhcpRelayScopeFact),
            self.fact(IpLockingCoverageFact),
        )
        atomic = self.result.add(f"Verify {VULNERABILITY_ID}.", vulnerability_ids=(VULNERABILITY_ID,))
        project_vulnerability_result(atomic, finding)
