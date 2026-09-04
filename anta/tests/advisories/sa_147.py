# Copyright (c) 2026 Arista Networks, Inc.
# Use of this source code is governed by the Apache License 2.0
# that can be found in the LICENSE file.
"""ANTA test for Arista Security Advisory 147."""

from __future__ import annotations

import re
from typing import TYPE_CHECKING, Any, ClassVar, cast

from anta._advisory.base import _AntaAdvisoryTest
from anta._advisory.eos_versions import AffectedStatus, VersionRule, evaluate_version
from anta._advisory.facts.eos import EosVersionFact
from anta._advisory.facts.models import (
    ComponentSoftwareVersion,
    Fact,
    FactDefinition,
    FactProblemKind,
    FeatureState,
    FeatureValue,
    MitigationState,
    MitigationValue,
    UnavailableFact,
)
from anta._advisory.facts.software import OpenSshClientVersionFact, OpenSshServerVersionFact
from anta._advisory.facts.ssh import SshServerFact, StrictHostKeyCheckingFact
from anta._advisory.findings.models import (
    AffectedComponentVersion,
    AffectedResult,
    ComponentVersionAssessment,
    EosReleaseAssessment,
    ErrorResult,
    MitigatedCondition,
    MitigatedResult,
    NotAffectedResult,
    VersionRelation,
    VulnerabilityResult,
)
from anta._advisory.findings.projection import project_vulnerability_result
from anta._advisory.models import (
    _AdvisoryMetadata,
    _AdvisoryVulnerability,
    _AdvisoryVulnerabilitySeverity,
)
from anta._advisory.optional_commands import OptionalCommandsMixin
from anta._advisory.remediation import (
    FixedRelease,
    software_version_plan,
)
from anta._eos.version import EOSVersion
from anta.decorators import preview_test_class

if TYPE_CHECKING:
    from anta.device import DeviceVersion

OPENSSH_VERSION_PATTERN = re.compile(r"^(?P<major>\d+)\.(?P<minor>\d+)(?:p(?P<patch>\d+))?(?:[^\d].*)?$")

CVE_60002_FIXED_RELEASES = (
    FixedRelease(EOSVersion(4, 35, 6, suffix="M")),
    FixedRelease(EOSVersion(4, 34, 8, suffix="M")),
)
EOS_AFFECTED_VERSION_MATRIX: tuple[VersionRule, ...] = (
    VersionRule(major=4, minor=36, patch_lte=2),
    VersionRule(major=4, minor=35, patch_lte=5),
    VersionRule(major=4, minor=34, patch_lt=7),
    VersionRule(major=4, minor=34, patch_eq=7, hotfix_lte=1),
    VersionRule(major=4, minor=33, patch_lte=10),
    VersionRule(major=4, minor_lt=33),
)
ADVISORY = _AdvisoryMetadata(
    sa_number="0147",
    title="Security Advisory 0147",
    vulnerabilities=(
        _AdvisoryVulnerability(
            id="CVE-2026-59995",
            severity=_AdvisoryVulnerabilitySeverity.MEDIUM,
            description="SFTP client issue when connecting to an untrusted server.",
        ),
        _AdvisoryVulnerability(
            id="CVE-2026-59996",
            severity=_AdvisoryVulnerabilitySeverity.MEDIUM,
            description=("SCP remote-to-remote client issue involving an untrusted server."),
        ),
        _AdvisoryVulnerability(
            id="CVE-2026-60001",
            severity=_AdvisoryVulnerabilitySeverity.MEDIUM,
            description="OpenSSH server issue affecting accepted SSH connections.",
        ),
        _AdvisoryVulnerability(
            id="CVE-2026-60002",
            severity=_AdvisoryVulnerabilitySeverity.CRITICAL,
            description=("SSH client issue when connecting to a malicious or compromised server."),
        ),
    ),
    url=("https://www.arista.com/en/support/advisories-notices/security-advisory/24515-security-advisory-0147"),
    description=(
        "Multiple vulnerabilities have been discovered in OpenSSH before version 10.4, which "
        "is shipped with multiple Arista products. One vulnerability (CVE-2026-60001) affects "
        "the server-side SSH daemon (sshd). The remaining three vulnerabilities "
        "(CVE-2026-60002, CVE-2026-59995, CVE-2026-59996) affect the client-side SSH, Secure "
        "File Transfer Protocol (SFTP), and Secure Copy Protocol (SCP) utilities, respectively."
    ),
)


def _is_openssh_before_10_4(version_string: str) -> bool | None:
    """Return whether an OpenSSH package version is older than upstream 10.4."""
    match = OPENSSH_VERSION_PATTERN.fullmatch(version_string.strip())
    if match is None:
        return None
    return (int(match.group("major")), int(match.group("minor"))) < (10, 4)


def _eos_scope_result(vulnerability_id: str, version: Fact[DeviceVersion]) -> tuple[VulnerabilityResult | None, EosReleaseAssessment | None]:
    """Return an early result or affected EOS context for one SA147 vulnerability."""
    if isinstance(version, UnavailableFact):
        return ErrorResult(vulnerability_id=vulnerability_id, problems=(version,)), None
    evaluation = evaluate_version(version.value, EOS_AFFECTED_VERSION_MATRIX)
    if evaluation.affected_status is AffectedStatus.UNKNOWN:
        problem = EosVersionFact.unavailable(FactProblemKind.INVALID, version.source)
        return ErrorResult(vulnerability_id=vulnerability_id, problems=(problem,)), None
    relation = VersionRelation.AFFECTED if evaluation.affected_status is AffectedStatus.AFFECTED else VersionRelation.OUTSIDE_SCOPE
    assessment = EosReleaseAssessment(version, relation)
    if relation is VersionRelation.OUTSIDE_SCOPE:
        return NotAffectedResult(vulnerability_id=vulnerability_id, decisive=(assessment,)), None
    return None, assessment


def _assess_client_issue(  # noqa: PLR0911
    *,
    vulnerability_id: str,
    eos_version: Fact[DeviceVersion],
    package_version: Fact[ComponentSoftwareVersion],
    fixed_releases: tuple[FixedRelease, ...] = (),
    mitigation: Fact[MitigationValue] | None = None,
) -> VulnerabilityResult:
    """Assess one OpenSSH client vulnerability from normalized facts."""
    scope_result, eos_context = _eos_scope_result(vulnerability_id, eos_version)
    if scope_result is not None:
        return scope_result
    if isinstance(package_version, UnavailableFact):
        return ErrorResult(vulnerability_id=vulnerability_id, problems=(package_version,))
    affected = _is_openssh_before_10_4(package_version.value.version)
    if affected is None:
        problem = OpenSshClientVersionFact.unavailable(FactProblemKind.INVALID, package_version.source)
        return ErrorResult(vulnerability_id=vulnerability_id, problems=(problem,))
    if not affected:
        return NotAffectedResult(
            vulnerability_id=vulnerability_id,
            decisive=(ComponentVersionAssessment(package_version, VersionRelation.FIXED),),
        )
    affected_component = AffectedComponentVersion(package_version)
    affected_eos = cast("EosReleaseAssessment", eos_context)
    remediation = software_version_plan(fixed_releases, current_version=cast("EOSVersion", affected_eos.fact.value))
    if mitigation is not None:
        if isinstance(mitigation, UnavailableFact):
            return ErrorResult(vulnerability_id=vulnerability_id, problems=(mitigation,))
        if mitigation.value.state is MitigationState.EFFECTIVE:
            return MitigatedResult(
                vulnerability_id=vulnerability_id,
                context=(affected_eos,),
                mitigated_conditions=(MitigatedCondition(affected_component, (mitigation,)),),
                remediation=remediation,
            )
    return AffectedResult(
        vulnerability_id=vulnerability_id,
        context=(affected_eos,),
        conditions=(affected_component,),
        remediation=remediation,
    )


def _assess_server_issue(  # noqa: PLR0911
    *,
    vulnerability_id: str,
    eos_version: Fact[DeviceVersion],
    package_version: Fact[ComponentSoftwareVersion],
    ssh_server: Fact[FeatureValue],
) -> VulnerabilityResult:
    """Assess the OpenSSH server vulnerability from normalized facts."""
    scope_result, eos_context = _eos_scope_result(vulnerability_id, eos_version)
    if scope_result is not None:
        return scope_result
    if not isinstance(ssh_server, UnavailableFact) and ssh_server.value.state is FeatureState.DISABLED:
        return NotAffectedResult(vulnerability_id=vulnerability_id, decisive=(ssh_server,))
    if isinstance(package_version, UnavailableFact):
        return ErrorResult(vulnerability_id=vulnerability_id, problems=(package_version,))
    affected = _is_openssh_before_10_4(package_version.value.version)
    if affected is None:
        problem = OpenSshServerVersionFact.unavailable(FactProblemKind.INVALID, package_version.source)
        return ErrorResult(vulnerability_id=vulnerability_id, problems=(problem,))
    if not affected:
        return NotAffectedResult(
            vulnerability_id=vulnerability_id,
            decisive=(ComponentVersionAssessment(package_version, VersionRelation.FIXED),),
        )
    if isinstance(ssh_server, UnavailableFact):
        return ErrorResult(vulnerability_id=vulnerability_id, problems=(ssh_server,))
    affected_eos = cast("EosReleaseAssessment", eos_context)
    return AffectedResult(
        vulnerability_id=vulnerability_id,
        context=(affected_eos, ComponentVersionAssessment(package_version, VersionRelation.AFFECTED)),
        conditions=(ssh_server,),
        remediation=software_version_plan((), current_version=cast("EOSVersion", affected_eos.fact.value)),
    )


@preview_test_class
class VerifySA147(OptionalCommandsMixin, _AntaAdvisoryTest):
    """Verify the four independent OpenSSH issues in Security Advisory 147.

    Expected Results
    ----------------
    * Success: The test will pass if every vulnerability is not affected.
    * Failure: The test will fail if any vulnerability is affected.
    * Error: The test will error if evidence required for a vulnerability is invalid.

    Examples
    --------
    ```yaml
    anta.tests.advisories.sa_147:
      - VerifySA147:
    ```
    """

    advisory: ClassVar[_AdvisoryMetadata] = ADVISORY
    required_facts: ClassVar[tuple[type[FactDefinition[Any]], ...]] = (
        EosVersionFact,
        OpenSshClientVersionFact,
        OpenSshServerVersionFact,
        SshServerFact,
        StrictHostKeyCheckingFact,
    )
    description = "Verify whether the device is impacted by SA 0147."
    _atomic_support = True

    @_AntaAdvisoryTest.anta_test
    def test(self) -> None:
        """Assess and project each OpenSSH vulnerability independently."""
        eos_version = self.fact(EosVersionFact)
        client_version = self.fact(OpenSshClientVersionFact)
        server_version = self.fact(OpenSshServerVersionFact)
        ssh_server = self.fact(SshServerFact)
        strict_host_key_checking = self.fact(StrictHostKeyCheckingFact)
        vulnerability_ids = tuple(vulnerability.id for vulnerability in ADVISORY.vulnerabilities)
        assessments = (
            _assess_client_issue(
                vulnerability_id=vulnerability_ids[0],
                eos_version=eos_version,
                package_version=client_version,
            ),
            _assess_client_issue(
                vulnerability_id=vulnerability_ids[1],
                eos_version=eos_version,
                package_version=client_version,
            ),
            _assess_server_issue(
                vulnerability_id=vulnerability_ids[2],
                eos_version=eos_version,
                package_version=server_version,
                ssh_server=ssh_server,
            ),
            _assess_client_issue(
                vulnerability_id=vulnerability_ids[3],
                eos_version=eos_version,
                package_version=client_version,
                fixed_releases=CVE_60002_FIXED_RELEASES,
                mitigation=strict_host_key_checking,
            ),
        )
        for vulnerability, finding in zip(ADVISORY.vulnerabilities, assessments, strict=True):
            atomic_result = self.result.add(
                f"Verify {vulnerability.id}.",
                vulnerability_ids=(vulnerability.id,),
            )
            project_vulnerability_result(atomic_result, finding)
