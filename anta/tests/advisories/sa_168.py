# Copyright (c) 2026 Arista Networks, Inc.
# Use of this source code is governed by the Apache License 2.0
# that can be found in the LICENSE file.
"""ANTA test for Arista Security Advisory 168."""

from __future__ import annotations

from datetime import date
from typing import Any, ClassVar, cast

from anta._advisory.base import _PREVIEW_WARNING, _AntaAdvisoryTest
from anta._advisory.eos_versions import VersionRule
from anta._advisory.facts.eos import EosVersionFact
from anta._advisory.facts.management import GnmiTransportFact, NetconfTransportFact, RestconfTransportFact
from anta._advisory.facts.models import AvailableFact, Fact, FactDefinition, FeatureState, FeatureValue, UnavailableFact
from anta._advisory.findings.assessment import assess_eos_scope
from anta._advisory.findings.models import AffectedResult, EosReleaseAssessment, ErrorResult, NotAffectedResult, VulnerabilityResult
from anta._advisory.findings.projection import project_vulnerability_result
from anta._advisory.models import _AdvisoryMetadata, _AdvisoryVulnerability, _AdvisoryVulnerabilitySeverity
from anta._advisory.optional_commands import OptionalCommandsMixin
from anta._advisory.remediation import AllOf, ConditionalAction, FixedRelease, OperationalAction, RemediationPlan, software_version_action
from anta._eos.version import EOSVersion
from anta.decorators import preview_test_class

AFFECTED_VERSION_MATRIX: tuple[VersionRule, ...] = (
    VersionRule(major=4, minor=36, patch_lte=1),
    VersionRule(major=4, minor_lte=35),
)
FIXED_RELEASES = (FixedRelease(EOSVersion(4, 36, 2, suffix="F")),)
ADVISORY = _AdvisoryMetadata(
    sa_number="0168",
    last_updated=date(2026, 9, 9),
    title="Security Advisory 0168",
    vulnerabilities=(
        _AdvisoryVulnerability(
            id="CVE-2026-2380",
            severity=_AdvisoryVulnerabilitySeverity.HIGH,
            description="OpenConfig requests and responses containing sensitive values may be written to local or accounting logs.",
        ),
    ),
    url="https://www.arista.com/en/support/advisories-notices/security-advisory/24724-security-advisory-0168",
    description="On affected EOS releases, enabled OpenConfig services may log sensitive request or response content.",
)
VULNERABILITY_ID = ADVISORY.vulnerabilities[0].id


def _remediation_plan(current_version: EOSVersion) -> RemediationPlan:
    """Return the source-backed software and conditional incident-response actions."""
    return RemediationPlan(
        AllOf(
            (
                software_version_action(FIXED_RELEASES, current_version=current_version),
                ConditionalAction(
                    "sensitive information was logged",
                    OperationalAction("Clean up affected local and remote logs, including rotated logs, as described in the advisory."),
                ),
                ConditionalAction(
                    "logged information contained secrets",
                    OperationalAction("Rotate exposed or compromised secrets as described in the advisory."),
                ),
            )
        )
    )


def _assess_sa168(version: Fact[EOSVersion], services: tuple[Fact[FeatureValue], ...]) -> VulnerabilityResult:
    """Assess the OR relationship across gNMI, RESTCONF, and NETCONF services."""
    enabled = tuple(fact for fact in services if isinstance(fact, AvailableFact) and fact.value.state is FeatureState.ENABLED)
    if not enabled and all(isinstance(fact, AvailableFact) for fact in services):
        return NotAffectedResult(vulnerability_id=VULNERABILITY_ID, decisive=cast("tuple[AvailableFact[FeatureValue], ...]", services))
    eos_release = assess_eos_scope(VULNERABILITY_ID, version, AFFECTED_VERSION_MATRIX)
    if not isinstance(eos_release, EosReleaseAssessment):
        return eos_release
    if not enabled:
        problems = tuple(fact for fact in services if isinstance(fact, UnavailableFact))
        return ErrorResult(vulnerability_id=VULNERABILITY_ID, problems=problems)
    return AffectedResult(
        vulnerability_id=VULNERABILITY_ID,
        conditions=enabled,
        context=(eos_release,),
        remediation=_remediation_plan(eos_release.fact.value),
    )


@preview_test_class(warning_message=_PREVIEW_WARNING)
class SA168(OptionalCommandsMixin, _AntaAdvisoryTest):
    """Verify whether the device is impacted by Security Advisory 0168.

    Expected Results
    ----------------
    * Success: EOS is outside scope or gNMI, RESTCONF, and NETCONF are all disabled or unsupported.
    * Failure: An affected EOS release has at least one of those OpenConfig services enabled.
    * Error: No service proves exposure and required EOS or service state cannot be determined.

    Examples
    --------
    ```yaml
    anta.tests.advisories:
      - SA168:
    ```
    """

    advisory: ClassVar[_AdvisoryMetadata] = ADVISORY
    required_facts: ClassVar[tuple[type[FactDefinition[Any]], ...]] = (EosVersionFact, GnmiTransportFact, RestconfTransportFact, NetconfTransportFact)
    description = "Verify whether the device is impacted by Security Advisory 0168."
    _atomic_support = True

    @_AntaAdvisoryTest.anta_test
    def test(self) -> None:
        """Derive facts, assess the vulnerability, and project it."""
        finding = _assess_sa168(
            self.fact(EosVersionFact),
            (self.fact(GnmiTransportFact), self.fact(RestconfTransportFact), self.fact(NetconfTransportFact)),
        )
        atomic = self.result.add(f"Verify {VULNERABILITY_ID}.", vulnerability_ids=(VULNERABILITY_ID,))
        project_vulnerability_result(atomic, finding)
