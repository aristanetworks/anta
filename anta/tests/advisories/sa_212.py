# Copyright (c) 2026 Arista Networks, Inc.
# Use of this source code is governed by the Apache License 2.0
# that can be found in the LICENSE file.
# pylint: disable=duplicate-code
"""ANTA test for Arista Security Advisory 212."""

from __future__ import annotations

from datetime import date
from typing import ClassVar

from anta._advisory.base import _PREVIEW_WARNING, _AntaAdvisoryTest
from anta._advisory.eos_versions import VersionRule
from anta._advisory.facts.avt import PathfinderRoleFact
from anta._advisory.facts.bgp_peering import BgpLinkStatePeeringFact
from anta._advisory.facts.eos import EosVersionFact
from anta._advisory.facts.models import ConfigurationState, Fact, FactsBase, FeatureState, UnavailableFact, fact_field, facts_dataclass
from anta._advisory.facts.platform import PlatformIdentityFact
from anta._advisory.findings.assessment import assess_eos_scope, assess_platform_scope
from anta._advisory.findings.models import AffectedResult, ErrorResult, NotAffectedResult, VulnerabilityResult
from anta._advisory.findings.projection import project_vulnerability_result
from anta._advisory.models import _AdvisoryMetadata, _AdvisoryVulnerability, _AdvisoryVulnerabilitySeverity
from anta._advisory.optional_commands import OptionalCommandsMixin
from anta._advisory.remediation import FixedRelease, software_version_plan
from anta._eos.platform import PlatformFamily
from anta._eos.version import EOSVersion
from anta.decorators import preview_test_class

AFFECTED_VERSION_MATRIX: tuple[VersionRule, ...] = (
    VersionRule(major=4, minor_lte=32),
    VersionRule(major=4, minor=33, patch_lt=11),
    VersionRule(major=4, minor=34, patch_lt=9),
    VersionRule(major=4, minor=35, patch_lt=7),
    VersionRule(major=4, minor=36, patch_lt=3),
)
FIXED_RELEASES = (
    FixedRelease(EOSVersion(4, 37, 0, suffix="F")),
    FixedRelease(EOSVersion(4, 36, 3, suffix="M")),
    FixedRelease(EOSVersion(4, 35, 7, suffix="M")),
    FixedRelease(EOSVersion(4, 34, 9, suffix="M")),
    FixedRelease(EOSVersion(4, 33, 11, suffix="M")),
)
AFFECTED_PLATFORM_FAMILIES = frozenset({PlatformFamily.AWE_5000, PlatformFamily.AWE_7200_R, PlatformFamily.CLOUDEOS, PlatformFamily.CVX})

ADVISORY = _AdvisoryMetadata(
    sa_number="0212",
    last_updated=date(2026, 11, 10),
    title="Security Advisory 0212",
    vulnerabilities=(
        _AdvisoryVulnerability(
            id="CVE-2026-120979",
            severity=_AdvisoryVulnerabilitySeverity.HIGH,
            description="Crafted BGP-LS packets may cause incorrect WAN path selection and disrupt traffic forwarding on Pathfinder nodes.",
        ),
    ),
    url="https://www.arista.com/en/support/advisories-notices/security-advisory/25034-security-advisory-0212",
    description="Affected EOS platforms with configured BGP-LS peering and the Pathfinder role may select incorrect WAN paths.",
)
VULNERABILITY_ID = "CVE-2026-120979"


def _assess_sa212(
    version: Fact[EosVersionFact],
    platform: Fact[PlatformIdentityFact],
    peering: Fact[BgpLinkStatePeeringFact],
    role: Fact[PathfinderRoleFact],
) -> VulnerabilityResult:
    """Assess affected scope, configured Link-State peering, and Pathfinder role."""
    if not isinstance(peering, UnavailableFact) and peering.value.state is ConfigurationState.NOT_CONFIGURED:
        return NotAffectedResult(vulnerability_id=VULNERABILITY_ID, decisive=(peering,))
    if not isinstance(role, UnavailableFact) and role.value.state is FeatureState.DISABLED:
        return NotAffectedResult(vulnerability_id=VULNERABILITY_ID, decisive=(role,))

    eos_scope = assess_eos_scope(VULNERABILITY_ID, version, AFFECTED_VERSION_MATRIX)
    platform_scope = assess_platform_scope(VULNERABILITY_ID, platform, AFFECTED_PLATFORM_FAMILIES)
    if isinstance(eos_scope, NotAffectedResult):
        return eos_scope
    if isinstance(platform_scope, NotAffectedResult):
        return platform_scope
    problems = (
        (eos_scope.problems if isinstance(eos_scope, ErrorResult) else ())
        + (platform_scope.problems if isinstance(platform_scope, ErrorResult) else ())
        + ((peering,) if isinstance(peering, UnavailableFact) else ())
        + ((role,) if isinstance(role, UnavailableFact) else ())
    )
    if isinstance(eos_scope, ErrorResult) or isinstance(platform_scope, ErrorResult) or isinstance(peering, UnavailableFact) or isinstance(role, UnavailableFact):
        return ErrorResult(vulnerability_id=VULNERABILITY_ID, problems=problems)
    return AffectedResult(
        vulnerability_id=VULNERABILITY_ID,
        context=(eos_scope, platform_scope),
        conditions=(peering, role),
        remediation=software_version_plan(FIXED_RELEASES, current_version=eos_scope.fact.value),
    )


@preview_test_class(warning_message=_PREVIEW_WARNING)
class SA212(OptionalCommandsMixin, _AntaAdvisoryTest):
    """Verify whether the device is impacted by Security Advisory 0212.

    Expected Results
    ----------------
    * Not Affected: EOS or platform is outside scope, no BGP-LS peering is configured, or the device reports a non-Pathfinder role.
    * Affected: An affected release on AWE 5000, AWE 7200R, CloudEOS, CVX, or vEOS has enabled BGP-LS activation and the Pathfinder role.
    * Error: Required EOS, platform, configured BGP-LS peering, or role evidence is missing, invalid, unsupported, or cannot be collected.

    Notes
    -----
    BGP-LS exposure is assessed from persistent Link-State address-family presence and neighbor or peer-group activation. A current neighbor,
    usable dynamic listener, peer ASN, router ID, negotiated capability, or established session is not required. Idle or disconnected sessions
    do not establish safety. An activated dynamic peer-group remains exposed with zero current neighbors, and an unused activated peer-group
    is conservatively treated as exposed because the test does not require proof of current group membership or a usable listener.

    Verified persistent BGP process, VRF, Link-State address-family, or neighbor shutdown establishes absence of the disabled exposure.
    Peer-group shutdown is inherited unless an explicit neighbor no-shutdown overrides it. An enabled member inheriting activation keeps its
    group exposed; explicit AF deactivation closes that member path. Whole-process, VRF, and AF shutdown still disable their entire scope.
    Unresolved inheritance cycles are conservatively treated as enabled rather than proving safety. At least one enabled activation in any
    configured instance and VRF is sufficient; shutdown settings and other address families do not leak across sibling scopes.
    Global peer-group shutdown is considered for VRF members. A locally redeclared group is conservatively treated as independent of its namesake.

    The reported AVT role is device-wide and does not require live paths or a working BGP session. The test does not add a BGP-LS DPS
    consumer-role prerequisite. Operational summaries are not collected, so unrelated incomplete peer or VRF records cannot veto established
    configuration exposure. Missing, malformed, unsupported, or failed persistent configuration evidence produces Error when needed.

    Successfully reported edge, zone transit, region transit, and unknown roles establish that the Pathfinder prerequisite is absent.
    A missing role, unrecognized role, or AVT command error (including an unconfigured AVT agent) is unavailable evidence and produces Error
    when role evidence is needed; it is never replaced with the valid unknown role. No configured BGP-LS peering, an excluded platform, or a
    fixed release independently establishes Not Affected even when other inputs are unavailable. Otherwise all required unavailable inputs
    are reported together.

    Platform scope includes AWE 5000, AWE 7200R, CloudEOS, CVX, and vEOS identities. CVX and vEOS identities are included conservatively
    because the raw vEOS model can represent CloudEOS. Ordinary cEOS-lab and vEOS-lab are excluded even if they accept the commands.
    Unrecognized or incomplete platform identity produces Error rather than assuming exclusion. All 4.32 and older EOS 4 trains
    remain in software scope because the advisory lists them as affected without a fixed release; later trains use the named fixed boundaries.

    The advisory provides no complete configuration mitigation, so established exposure is Affected and remediation is a software upgrade.
    The test assesses configuration exposure, not exploitation or the advisory's path-change indicators of compromise.

    Examples
    --------
    ```yaml
    anta.tests.advisories:
      - SA212:
    ```
    """

    @facts_dataclass
    class Facts(FactsBase):
        """Collected facts required to assess the advisory."""

        version: Fact[EosVersionFact] = fact_field(EosVersionFact)
        platform: Fact[PlatformIdentityFact] = fact_field(PlatformIdentityFact)
        peering: Fact[BgpLinkStatePeeringFact] = fact_field(BgpLinkStatePeeringFact)
        role: Fact[PathfinderRoleFact] = fact_field(PathfinderRoleFact)

    advisory: ClassVar[_AdvisoryMetadata] = ADVISORY
    description = "Verify whether the device is impacted by Security Advisory 0212."
    _atomic_support = True

    @_AntaAdvisoryTest.anta_test
    def test(self) -> None:
        """Collect facts, assess the vulnerability, and project its atomic result."""
        facts = self.Facts.collect(self)
        finding = _assess_sa212(facts.version, facts.platform, facts.peering, facts.role)
        atomic = self.result.add(f"Verify {VULNERABILITY_ID}.", vulnerability_ids=(VULNERABILITY_ID,))
        project_vulnerability_result(atomic, finding)
