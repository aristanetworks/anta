# Copyright (c) 2026 Arista Networks, Inc.
# Use of this source code is governed by the Apache License 2.0
# that can be found in the LICENSE file.
# pylint: disable=duplicate-code
"""ANTA test for Arista Security Advisory 117."""

from __future__ import annotations

from datetime import date
from typing import ClassVar

from anta._advisory.base import _PREVIEW_WARNING, _AntaAdvisoryTest
from anta._advisory.eos_versions import VersionRule
from anta._advisory.facts.eos import EosVersionFact
from anta._advisory.facts.management import GnmiTransportFact
from anta._advisory.facts.models import Fact, FactsBase, FeatureState, UnavailableFact, fact_field, facts_dataclass
from anta._advisory.findings.assessment import assess_eos_scope
from anta._advisory.findings.models import (
    EosReleaseAssessment,
    ErrorResult,
    InconclusiveResult,
    NotAffectedResult,
    Unobservable,
    UnobservableKind,
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
    last_updated=date(2025, 5, 20),
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


def _assess_sa117(version: Fact[EosVersionFact], gnmi: Fact[GnmiTransportFact]) -> VulnerabilityResult:
    """Assess CVE-2025-0936 from normalized facts."""
    vulnerability_id = ADVISORY.vulnerabilities[0].id
    release = assess_eos_scope(vulnerability_id, version, AFFECTED_VERSION_MATRIX)
    if not isinstance(release, EosReleaseAssessment):
        return release

    if isinstance(gnmi, UnavailableFact):
        return ErrorResult(vulnerability_id=vulnerability_id, problems=(gnmi,))
    if gnmi.value.state is not FeatureState.ENABLED:
        return NotAffectedResult(vulnerability_id=vulnerability_id, decisive=(gnmi,))

    # We are not able to resolve the gNOI File and effective gNSI Authz controls
    # for possible mitigation so we say inconclusive.
    return InconclusiveResult(
        vulnerability_id=vulnerability_id,
        indications=(release, gnmi),
        unresolved=(
            Unobservable(UnobservableKind.DEVICE_STATE_NOT_EXPOSED, "gNOI File service state"),
            Unobservable(UnobservableKind.DEVICE_STATE_NOT_EXPOSED, "effective gNSI Authz control"),
        ),
        remediation=software_version_plan(FIXED_RELEASES, current_version=release.fact.value),
    )


@preview_test_class(warning_message=_PREVIEW_WARNING)
class SA117(OptionalCommandsMixin, _AntaAdvisoryTest):
    """Verify whether the device is impacted by Security Advisory 0117.

    Expected Results
    ----------------
    * Not Affected: EOS is outside scope or no gNMI transport is enabled.
    * Inconclusive: An affected EOS release has gNMI enabled, but the gNOI File service and effective gNSI Authz controls cannot be
      evaluated.
    * Error: Required EOS or gNMI state cannot be determined.

    Notes
    -----
    Exposure remains inconclusive because disabling the gNOI File service and an
    effective gNSI Authz policy that blocks TransferToRemote cannot currently be evaluated
    with trusted narrow EOS evidence.

    The advisory requires gNMI accounting or an advisory-identified OpenConfig trace selector. This test does not
    use OpenConfig trace state: an operator can enable the trace at any time with `start trace`, which leaves no
    running-config record and disappears from `show trace OpenConfig` once the timer expires, so trace state cannot
    rule out exposure. Because the trace branch cannot be excluded, accounting state cannot change the result either.

    Examples
    --------
    ```yaml
    anta.tests.advisories:
      - SA117:
    ```
    """

    @facts_dataclass
    class Facts(FactsBase):
        """Collected facts required to assess the advisory."""

        version: Fact[EosVersionFact] = fact_field(EosVersionFact)
        gnmi: Fact[GnmiTransportFact] = fact_field(GnmiTransportFact)

    advisory: ClassVar[_AdvisoryMetadata] = ADVISORY
    description = "Verify whether the device is impacted by Security Advisory 0117."
    _atomic_support = True

    @_AntaAdvisoryTest.anta_test
    def test(self) -> None:
        """Assess and project the advisory vulnerability."""
        facts = self.Facts.collect(self)
        finding = _assess_sa117(facts.version, facts.gnmi)
        vulnerability = ADVISORY.vulnerabilities[0]
        atomic_result = self.result.add(
            f"Verify {vulnerability.id}.",
            vulnerability_ids=(vulnerability.id,),
        )
        project_vulnerability_result(atomic_result, finding)
