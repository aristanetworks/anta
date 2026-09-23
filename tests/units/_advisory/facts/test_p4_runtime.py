# Copyright (c) 2026 Arista Networks, Inc.
# Use of this source code is governed by the Apache License 2.0
# that can be found in the LICENSE file.
"""Unit tests for facts normalized from EOS P4Runtime output."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

import pytest

from anta._advisory.facts.models import AvailableFact, FactProblemKind, FeatureState, UnavailableFact
from anta._advisory.facts.p4_runtime import P4RuntimeAccountingFact, P4RuntimeFact, P4RuntimeMtlsFact
from tests.units.anta_tests.advisories import OfflineAntaDevice

if TYPE_CHECKING:
    from anta.models import AntaCommand


def command(definition: type[P4RuntimeFact | P4RuntimeAccountingFact], output: dict[str, Any] | str | None) -> AntaCommand:
    """Return a copied fact command populated with output."""
    value = definition.commands[0].model_copy()
    value.output = output
    return value


def declared_command(declared: AntaCommand, output: dict[str, Any] | str | None) -> AntaCommand:
    """Return one copied command from a multi-command fact definition."""
    value = declared.model_copy()
    value.output = output
    return value


P4_RUNTIME_DISABLED_WITHOUT_TRANSPORT: tuple[dict[str, object], ...] = (
    {"devices": {}, "enabled": False, "numClients": 0},
    {"authzEnabled": False, "devices": {}, "enabled": False, "lastServiceStartTimeStamp": 0, "numClients": 0},
)


@pytest.mark.parametrize(("enabled", "state"), [(True, FeatureState.ENABLED), (False, FeatureState.DISABLED)])
def test_p4_runtime_states(enabled: bool, state: FeatureState) -> None:
    """Normalize P4Runtime enablement."""
    fact = P4RuntimeFact.derive(OfflineAntaDevice("unit-test"), (command(P4RuntimeFact, {"enabled": enabled}),))

    assert isinstance(fact, AvailableFact)
    assert fact.value.state is state


@pytest.mark.parametrize(("enabled", "state"), [(True, FeatureState.ENABLED), (False, FeatureState.DISABLED)])
def test_p4_runtime_accounting_states(enabled: bool, state: FeatureState) -> None:
    """Normalize P4Runtime request accounting."""
    output = {"enabled": True, "transport": {"accountingRequests": enabled}}
    fact = P4RuntimeAccountingFact.derive(OfflineAntaDevice("unit-test"), (command(P4RuntimeAccountingFact, output),))

    assert isinstance(fact, AvailableFact)
    assert fact.value.state is state


@pytest.mark.parametrize(
    ("p4", "ssl", "state", "source_index"),
    [
        ({"enabled": True, "transport": {"sslProfile": ""}}, {}, FeatureState.DISABLED, 0),
        (
            {"enabled": True, "transport": {"sslProfile": "campus"}},
            {"profileStatus": {"campus": {"trustedCertificates": []}}},
            FeatureState.DISABLED,
            1,
        ),
        (
            {"enabled": True, "transport": {"sslProfile": "campus"}},
            {"profileStatus": {"campus": {"trustedCertificates": ["root-ca.crt"]}}},
            FeatureState.ENABLED,
            1,
        ),
    ],
)
def test_p4_runtime_mtls_states(p4: dict[str, object], ssl: dict[str, object], state: FeatureState, source_index: int) -> None:
    """Normalize no TLS, TLS without trust, and mutual TLS."""
    commands = tuple(declared_command(declared, output) for declared, output in zip(P4RuntimeMtlsFact.commands, (p4, ssl), strict=True))
    fact = P4RuntimeMtlsFact.derive(OfflineAntaDevice("unit-test"), commands)

    assert isinstance(fact, AvailableFact)
    assert fact.value.state is state
    assert fact.source.name == P4RuntimeMtlsFact.commands[source_index].command


@pytest.mark.parametrize(
    ("definition", "output"),
    [
        (P4RuntimeFact, {}),
        (P4RuntimeAccountingFact, {}),
        (P4RuntimeAccountingFact, {"enabled": True}),
        (P4RuntimeAccountingFact, {"enabled": True, "transport": {}}),
    ],
)
def test_p4_runtime_rejects_missing_fields(definition, output: dict[str, object]) -> None:  # noqa: ANN001
    """Reject incomplete P4Runtime output."""
    fact = definition.derive(OfflineAntaDevice("unit-test"), (command(definition, output),))

    assert isinstance(fact, UnavailableFact)
    assert fact.problem is FactProblemKind.MISSING


@pytest.mark.parametrize("output", P4_RUNTIME_DISABLED_WITHOUT_TRANSPORT)
@pytest.mark.parametrize("definition", [P4RuntimeFact, P4RuntimeAccountingFact])
def test_p4_runtime_disabled_without_transport(definition: type[P4RuntimeFact | P4RuntimeAccountingFact], output: dict[str, object]) -> None:
    """Treat a disabled P4Runtime service as absent without requiring transport."""
    fact = definition.derive(OfflineAntaDevice("unit-test"), (command(definition, output),))

    assert isinstance(fact, AvailableFact)
    assert fact.value.state is FeatureState.DISABLED


@pytest.mark.parametrize("definition", [P4RuntimeFact, P4RuntimeAccountingFact])
def test_p4_runtime_unsupported_proves_feature_absence(definition: type[P4RuntimeFact | P4RuntimeAccountingFact]) -> None:
    """Normalize the feature-specific unsupported response as absence."""
    value = command(definition, None)
    value.errors = ["This command is not supported on this hardware platform"]

    fact = definition.derive(OfflineAntaDevice("unit-test"), (value,))

    assert isinstance(fact, AvailableFact)
    assert fact.value.state is FeatureState.UNSUPPORTED
    assert fact.source.name == P4RuntimeMtlsFact.commands[0].command


def test_p4_runtime_mtls_unsupported_p4_proves_feature_absence() -> None:
    """Normalize unsupported P4Runtime as absence without requiring SSL state."""
    p4, ssl = (declared.model_copy() for declared in P4RuntimeMtlsFact.commands)
    p4.output = None
    p4.errors = ["This command is not supported on this hardware platform"]
    ssl.output = None

    fact = P4RuntimeMtlsFact.derive(OfflineAntaDevice("unit-test"), (p4, ssl))

    assert isinstance(fact, AvailableFact)
    assert fact.value.state is FeatureState.UNSUPPORTED


def test_p4_runtime_mtls_requires_supported_ssl_output_for_named_profile() -> None:
    """Keep SSL-profile state unavailable when a named profile cannot be inspected."""
    p4, ssl = (declared.model_copy() for declared in P4RuntimeMtlsFact.commands)
    p4.output = {"enabled": True, "transport": {"sslProfile": "campus"}}
    ssl.output = None
    ssl.errors = ["This command is not supported on this hardware platform"]

    fact = P4RuntimeMtlsFact.derive(OfflineAntaDevice("unit-test"), (p4, ssl))

    assert isinstance(fact, UnavailableFact)
    assert fact.problem is FactProblemKind.UNSUPPORTED
    assert fact.source.name == P4RuntimeMtlsFact.commands[1].command


def test_p4_runtime_mtls_ignores_unsupported_ssl_without_named_profile() -> None:
    """Do not require SSL evidence after absent profile configuration proves mTLS disabled."""
    p4, ssl = (declared.model_copy() for declared in P4RuntimeMtlsFact.commands)
    p4.output = {"enabled": True, "transport": {"sslProfile": ""}}
    ssl.output = None
    ssl.errors = ["This command is not supported on this hardware platform"]

    fact = P4RuntimeMtlsFact.derive(OfflineAntaDevice("unit-test"), (p4, ssl))

    assert isinstance(fact, AvailableFact)
    assert fact.value.state is FeatureState.DISABLED
    assert fact.source.name == P4RuntimeMtlsFact.commands[0].command


@pytest.mark.parametrize("output", P4_RUNTIME_DISABLED_WITHOUT_TRANSPORT)
def test_p4_runtime_mtls_disabled_without_transport(output: dict[str, object]) -> None:
    """Treat a disabled P4Runtime service as mTLS-absent without requiring SSL-profile data."""
    p4, ssl = (declared.model_copy() for declared in P4RuntimeMtlsFact.commands)
    p4.output = output
    ssl.output = None
    ssl.errors = ["This command is not supported on this hardware platform"]

    fact = P4RuntimeMtlsFact.derive(OfflineAntaDevice("unit-test"), (p4, ssl))

    assert isinstance(fact, AvailableFact)
    assert fact.value.state is FeatureState.DISABLED
    assert fact.source.name == P4RuntimeMtlsFact.commands[0].command


def test_p4_runtime_mtls_rejects_missing_transport_when_enabled() -> None:
    """Keep mTLS unavailable when an enabled service omits transport."""
    p4, ssl = (declared.model_copy() for declared in P4RuntimeMtlsFact.commands)
    p4.output = {"enabled": True}
    ssl.output = {}

    fact = P4RuntimeMtlsFact.derive(OfflineAntaDevice("unit-test"), (p4, ssl))

    assert isinstance(fact, UnavailableFact)
    assert fact.problem is FactProblemKind.MISSING
    assert fact.source.name == P4RuntimeMtlsFact.commands[0].command
