# Copyright (c) 2026 Arista Networks, Inc.
# Use of this source code is governed by the Apache License 2.0
# that can be found in the LICENSE file.
# pylint: disable=duplicate-code
"""Unit tests for Arista Security Advisory 222."""

from __future__ import annotations

from datetime import date
from typing import TYPE_CHECKING, Literal, TypeAlias

import pytest

from anta._advisory.eos_versions import AffectedStatus
from anta._advisory.facts.eos import EosVersionFact
from anta._advisory.facts.models import AvailableFact, ConfigurationState, FactProblemKind
from anta._advisory.facts.rpki import RpkiCacheServer, RpkiCacheServerFact, RpkiCacheServerProblem
from anta._advisory.findings.models import AffectedResult, ConfigurationAssessment, EosReleaseAssessment, ErrorResult, NotAffectedResult, VersionRelation
from anta._advisory.models import _AdvisoryVulnerabilitySeverity
from anta._advisory.remediation import ChangeSoftwareVersion, FixedRelease, KnownFixedReleases, RemediationPlan, SoftwareTarget
from anta._eos.version import EOSVersion, parse_eos_version
from anta.models import AntaCommand
from anta.result_manager.models import AntaTestStatus
from anta.tests.advisories.sa_222 import (
    ADVISORY,
    CACHE_SERVER,
    CVE_2026_121291_AFFECTED_VERSION_MATRIX,
    CVE_2026_121292_AFFECTED_VERSION_MATRIX,
    SA222,
    _assess_cve_2026_121291,
    _assess_cve_2026_121292,
)
from tests.units.anta_tests import (
    build_eos_version,
    test,  # noqa: F401 - Pytest collects this imported test function.
)
from tests.units.anta_tests.advisories.fact_builders import SOURCE, assert_version_statuses, eos_version_fact

if TYPE_CHECKING:
    from collections.abc import Callable

    from anta._advisory.facts.models import Fact
    from anta._advisory.findings.models import VulnerabilityResult
    from tests.units.anta_tests import AntaUnitTestData, AtomicResult, UnitTestResult

    Assessment: TypeAlias = Callable[[Fact[EosVersionFact], Fact[RpkiCacheServerFact]], VulnerabilityResult]

Status: TypeAlias = Literal[AntaTestStatus.SUCCESS, AntaTestStatus.FAILURE, AntaTestStatus.ERROR]
SYNC_ID = "CVE-2026-121291"
READ_ID = "CVE-2026-121292"
COMMAND = r"show running-config all section ^\s+rpki\scache\s"
SYNC_FIXED_RELEASES = (
    FixedRelease(EOSVersion(4, 36, 3, suffix="M")),
    FixedRelease(EOSVersion(4, 35, 7, suffix="M")),
)
READ_FIXED_RELEASES = (
    FixedRelease(EOSVersion(4, 36, 3, suffix="M")),
    FixedRelease(EOSVersion(4, 35, 7, suffix="M")),
    FixedRelease(EOSVersion(4, 34, 9, suffix="M")),
    FixedRelease(EOSVersion(4, 33, 11, suffix="M")),
)

# Captured from EOS 4.35.1F with an IPv4 cache in the default VRF, an IPv6 cache on a custom port, and a cache without a host. No
# session was established because the hosts are documentation addresses.
CACHE_CONFIG = """router bgp 65000
   rpki cache C4
      host 192.0.2.10 vrf default port 323
      preference 5
      no refresh-interval
      no retry-interval
      no expire-interval
      no local-interface
      no roa table
      !
      transport tcp
         no tcp keepalive
   rpki cache C6
      host 2001:db8::10 vrf default port 3323
      preference 5
      no refresh-interval
      no retry-interval
      no expire-interval
      no local-interface
      no roa table
      !
      transport tcp
         no tcp keepalive
   rpki cache NOHOST
      no host
      preference 5
      no refresh-interval
      no retry-interval
      no expire-interval
      no local-interface
      no roa table
      !
      transport tcp
         no tcp keepalive
"""
# Captured from EOS 4.37.0F with a cache that has no host.
NO_HOST_CONFIG = """router bgp 65000
   rpki cache NOHOST
      no host
      preference 5
      no refresh-interval
      no retry-interval
      no expire-interval
      no local-interface
      no roa table
      no aspa
      !
      transport tcp
         no tcp keepalive
"""
# Captured from EOS 4.37.0F with an IPv4 cache in a non-default VRF.
VRF_CACHE_CONFIG = """router bgp 65000
   rpki cache CVRF
      host 192.0.2.11 vrf SA222 port 323
      preference 5
      no refresh-interval
      no retry-interval
      no expire-interval
      no local-interface
      no roa table
      no aspa
      !
      transport tcp
         no tcp keepalive
"""


def cache_section(name: str, *hosts: str) -> str:
    """Render one cache section with the given host statements and the remaining EOS 4.35.1F defaults."""
    rendered_hosts = "".join(f"      {host}\n" for host in hosts)
    return (
        f"   rpki cache {name}\n{rendered_hosts}      preference 5\n      no refresh-interval\n      no retry-interval\n"
        "      no expire-interval\n      no local-interface\n      no roa table\n      !\n      transport tcp\n         no tcp keepalive\n"
    )


GOOD = cache_section("GOOD", "host 192.0.2.10 vrf default port 323")
BAD = cache_section("BAD")
CONTRADICTORY = cache_section("GOOD", "host 192.0.2.10 vrf default port 323", "host 192.0.2.11 vrf default port 323")
NOHOST = cache_section("NOHOST", "no host")
AFFECTED = "The device is affected because EOS version '{version}' is affected and the RPKI cache server configuration is configured."
OUTSIDE = "The device is not affected because EOS version '{version}' is outside the affected releases."
NO_CACHE = "The device is not affected because the RPKI cache server configuration is not configured."
MISSING_VERSION = "The test could not determine the EOS version because it is missing from device metadata."
INVALID_CACHES = f"The test could not determine the RPKI cache server configuration because the '{COMMAND}' output is invalid."
INCOMPLETE_CACHES = f"The test could not determine the RPKI cache server configuration because the '{COMMAND}' output is incomplete."


def remediation(version: str, fixed_releases: tuple[FixedRelease, ...]) -> RemediationPlan:
    """Build an independent software-version plan for the given current release."""
    return RemediationPlan(ChangeSoftwareVersion(SoftwareTarget.EOS, parse_eos_version(version).unwrap(), KnownFixedReleases(fixed_releases)))


def expected_result(
    sync: tuple[Status, str, RemediationPlan | None],
    read: tuple[Status, str, RemediationPlan | None],
) -> UnitTestResult:
    """Build parent and per-vulnerability atomic expectations, in advisory order."""
    atomic_results: list[AtomicResult] = []
    for vulnerability_id, (status, message, plan) in ((SYNC_ID, sync), (READ_ID, read)):
        atomic: AtomicResult = {"description": f"Verify {vulnerability_id}.", "result": status, "messages": [message]}
        if plan is not None:
            atomic["remediation"] = plan
        atomic_results.append(atomic)
    statuses = {sync[0], read[0]}
    parent: Status = AntaTestStatus.SUCCESS
    if AntaTestStatus.ERROR in statuses:
        parent = AntaTestStatus.ERROR
    elif AntaTestStatus.FAILURE in statuses:
        parent = AntaTestStatus.FAILURE
    return {
        "result": parent,
        "messages": [sync[1], read[1]],
        "remediations": [plan for plan in dict.fromkeys((sync[2], read[2])) if plan is not None],
        "atomic_results": atomic_results,
    }


def affected(version: str, fixed_releases: tuple[FixedRelease, ...]) -> tuple[Status, str, RemediationPlan]:
    """Expect an affected vulnerability with its own software remediation."""
    return AntaTestStatus.FAILURE, AFFECTED.format(version=version), remediation(version, fixed_releases)


def outside(version: str) -> tuple[Status, str, None]:
    """Expect a vulnerability outside its affected releases."""
    return AntaTestStatus.SUCCESS, OUTSIDE.format(version=version), None


NOT_CONFIGURED: tuple[Status, str, None] = (AntaTestStatus.SUCCESS, NO_CACHE, None)

_DATA: AntaUnitTestData = {
    (SA222, "failure-both-configured-caches-without-session"): {
        "version": build_eos_version("4.35.6M"),
        "eos_data": [CACHE_CONFIG],
        "expected": expected_result(affected("4.35.6M", SYNC_FIXED_RELEASES), affected("4.35.6M", READ_FIXED_RELEASES)),
    },
    (SA222, "failure-both-four-part-release"): {
        "version": build_eos_version("4.36.0.1F"),
        "eos_data": [CACHE_CONFIG],
        "expected": expected_result(affected("4.36.0.1F", SYNC_FIXED_RELEASES), affected("4.36.0.1F", READ_FIXED_RELEASES)),
    },
    (SA222, "failure-both-release-without-published-fix-in-train"): {
        "version": build_eos_version("4.37.0F"),
        "eos_data": [VRF_CACHE_CONFIG],
        "expected": expected_result(affected("4.37.0F", SYNC_FIXED_RELEASES), affected("4.37.0F", READ_FIXED_RELEASES)),
    },
    (SA222, "failure-read-only-before-sync-introduction"): {
        "version": build_eos_version("4.34.8M"),
        "eos_data": [CACHE_CONFIG],
        "expected": expected_result(outside("4.34.8M"), affected("4.34.8M", READ_FIXED_RELEASES)),
    },
    (SA222, "failure-read-only-at-read-introduction"): {
        "version": build_eos_version("4.24.0F"),
        "eos_data": [CACHE_CONFIG],
        "expected": expected_result(outside("4.24.0F"), affected("4.24.0F", READ_FIXED_RELEASES)),
    },
    (SA222, "failure-read-only-end-of-support-train"): {
        "version": build_eos_version("4.31.10M"),
        "eos_data": [VRF_CACHE_CONFIG],
        "expected": expected_result(outside("4.31.10M"), affected("4.31.10M", READ_FIXED_RELEASES)),
    },
    (SA222, "success-both-fixed-release"): {
        "version": build_eos_version("4.35.7M"),
        "eos_data": [CACHE_CONFIG],
        "expected": expected_result(outside("4.35.7M"), outside("4.35.7M")),
    },
    (SA222, "success-both-before-read-introduction"): {
        "version": build_eos_version("4.23.0F"),
        "eos_data": [CACHE_CONFIG],
        "expected": expected_result(outside("4.23.0F"), outside("4.23.0F")),
    },
    (SA222, "success-both-unlisted-later-train"): {
        "version": build_eos_version("4.38.0F"),
        "eos_data": [CACHE_CONFIG],
        "expected": expected_result(outside("4.38.0F"), outside("4.38.0F")),
    },
    (SA222, "success-no-cache-short-circuits-missing-version"): {
        "version": None,
        "eos_data": [""],
        "expected": expected_result(NOT_CONFIGURED, NOT_CONFIGURED),
    },
    (SA222, "success-cache-without-host"): {
        "version": build_eos_version("4.37.0F"),
        "eos_data": [NO_HOST_CONFIG],
        "expected": expected_result(NOT_CONFIGURED, NOT_CONFIGURED),
    },
    (SA222, "error-missing-version"): {
        "version": None,
        "eos_data": [CACHE_CONFIG],
        "expected": expected_result((AntaTestStatus.ERROR, MISSING_VERSION, None), (AntaTestStatus.ERROR, MISSING_VERSION, None)),
    },
    (SA222, "error-malformed-cache-configuration"): {
        "version": build_eos_version("4.35.6M"),
        "eos_data": ["router bgp 65000\n   rpki cache C1\n      no host\n      host 192.0.2.10 vrf default port 323\n"],
        "expected": expected_result((AntaTestStatus.ERROR, INVALID_CACHES, None), (AntaTestStatus.ERROR, INVALID_CACHES, None)),
    },
    (SA222, "error-read-only-malformed-configuration-before-sync-introduction"): {
        "version": build_eos_version("4.34.8M"),
        "eos_data": ["router bgp 65000\n   vrf BLUE\n      rpki cache C1\n"],
        "expected": expected_result(outside("4.34.8M"), (AntaTestStatus.ERROR, INVALID_CACHES, None)),
    },
    (SA222, "failure-both-valid-cache-before-cache-without-host-statement"): {
        "version": build_eos_version("4.35.1F"),
        "eos_data": [f"router bgp 65000\n{GOOD}{BAD}"],
        "expected": expected_result(affected("4.35.1F", SYNC_FIXED_RELEASES), affected("4.35.1F", READ_FIXED_RELEASES)),
    },
    (SA222, "failure-both-valid-cache-after-cache-without-host-statement"): {
        "version": build_eos_version("4.35.1F"),
        "eos_data": [f"router bgp 65000\n{BAD}{GOOD}"],
        "expected": expected_result(affected("4.35.1F", SYNC_FIXED_RELEASES), affected("4.35.1F", READ_FIXED_RELEASES)),
    },
    (SA222, "failure-both-valid-cache-beside-contradictory-cache"): {
        "version": build_eos_version("4.35.1F"),
        "eos_data": [f"router bgp 65000\n{CONTRADICTORY.replace('rpki cache GOOD', 'rpki cache OTHER')}{GOOD}"],
        "expected": expected_result(affected("4.35.1F", SYNC_FIXED_RELEASES), affected("4.35.1F", READ_FIXED_RELEASES)),
    },
    (SA222, "error-contradictory-witness"): {
        "version": build_eos_version("4.35.1F"),
        "eos_data": [f"router bgp 65000\n{CONTRADICTORY}"],
        "expected": expected_result((AntaTestStatus.ERROR, INVALID_CACHES, None), (AntaTestStatus.ERROR, INVALID_CACHES, None)),
    },
    (SA222, "error-contradictory-witness-beside-cache-without-host-statement"): {
        "version": build_eos_version("4.35.1F"),
        "eos_data": [f"router bgp 65000\n{BAD}{CONTRADICTORY}"],
        "expected": expected_result(
            (AntaTestStatus.ERROR, f"{INCOMPLETE_CACHES} {INVALID_CACHES}", None), (AntaTestStatus.ERROR, f"{INCOMPLETE_CACHES} {INVALID_CACHES}", None)
        ),
    },
    (SA222, "error-cache-without-host-statement-prevents-absence"): {
        "version": build_eos_version("4.35.1F"),
        "eos_data": [f"router bgp 65000\n{NOHOST}{BAD}"],
        "expected": expected_result((AntaTestStatus.ERROR, INCOMPLETE_CACHES, None), (AntaTestStatus.ERROR, INCOMPLETE_CACHES, None)),
    },
    (SA222, "success-both-fixed-release-with-cache-without-host-statement"): {
        "version": build_eos_version("4.35.7M"),
        "eos_data": [f"router bgp 65000\n{BAD}"],
        "expected": expected_result(outside("4.35.7M"), outside("4.35.7M")),
    },
}


def cache_fact(*caches: RpkiCacheServer, problems: tuple[RpkiCacheServerProblem, ...] = ()) -> AvailableFact[RpkiCacheServerFact]:
    """Build normalized RPKI cache server configuration for direct assessment tests."""
    return RpkiCacheServerFact(caches, problems).available(SOURCE)


def problem(name: str, kind: FactProblemKind) -> RpkiCacheServerProblem:
    """Build one cache whose host configuration is unavailable."""
    return RpkiCacheServerProblem(name, RpkiCacheServerFact.unavailable(kind, SOURCE))


HOST = RpkiCacheServer("C1", "192.0.2.10", "default", 323, "tcp")
CONFIGURED = cache_fact(HOST)
ABSENT = cache_fact(RpkiCacheServer("C1", None, None, None, "tcp"))
CONFIGURED_EXPOSURE = ConfigurationAssessment(CONFIGURED, CACHE_SERVER, ConfigurationState.CONFIGURED)
ABSENT_EXPOSURE = ConfigurationAssessment(ABSENT, CACHE_SERVER, ConfigurationState.NOT_CONFIGURED)
ASSESSMENTS = ((SYNC_ID, _assess_cve_2026_121291), (READ_ID, _assess_cve_2026_121292))


def test_advisory_metadata() -> None:
    """Verify advisory identifiers, tracker URL, and approved revision date."""
    assert ADVISORY.sa_number == "0222"
    assert ADVISORY.title == "Security Advisory 0222"
    assert ADVISORY.url == "https://www.arista.com/en/support/advisories-notices/security-advisory/25044-security-advisory-0222"
    assert ADVISORY.last_updated == date(2026, 11, 10)
    assert tuple((item.id, item.severity) for item in ADVISORY.vulnerabilities) == (
        (SYNC_ID, _AdvisoryVulnerabilitySeverity.HIGH),
        (READ_ID, _AdvisoryVulnerabilitySeverity.HIGH),
    )


def test_sa222_commands_are_derived_from_required_facts() -> None:
    """Collect only the persistent RPKI cache configuration; the EOS version comes from device metadata."""
    assert [(command.command, command.ofmt) for command in SA222.commands if isinstance(command, AntaCommand)] == [(COMMAND, "text")]
    assert len(SA222.commands) == 1


def test_cve_2026_121291_version_boundaries() -> None:
    """Start at 4.35.0F, end at each named fix, and keep the 4.37 train without a published fix affected."""
    assert_version_statuses(
        CVE_2026_121291_AFFECTED_VERSION_MATRIX,
        (
            ("4.38.0F", AffectedStatus.NOT_AFFECTED),
            ("4.37.99M", AffectedStatus.AFFECTED),
            ("4.37.1F", AffectedStatus.AFFECTED),
            ("4.37.0.1F", AffectedStatus.AFFECTED),
            ("4.37.0F", AffectedStatus.AFFECTED),
            ("4.36.0F", AffectedStatus.AFFECTED),
            ("4.36.0.1F", AffectedStatus.AFFECTED),
            ("4.36.2F", AffectedStatus.AFFECTED),
            ("4.36.2.1F", AffectedStatus.AFFECTED),
            ("4.36.3M", AffectedStatus.NOT_AFFECTED),
            ("4.35.0F", AffectedStatus.AFFECTED),
            ("4.35.6M", AffectedStatus.AFFECTED),
            ("4.35.6.1M", AffectedStatus.AFFECTED),
            ("4.35.7M", AffectedStatus.NOT_AFFECTED),
            ("4.34.99M", AffectedStatus.NOT_AFFECTED),
            ("4.34.8M", AffectedStatus.NOT_AFFECTED),
            ("4.34.0F", AffectedStatus.NOT_AFFECTED),
            ("4.33.10M", AffectedStatus.NOT_AFFECTED),
            ("4.32.0F", AffectedStatus.NOT_AFFECTED),
            ("4.24.0F", AffectedStatus.NOT_AFFECTED),
            ("4.23.0F", AffectedStatus.NOT_AFFECTED),
        ),
    )


def test_cve_2026_121292_version_boundaries() -> None:
    """Start at 4.24.0F, include every older train, end at each named fix, and keep the 4.37 train affected."""
    assert_version_statuses(
        CVE_2026_121292_AFFECTED_VERSION_MATRIX,
        (
            ("4.38.0F", AffectedStatus.NOT_AFFECTED),
            ("4.37.99M", AffectedStatus.AFFECTED),
            ("4.37.1F", AffectedStatus.AFFECTED),
            ("4.37.0.1F", AffectedStatus.AFFECTED),
            ("4.37.0F", AffectedStatus.AFFECTED),
            ("4.36.0F", AffectedStatus.AFFECTED),
            ("4.36.2F", AffectedStatus.AFFECTED),
            ("4.36.2.1F", AffectedStatus.AFFECTED),
            ("4.36.3M", AffectedStatus.NOT_AFFECTED),
            ("4.35.0F", AffectedStatus.AFFECTED),
            ("4.35.6M", AffectedStatus.AFFECTED),
            ("4.35.6.1M", AffectedStatus.AFFECTED),
            ("4.35.7M", AffectedStatus.NOT_AFFECTED),
            ("4.34.0F", AffectedStatus.AFFECTED),
            ("4.34.8M", AffectedStatus.AFFECTED),
            ("4.34.8.1M", AffectedStatus.AFFECTED),
            ("4.34.9M", AffectedStatus.NOT_AFFECTED),
            ("4.33.0F", AffectedStatus.AFFECTED),
            ("4.33.10M", AffectedStatus.AFFECTED),
            ("4.33.10.1M", AffectedStatus.AFFECTED),
            ("4.33.11M", AffectedStatus.NOT_AFFECTED),
            ("4.32.0F", AffectedStatus.AFFECTED),
            ("4.32.99M", AffectedStatus.AFFECTED),
            ("4.31.10M", AffectedStatus.AFFECTED),
            ("4.30.0F", AffectedStatus.AFFECTED),
            ("4.25.0F", AffectedStatus.AFFECTED),
            ("4.24.0F", AffectedStatus.AFFECTED),
            ("4.24.0.1F", AffectedStatus.AFFECTED),
            ("4.23.99M", AffectedStatus.NOT_AFFECTED),
            ("4.23.0F", AffectedStatus.NOT_AFFECTED),
            ("4.22.1F", AffectedStatus.NOT_AFFECTED),
        ),
    )


@pytest.mark.parametrize(("vulnerability_id", "fixed_releases"), [(SYNC_ID, SYNC_FIXED_RELEASES), (READ_ID, READ_FIXED_RELEASES)])
def test_affected_with_configured_cache_server(vulnerability_id: str, fixed_releases: tuple[FixedRelease, ...]) -> None:
    """An affected release with a configured cache server is affected and remediated by that vulnerability's own fixed releases."""
    assess = dict(ASSESSMENTS)[vulnerability_id]
    finding = assess(eos_version_fact("4.36.2F"), CONFIGURED)
    assert isinstance(finding, AffectedResult)
    assert finding.vulnerability_id == vulnerability_id
    assert finding.conditions == (CONFIGURED_EXPOSURE,)
    assert finding.context[0].relation is VersionRelation.AFFECTED
    assert finding.remediation == remediation("4.36.2F", fixed_releases)


def test_one_vulnerability_affected_and_other_outside_scope() -> None:
    """The 4.34 train is outside the synchronization issue but within the out-of-bounds read issue."""
    sync = _assess_cve_2026_121291(eos_version_fact("4.34.8M"), CONFIGURED)
    read = _assess_cve_2026_121292(eos_version_fact("4.34.8M"), CONFIGURED)
    assert isinstance(sync, NotAffectedResult)
    assert sync.vulnerability_id == SYNC_ID
    assert isinstance(sync.decisive[0], EosReleaseAssessment)
    assert sync.decisive[0].relation is VersionRelation.OUTSIDE_SCOPE
    assert isinstance(read, AffectedResult)
    assert read.vulnerability_id == READ_ID


@pytest.mark.parametrize(("vulnerability_id", "assess"), ASSESSMENTS)
def test_absent_cache_server_short_circuits_unavailable_version(vulnerability_id: str, assess: Assessment) -> None:
    """No configured cache server establishes absence without requiring the EOS version."""
    missing_version = EosVersionFact.unavailable(FactProblemKind.MISSING, SOURCE)
    assert assess(missing_version, ABSENT) == NotAffectedResult(vulnerability_id=vulnerability_id, decisive=(ABSENT_EXPOSURE,))


@pytest.mark.parametrize(("vulnerability_id", "assess"), ASSESSMENTS)
def test_validated_host_survives_other_cache_problems(vulnerability_id: str, assess: Assessment) -> None:
    """Only the caches with a validated host are the witness; problems with other caches do not prevent the affected result."""
    unknown = RpkiCacheServer("NOHOST", None, None, None, "tcp")
    finding = assess(eos_version_fact("4.35.1F"), cache_fact(unknown, HOST, problems=(problem("BAD", FactProblemKind.MISSING),)))
    assert isinstance(finding, AffectedResult)
    assert finding.vulnerability_id == vulnerability_id
    assert finding.conditions == (CONFIGURED_EXPOSURE,)


@pytest.mark.parametrize(("vulnerability_id", "assess"), ASSESSMENTS)
def test_cache_problems_without_witness_prevent_absence(vulnerability_id: str, assess: Assessment) -> None:
    """Without a validated host, every distinct cache problem kind is reported once, independently of cache order."""
    missing = problem("A", FactProblemKind.MISSING)
    malformed = problem("B", FactProblemKind.MALFORMED)
    expected = ErrorResult(vulnerability_id=vulnerability_id, problems=(missing.fact, malformed.fact))
    for problems in ((missing, malformed, problem("C", FactProblemKind.MISSING)), (malformed, missing)):
        assert assess(eos_version_fact("4.35.1F"), cache_fact(*ABSENT.value.caches, problems=problems)) == expected


@pytest.mark.parametrize(("vulnerability_id", "assess"), ASSESSMENTS)
def test_outside_scope_release_short_circuits_unavailable_configuration(vulnerability_id: str, assess: Assessment) -> None:
    """A fixed release establishes absence without requiring the cache configuration."""
    malformed = RpkiCacheServerFact.unavailable(FactProblemKind.MALFORMED, SOURCE)
    finding = assess(eos_version_fact("4.36.3M"), malformed)
    assert isinstance(finding, NotAffectedResult)
    assert finding.vulnerability_id == vulnerability_id


@pytest.mark.parametrize(("vulnerability_id", "assess"), ASSESSMENTS)
def test_errors_aggregate_every_unavailable_required_fact(vulnerability_id: str, assess: Assessment) -> None:
    """Report the EOS version and cache configuration together, and each alone when only it is unavailable."""
    missing_version = EosVersionFact.unavailable(FactProblemKind.MISSING, SOURCE)
    failed = RpkiCacheServerFact.unavailable(FactProblemKind.COLLECTION_FAILED, SOURCE)
    assert assess(missing_version, failed) == ErrorResult(vulnerability_id=vulnerability_id, problems=(missing_version, failed))
    assert assess(missing_version, CONFIGURED) == ErrorResult(vulnerability_id=vulnerability_id, problems=(missing_version,))
    assert assess(eos_version_fact("4.35.6M"), failed) == ErrorResult(vulnerability_id=vulnerability_id, problems=(failed,))
