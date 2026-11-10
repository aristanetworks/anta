# Copyright (c) 2026 Arista Networks, Inc.
# Use of this source code is governed by the Apache License 2.0
# that can be found in the LICENSE file.
"""ANTA test for Arista Security Advisory 222."""

from __future__ import annotations

from datetime import date
from typing import TYPE_CHECKING, ClassVar, cast

from anta._advisory.base import _PREVIEW_WARNING, _AntaAdvisoryTest
from anta._advisory.eos_versions import VersionRule
from anta._advisory.facts.eos import EosVersionFact
from anta._advisory.facts.models import (
    ConfigurationState,
    Fact,
    FactProblemKind,
    FactsBase,
    FeatureName,
    SubFeature,
    UnavailableFact,
    fact_field,
    facts_dataclass,
)
from anta._advisory.facts.rpki import RpkiCacheServerFact
from anta._advisory.findings.assessment import assess_eos_version
from anta._advisory.findings.models import (
    AffectedResult,
    ConfigurationAssessment,
    EosReleaseAssessment,
    ErrorResult,
    NotAffectedResult,
    VersionRelation,
    VulnerabilityResult,
)
from anta._advisory.findings.projection import project_vulnerability_result
from anta._advisory.models import _AdvisoryMetadata, _AdvisoryVulnerability, _AdvisoryVulnerabilitySeverity
from anta._advisory.optional_commands import OptionalCommandsMixin
from anta._advisory.remediation import FixedRelease, software_version_plan
from anta._eos.version import EOSVersion
from anta.decorators import preview_test_class

if TYPE_CHECKING:
    from collections.abc import Sequence

# pylint: disable=duplicate-code  # Advisory version metadata stays local even when identical.
CVE_2026_121291_AFFECTED_VERSION_MATRIX: tuple[VersionRule, ...] = (
    VersionRule(major=4, minor=37),
    VersionRule(major=4, minor=36, patch_lte=2),
    VersionRule(major=4, minor=35, patch_lte=6),
)
CVE_2026_121291_FIXED_RELEASES = (
    FixedRelease(EOSVersion(4, 36, 3, suffix="M")),
    FixedRelease(EOSVersion(4, 35, 7, suffix="M")),
)
CVE_2026_121292_AFFECTED_VERSION_MATRIX: tuple[VersionRule, ...] = (
    VersionRule(major=4, minor=37),
    VersionRule(major=4, minor=36, patch_lte=2),
    VersionRule(major=4, minor=35, patch_lte=6),
    VersionRule(major=4, minor=34, patch_lte=8),
    VersionRule(major=4, minor=33, patch_lte=10),
    VersionRule(major=4, minor_gte=24, minor_lt=33),
)
CVE_2026_121292_FIXED_RELEASES = (
    FixedRelease(EOSVersion(4, 36, 3, suffix="M")),
    FixedRelease(EOSVersion(4, 35, 7, suffix="M")),
    FixedRelease(EOSVersion(4, 34, 9, suffix="M")),
    FixedRelease(EOSVersion(4, 33, 11, suffix="M")),
)
ADVISORY = _AdvisoryMetadata(
    sa_number="0222",
    last_updated=date(2026, 11, 10),
    title="Security Advisory 0222",
    vulnerabilities=(
        _AdvisoryVulnerability(
            id="CVE-2026-121291",
            severity=_AdvisoryVulnerabilitySeverity.HIGH,
            description=(
                "A crafted RPKI Error Report may leave EOS believing a cache reset is in progress, preventing ROA publication, withdrawal "
                "reconciliation, and BGP origin-validation updates."
            ),
        ),
        _AdvisoryVulnerability(
            id="CVE-2026-121292",
            severity=_AdvisoryVulnerabilitySeverity.HIGH,
            description=(
                "A malformed RPKI Error Report may cause an out-of-bounds read, potentially terminating the RPKI agent or exposing memory contents through logging."
            ),
        ),
    ),
    url="https://www.arista.com/en/support/advisories-notices/security-advisory/25044-security-advisory-0222",
    description=(
        "Crafted RPKI messages from an attacker controlling an RPKI cache or router-to-cache traffic may cause incorrect BGP route validation, "
        "restart the RPKI agent, or expose memory contents through logging."
    ),
)
SYNC_ID, READ_ID = (vulnerability.id for vulnerability in ADVISORY.vulnerabilities)
CACHE_SERVER = SubFeature(FeatureName.RPKI, "cache server")


def _assess_cache_servers(cache_servers: Fact[RpkiCacheServerFact]) -> ConfigurationAssessment | tuple[UnavailableFact[RpkiCacheServerFact], ...]:
    """Prefer a cache with a validated host; otherwise require every cache to be interpreted to establish absence."""
    if isinstance(cache_servers, UnavailableFact):
        return (cache_servers,)
    witnesses = tuple(cache for cache in cache_servers.value.caches if cache.host is not None)
    if witnesses:
        return ConfigurationAssessment(RpkiCacheServerFact(witnesses).available(cache_servers.source), CACHE_SERVER, ConfigurationState.CONFIGURED)
    if cache_servers.value.problems:
        kinds = {problem.fact.problem: problem.fact for problem in cache_servers.value.problems}
        return tuple(kinds[kind] for kind in FactProblemKind if kind in kinds)
    return ConfigurationAssessment(cache_servers, CACHE_SERVER, ConfigurationState.NOT_CONFIGURED)


def _assess_rpki_cache_issue(
    vulnerability_id: str,
    version: Fact[EosVersionFact],
    cache_servers: Fact[RpkiCacheServerFact],
    affected_versions: Sequence[VersionRule],
    fixed_releases: Sequence[FixedRelease],
) -> VulnerabilityResult:
    """Assess one RPKI cache vulnerability from its own EOS scope and the shared configured cache server exposure."""
    exposure = _assess_cache_servers(cache_servers)
    if isinstance(exposure, ConfigurationAssessment) and exposure.state is ConfigurationState.NOT_CONFIGURED:
        return NotAffectedResult(vulnerability_id=vulnerability_id, decisive=(exposure,))
    eos_release = assess_eos_version(version, affected_versions)
    if isinstance(eos_release, EosReleaseAssessment) and eos_release.relation is VersionRelation.OUTSIDE_SCOPE:
        return NotAffectedResult(vulnerability_id=vulnerability_id, decisive=(eos_release,))
    problems: tuple[UnavailableFact[object], ...] = (
        *((eos_release,) if isinstance(eos_release, UnavailableFact) else ()),
        *(exposure if isinstance(exposure, tuple) else ()),
    )
    if problems:
        return ErrorResult(vulnerability_id=vulnerability_id, problems=problems)
    eos_release = cast("EosReleaseAssessment", eos_release)
    return AffectedResult(
        vulnerability_id=vulnerability_id,
        context=(eos_release,),
        conditions=(cast("ConfigurationAssessment", exposure),),
        remediation=software_version_plan(fixed_releases, current_version=eos_release.fact.value),
    )


def _assess_cve_2026_121291(version: Fact[EosVersionFact], cache_servers: Fact[RpkiCacheServerFact]) -> VulnerabilityResult:
    """Assess the reset synchronization issue, introduced in 4.35.0F."""
    return _assess_rpki_cache_issue(SYNC_ID, version, cache_servers, CVE_2026_121291_AFFECTED_VERSION_MATRIX, CVE_2026_121291_FIXED_RELEASES)


def _assess_cve_2026_121292(version: Fact[EosVersionFact], cache_servers: Fact[RpkiCacheServerFact]) -> VulnerabilityResult:
    """Assess the out-of-bounds read issue, introduced in 4.24.0F."""
    return _assess_rpki_cache_issue(READ_ID, version, cache_servers, CVE_2026_121292_AFFECTED_VERSION_MATRIX, CVE_2026_121292_FIXED_RELEASES)


@preview_test_class(warning_message=_PREVIEW_WARNING)
class SA222(OptionalCommandsMixin, _AntaAdvisoryTest):
    """Verify whether the device is impacted by Security Advisory 0222.

    Expected Results
    ----------------
    * Not Affected: The EOS version is outside the affected releases of a vulnerability, or no RPKI cache under ``router bgp`` has a
      configured host.
    * Affected: On an EOS release affected by a vulnerability, at least one RPKI cache under ``router bgp`` has a configured host.
    * Error: The EOS version is missing or invalid, the RPKI cache configuration cannot be collected or parsed, or no cache has a
      validated host while the host configuration of another cache is missing, invalid, or contradictory.

    Notes
    -----
    The two vulnerabilities have different affected releases and are reported separately. Both require one or more configured RPKI caches
    and an RPKI-to-Router session to the cache.

    Exposure is assessed from persistent configuration rather than RPKI session state. A configured cache whose session is down, idle, or
    not yet established is still affected because the session can be established later without a configuration change. Each cache counts
    when it has a host, whatever its address family, VRF, port, or transport, including a host name that does not resolve, a VRF that is
    not configured yet, or a TLS transport without an SSL profile. A cache without a host cannot open a session and does not count. A
    BGP ``shutdown`` does not stop RPKI cache sessions, so it does not make the device safe.

    One cache with a validated host is sufficient despite incomplete host evidence for other caches; otherwise, every cache must be
    interpreted to establish that none has a host. A cache with contradictory host statements is never used as that witness.

    The advisory provides no mitigation. Clearing an RPKI cache or restarting the RPKI agent may recover a stuck synchronization state
    but does not prevent recurrence, so the remediation is a software upgrade. The test does not inspect RPKI counters or logs and does
    not detect exploitation.

    Examples
    --------
    ```yaml
    anta.tests.advisories:
      - SA222:
    ```
    """

    @facts_dataclass
    class Facts(FactsBase):
        """Collected facts required to assess the advisory."""

        version: Fact[EosVersionFact] = fact_field(EosVersionFact)
        cache_servers: Fact[RpkiCacheServerFact] = fact_field(RpkiCacheServerFact)

    advisory: ClassVar[_AdvisoryMetadata] = ADVISORY
    description = "Verify whether the device is impacted by Security Advisory 0222."
    _atomic_support = True

    @_AntaAdvisoryTest.anta_test
    def test(self) -> None:
        """Collect facts, assess both vulnerabilities, and project their atomic results."""
        facts = self.Facts.collect(self)
        for vulnerability_id, assess in ((SYNC_ID, _assess_cve_2026_121291), (READ_ID, _assess_cve_2026_121292)):
            finding = assess(facts.version, facts.cache_servers)
            atomic = self.result.add(f"Verify {vulnerability_id}.", vulnerability_ids=(vulnerability_id,))
            project_vulnerability_result(atomic, finding)
