# Copyright (c) 2026 Arista Networks, Inc.
# Use of this source code is governed by the Apache License 2.0
# that can be found in the LICENSE file.
"""Persistent BGP RPKI cache server configuration, independent of RPKI session state."""

from __future__ import annotations

import pytest

from anta._advisory.facts.models import AvailableFact, Fact, FactProblemKind, UnavailableFact
from anta._advisory.facts.rpki import RpkiCacheServer, RpkiCacheServerFact
from anta._advisory.optional_commands import OptionalAntaCommand
from tests.units.anta_tests.advisories import OfflineAntaDevice

COMMAND = r"show running-config all section ^\s+rpki\scache\s"

# Captured from EOS 4.36.0.1F; 4.31.10M, 4.34.1F, and 4.35.1F render the same output. Every session was down or idle: the hosts are
# documentation addresses, CTLS has no SSL profile, and CUNDEFVRF uses a VRF that is not configured.
CACHES_CONFIG = """router bgp 65000
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
   rpki cache CFQDN
      host rpki.example.invalid vrf default port 323
      preference 5
      no refresh-interval
      no retry-interval
      no expire-interval
      no local-interface
      no roa table
      !
      transport tcp
         no tcp keepalive
   rpki cache CINVRF
      host 192.0.2.14 vrf default port 323
      preference 5
      no refresh-interval
      no retry-interval
      no expire-interval
      no local-interface
      no roa table
      !
      transport tcp
         no tcp keepalive
   rpki cache CTLS
      host 192.0.2.12 vrf default port 324
      preference 5
      no refresh-interval
      no retry-interval
      no expire-interval
      no local-interface
      no roa table
      !
      transport tls
         no tcp keepalive
         no ssl profile
   rpki cache CUNDEFVRF
      host 192.0.2.13 vrf SA222UNDEF port 323
      preference 5
      no refresh-interval
      no retry-interval
      no expire-interval
      no local-interface
      no roa table
      !
      transport tcp
         no tcp keepalive
   rpki cache CVRF
      host 192.0.2.11 vrf SA222 port 323
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
# Captured from EOS 4.37.0F, which adds the ASPA setting, with one cache that has no host.
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
CACHES = (
    RpkiCacheServer("C4", "192.0.2.10", "default", 323, "tcp"),
    RpkiCacheServer("C6", "2001:db8::10", "default", 3323, "tcp"),
    RpkiCacheServer("CFQDN", "rpki.example.invalid", "default", 323, "tcp"),
    RpkiCacheServer("CINVRF", "192.0.2.14", "default", 323, "tcp"),
    RpkiCacheServer("CTLS", "192.0.2.12", "default", 324, "tls"),
    RpkiCacheServer("CUNDEFVRF", "192.0.2.13", "SA222UNDEF", 323, "tcp"),
    RpkiCacheServer("CVRF", "192.0.2.11", "SA222", 323, "tcp"),
    RpkiCacheServer("NOHOST", None, None, None, "tcp"),
)


def derive(output: str | dict[str, object] | None, errors: list[str] | None = None) -> Fact[RpkiCacheServerFact]:
    """Derive the fact from one simulated command collection."""
    command = RpkiCacheServerFact.commands[0].model_copy()
    command.output = output
    command.errors = errors or []
    return RpkiCacheServerFact.derive(OfflineAntaDevice("unit-test"), (command,))


def test_command_declaration() -> None:
    """Collect the persistent cache configuration with explicit defaults and handle every command error in the fact."""
    (command,) = RpkiCacheServerFact.commands
    assert isinstance(command, OptionalAntaCommand)
    assert (command.command, command.ofmt, command.defer_errors) == (COMMAND, "text", True)


def test_configured_caches_retain_identity_host_vrf_port_and_transport() -> None:
    """IPv4, IPv6, name, VRF, and TLS hosts are retained regardless of session state; a cache without a host is retained."""
    fact = derive(CACHES_CONFIG)
    assert isinstance(fact, AvailableFact)
    assert fact.value.caches == CACHES
    assert fact.value.problems == ()
    assert fact.source.name == COMMAND


@pytest.mark.parametrize(
    ("config", "caches"),
    [
        pytest.param("", (), id="no-bgp-or-no-cache"),
        pytest.param(NO_HOST_CONFIG, (RpkiCacheServer("NOHOST", None, None, None, "tcp"),), id="4.37-cache-without-host"),
        pytest.param(
            CACHES_CONFIG.split("   rpki cache C6\n", maxsplit=1)[0].replace("host 192.0.2.10 vrf default port 323", "no host"),
            (RpkiCacheServer("C4", None, None, None, "tcp"),),
            id="host-removed",
        ),
    ],
)
def test_caches_without_host_are_completely_observed(config: str, caches: tuple[RpkiCacheServer, ...]) -> None:
    """Empty output and caches rendering ``no host`` are complete observations without any host."""
    fact = derive(config)
    assert isinstance(fact, AvailableFact)
    assert fact.value.caches == caches
    assert fact.value.problems == ()


def test_4_37_aspa_setting_is_ignored() -> None:
    """The additional ASPA setting rendered by EOS 4.37 does not change a configured host."""
    fact = derive(NO_HOST_CONFIG.replace("      no host\n", "      host 192.0.2.10 vrf default port 323\n"))
    assert isinstance(fact, AvailableFact)
    assert fact.value.caches == (RpkiCacheServer("NOHOST", "192.0.2.10", "default", 323, "tcp"),)


def test_host_without_rendered_vrf_or_port_is_configured() -> None:
    """A host statement without the default VRF and port still configures a cache server."""
    fact = derive("router bgp 65000\n   rpki cache C1\n      host 192.0.2.10\n      transport tcp\n")
    assert isinstance(fact, AvailableFact)
    assert fact.value.caches == (RpkiCacheServer("C1", "192.0.2.10", None, None, "tcp"),)


GOOD = "   rpki cache GOOD\n      host 192.0.2.10 vrf default port 323\n      transport tcp\n"
GOOD_SERVER = RpkiCacheServer("GOOD", "192.0.2.10", "default", 323, "tcp")


@pytest.mark.parametrize(
    ("bad", "problem"),
    [
        pytest.param("   rpki cache BAD\n      transport tcp\n", FactProblemKind.MISSING, id="without-host-statement"),
        pytest.param("   rpki cache BAD\n      host\n      transport tcp\n", FactProblemKind.MALFORMED, id="host-without-address"),
        pytest.param("   rpki cache BAD\n      host 192.0.2.11 vrf\n", FactProblemKind.MALFORMED, id="host-with-truncated-vrf"),
        pytest.param("   rpki cache BAD\n      host 192.0.2.11\n      host 192.0.2.11\n", FactProblemKind.MALFORMED, id="repeated-host"),
        pytest.param("   rpki cache BAD\n      no host\n      host 192.0.2.11\n", FactProblemKind.CONTRADICTORY, id="host-and-no-host"),
        pytest.param("   rpki cache BAD\n      host 192.0.2.11\n      host 192.0.2.12\n", FactProblemKind.CONTRADICTORY, id="two-hosts"),
    ],
)
@pytest.mark.parametrize("good_first", [True, False], ids=["good-first", "bad-first"])
def test_cache_problem_retains_sibling_caches(bad: str, problem: FactProblemKind, *, good_first: bool) -> None:
    """Incomplete host evidence for one cache is retained by name without discarding a separately identified valid cache."""
    sections = (GOOD, bad) if good_first else (bad, GOOD)
    fact = derive("router bgp 65000\n" + "".join(sections))
    assert isinstance(fact, AvailableFact)
    assert fact.value.caches == (GOOD_SERVER,)
    ((name, unavailable),) = ((item.name, item.fact) for item in fact.value.problems)
    assert name == "BAD"
    assert unavailable.problem is problem
    assert unavailable.source.name == COMMAND


def test_contradictory_cache_retains_each_observation() -> None:
    """Contradictory host statements are retained as distinct observations of the same cache, never as a configured host."""
    fact = derive("router bgp 65000\n   rpki cache C1\n      no host\n      host 192.0.2.10 vrf default port 323\n      transport tcp\n")
    assert isinstance(fact, AvailableFact)
    assert fact.value.caches == ()
    (problem,) = fact.value.problems
    assert problem.fact.problem is FactProblemKind.CONTRADICTORY
    assert problem.fact.observations == (
        RpkiCacheServerFact((RpkiCacheServer("C1", None, None, None, "tcp"),)),
        RpkiCacheServerFact((RpkiCacheServer("C1", "192.0.2.10", "default", 323, "tcp"),)),
    )


def test_duplicate_cache_name_is_one_problem() -> None:
    """Sections sharing a cache name are not separately identified, so neither provides a host; other caches are retained."""
    fact = derive("router bgp 65000\n   rpki cache C1\n      no host\n   rpki cache C1\n      host 192.0.2.10\n" + GOOD)
    assert isinstance(fact, AvailableFact)
    assert fact.value.caches == (GOOD_SERVER,)
    assert [(item.name, item.fact.problem) for item in fact.value.problems] == [("C1", FactProblemKind.MALFORMED)]


@pytest.mark.parametrize(
    ("output", "errors", "problem"),
    [
        pytest.param(None, None, FactProblemKind.MISSING, id="missing-output"),
        pytest.param({"cmds": {}}, None, FactProblemKind.MALFORMED, id="structured-output"),
        pytest.param("router rip\n   rpki cache C1\n      no host\n", None, FactProblemKind.MALFORMED, id="other-root"),
        pytest.param("   rpki cache C1\n      no host\n", None, FactProblemKind.MALFORMED, id="cache-without-router-bgp"),
        pytest.param("router bgp 65000\n   vrf BLUE\n      rpki cache C1\n         no host\n", None, FactProblemKind.MALFORMED, id="vrf-scoped-cache"),
        pytest.param("router bgp 65000\n   rpki cache\n", None, FactProblemKind.MALFORMED, id="cache-without-name"),
        pytest.param("router bgp 65000\n\trpki cache C1\n", None, FactProblemKind.MALFORMED, id="tab-indentation"),
        pytest.param("router bgp 65000\n  rpki cache C1\n", None, FactProblemKind.MALFORMED, id="uneven-indentation"),
        pytest.param("router bgp 65000\n      host 192.0.2.10\n", None, FactProblemKind.MALFORMED, id="skipped-level"),
        pytest.param("router bgp 65000\n" + GOOD + "   rpki cache\n", None, FactProblemKind.MALFORMED, id="malformed-boundary-after-valid-cache"),
        pytest.param(None, ["Connection timed out"], FactProblemKind.COLLECTION_FAILED, id="collection-failed"),
        pytest.param(None, ["This command is not supported on this hardware platform"], FactProblemKind.UNSUPPORTED, id="unsupported"),
    ],
)
def test_unavailable_configuration(output: str | dict[str, object] | None, errors: list[str] | None, problem: FactProblemKind) -> None:
    """Missing, failed, or unsupported output and malformed cache boundaries never establish absence or a host, and keep their source."""
    fact = derive(output, errors)
    assert isinstance(fact, UnavailableFact)
    assert fact.problem is problem
    assert fact.source.name == COMMAND
