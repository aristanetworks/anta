# Copyright (c) 2026 Arista Networks, Inc.
# Use of this source code is governed by the Apache License 2.0
# that can be found in the LICENSE file.
# pylint: disable=duplicate-code
"""ANTA test for Arista Security Advisory 117."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, ClassVar, cast

from anta._advisory.base import _AntaAdvisoryTest
from anta._advisory.eos_versions import AffectedStatus, VersionRule, evaluate_version
from anta._advisory.facts.eos import EosVersionFact
from anta._advisory.facts.management import GnmiAccountingFact, GnmiTransportFact, RiskyOpenConfigTraceFact
from anta._advisory.facts.models import ConfigurationState, ConfigurationValue, Fact, FactDefinition, FactProblemKind, FeatureState, FeatureValue, UnavailableFact
from anta._advisory.findings.models import (
    EosReleaseAssessment,
    ErrorResult,
    InconclusiveResult,
    NotAffectedResult,
    Unobservable,
    UnobservableKind,
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

AFFECTED_VERSION_MATRIX: tuple[VersionRule, ...] = (
    VersionRule(major=4, minor=30, patch_gte=1, patch_lt=10),
    VersionRule(major=4, minor=31, patch_lt=7),
    VersionRule(major=4, minor=32, patch_lt=5),
    VersionRule(major=4, minor=33, patch_lt=1),
    VersionRule(major=4, minor=33, patch_eq=1, exclude_suffixes=("FX-wbb",)),
)

FIXED_RELEASES = (
    FixedRelease(EOSVersion(4, 30, 10, suffix="M")),
    FixedRelease(EOSVersion(4, 31, 7, suffix="M")),
    FixedRelease(EOSVersion(4, 32, 5, suffix="M")),
    FixedRelease(EOSVersion(4, 33, 2, suffix="F")),
)
ADVISORY = _AdvisoryMetadata(
    sa_number="0117",
    title="Security Advisory 0117",
    vulnerabilities=(
        _AdvisoryVulnerability(
            id="CVE-2025-0936",
            severity=_AdvisoryVulnerabilitySeverity.MEDIUM,
            description=("gNOI TransferToRemote credential exposure through OpenConfig accounting or tracing."),
        ),
    ),
    url=("https://www.arista.com/en/support/advisories-notices/security-advisory/21394-security-advisory-0117"),
    description=(
        "On affected platforms running Arista EOS with a gNMI transport enabled, running the "
        "gNOI File TransferToRemote RPC with credentials for a remote server may cause these "
        "remote-server credentials to be logged or accounted on the local EOS device or "
        "possibly on other remote accounting servers (i.e. TACACS, RADIUS, etc)."
    ),
)


# pylint: disable-next=too-many-return-statements
def _assess_sa117(  # noqa: PLR0911
    version: Fact[DeviceVersion],
    gnmi: Fact[FeatureValue],
    accounting: Fact[FeatureValue],
    trace: Fact[ConfigurationValue],
) -> VulnerabilityResult:
    """Assess CVE-2025-0936 from normalized facts."""
    vulnerability_id = ADVISORY.vulnerabilities[0].id
    if isinstance(version, UnavailableFact):
        return ErrorResult(vulnerability_id=vulnerability_id, problems=(version,))
    version_evaluation = evaluate_version(version.value, AFFECTED_VERSION_MATRIX)
    if version_evaluation.affected_status is AffectedStatus.UNKNOWN:
        return ErrorResult(vulnerability_id=vulnerability_id, problems=(EosVersionFact.unavailable(FactProblemKind.INVALID, version.source),))
    if version_evaluation.affected_status is AffectedStatus.NOT_AFFECTED:
        return NotAffectedResult(
            vulnerability_id=vulnerability_id,
            decisive=(EosReleaseAssessment(version, VersionRelation.OUTSIDE_SCOPE),),
        )

    if isinstance(gnmi, UnavailableFact):
        return ErrorResult(vulnerability_id=vulnerability_id, problems=(gnmi,))
    if gnmi.value.state is not FeatureState.ENABLED:
        return NotAffectedResult(vulnerability_id=vulnerability_id, decisive=(gnmi,))

    release = EosReleaseAssessment(version, VersionRelation.AFFECTED)
    remediation = software_version_plan(FIXED_RELEASES, current_version=cast("EOSVersion", version.value))
    if not isinstance(accounting, UnavailableFact) and accounting.value.state is FeatureState.ENABLED:
        # We are not able to resolve the gNOI File and effective gNSI Authz controls
        # for possible mitigation so we say inconclusive.
        return InconclusiveResult(
            vulnerability_id=vulnerability_id,
            indications=(release, gnmi, accounting),
            unresolved=(
                Unobservable(UnobservableKind.DEVICE_STATE_NOT_EXPOSED, "gNOI File service state"),
                Unobservable(UnobservableKind.DEVICE_STATE_NOT_EXPOSED, "effective gNSI Authz control"),
            ),
            remediation=remediation,
        )
    if not isinstance(trace, UnavailableFact) and trace.value.state is ConfigurationState.CONFIGURED:
        # We are not able to resolve the gNOI File and effective gNSI Authz controls
        # for possible mitigation so we say inconclusive.
        return InconclusiveResult(
            vulnerability_id=vulnerability_id,
            indications=(release, gnmi, trace),
            unresolved=(
                Unobservable(UnobservableKind.DEVICE_STATE_NOT_EXPOSED, "gNOI File service state"),
                Unobservable(UnobservableKind.DEVICE_STATE_NOT_EXPOSED, "effective gNSI Authz control"),
            ),
            remediation=remediation,
        )
    if isinstance(accounting, UnavailableFact):
        return ErrorResult(vulnerability_id=vulnerability_id, problems=(accounting,))
    if isinstance(trace, UnavailableFact):
        return ErrorResult(vulnerability_id=vulnerability_id, problems=(trace,))
    return NotAffectedResult(vulnerability_id=vulnerability_id, decisive=(accounting, trace))


@preview_test_class
class VerifySA117(OptionalCommandsMixin, _AntaAdvisoryTest):
    """Assess SA117 credential exposure through OpenConfig accounting or tracing.

    Notes
    -----
    Exposure signals remain inconclusive because disabling the gNOI File service and an
    effective gNSI Authz policy that blocks TransferToRemote cannot currently be evaluated
    with trusted narrow EOS evidence.

    Expected Results
    ----------------
    * Success: The test will pass if the EOS version or configuration is not affected.
    * Inconclusive: The test is inconclusive if exposure signals exist but required control evidence is unavailable.
    * Error: The test will error if required EOS version or configuration evidence is invalid.

    Examples
    --------
    ```yaml
    anta.tests.advisories.sa_117:
      - VerifySA117:
    ```
    """

    advisory: ClassVar[_AdvisoryMetadata] = ADVISORY
    required_facts: ClassVar[tuple[type[FactDefinition[Any]], ...]] = (
        EosVersionFact,
        GnmiTransportFact,
        GnmiAccountingFact,
        RiskyOpenConfigTraceFact,
    )
    description = "Verify whether the device is impacted by SA 0117."
    _atomic_support = True

    @_AntaAdvisoryTest.anta_test
    def test(self) -> None:
        """Assess and project the advisory vulnerability."""
        finding = _assess_sa117(
            self.fact(EosVersionFact),
            self.fact(GnmiTransportFact),
            self.fact(GnmiAccountingFact),
            self.fact(RiskyOpenConfigTraceFact),
        )
        vulnerability = ADVISORY.vulnerabilities[0]
        atomic_result = self.result.add(
            f"Verify {vulnerability.id}.",
            vulnerability_ids=(vulnerability.id,),
        )
        project_vulnerability_result(atomic_result, finding)
