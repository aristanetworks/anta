# Copyright (c) 2026 Arista Networks, Inc.
# Use of this source code is governed by the Apache License 2.0
# that can be found in the LICENSE file.
# pylint: disable=duplicate-code  # Keep advisory-specific scope constants local to each test.
"""ANTA test for Arista Security Advisory 201, revision 1.2."""

from __future__ import annotations

import re
from datetime import date
from typing import ClassVar

from anta._advisory.base import _PREVIEW_WARNING, _AntaAdvisoryTest
from anta._advisory.eos_versions import VersionRule
from anta._advisory.facts.eos import EosVersionFact
from anta._advisory.facts.models import AvailableFact, Fact, FactProblemKind, FactsBase, FeatureState, UnavailableFact, fact_field, facts_dataclass
from anta._advisory.facts.software import TerminAttrVersionFact
from anta._advisory.facts.terminattr import TerminAttrDefaultCaTlsFact
from anta._advisory.findings.assessment import assess_eos_version
from anta._advisory.findings.models import (
    AffectedComponentVersion,
    AffectedResult,
    ComponentVersionAssessment,
    EosReleaseAssessment,
    ErrorResult,
    FindingEvidence,
    InconclusiveResult,
    NotAffectedResult,
    Unobservable,
    UnobservableKind,
    VersionRelation,
    VulnerabilityResult,
)
from anta._advisory.findings.projection import project_vulnerability_result
from anta._advisory.models import _AdvisoryMetadata, _AdvisoryVulnerability, _AdvisoryVulnerabilitySeverity
from anta._advisory.optional_commands import OptionalCommandsMixin
from anta._advisory.remediation import (
    AnyOf,
    ApplyConfiguration,
    ConditionalAction,
    FixedRelease,
    RemediationPlan,
    RunCommand,
    Sequence,
    SoftwareTarget,
    software_version_action,
    software_version_plan,
)
from anta._advisory.version import SemanticVersion
from anta._eos.version import EOSVersion
from anta.decorators import preview_test_class

AFFECTED_VERSION_MATRIX: tuple[VersionRule, ...] = (
    VersionRule(major=4, minor=36, patch_lte=3),
    VersionRule(major=4, minor=35, patch_lte=7),
    VersionRule(major=4, minor=34, patch_lte=9),
    VersionRule(major=4, minor=33, patch_lte=11),
    VersionRule(major=4, minor=32),
    VersionRule(major=4, minor=31),
    VersionRule(major=4, minor=30),
    VersionRule(major=4, minor=29),
    VersionRule(major=4, minor=28, patch_lte=14),
    VersionRule(major=4, minor_lt=28),
)
# Revision 1.2 does not identify a fixed EOS release. Outside scope is not a claim of a published fix.
FIXED_RELEASES: tuple[FixedRelease, ...] = ()
# Each key is a v1.x minor release. None means every patch is affected;
# otherwise the last affected patch is inclusive. Unlisted minors are outside scope.
TERMINATTR_LAST_AFFECTED_PATCH: dict[int, int | None] = {
    46: 2,
    45: None,
    44: None,
    43: 10,
    42: None,
    41: None,
    40: 14,
    39: None,
    38: None,
    37: 14,
    36: None,
    35: None,
    34: 14,
    33: None,
    32: None,
    31: 17,
    30: None,
    29: None,
    28: None,
    27: None,
    26: None,
    25: None,
    24: None,
    23: None,
    22: None,
    21: None,
    20: None,
    19: None,
    18: None,
    17: None,
    16: None,
    15: None,
    14: None,
    13: None,
    12: None,
    11: None,
    10: None,
    9: None,
    8: None,
    7: None,
    6: None,
    5: None,
    4: None,
    3: None,
    2: None,
    1: None,
    0: None,
}
TERMINATTR_FIXED_RELEASES = (
    FixedRelease(SemanticVersion(1, 46, 3, prefix="v")),
    FixedRelease(SemanticVersion(1, 43, 11, prefix="v")),
    FixedRelease(SemanticVersion(1, 40, 15, prefix="v")),
    FixedRelease(SemanticVersion(1, 37, 15, prefix="v")),
    FixedRelease(SemanticVersion(1, 34, 15, prefix="v")),
    FixedRelease(SemanticVersion(1, 31, 18, prefix="v")),
)
TERMINATTR_EOS_COMPATIBILITY = {
    SemanticVersion(1, 46, 3): (EOSVersion(4, 30, 0, suffix="F"), EOSVersion(4, 36, 3, suffix="M")),
    SemanticVersion(1, 43, 11): (EOSVersion(4, 30, 0, suffix="F"), EOSVersion(4, 35, 7, suffix="M")),
    SemanticVersion(1, 40, 15): (EOSVersion(4, 29, 0, suffix="F"), EOSVersion(4, 34, 8, suffix="M")),
    SemanticVersion(1, 37, 15): (EOSVersion(4, 28, 0, suffix="F"), EOSVersion(4, 33, 10, suffix="M")),
    SemanticVersion(1, 34, 15): (EOSVersion(4, 27, 0, suffix="F"), EOSVersion(4, 32, 11, suffix="M")),
    SemanticVersion(1, 31, 18): (None, EOSVersion(4, 31, 10, suffix="M")),
}
CA_DISTRUST_CONFIGURATION = (
    "event-handler sa_0201_fix",
    "trigger on-boot",
    "trigger on-config disabled",
    "action bash",
    "d=/etc/pki/ca-trust/source/blocklist; [ -d $d ] || d=/etc/pki/ca-trust/source/blacklist",
    "trust extract --overwrite --format=pem-bundle \\",
    "  --filter='pkcs11:object=Comodo%20AAA%20Services%20root;type=cert' \\",
    "  $d/Comodo_AAA_Services_root.pem &&",
    "openssl x509 -in $d/Comodo_AAA_Services_root.pem \\",
    "  -out $d/Comodo_AAA_Services_root.pem \\",
    "  -trustout -addreject anyExtendedKeyUsage &&",
    "trust extract --overwrite --format=pem-bundle \\",
    "  --filter='pkcs11:object=emSign%20ECC%20Root%20CA%20-%20G3;type=cert' \\",
    "  $d/emSign_ECC_Root_CA_-_G3.pem &&",
    "openssl x509 -in $d/emSign_ECC_Root_CA_-_G3.pem \\",
    "  -out $d/emSign_ECC_Root_CA_-_G3.pem \\",
    "  -trustout -addreject anyExtendedKeyUsage &&",
    "update-ca-trust &&",
    "kill -9 $(pidof TerminAttr)",
    "EOF",
    "exit",
)
CUSTOM_PROGRAM_CONDITION = "custom scripts or programs use the default EOS trust store for outbound TLS"

ADVISORY = _AdvisoryMetadata(
    sa_number="0201",
    last_updated=date(2026, 10, 29),
    title="Security Advisory 0201",
    vulnerabilities=(
        _AdvisoryVulnerability(
            id="CVE-2026-111943",
            # Arista's provisional CVSS 4 estimate is 9.2; the CVE owner has not published a score.
            severity=_AdvisoryVulnerabilitySeverity.CRITICAL,
            description="Compromised eMudhra intermediate CA certificates permit man-in-the-middle attacks against outbound TLS clients.",
        ),
    ),
    url="https://www.arista.com/en/support/advisories-notices/security-advisory/24847-security-advisory-0201",
    description="Affected EOS trust stores and TerminAttr clients may trust compromised CA certificates when verifying outbound TLS connections.",
)
VULNERABILITY_ID = ADVISORY.vulnerabilities[0].id


def _parse_terminattr_version(value: str) -> SemanticVersion | None:
    """Parse the component's stable package-version representation."""
    match = re.fullmatch(r"v(\d+)\.(\d+)\.(\d+)", value)
    return SemanticVersion(*(int(part) for part in match.groups()), prefix="v") if match else None


def _terminattr_version_assessment(fact: Fact[TerminAttrVersionFact]) -> ComponentVersionAssessment | UnavailableFact[TerminAttrVersionFact]:
    """Interpret all component trains in the affected-software list independently of EOS."""
    if isinstance(fact, UnavailableFact):
        return fact
    version = _parse_terminattr_version(fact.value.version)
    if version is None:
        return TerminAttrVersionFact.unavailable(FactProblemKind.INVALID, fact.source)
    if version.major == 1:
        last_patch = TERMINATTR_LAST_AFFECTED_PATCH.get(version.minor)
        affected = version.minor in TERMINATTR_LAST_AFFECTED_PATCH and (last_patch is None or version.patch <= last_patch)
    else:
        affected = version.major < 1
    return ComponentVersionAssessment(fact, VersionRelation.AFFECTED if affected else VersionRelation.OUTSIDE_SCOPE)


def _compatible_terminattr_fixes(version: EOSVersion) -> tuple[FixedRelease, ...]:
    """Select only the component releases explicitly supported on the observed EOS."""
    return tuple(
        release
        for release in TERMINATTR_FIXED_RELEASES
        if isinstance(release.version, SemanticVersion)
        and (bounds := TERMINATTR_EOS_COMPATIBILITY[release.version])
        and (bounds[0] is None or bounds[0] <= version)
        and version <= bounds[1]
    )


def _remediation(eos: EosReleaseAssessment, component: ComponentVersionAssessment | None) -> RemediationPlan:
    """Resolve both software paths while retaining the source's conditional boot-script alternative."""
    eos_action = software_version_action(FIXED_RELEASES, current_version=eos.fact.value)
    if component is None or component.relation is not VersionRelation.AFFECTED:
        return RemediationPlan(eos_action)
    version = _parse_terminattr_version(component.fact.value.version)
    assert version is not None  # noqa: S101
    fixes = _compatible_terminattr_fixes(eos.fact.value)
    if eos.relation is VersionRelation.OUTSIDE_SCOPE:
        return software_version_plan(fixes, current_version=version, software=SoftwareTarget.TERMINATTR)
    if not fixes:
        return RemediationPlan(eos_action)
    return RemediationPlan(
        AnyOf(
            (
                eos_action,
                Sequence(
                    (
                        software_version_action(fixes, current_version=version, software=SoftwareTarget.TERMINATTR),
                        ConditionalAction(CUSTOM_PROGRAM_CONDITION, ApplyConfiguration(CA_DISTRUST_CONFIGURATION)),
                        ConditionalAction(CUSTOM_PROGRAM_CONDITION, RunCommand(("reload",))),
                    )
                ),
            )
        )
    )


def _required_fact_errors(
    eos: EosReleaseAssessment | UnavailableFact[EosVersionFact],
    tls: Fact[TerminAttrDefaultCaTlsFact],
    component: ComponentVersionAssessment | UnavailableFact[TerminAttrVersionFact],
) -> ErrorResult | None:
    """Collect every required input problem, ignoring evidence for a closed client path."""
    tls_disabled = isinstance(tls, AvailableFact) and tls.value.state is FeatureState.DISABLED
    component_outside = isinstance(component, ComponentVersionAssessment) and component.relation is VersionRelation.OUTSIDE_SCOPE
    problems: list[UnavailableFact[object]] = []
    if isinstance(eos, UnavailableFact):
        problems.append(eos)
    if not component_outside and isinstance(tls, UnavailableFact):
        problems.append(tls)
    if not tls_disabled and isinstance(component, UnavailableFact):
        problems.append(component)
    if problems:
        return ErrorResult(vulnerability_id=VULNERABILITY_ID, problems=tuple(problems))
    return None


def _assess_sa201_exposure(
    eos: EosReleaseAssessment,
    tls: Fact[TerminAttrDefaultCaTlsFact],
    component: ComponentVersionAssessment | UnavailableFact[TerminAttrVersionFact],
) -> AffectedResult | InconclusiveResult:
    """Resolve observable TerminAttr exposure and retain uncertainty about other TLS clients."""
    tls_disabled = isinstance(tls, AvailableFact) and tls.value.state is FeatureState.DISABLED
    component_outside = isinstance(component, ComponentVersionAssessment) and component.relation is VersionRelation.OUTSIDE_SCOPE
    applicable_component = component if not tls_disabled and isinstance(component, ComponentVersionAssessment) else None
    remediation = _remediation(eos, applicable_component)
    indications: list[FindingEvidence] = [eos]
    unresolved = []

    if applicable_component is not None:
        indications.append(applicable_component)
    if not tls_disabled and not component_outside:
        assert isinstance(tls, AvailableFact)  # noqa: S101
        indications.append(tls)
        # Only the endpoint explicitly identified by this advisory is a decisive
        # CVaaS destination. DNS aliases and other endpoints need external identification.
        documented_destination = any(
            connection.ca_file is None and any(address.rsplit(":", 1)[0].lower().rstrip(".") == "apiserver.arista.io" for address in connection.addresses)
            for connection in tls.value.connections
        )
        if documented_destination:
            assert isinstance(applicable_component, ComponentVersionAssessment)  # noqa: S101
            return AffectedResult(
                vulnerability_id=VULNERABILITY_ID,
                context=(eos,),
                conditions=(AffectedComponentVersion(applicable_component.fact), tls),
                remediation=remediation,
            )
        if not documented_destination:
            unresolved.append(Unobservable(UnobservableKind.EXTERNAL_STATE, "whether the configured default-CA TLS destination is CVaaS"))
    if eos.relation is VersionRelation.AFFECTED:
        unresolved.append(Unobservable(UnobservableKind.DEVICE_STATE_NOT_EXPOSED, "custom programs' outbound TLS behavior and trust-store selection"))
    return InconclusiveResult(vulnerability_id=VULNERABILITY_ID, indications=tuple(indications), unresolved=tuple(unresolved), remediation=remediation)


def _assess_sa201(
    version: Fact[EosVersionFact],
    tls: Fact[TerminAttrDefaultCaTlsFact],
    terminattr: Fact[TerminAttrVersionFact],
) -> VulnerabilityResult:
    """Apply software exclusions before required inputs and exposure assessment on every EOS platform."""
    eos = assess_eos_version(version, AFFECTED_VERSION_MATRIX)
    component = _terminattr_version_assessment(terminattr)
    if isinstance(eos, EosReleaseAssessment) and eos.relation is VersionRelation.OUTSIDE_SCOPE:
        if isinstance(tls, AvailableFact) and tls.value.state is FeatureState.DISABLED:
            return NotAffectedResult(vulnerability_id=VULNERABILITY_ID, decisive=(eos, tls))
        if isinstance(component, ComponentVersionAssessment) and component.relation is VersionRelation.OUTSIDE_SCOPE:
            return NotAffectedResult(vulnerability_id=VULNERABILITY_ID, decisive=(eos, component))

    errors = _required_fact_errors(eos, tls, component)
    if errors is not None:
        return errors

    assert isinstance(eos, EosReleaseAssessment)  # noqa: S101
    return _assess_sa201_exposure(eos, tls, component)


@preview_test_class(warning_message=_PREVIEW_WARNING)
class SA201(OptionalCommandsMixin, _AntaAdvisoryTest):
    """Assess outbound TLS certificate-trust exposure described by Security Advisory 0201.

    Expected Results
    ----------------
    * Not Affected: Both software/exposure paths are outside scope.
    * Affected: Affected TerminAttr has a configured default-CA TLS client to the documented CVaaS endpoint.
    * Inconclusive: An unidentified destination or custom-program behavior on affected EOS prevents a complete assessment.
    * Error: Required EOS version, TerminAttr configuration, or applicable component version is unavailable or invalid.

    Notes
    -----
    EOS and TerminAttr releases are assessed independently. Enabled, persistently configured TerminAttr clients are evaluated even when no
    session is currently established. Explicit CA selection closes only that client path; a TerminAttr upgrade does not close the separate
    custom-program path on affected EOS. Arbitrary programs' TLS behavior and CA selection cannot be established by this test.

    CA argument placement follows the advisory's explicit impacted and non-impacted examples: after the token file for token-secure, or
    after the certificate and key for certs. The prose's reference to a second argument is not used to reinterpret those examples.

    Only the advisory's explicitly identified CVaaS endpoint, apiserver.arista.io, proves a CVaaS destination; other default-CA destinations
    remain inconclusive. Secure certs and token-secure authentication, including per-cluster options, are supported. Other authentication
    modes require additional evidence and produce an error when needed. All EOS platforms, including CVX, are assessed without platform-family
    exclusions. Other Arista products covered by the advisory are outside this test.

    No mitigation success is claimed from an on-boot event handler: its configuration alone cannot prove execution or effective CA distrust.
    The advisory's CA-distrust workaround requires a reload and can disrupt legitimate TLS endpoints relying on the distrusted roots.

    Examples
    --------
    ```yaml
    anta.tests.advisories:
      - SA201:
    ```
    """

    @facts_dataclass
    class Facts(FactsBase):
        """Collected facts required to assess the advisory."""

        version: Fact[EosVersionFact] = fact_field(EosVersionFact)
        tls: Fact[TerminAttrDefaultCaTlsFact] = fact_field(TerminAttrDefaultCaTlsFact)
        terminattr: Fact[TerminAttrVersionFact] = fact_field(TerminAttrVersionFact)

    advisory: ClassVar[_AdvisoryMetadata] = ADVISORY
    description = "Verify whether the device is impacted by Security Advisory 0201."
    _atomic_support = True

    @_AntaAdvisoryTest.anta_test
    def test(self) -> None:
        """Collect declared facts, assess the vulnerability, and project its atomic result."""
        facts = self.Facts.collect(self)
        finding = _assess_sa201(facts.version, facts.tls, facts.terminattr)
        atomic = self.result.add(f"Verify {VULNERABILITY_ID}.", vulnerability_ids=(VULNERABILITY_ID,))
        project_vulnerability_result(atomic, finding)
