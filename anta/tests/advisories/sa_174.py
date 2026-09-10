# Copyright (c) 2026 Arista Networks, Inc.
# Use of this source code is governed by the Apache License 2.0
# that can be found in the LICENSE file.
"""ANTA test for Arista Security Advisory 174."""

from __future__ import annotations

from datetime import date
from typing import Any, ClassVar, cast

from anta._advisory.base import _PREVIEW_WARNING, _AntaAdvisoryTest
from anta._advisory.eos_versions import VersionRule
from anta._advisory.facts.eos import EosVersionFact
from anta._advisory.facts.management import GnsiAcctzFact, GnsiAuthzFact
from anta._advisory.facts.models import (
    AvailableFact,
    Fact,
    FactDefinition,
    FeatureState,
    FeatureValue,
    UnavailableFact,
)
from anta._advisory.facts.p4_runtime import P4RuntimeAccountingFact, P4RuntimeFact, P4RuntimeMtlsFact
from anta._advisory.findings.assessment import assess_eos_scope
from anta._advisory.findings.models import (
    AffectedFeatureState,
    AffectedResult,
    EosReleaseAssessment,
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
from anta._eos.version import EOSVersion
from anta.decorators import preview_test_class

AFFECTED_VERSION_MATRIX: tuple[VersionRule, ...] = (
    VersionRule(major=4, minor=36, patch_lte=1),
    VersionRule(major=4, minor=35, patch_lte=5),
    VersionRule(major=4, minor=34, patch_lte=7),
    VersionRule(major=4, minor=33),
    VersionRule(major=4, minor=32),
    VersionRule(major=4, minor=31),
    VersionRule(major=4, minor=30),
    VersionRule(major=4, minor=29, patch_gte=2),
)
FIXED_RELEASES = (
    FixedRelease(EOSVersion(4, 36, 2, suffix="F")),
    FixedRelease(EOSVersion(4, 35, 6, suffix="M")),
    FixedRelease(EOSVersion(4, 34, 8, suffix="M")),
)

ADVISORY = _AdvisoryMetadata(
    sa_number="0174",
    last_updated=date(2026, 9, 9),
    title="Security Advisory 0174",
    vulnerabilities=(
        _AdvisoryVulnerability(
            id="CVE-2026-73453",
            severity=_AdvisoryVulnerabilitySeverity.CRITICAL,
            description="An unauthenticated P4Runtime client may achieve arbitrary code execution.",
        ),
    ),
    url="https://www.arista.com/en/support/advisories-notices/security-advisory/24730-security-advisory-0174",
    description=(
        "On affected EOS releases, an unauthenticated client may achieve arbitrary code execution when P4Runtime uses no mutual TLS, or "
        "when request accounting is active without gNSI Authz RPC authorization."
    ),
)
VULNERABILITY_ID = ADVISORY.vulnerabilities[0].id


def _known_feature(fact: Fact[FeatureValue], state: FeatureState) -> bool:
    """Return whether a feature fact is available in the requested state."""
    return not isinstance(fact, UnavailableFact) and fact.value.state is state


# pylint: disable-next=too-many-return-statements
def _assess_sa174(  # noqa: PLR0911
    version: Fact[EOSVersion],
    p4_runtime: Fact[FeatureValue],
    mtls: Fact[FeatureValue],
    p4_accounting: Fact[FeatureValue],
    gnsi_acctz: Fact[FeatureValue],
    authz: Fact[FeatureValue],
) -> VulnerabilityResult:
    """Assess P4Runtime transport security, accounting, Authz state, and policy observability."""
    if not isinstance(p4_runtime, UnavailableFact) and p4_runtime.value.state is not FeatureState.ENABLED:
        return NotAffectedResult(vulnerability_id=VULNERABILITY_ID, decisive=(p4_runtime,))
    eos_release = assess_eos_scope(VULNERABILITY_ID, version, AFFECTED_VERSION_MATRIX)
    if not isinstance(eos_release, EosReleaseAssessment):
        return eos_release
    if isinstance(p4_runtime, UnavailableFact):
        return ErrorResult(vulnerability_id=VULNERABILITY_ID, problems=(p4_runtime,))
    remediation = software_version_plan(FIXED_RELEASES, current_version=eos_release.fact.value)
    if isinstance(mtls, UnavailableFact):
        return ErrorResult(vulnerability_id=VULNERABILITY_ID, problems=(mtls,))
    if mtls.value.state is not FeatureState.ENABLED:
        return AffectedResult(
            vulnerability_id=VULNERABILITY_ID,
            conditions=(p4_runtime, AffectedFeatureState(mtls.definition, mtls.value, mtls.source)),
            context=(eos_release,),
            remediation=remediation,
        )

    accounting_facts = (p4_accounting, gnsi_acctz)
    enabled_accounting = tuple(cast("AvailableFact[FeatureValue]", fact) for fact in accounting_facts if _known_feature(fact, FeatureState.ENABLED))
    unavailable_accounting = tuple(fact for fact in accounting_facts if isinstance(fact, UnavailableFact))
    if not enabled_accounting:
        if unavailable_accounting:
            return ErrorResult(vulnerability_id=VULNERABILITY_ID, problems=unavailable_accounting)
        return NotAffectedResult(
            vulnerability_id=VULNERABILITY_ID,
            decisive=tuple(cast("AvailableFact[FeatureValue]", fact) for fact in accounting_facts),
        )
    if isinstance(authz, UnavailableFact):
        return ErrorResult(vulnerability_id=VULNERABILITY_ID, problems=(authz,))
    if authz.value.state is FeatureState.ENABLED:
        return InconclusiveResult(
            vulnerability_id=VULNERABILITY_ID,
            indications=(eos_release, p4_runtime, mtls, *enabled_accounting, authz),
            unresolved=(
                Unobservable(
                    UnobservableKind.DEVICE_STATE_NOT_EXPOSED,
                    "whether the installed gNSI Authz policy permits only the documented SPIFFE identity",
                ),
            ),
            remediation=remediation,
        )
    return AffectedResult(
        vulnerability_id=VULNERABILITY_ID,
        conditions=(p4_runtime, mtls, *enabled_accounting, AffectedFeatureState(authz.definition, authz.value, authz.source)),
        context=(eos_release,),
        remediation=remediation,
    )


@preview_test_class(warning_message=_PREVIEW_WARNING)
class SA174(OptionalCommandsMixin, _AntaAdvisoryTest):
    """Verify whether the device is impacted by Security Advisory 0174.

    Expected Results
    ----------------
    * Success: EOS is outside scope, P4Runtime is disabled, or mTLS is used without request accounting or gNSI Acctz.
    * Failure: P4Runtime lacks mTLS, or accounting is active while gNSI Authz is disabled or unsupported.
    * Inconclusive: Accounting and gNSI Authz are enabled, but the installed Authz policy cannot be verified.
    * Error: Required EOS, P4Runtime, TLS, accounting, or gNSI Authz state cannot be determined.

    Examples
    --------
    ```yaml
    anta.tests.advisories:
      - SA174:
    ```
    """

    advisory: ClassVar[_AdvisoryMetadata] = ADVISORY
    required_facts: ClassVar[tuple[type[FactDefinition[Any]], ...]] = (
        EosVersionFact,
        P4RuntimeFact,
        P4RuntimeMtlsFact,
        P4RuntimeAccountingFact,
        GnsiAcctzFact,
        GnsiAuthzFact,
    )
    description = "Verify whether the device is impacted by Security Advisory 0174."
    _atomic_support = True

    @_AntaAdvisoryTest.anta_test
    def test(self) -> None:
        """Derive facts, assess the vulnerability, and project it."""
        finding = _assess_sa174(
            self.fact(EosVersionFact),
            self.fact(P4RuntimeFact),
            self.fact(P4RuntimeMtlsFact),
            self.fact(P4RuntimeAccountingFact),
            self.fact(GnsiAcctzFact),
            self.fact(GnsiAuthzFact),
        )
        atomic = self.result.add(f"Verify {VULNERABILITY_ID}.", vulnerability_ids=(VULNERABILITY_ID,))
        project_vulnerability_result(atomic, finding)
