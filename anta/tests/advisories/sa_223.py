# Copyright (c) 2026 Arista Networks, Inc.
# Use of this source code is governed by the Apache License 2.0
# that can be found in the LICENSE file.
"""ANTA test for Arista Security Advisory 223."""

from __future__ import annotations

from datetime import date
from typing import TYPE_CHECKING, ClassVar

from anta._advisory.base import _PREVIEW_WARNING, _AntaAdvisoryTest
from anta._advisory.eos_versions import VersionRule
from anta._advisory.facts.bfd import SbfdInitiatorRoundTripDelayFact, SbfdReflectorProxyFact
from anta._advisory.facts.eos import EosVersionFact
from anta._advisory.facts.models import Fact, FactsBase, FeatureState, UnavailableFact, fact_field, facts_dataclass
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

if TYPE_CHECKING:
    from collections.abc import Sequence

# pylint: disable=duplicate-code  # Advisory version metadata stays local even when identical.
CVE_121294_AFFECTED_VERSIONS: tuple[VersionRule, ...] = (
    VersionRule(major=4, minor=36, patch_lte=2),
    VersionRule(major=4, minor=35, patch_lte=6),
    VersionRule(major=4, minor=34, patch_lte=8),
    VersionRule(major=4, minor=33, patch_lte=10),
    VersionRule(major=4, minor_gte=29, minor_lte=32),
    VersionRule(major=4, minor=28, patch_gte=2),
)
CVE_121295_AFFECTED_VERSIONS: tuple[VersionRule, ...] = (
    VersionRule(major=4, minor=36, patch_lte=2),
    VersionRule(major=4, minor=35, patch_lte=6),
    VersionRule(major=4, minor=34, patch_lte=8),
    VersionRule(major=4, minor=33, patch_lte=10),
    VersionRule(major=4, minor_gte=29, minor_lte=32),
)
FIXED_RELEASES = (
    FixedRelease(EOSVersion(4, 37, 0, suffix="F")),
    FixedRelease(EOSVersion(4, 36, 3, suffix="M")),
    FixedRelease(EOSVersion(4, 35, 7, suffix="M")),
    FixedRelease(EOSVersion(4, 34, 9, suffix="M")),
    FixedRelease(EOSVersion(4, 33, 11, suffix="M")),
)
# pylint: enable=duplicate-code
AFFECTED_PLATFORM_FAMILIES = frozenset(
    {
        PlatformFamily.SERIES_710,
        PlatformFamily.SERIES_720_D,
        PlatformFamily.SERIES_720_XP,
        PlatformFamily.SERIES_722_XPM,
        PlatformFamily.SERIES_750_X,
        PlatformFamily.SERIES_7010_TX,
        PlatformFamily.SERIES_7020_R,
        PlatformFamily.SERIES_7020_R4,
        PlatformFamily.SERIES_7280_R,
        PlatformFamily.SERIES_7280_R2,
        PlatformFamily.SERIES_7280_R3,
        PlatformFamily.SERIES_7280_R4,
        PlatformFamily.SERIES_7500_R,
        PlatformFamily.SERIES_7500_R2,
        PlatformFamily.SERIES_7500_R3,
        PlatformFamily.SERIES_7800_R3,
        PlatformFamily.SERIES_7800_R4,
        PlatformFamily.SERIES_7700_R4,
        PlatformFamily.CLOUDEOS,
        PlatformFamily.CEOS_LAB,
        PlatformFamily.VEOS_LAB,
        PlatformFamily.CVX,
    }
)

ADVISORY = _AdvisoryMetadata(
    sa_number="0223",
    last_updated=date(2026, 11, 10),
    title="Security Advisory 0223",
    vulnerabilities=(
        _AdvisoryVulnerability(
            id="CVE-2026-121294",
            severity=_AdvisoryVulnerabilitySeverity.MEDIUM,
            description="A crafted S-BFD PDU may cause an S-BFD reflector proxy to temporarily stop reflecting S-BFD packets.",
        ),
        _AdvisoryVulnerability(
            id="CVE-2026-121295",
            severity=_AdvisoryVulnerabilitySeverity.HIGH,
            description="A crafted S-BFD PDU may crash the kernel of an S-BFD initiator that measures round-trip delay and reboot the device.",
        ),
    ),
    url="https://www.arista.com/en/support/advisories-notices/security-advisory/25045-security-advisory-0223",
    description=(
        "On affected EOS platforms with S-BFD configured, an unauthenticated attacker may send crafted S-BFD PDUs that stop reflector proxy "
        "reflection or reboot an initiator that measures round-trip delay."
    ),
)
REFLECTOR_PROXY_ID, ROUND_TRIP_DELAY_ID = (vulnerability.id for vulnerability in ADVISORY.vulnerabilities)


def _assess_sbfd_issue(
    vulnerability_id: str,
    version: Fact[EosVersionFact],
    platform: Fact[PlatformIdentityFact],
    exposure: Fact[SbfdReflectorProxyFact] | Fact[SbfdInitiatorRoundTripDelayFact],
    affected_versions: Sequence[VersionRule],
) -> VulnerabilityResult:
    """Assess one S-BFD issue from its own configured feature, release scope, and the shared platform scope."""
    if not isinstance(exposure, UnavailableFact) and exposure.value.state is not FeatureState.ENABLED:
        return NotAffectedResult(vulnerability_id=vulnerability_id, decisive=(exposure,))

    eos_scope = assess_eos_scope(vulnerability_id, version, affected_versions)
    platform_scope = assess_platform_scope(vulnerability_id, platform, AFFECTED_PLATFORM_FAMILIES)
    if isinstance(eos_scope, NotAffectedResult):
        return eos_scope
    if isinstance(platform_scope, NotAffectedResult):
        return platform_scope
    problems = (
        (eos_scope.problems if isinstance(eos_scope, ErrorResult) else ())
        + (platform_scope.problems if isinstance(platform_scope, ErrorResult) else ())
        + ((exposure,) if isinstance(exposure, UnavailableFact) else ())
    )
    if isinstance(eos_scope, ErrorResult) or isinstance(platform_scope, ErrorResult) or isinstance(exposure, UnavailableFact):
        return ErrorResult(vulnerability_id=vulnerability_id, problems=problems)
    return AffectedResult(
        vulnerability_id=vulnerability_id,
        context=(eos_scope, platform_scope),
        conditions=(exposure,),
        remediation=software_version_plan(FIXED_RELEASES, current_version=eos_scope.fact.value),
    )


def _assess_reflector_proxy(
    version: Fact[EosVersionFact],
    platform: Fact[PlatformIdentityFact],
    reflector_proxy: Fact[SbfdReflectorProxyFact],
) -> VulnerabilityResult:
    """Assess CVE-2026-121294 from the configured S-BFD reflector proxy."""
    return _assess_sbfd_issue(REFLECTOR_PROXY_ID, version, platform, reflector_proxy, CVE_121294_AFFECTED_VERSIONS)


def _assess_round_trip_delay(
    version: Fact[EosVersionFact],
    platform: Fact[PlatformIdentityFact],
    round_trip_delay: Fact[SbfdInitiatorRoundTripDelayFact],
) -> VulnerabilityResult:
    """Assess CVE-2026-121295 from the configured S-BFD initiator round-trip delay measurement."""
    return _assess_sbfd_issue(ROUND_TRIP_DELAY_ID, version, platform, round_trip_delay, CVE_121295_AFFECTED_VERSIONS)


@preview_test_class(warning_message=_PREVIEW_WARNING)
class SA223(OptionalCommandsMixin, _AntaAdvisoryTest):
    """Verify whether the device is impacted by Security Advisory 0223.

    Expected Results
    ----------------
    * Not Affected: For each vulnerability, the EOS version or platform is outside its scope, or its S-BFD setting is not configured.
    * Affected: An affected release on an affected platform has an S-BFD reflector proxy (CVE-2026-121294) or S-BFD initiator round-trip
      delay measurement (CVE-2026-121295) configured.
    * Error: Required EOS, platform, or S-BFD configuration evidence is missing, cannot be collected, or cannot be interpreted.

    Notes
    -----
    Each vulnerability is assessed and reported separately. CVE-2026-121294 requires a reflector local discriminator with the ``proxy``
    keyword; a reflector without ``proxy`` is not exposed to it. CVE-2026-121295 requires ``initiator measurement delay round-trip``.
    Either, both, or neither may apply to one device. A configuration line that cannot be interpreted for one setting does not hide
    established exposure through the other.

    Exposure is assessed from the persistent ``router bfd`` S-BFD configuration, not from operational state. A configured S-BFD setting is
    exposed even when no S-BFD session exists or every session is down, because sessions can come up without a configuration change.
    BFD administrative shutdown is not treated as removing exposure because the advisory does not state that it does.

    Platform scope is the advisory's affected platform list. Platforms outside it, including the listed unaffected AWE 5000, AWE 7200R,
    7300X/X3, 7320X, 7358X4, 7368X4, 7388X5, 7130, 7170, 7050X3/X4, 7060X/X2/X4/X5/X6/XE7, and 7260X/X3 families, are Not Affected.
    Unrecognized or incomplete platform identity produces Error rather than assuming exclusion. An absent S-BFD setting, an out-of-scope
    release, or an excluded platform independently establishes Not Affected even when other inputs are unavailable.

    EOS 4.29 through 4.32 remain in software scope for both vulnerabilities because the advisory lists them as affected without a fixed
    release; CVE-2026-121294 additionally covers 4.28.2F and later 4.28 releases. The advisory provides no mitigation, so established
    exposure is Affected and remediation is a software upgrade. The test does not detect exploitation.

    Examples
    --------
    ```yaml
    anta.tests.advisories:
      - SA223:
    ```
    """

    @facts_dataclass
    class Facts(FactsBase):
        """Collected facts required to assess the advisory."""

        version: Fact[EosVersionFact] = fact_field(EosVersionFact)
        platform: Fact[PlatformIdentityFact] = fact_field(PlatformIdentityFact)
        reflector_proxy: Fact[SbfdReflectorProxyFact] = fact_field(SbfdReflectorProxyFact)
        round_trip_delay: Fact[SbfdInitiatorRoundTripDelayFact] = fact_field(SbfdInitiatorRoundTripDelayFact)

    advisory: ClassVar[_AdvisoryMetadata] = ADVISORY
    description = "Verify whether the device is impacted by Security Advisory 0223."
    _atomic_support = True

    @_AntaAdvisoryTest.anta_test
    def test(self) -> None:
        """Collect facts, assess both vulnerabilities, and project their atomic results."""
        facts = self.Facts.collect(self)
        for vulnerability_id, finding in (
            (REFLECTOR_PROXY_ID, _assess_reflector_proxy(facts.version, facts.platform, facts.reflector_proxy)),
            (ROUND_TRIP_DELAY_ID, _assess_round_trip_delay(facts.version, facts.platform, facts.round_trip_delay)),
        ):
            atomic = self.result.add(f"Verify {vulnerability_id}.", vulnerability_ids=(vulnerability_id,))
            project_vulnerability_result(atomic, finding)
