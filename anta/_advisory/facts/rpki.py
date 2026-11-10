# Copyright (c) 2026 Arista Networks, Inc.
# Use of this source code is governed by the Apache License 2.0
# that can be found in the LICENSE file.
"""Persistent BGP RPKI cache server configuration."""

from __future__ import annotations

import re
from collections import Counter
from dataclasses import dataclass
from typing import TYPE_CHECKING, ClassVar

from anta._advisory.facts.models import (
    CommandsFactDefinition,
    Fact,
    FactProblemKind,
    FactSource,
    FactSourceKind,
    UnavailableFact,
)
from anta._advisory.optional_commands import OptionalAntaCommand, is_unsupported_optional_command

if TYPE_CHECKING:
    from anta.models import AntaCommand

RPKI_CACHE_CONFIG_COMMAND = OptionalAntaCommand(command=r"show running-config all section ^\s+rpki\scache\s", ofmt="text", defer_errors=True)
_INDENT = 3
_CACHE_SETTING_LEVEL = 2
_ROUTER_BGP = re.compile(r"router bgp \S+")
_CACHE = re.compile(r"rpki cache (?P<name>\S+)")
_HOST = re.compile(r"host (?P<host>\S+)(?: vrf (?P<vrf>\S+))?(?: port (?P<port>\d+))?")
_TRANSPORT = re.compile(r"transport (?P<transport>\S+)")


@dataclass(frozen=True, slots=True)
class RpkiCacheServer:
    """One configured RPKI cache and its configured host, if any.

    ``host`` is ``None`` when the cache explicitly renders ``no host``. The VRF and port are retained as rendered; they are not
    validated against configured VRFs or reachability.
    """

    name: str
    host: str | None
    vrf: str | None = None
    port: int | None = None
    transport: str | None = None


@dataclass(frozen=True, slots=True)
class RpkiCacheServerProblem:
    """One RPKI cache whose host configuration cannot be interpreted."""

    name: str
    fact: UnavailableFact[RpkiCacheServerFact]


@dataclass(slots=True)
class _Cache:
    """Statements collected for one cache before validation."""

    name: str
    hosts: list[str]
    transport: str | None = None


def _child(cache: _Cache, text: str) -> None:
    """Record the host and transport statements of one cache; other settings are not interpreted."""
    if text == "no host" or text.split(maxsplit=1)[0] == "host":
        cache.hosts.append(text)
    elif (transport := _TRANSPORT.fullmatch(text)) is not None:
        cache.transport = transport["transport"]


def _caches(config: str) -> list[_Cache] | None:
    """Parse the cache hierarchy rendered below ``router bgp``; return None for any unexpected structure.

    Each line may be at most one level deeper than the previous one, so every cache has a ``router bgp`` parent.
    """
    caches: list[_Cache] = []
    previous = -1
    for raw in config.splitlines():
        text = raw.strip()
        if not text or text == "!":
            continue
        indent = raw[: len(raw) - len(raw.lstrip())]
        if "\t" in indent or len(indent) % _INDENT or len(indent) // _INDENT > previous + 1:
            return None
        level = previous = len(indent) // _INDENT
        if level == 0:
            if _ROUTER_BGP.fullmatch(text) is None:
                return None
        elif level == 1:
            if (match := _CACHE.fullmatch(text)) is None:
                return None
            caches.append(_Cache(match["name"], []))
        elif level == _CACHE_SETTING_LEVEL:
            _child(caches[-1], text)
    return caches


def _host(cache: _Cache, text: str) -> RpkiCacheServer | None:
    """Interpret one host statement of a cache; return None when it is malformed."""
    if text == "no host":
        return RpkiCacheServer(cache.name, None, transport=cache.transport)
    if (host := _HOST.fullmatch(text)) is None:
        return None
    port = int(host["port"]) if host["port"] is not None else None
    return RpkiCacheServer(cache.name, host["host"], host["vrf"], port, cache.transport)


def _cache_server(cache: _Cache, source: FactSource) -> RpkiCacheServer | UnavailableFact[RpkiCacheServerFact]:
    """Validate the complete host observation of one uniquely named cache."""
    if not cache.hosts:
        return RpkiCacheServerFact.unavailable(FactProblemKind.MISSING, source)
    servers = [_host(cache, text) for text in cache.hosts]
    if any(server is None for server in servers):
        return RpkiCacheServerFact.unavailable(FactProblemKind.MALFORMED, source)
    distinct = tuple(dict.fromkeys(server for server in servers if server is not None))
    if len(servers) > 1:
        if len(distinct) == 1:
            return RpkiCacheServerFact.unavailable(FactProblemKind.MALFORMED, source)
        observations = tuple(RpkiCacheServerFact(caches=(server,)) for server in distinct)
        return RpkiCacheServerFact.unavailable(FactProblemKind.CONTRADICTORY, source, observations=observations)
    return distinct[0]


@dataclass(frozen=True, slots=True)
class RpkiCacheServerFact(CommandsFactDefinition["RpkiCacheServerFact"]):
    """Persistently configured BGP RPKI caches and their hosts, independent of RPKI session state.

    Each cache is validated independently: a cache without a host statement, with a malformed or repeated one, or sharing its name
    with another cache is retained in ``problems`` instead of ``caches``. Availability therefore does not establish that every cache
    was interpreted, and classifying caches as an exposure is left to the advisory.
    """

    key: ClassVar[str] = "configuration.rpki.cache_server"
    label: ClassVar[str] = "RPKI cache server configuration"
    commands: ClassVar[tuple[AntaCommand, ...]] = (RPKI_CACHE_CONFIG_COMMAND,)
    caches: tuple[RpkiCacheServer, ...] = ()
    problems: tuple[RpkiCacheServerProblem, ...] = ()

    @classmethod
    def parse(cls, commands: tuple[AntaCommand, ...]) -> Fact[RpkiCacheServerFact]:
        """Normalize every configured cache; each must render exactly one host or ``no host`` statement."""
        (command,) = commands
        source = FactSource(command.command, FactSourceKind.COMMAND)
        if command.error:
            problem = FactProblemKind.UNSUPPORTED if is_unsupported_optional_command(command) else FactProblemKind.COLLECTION_FAILED
            return cls.unavailable(problem, source)
        if command.output is None:
            return cls.unavailable(FactProblemKind.MISSING, source)
        if not isinstance(command.output, str):
            return cls.unavailable(FactProblemKind.MALFORMED, source)
        parsed = _caches(command.output)
        if parsed is None:
            return cls.unavailable(FactProblemKind.MALFORMED, source)
        sections = Counter(cache.name for cache in parsed)
        caches: list[RpkiCacheServer] = []
        problems: dict[str, RpkiCacheServerProblem] = {}
        for cache in parsed:
            server = cls.unavailable(FactProblemKind.MALFORMED, source) if sections[cache.name] > 1 else _cache_server(cache, source)
            if isinstance(server, UnavailableFact):
                problems.setdefault(cache.name, RpkiCacheServerProblem(cache.name, server))
            else:
                caches.append(server)
        return cls(tuple(caches), tuple(problems.values())).available(source)
