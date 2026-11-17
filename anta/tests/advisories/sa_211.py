# Copyright (c) 2026 Arista Networks, Inc.
# Use of this source code is governed by the Apache License 2.0
# that can be found in the LICENSE file.
"""ANTA test for Arista Security Advisory 211."""

from __future__ import annotations

from datetime import date
from typing import ClassVar

from anta._advisory.base import _PREVIEW_WARNING, _AntaAdvisoryTest
from anta._advisory.eos_versions import VersionRule
from anta._advisory.facts.bgp_link_state import BgpLinkStateDpsConsumerFact
from anta._advisory.facts.eos import EosVersionFact
from anta._advisory.facts.models import ConfigurationState, Fact, FactsBase, UnavailableFact, fact_field, facts_dataclass
from anta._advisory.findings.assessment import assess_eos_scope
from anta._advisory.findings.models import AffectedResult, ErrorResult, NotAffectedResult, VulnerabilityResult
from anta._advisory.findings.projection import project_vulnerability_result
from anta._advisory.models import _AdvisoryMetadata, _AdvisoryVulnerability, _AdvisoryVulnerabilitySeverity
from anta._advisory.optional_commands import OptionalCommandsMixin
from anta._advisory.remediation import FixedRelease, software_version_plan
from anta._eos.version import EOSVersion
from anta.decorators import preview_test_class

AFFECTED_VERSION_MATRIX: tuple[VersionRule, ...] = (
    VersionRule(major=4, minor_lte=32),
    VersionRule(major=4, minor=33, patch_lte=10),
    VersionRule(major=4, minor=34, patch_lte=8),
    VersionRule(major=4, minor=35, patch_lte=6),
    VersionRule(major=4, minor=36, patch_lte=2),
)
FIXED_RELEASES = (
    FixedRelease(EOSVersion(4, 33, 11, suffix="M")),
    FixedRelease(EOSVersion(4, 34, 9, suffix="M")),
    FixedRelease(EOSVersion(4, 35, 7, suffix="M")),
    FixedRelease(EOSVersion(4, 36, 3, suffix="M")),
    FixedRelease(EOSVersion(4, 37, 0, suffix="F")),
)
ADVISORY = _AdvisoryMetadata(
    sa_number="0211",
    last_updated=date(2026, 11, 10),
    title="Security Advisory 0211",
    vulnerabilities=(
        _AdvisoryVulnerability(
            id="CVE-2026-120978",
            severity=_AdvisoryVulnerabilitySeverity.MEDIUM,
            description="A crafted BGP-LS message may restart the BGP agent when the DPS consumer role and Link-State peering are configured.",
        ),
    ),
    url="https://www.arista.com/en/support/advisories-notices/security-advisory/25033-security-advisory-0211",
    description="A crafted BGP-LS message may restart the BGP agent when the DPS consumer role and Link-State peering are configured.",
)
VULNERABILITY_ID = ADVISORY.vulnerabilities[0].id


def _assess_sa211(version: Fact[EosVersionFact], exposure: Fact[BgpLinkStateDpsConsumerFact]) -> VulnerabilityResult:
    """Assess persistent BGP-LS DPS consumer peering exposure on affected software."""
    if not isinstance(exposure, UnavailableFact) and exposure.value.state is ConfigurationState.NOT_CONFIGURED:
        return NotAffectedResult(vulnerability_id=VULNERABILITY_ID, decisive=(exposure,))
    eos_scope = assess_eos_scope(VULNERABILITY_ID, version, AFFECTED_VERSION_MATRIX)
    if isinstance(eos_scope, NotAffectedResult):
        return eos_scope
    problems = (() if not isinstance(eos_scope, ErrorResult) else eos_scope.problems) + (() if not isinstance(exposure, UnavailableFact) else (exposure,))
    if isinstance(eos_scope, ErrorResult) or isinstance(exposure, UnavailableFact):
        return ErrorResult(vulnerability_id=VULNERABILITY_ID, problems=problems)
    return AffectedResult(
        vulnerability_id=VULNERABILITY_ID,
        context=(eos_scope,),
        conditions=(exposure,),
        remediation=software_version_plan(FIXED_RELEASES, current_version=eos_scope.fact.value),
    )


@preview_test_class(warning_message=_PREVIEW_WARNING)
class SA211(OptionalCommandsMixin, _AntaAdvisoryTest):
    """Verify whether the device is impacted by Security Advisory 0211.

    Expected Results
    ----------------
    * Not Affected: EOS is outside scope, or configured Link-State peering with the DPS consumer role is absent.
    * Affected: An affected EOS release has persistent Link-State activation and the DPS consumer role in the same BGP instance and VRF.
    * Error: Required software, configured peering, processing role, or scope identity evidence is unavailable or inconsistent.

    Notes
    -----
    Persistent Link-State activation remains exposure while sessions are idle, down, or disconnected. Activated unused peer groups
    and dynamic listeners without instantiated peers are conservatively included. Confirmed persistent administrative shutdown of
    the BGP instance, VRF, Link-State address family, or every activated neighbor/group establishes absence of exposure.
    Session establishment, negotiated capabilities, route counts, and observed attack traffic do not establish configured absence.
    Pathfinder and transport authentication are not additional prerequisites for this assessment.

    Link-State activation and the DPS consumer role are correlated by configured BGP instance and VRF. Numeric and asdot local-AS
    forms are compared by their ASN value; missing, malformed, or mismatched instance evidence produces Error. Operational router
    IDs, runtime peer inventories, and remote peer ASNs are not required. A consumer role in one instance or VRF is not combined with
    activation from another. The processing-role command uses structured role and protocol values; other consumer
    protocols and a propagator-only role do not satisfy the DPS consumer requirement. Valid empty role lists or an empty Link-State
    family object establish that the role is absent, while missing or malformed required role evidence produces Error.

    Persistent BGP configuration supplies the activation and administrative-state evidence. Absence of administratively enabled
    Link-State activation establishes Not Affected independently of failed role collection. An activated scope missing from structured role output,
    or an explicit configured consumer contradicted by that output, produces Error. The test does not collect a runtime peer summary.

    A fixed release or decisive feature absence independently establishes Not Affected even if unrelated inputs are unavailable.
    Otherwise all required unavailable facts are retained. All EOS platforms are in scope without a platform allowlist. EOS 4.32
    and earlier EOS 4 trains remain in software scope without a named fix; subsequent trains use their named fixed release boundaries.

    No complete configuration mitigation is available. Established exposure is Affected with fixed software as remediation.
    The test assesses configured exposure and does not determine whether exploitation has occurred.

    Examples
    --------
    ```yaml
    anta.tests.advisories:
      - SA211:
    ```
    """

    @facts_dataclass
    class Facts(FactsBase):
        """Collected software and persistent configuration evidence."""

        version: Fact[EosVersionFact] = fact_field(EosVersionFact)
        exposure: Fact[BgpLinkStateDpsConsumerFact] = fact_field(BgpLinkStateDpsConsumerFact)

    advisory: ClassVar[_AdvisoryMetadata] = ADVISORY
    description = "Verify whether the device is impacted by Security Advisory 0211."
    _atomic_support = True

    @_AntaAdvisoryTest.anta_test
    def test(self) -> None:
        """Derive facts, assess exposure, and project the structured finding."""
        facts = self.Facts.collect(self)
        finding = _assess_sa211(facts.version, facts.exposure)
        atomic = self.result.add(f"Verify {VULNERABILITY_ID}.", vulnerability_ids=(VULNERABILITY_ID,))
        project_vulnerability_result(atomic, finding)
