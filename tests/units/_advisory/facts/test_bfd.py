# Copyright (c) 2026 Arista Networks, Inc.
# Use of this source code is governed by the Apache License 2.0
# that can be found in the LICENSE file.
"""Tests for facts normalized from the persistent router BFD configuration."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

import pytest

from anta._advisory.facts.bfd import SbfdInitiatorRoundTripDelayFact, SbfdReflectorProxyFact
from anta._advisory.facts.models import AvailableFact, FactProblemKind, FeatureState, UnavailableFact
from tests.units.anta_tests.advisories import OfflineAntaDevice

if TYPE_CHECKING:
    from anta.models import AntaCommand

COMMAND = "show running-config section sbfd"
# Captured from vEOS-lab 4.36.2F and DCS-7280SR2-48YC6 4.32.0F.
REFLECTOR = "router bfd\n   sbfd\n      reflector local-discriminator 10.0.0.1\n"
REFLECTOR_PROXY = "router bfd\n   sbfd\n      reflector local-discriminator 10.0.0.1 proxy\n"
REFLECTOR_PROXY_U32 = "router bfd\n   sbfd\n      reflector local-discriminator 1000 proxy\n"
ROUND_TRIP_DELAY = "router bfd\n   sbfd\n      initiator measurement delay round-trip\n"
BOTH = "router bfd\n   sbfd\n      initiator measurement delay round-trip\n      reflector local-discriminator 10.0.0.1 proxy\n"
ROUND_TRIP_DELAY_WITH_TE_POLICY = (
    "router bfd\n"
    "   sbfd\n"
    "      initiator measurement delay round-trip\n"
    "router traffic-engineering\n"
    "   segment-routing\n"
    "      policy endpoint 10.1.1.1 color 100\n"
    "         sbfd remote-discriminator 10.0.0.9\n"
)
TE_POLICY_ONLY = "router traffic-engineering\n   segment-routing\n      policy endpoint 10.1.1.1 color 100\n         sbfd remote-discriminator 10.0.0.9\n"
# Shape rendered by `show running-config all section sbfd` with only S-BFD defaults.
DEFAULTS_RENDERED = (
    "router bfd\n"
    "   sbfd\n"
    "      no local-interface\n"
    "      initiator interval 300 multiplier 3\n"
    "      no initiator measurement delay round-trip\n"
    "      reflector min-rx 300\n"
    "      no reflector local-discriminator\n"
)


def sbfd_command(definition: type[SbfdReflectorProxyFact | SbfdInitiatorRoundTripDelayFact], output: dict[str, Any] | str | None) -> AntaCommand:
    """Copy the S-BFD configuration command declared by a fact with one response."""
    command = definition.commands[0].model_copy()
    command.output = output
    return command


@pytest.mark.parametrize(
    ("output", "proxy", "discriminator", "round_trip_delay"),
    [
        pytest.param("", FeatureState.DISABLED, None, FeatureState.DISABLED, id="no-bfd-or-sbfd-defaults-only"),
        pytest.param(REFLECTOR, FeatureState.DISABLED, "10.0.0.1", FeatureState.DISABLED, id="reflector-without-proxy"),
        pytest.param(REFLECTOR_PROXY, FeatureState.ENABLED, "10.0.0.1", FeatureState.DISABLED, id="reflector-proxy"),
        pytest.param(REFLECTOR_PROXY_U32, FeatureState.ENABLED, "1000", FeatureState.DISABLED, id="reflector-proxy-u32-discriminator"),
        pytest.param(ROUND_TRIP_DELAY, FeatureState.DISABLED, None, FeatureState.ENABLED, id="initiator-round-trip-delay"),
        pytest.param(BOTH, FeatureState.ENABLED, "10.0.0.1", FeatureState.ENABLED, id="both"),
        pytest.param(ROUND_TRIP_DELAY_WITH_TE_POLICY, FeatureState.DISABLED, None, FeatureState.ENABLED, id="unrelated-te-policy-block"),
        pytest.param(TE_POLICY_ONLY, FeatureState.DISABLED, None, FeatureState.DISABLED, id="te-policy-without-router-bfd"),
        pytest.param(DEFAULTS_RENDERED, FeatureState.DISABLED, None, FeatureState.DISABLED, id="explicit-negations"),
        pytest.param("router bfd\n   shutdown\n   !\n   sbfd\n", FeatureState.DISABLED, None, FeatureState.DISABLED, id="empty-sbfd-mode"),
    ],
)
def test_sbfd_states(output: str, proxy: FeatureState, discriminator: str | None, round_trip_delay: FeatureState) -> None:
    """Each S-BFD setting is observed independently from the same persistent configuration."""
    device = OfflineAntaDevice("unit-test")
    reflector_fact = SbfdReflectorProxyFact.derive(device, (sbfd_command(SbfdReflectorProxyFact, output),))
    delay_fact = SbfdInitiatorRoundTripDelayFact.derive(device, (sbfd_command(SbfdInitiatorRoundTripDelayFact, output),))
    assert isinstance(reflector_fact, AvailableFact)
    assert isinstance(delay_fact, AvailableFact)
    assert reflector_fact.value.state is proxy
    assert reflector_fact.value.local_discriminator == discriminator
    assert delay_fact.value.state is round_trip_delay
    assert reflector_fact.source.name == COMMAND
    assert delay_fact.source.name == COMMAND


@pytest.mark.parametrize(
    ("output", "problem"),
    [
        pytest.param(None, FactProblemKind.MISSING, id="no-output"),
        pytest.param({"output": BOTH}, FactProblemKind.MALFORMED, id="structured-output"),
        pytest.param("   sbfd\n      reflector local-discriminator 10.0.0.1 proxy\n", FactProblemKind.MALFORMED, id="orphan-indented-line"),
        pytest.param(BOTH + BOTH, FactProblemKind.MALFORMED, id="repeated-router-bfd"),
        pytest.param("router bfd\n   sbfd\n   sbfd\n      initiator measurement delay round-trip\n", FactProblemKind.MALFORMED, id="repeated-sbfd"),
        pytest.param("router bfd\n   sbfd\n      initiator measurement delay round-trip\n         nested\n", FactProblemKind.MALFORMED, id="nested-sbfd-child"),
    ],
)
@pytest.mark.parametrize("definition", [SbfdReflectorProxyFact, SbfdInitiatorRoundTripDelayFact])
def test_sbfd_unavailable(
    definition: type[SbfdReflectorProxyFact | SbfdInitiatorRoundTripDelayFact], output: dict[str, Any] | str | None, problem: FactProblemKind
) -> None:
    """Uninterpretable output never becomes an absent S-BFD setting."""
    fact = definition.derive(OfflineAntaDevice("unit-test"), (sbfd_command(definition, output),))
    assert isinstance(fact, UnavailableFact)
    assert fact.problem is problem
    assert fact.source.name == COMMAND


MALFORMED_REFLECTOR = "      reflector local-discriminator 10.0.0.1 relay\n"
UNKNOWN_MEASUREMENT = "      initiator measurement delay one-way\n"
NESTED_UNRELATED = "      local-interface Loopback0\n         nested\n"


@pytest.mark.parametrize(
    ("output", "proxy", "round_trip_delay"),
    [
        pytest.param(
            "router bfd\n   sbfd\n      reflector local-discriminator 10.0.0.1\n      reflector local-discriminator 10.0.0.2 proxy\n",
            FactProblemKind.MALFORMED,
            FeatureState.DISABLED,
            id="repeated-reflector",
        ),
        pytest.param(
            "router bfd\n   sbfd\n      reflector local-discriminator proxy\n",
            FactProblemKind.MALFORMED,
            FeatureState.DISABLED,
            id="reflector-without-discriminator",
        ),
        pytest.param(f"router bfd\n   sbfd\n{MALFORMED_REFLECTOR}", FactProblemKind.MALFORMED, FeatureState.DISABLED, id="unknown-reflector-option"),
        pytest.param(f"router bfd\n   sbfd\n{UNKNOWN_MEASUREMENT}", FeatureState.DISABLED, FactProblemKind.MALFORMED, id="unknown-measurement"),
        pytest.param(
            f"router bfd\n   sbfd\n{UNKNOWN_MEASUREMENT}      reflector local-discriminator 10.0.0.1 proxy\n",
            FeatureState.ENABLED,
            FactProblemKind.MALFORMED,
            id="reflector-proxy-with-unknown-measurement",
        ),
        pytest.param(
            f"router bfd\n   sbfd\n      initiator measurement delay round-trip\n{MALFORMED_REFLECTOR}",
            FactProblemKind.MALFORMED,
            FeatureState.ENABLED,
            id="round-trip-delay-with-malformed-reflector",
        ),
        pytest.param(
            f"router bfd\n   sbfd\n{NESTED_UNRELATED}      reflector local-discriminator 10.0.0.1 proxy\n",
            FeatureState.ENABLED,
            FactProblemKind.MALFORMED,
            id="reflector-proxy-with-unrecognized-nesting",
        ),
        pytest.param(
            f"router bfd\n   sbfd\n{NESTED_UNRELATED}      initiator measurement delay round-trip\n",
            FactProblemKind.MALFORMED,
            FeatureState.ENABLED,
            id="round-trip-delay-with-unrecognized-nesting",
        ),
    ],
)
def test_sbfd_settings_are_parsed_independently(output: str, proxy: FeatureState | FactProblemKind, round_trip_delay: FeatureState | FactProblemKind) -> None:
    """A problem confined to one setting neither hides nor fabricates the other setting from the same output."""
    device = OfflineAntaDevice("unit-test")
    facts = (
        (SbfdReflectorProxyFact.derive(device, (sbfd_command(SbfdReflectorProxyFact, output),)), proxy),
        (SbfdInitiatorRoundTripDelayFact.derive(device, (sbfd_command(SbfdInitiatorRoundTripDelayFact, output),)), round_trip_delay),
    )
    for fact, expected in facts:
        assert fact.source.name == COMMAND
        if isinstance(expected, FactProblemKind):
            assert isinstance(fact, UnavailableFact)
            assert fact.problem is expected
        else:
            assert isinstance(fact, AvailableFact)
            assert fact.value.state is expected


@pytest.mark.parametrize(
    ("errors", "problem"),
    [
        pytest.param(["This command is not supported on this hardware platform"], FactProblemKind.UNSUPPORTED, id="unsupported"),
        pytest.param(["permission denied"], FactProblemKind.COLLECTION_FAILED, id="collection-failed"),
        pytest.param(["This command is not supported on this hardware platform", "permission denied"], FactProblemKind.COLLECTION_FAILED, id="mixed"),
    ],
)
@pytest.mark.parametrize("definition", [SbfdReflectorProxyFact, SbfdInitiatorRoundTripDelayFact])
def test_sbfd_command_errors(definition: type[SbfdReflectorProxyFact | SbfdInitiatorRoundTripDelayFact], errors: list[str], problem: FactProblemKind) -> None:
    """Deferred command errors are retained as precise problems of the declared source."""
    command = sbfd_command(definition, None)
    command.errors = errors
    fact = definition.derive(OfflineAntaDevice("unit-test"), (command,))
    assert isinstance(fact, UnavailableFact)
    assert fact.problem is problem
    assert fact.source.name == COMMAND


@pytest.mark.parametrize("definition", [SbfdReflectorProxyFact, SbfdInitiatorRoundTripDelayFact])
def test_sbfd_requires_declared_command(definition: type[SbfdReflectorProxyFact | SbfdInitiatorRoundTripDelayFact]) -> None:
    """A missing command slice is a collection failure of the declared source."""
    fact = definition.derive(OfflineAntaDevice("unit-test"), ())
    assert isinstance(fact, UnavailableFact)
    assert fact.problem is FactProblemKind.COLLECTION_FAILED
    assert fact.source.name == COMMAND
