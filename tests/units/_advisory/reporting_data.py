# Copyright (c) 2026 Arista Networks, Inc.
# Use of this source code is governed by the Apache License 2.0
# that can be found in the LICENSE file.
"""Shared realistic data for security advisory reporter tests.

Regenerate the checked-in reports with ``uv run python -m tests.units._advisory.generate_report_fixtures``.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Literal, TypeAlias, cast

from typing_extensions import assert_never

from anta._advisory.facts.eos import EosVersionFact
from anta._advisory.facts.models import Fact, FactDefinition, FactProblemKind, FactSource, FactSourceKind, MitigationState, MitigationValue
from anta._advisory.findings.models import (
    AffectedEosRelease,
    AffectedResult,
    EosReleaseAssessment,
    ErrorResult,
    InconclusiveResult,
    MitigatedCondition,
    MitigatedResult,
    NotAffectedResult,
    Unobservable,
    UnobservableKind,
    VersionRelation,
    VulnerabilityResult,
)
from anta._advisory.findings.projection import _get_anta_status
from anta._advisory.remediation import OperationalAction, RemediationPlan, software_version_plan
from anta._advisory.results import _AdvisoryTestResult
from anta._eos.version import EOSVersion
from anta.result_manager import ResultManager
from anta.result_manager.models import AntaTestStatus
from anta.tests.advisories.sa_117 import VerifySA117
from anta.tests.advisories.sa_146 import EOS_FIXED_RELEASES, VerifySA146
from anta.tests.advisories.sa_147 import CVE_60002_FIXED_RELEASES, VerifySA147

if TYPE_CHECKING:
    from collections.abc import Iterable

    from anta._advisory.models import _AdvisoryMetadata
    from anta.device import AntaDevice
    from anta.models import AntaCommand

SA117_ADVISORY = cast("_AdvisoryMetadata", vars(VerifySA117)["advisory"])
SA146_ADVISORY = cast("_AdvisoryMetadata", vars(VerifySA146)["advisory"])
SA147_ADVISORY = cast("_AdvisoryMetadata", vars(VerifySA147)["advisory"])
_PUBLISHED_TEST_METADATA = {
    SA117_ADVISORY.sa_number: (VerifySA117.__name__, VerifySA117.description),
    SA146_ADVISORY.sa_number: (VerifySA146.__name__, VerifySA146.description),
    SA147_ADVISORY.sa_number: (VerifySA147.__name__, VerifySA147.description),
}
_SA147_CLIENT_VULNERABILITY_IDS = ("CVE-2026-59995", "CVE-2026-59996", "CVE-2026-60002")
_SA147_SERVER_VULNERABILITY_ID = "CVE-2026-60001"
_SA146_SPINE1_EOS = EOSVersion(4, 35, 5, suffix="M")
_SA147_LEAF1_EOS = EOSVersion(4, 32, 4, suffix="M")
_SA147_LEAF3_EOS = EOSVersion(4, 32, 1, suffix="M")
_SA147_SPINE2_EOS = EOSVersion(4, 31, 6, suffix="M")
_SA147_LEAF2_DC2_EOS = EOSVersion(4, 30, 10, suffix="M")
_SOURCE = FactSource("synthetic reporter evidence", FactSourceKind.DEVICE_METADATA)
_FindingKind: TypeAlias = Literal["not affected", "mitigated", "inconclusive", "affected", "error"]


class _SyntheticMitigationFact(FactDefinition[MitigationValue]):
    """Synthetic mitigation identity used to build valid reporter findings."""

    key = "mitigation.synthetic"
    label = "Synthetic mitigation"

    @classmethod
    def derive(cls, device: AntaDevice, commands: tuple[AntaCommand, ...] = ()) -> Fact[MitigationValue]:
        """Reject derivation because reporter data supplies normalized evidence."""
        _ = cls, device, commands
        raise NotImplementedError


def _build_finding(vulnerability_id: str, kind: _FindingKind, remediation: RemediationPlan | None) -> VulnerabilityResult:
    """Build a valid structured finding matching synthetic reporter semantics."""
    eos = EosVersionFact.available(EOSVersion(4, 32, 1, suffix="F"), _SOURCE)
    plan = remediation or RemediationPlan(OperationalAction("Apply the advisory remediation and rerun the test."))
    if kind == "mitigated":
        mitigation = _SyntheticMitigationFact.available(MitigationValue(MitigationState.EFFECTIVE), _SOURCE)
        return MitigatedResult(
            vulnerability_id=vulnerability_id,
            mitigated_conditions=(MitigatedCondition(AffectedEosRelease(eos), (mitigation,)),),
            remediation=plan,
        )
    if kind == "not affected":
        return NotAffectedResult(vulnerability_id=vulnerability_id, decisive=(EosReleaseAssessment(eos, VersionRelation.OUTSIDE_SCOPE),))
    if kind == "inconclusive":
        return InconclusiveResult(
            vulnerability_id=vulnerability_id,
            indications=(EosReleaseAssessment(eos, VersionRelation.AFFECTED),),
            unresolved=(Unobservable(UnobservableKind.OPERATOR_ACTION, "synthetic reporter condition"),),
            remediation=plan,
        )
    if kind == "affected":
        return AffectedResult(vulnerability_id=vulnerability_id, conditions=(AffectedEosRelease(eos),), remediation=plan)
    if kind == "error":
        problem = EosVersionFact.unavailable(FactProblemKind.MISSING, _SOURCE)
        return ErrorResult(vulnerability_id=vulnerability_id, problems=(problem,))
    return assert_never(kind)


def build_security_advisory_result(
    name: str,
    status: AntaTestStatus,
    message: str,
    advisory: _AdvisoryMetadata,
    *,
    with_atomics: bool = True,
    finding_kind: _FindingKind | None = None,
) -> _AdvisoryTestResult:
    """Create a security advisory result with explicitly requested structured findings."""
    test_name, description = _PUBLISHED_TEST_METADATA.get(
        advisory.sa_number,
        (f"VerifySA{int(advisory.sa_number)}", f"Verify that the device is not exposed to Arista Security Advisory {advisory.sa_number}."),
    )
    result = _AdvisoryTestResult(
        name=name,
        test=test_name,
        categories=["advisories"],
        description=description,
        advisory=advisory,
    )
    if finding_kind is None and status in {AntaTestStatus.ERROR, AntaTestStatus.SKIPPED}:
        result._set_status(status, message)
        return result
    if not with_atomics:
        result.result = status
        result.messages.append(message)
        return result
    result.messages.append(message)
    if finding_kind is None:
        if status in {AntaTestStatus.SUCCESS, AntaTestStatus.FAILURE}:
            msg = "Evaluated reporter fixtures must declare their structured finding kind"
            raise ValueError(msg)
        return result
    for vulnerability in advisory.vulnerabilities:
        _add_vulnerability_atomic(result, vulnerability.id, status, message, finding_kind=finding_kind)
    return result


def _sa147_plan(eos_version: EOSVersion, *, vulnerability_id: str) -> RemediationPlan:
    """Return the production SA147 software-version plan for one vulnerability."""
    fixed_releases = CVE_60002_FIXED_RELEASES if vulnerability_id == "CVE-2026-60002" else ()
    return software_version_plan(fixed_releases, current_version=eos_version)


def _add_vulnerability_atomic(
    result: _AdvisoryTestResult,
    vulnerability_id: str,
    status: AntaTestStatus,
    message: str,
    *,
    remediation: RemediationPlan | None = None,
    finding_kind: _FindingKind | None = None,
) -> None:
    """Add one vulnerability-scoped atomic result."""
    if status is AntaTestStatus.SKIPPED:
        result.add(f"Verify {vulnerability_id}.", status, [message], vulnerability_id=vulnerability_id)
        return
    atomic = result.add(
        f"Verify {vulnerability_id}.",
        vulnerability_id=vulnerability_id,
    )
    default_finding_kinds: dict[AntaTestStatus, _FindingKind] = {
        AntaTestStatus.SUCCESS: "not affected",
        AntaTestStatus.FAILURE: "affected",
        AntaTestStatus.ERROR: "error",
    }
    kind = default_finding_kinds[status] if finding_kind is None else finding_kind
    finding = _build_finding(vulnerability_id, kind, remediation)
    mapped_status = _get_anta_status(finding)
    if status is not mapped_status:
        msg = f"Finding kind {kind!r} maps to {mapped_status}, not {status}"
        raise ValueError(msg)
    atomic.set_finding(finding)
    atomic._set_status(mapped_status, message)


def _add_sa147_affected_findings(
    result: _AdvisoryTestResult,
    eos_version: EOSVersion,
    *,
    client_package: str,
    server_package: str,
) -> None:
    """Add per-CVE affected findings with the remediations VerifySA147 would attach."""
    client_message = f"The device is affected because EOS version '{eos_version}' is affected and openssh-clients '{client_package}' is affected."
    server_message = (
        f"The device is affected because EOS version '{eos_version}' is affected, openssh-server '{server_package}' is affected, and the SSH feature is enabled."
    )
    for vulnerability_id in _SA147_CLIENT_VULNERABILITY_IDS:
        _add_vulnerability_atomic(
            result,
            vulnerability_id,
            AntaTestStatus.FAILURE,
            client_message,
            remediation=_sa147_plan(eos_version, vulnerability_id=vulnerability_id),
        )
    _add_vulnerability_atomic(
        result,
        _SA147_SERVER_VULNERABILITY_ID,
        AntaTestStatus.FAILURE,
        server_message,
        remediation=_sa147_plan(eos_version, vulnerability_id=_SA147_SERVER_VULNERABILITY_ID),
    )


def _add_findings(
    manager: ResultManager,
    advisory: _AdvisoryMetadata,
    findings: Iterable[tuple[str, AntaTestStatus, str, _FindingKind | None]],
) -> list[_AdvisoryTestResult]:
    """Add realistic per-device findings for one advisory."""
    results = []
    for device, status, message, finding_kind in findings:
        result = build_security_advisory_result(device, status, message, advisory, with_atomics=finding_kind is not None, finding_kind=finding_kind)
        manager.add(result)
        results.append(result)
    return results


def build_security_advisory_result_manager() -> ResultManager:
    """Build the shared three-advisory, eight-device reporter dataset."""
    manager = ResultManager()
    _add_findings(
        manager,
        SA117_ADVISORY,
        [
            (
                "DC1-LEAF1",
                AntaTestStatus.FAILURE,
                (
                    "The assessment is inconclusive and the device may be affected because EOS version '4.32.4M' has an enabled gNMI transport "
                    "with accounting enabled, but the gNOI File and effective gNSI Authz controls cannot be determined."
                ),
                "inconclusive",
            ),
            ("DC1-LEAF2", AntaTestStatus.SUCCESS, "EOS 4.32.5M is not affected by this advisory.", "not affected"),
            ("DC1-LEAF3", AntaTestStatus.ERROR, "The EOS version could not be determined from the available command output.", "error"),
            ("DC1-LEAF4", AntaTestStatus.SKIPPED, "Device was unreachable during test execution.", None),
            ("DC1-SPINE1", AntaTestStatus.SUCCESS, "EOS 4.33.2F is not affected by this advisory.", "not affected"),
            (
                "DC1-SPINE2",
                AntaTestStatus.FAILURE,
                (
                    "The assessment is inconclusive and the device may be affected because EOS version '4.31.6M' has an enabled gNMI transport and OpenConfig "
                    "tracing includes a selector identified by the advisory, but the gNOI File and effective gNSI Authz controls cannot be determined."
                ),
                "inconclusive",
            ),
            ("DC2-LEAF1", AntaTestStatus.SUCCESS, "The device configuration is not affected by this advisory.", "not affected"),
            ("DC2-LEAF2", AntaTestStatus.SUCCESS, "EOS 4.30.10M is not affected by this advisory.", "not affected"),
        ],
    )
    sa147_results = _add_findings(
        manager,
        SA147_ADVISORY,
        [
            (
                "DC1-LEAF1",
                AntaTestStatus.FAILURE,
                (
                    f"The device is affected because EOS version '{_SA147_LEAF1_EOS}' is affected, openssh-server '9.9p1' is affected, "
                    "and the SSH feature is enabled."
                ),
                None,
            ),
            ("DC1-LEAF2", AntaTestStatus.SUCCESS, "The device is not affected because its EOS version is outside the published affected range.", "not affected"),
            (
                "DC1-LEAF3",
                AntaTestStatus.FAILURE,
                (
                    f"The device is affected because EOS version '{_SA147_LEAF3_EOS}' is affected, openssh-server '9.8p1' is affected, "
                    "and the SSH feature is enabled."
                ),
                None,
            ),
            ("DC1-LEAF4", AntaTestStatus.SKIPPED, "Device was unreachable during test execution.", None),
            ("DC1-SPINE1", AntaTestStatus.SUCCESS, "The device is not affected because openssh-clients and openssh-server '10.4p1' are fixed.", "not affected"),
            (
                "DC1-SPINE2",
                AntaTestStatus.FAILURE,
                (
                    f"The device is affected because EOS version '{_SA147_SPINE2_EOS}' is affected, openssh-server '9.9p2' is affected, "
                    "and the SSH feature is enabled."
                ),
                None,
            ),
            ("DC2-LEAF1", AntaTestStatus.ERROR, "The openssh-clients package version could not be determined from 'show version detail'.", "error"),
            (
                "DC2-LEAF2",
                AntaTestStatus.FAILURE,
                (
                    f"The device is affected because EOS version '{_SA147_LEAF2_DC2_EOS}' is affected, openssh-server '9.7p1' is affected, "
                    "and the SSH feature is enabled."
                ),
                None,
            ),
        ],
    )
    _add_vulnerability_atomic(
        sa147_results[0],
        "CVE-2026-59995",
        AntaTestStatus.FAILURE,
        (
            f"The assessment is inconclusive and the device may be affected because EOS version '{_SA147_LEAF1_EOS}' is affected, "
            "openssh-clients '9.9p1' is affected, but operator-initiated SFTP use with an untrusted server cannot be determined."
        ),
        remediation=_sa147_plan(_SA147_LEAF1_EOS, vulnerability_id="CVE-2026-59995"),
        finding_kind="inconclusive",
    )
    _add_vulnerability_atomic(
        sa147_results[0],
        "CVE-2026-59996",
        AntaTestStatus.FAILURE,
        (
            f"The assessment is inconclusive and the device may be affected because EOS version '{_SA147_LEAF1_EOS}' is affected, "
            "openssh-clients '9.9p1' is affected, but operator-initiated SCP remote-to-remote use with an untrusted server cannot be determined."
        ),
        remediation=_sa147_plan(_SA147_LEAF1_EOS, vulnerability_id="CVE-2026-59996"),
        finding_kind="inconclusive",
    )
    _add_vulnerability_atomic(
        sa147_results[0],
        "CVE-2026-60001",
        AntaTestStatus.FAILURE,
        (f"The device is affected because EOS version '{_SA147_LEAF1_EOS}' is affected, openssh-server '9.9p1' is affected, and the SSH feature is enabled."),
        remediation=_sa147_plan(_SA147_LEAF1_EOS, vulnerability_id="CVE-2026-60001"),
    )
    _add_vulnerability_atomic(
        sa147_results[0],
        "CVE-2026-60002",
        AntaTestStatus.SUCCESS,
        (f"The device is affected but mitigated because EOS version '{_SA147_LEAF1_EOS}' is affected and openssh-clients '9.9p1' uses strict host-key checking."),
        remediation=_sa147_plan(_SA147_LEAF1_EOS, vulnerability_id="CVE-2026-60002"),
        finding_kind="mitigated",
    )
    _add_sa147_affected_findings(sa147_results[2], _SA147_LEAF3_EOS, client_package="9.8p1", server_package="9.8p1")
    _add_sa147_affected_findings(sa147_results[5], _SA147_SPINE2_EOS, client_package="9.9p2", server_package="9.9p2")
    _add_sa147_affected_findings(sa147_results[7], _SA147_LEAF2_DC2_EOS, client_package="9.7p1", server_package="9.7p1")
    sa146_results = _add_findings(
        manager,
        SA146_ADVISORY,
        [
            ("DC1-LEAF1", AntaTestStatus.SUCCESS, "The device is not affected because no enabled gRPC server is on an affected software version.", "not affected"),
            ("DC1-LEAF2", AntaTestStatus.SUCCESS, "The device is not affected because no enabled gRPC server is on an affected software version.", "not affected"),
            ("DC1-LEAF3", AntaTestStatus.SUCCESS, "The device is not affected because no enabled gRPC server is on an affected software version.", "not affected"),
            ("DC1-LEAF4", AntaTestStatus.SKIPPED, "Device was unreachable during test execution.", None),
            (
                "DC1-SPINE1",
                AntaTestStatus.FAILURE,
                "The device is affected because vulnerable gRPC server path(s) are enabled without complete mTLS: gNMI.",
                None,
            ),
            ("DC1-SPINE2", AntaTestStatus.SUCCESS, "The device is not affected because no enabled gRPC server is on an affected software version.", "not affected"),
            ("DC2-LEAF1", AntaTestStatus.ERROR, "The following required evidence is unavailable or invalid: gRIBI enabled state.", "error"),
            ("DC2-LEAF2", AntaTestStatus.SUCCESS, "The device is not affected because no enabled gRPC server is on an affected software version.", "not affected"),
        ],
    )
    _add_vulnerability_atomic(
        sa146_results[4],
        "GHSA-hrxh-6v49-42gf",
        AntaTestStatus.FAILURE,
        "The device is affected because vulnerable gRPC server path(s) are enabled without complete mTLS: gNMI.",
        remediation=software_version_plan(EOS_FIXED_RELEASES, current_version=_SA146_SPINE1_EOS),
    )
    return manager


def build_security_advisory_md_result_manager() -> ResultManager:
    """Build the shared reporter dataset with per-vulnerability remediations for Markdown and CSV."""
    return build_security_advisory_result_manager()
