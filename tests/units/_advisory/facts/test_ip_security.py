# Copyright (c) 2026 Arista Networks, Inc.
# Use of this source code is governed by the Apache License 2.0
# that can be found in the LICENSE file.
"""Tests for controller presence and any configured IPsec anti-replay policy."""

from __future__ import annotations

from typing import TYPE_CHECKING, cast

import pytest

from anta._advisory.facts.ip_security import IpsecKeyControllerFact, IpsecSaAntiReplayFact
from anta._advisory.facts.models import AvailableFact, FactProblemKind, FeatureState, UnavailableFact
from tests.units.anta_tests.advisories import OfflineAntaDevice

if TYPE_CHECKING:
    from anta.models import AntaCommand

CONTROLLER = {
    "keyController": {
        "dhGroup": "modp4096",
        "encryptAlgo": "unknownEncr",
        "hashAlgo": "unknownIntegrity",
        "firstKeyAddTime": 0.0,
        "firstDhKeyAddTime": 1794304414,
        "lastKeyUptime": 0,
        "rekeyTime": 0,
    }
}
SA_POLICY = {
    "espAes": "aes256",
    "espSha": "sha256",
    "pfsGroup": "modp2048",
    "saLifetime": 3600,
    "saLifetimeUnit": "hours",
    "replayWindowSize": 16384,
    "packetLimit": 4000000000,
    "byteLimit": 6442450944000,
    "cryptoSuites": [],
}


def command(definition: type[IpsecKeyControllerFact | IpsecSaAntiReplayFact], output: object) -> AntaCommand:
    """Populate a copied declared command, permitting malformed payload tests."""
    value = definition.commands[0].model_copy()
    value.output = cast("dict[str, object] | str | None", output)
    return value


@pytest.mark.parametrize(
    "output",
    [CONTROLLER, {"keyController": {**CONTROLLER["keyController"], "encryptAlgo": "aes256", "hashAlgo": "sha256"}}, {"keyController": {"dhGroup": "modp4096"}}],
)
def test_configured_controller_without_keys_is_enabled(output: dict[str, object]) -> None:
    """Presence does not require a profile name, known algorithms, or generated keys."""
    fact = IpsecKeyControllerFact.derive(OfflineAntaDevice("test"), (command(IpsecKeyControllerFact, output),))
    assert isinstance(fact, AvailableFact)
    assert fact.value.state is FeatureState.ENABLED


def test_empty_controller_root_is_unconfigured() -> None:
    """Use the captured unconfigured response."""
    fact = IpsecKeyControllerFact.derive(OfflineAntaDevice("test"), (command(IpsecKeyControllerFact, {}),))
    assert isinstance(fact, AvailableFact)
    assert fact.value.state is FeatureState.DISABLED


@pytest.mark.parametrize(
    ("output", "problem"),
    [
        ({"other": {}}, FactProblemKind.MISSING),
        ({"keyController": {}}, FactProblemKind.MISSING),
        ({"keyController": None}, FactProblemKind.MALFORMED),
        ({"keyController": []}, FactProblemKind.MALFORMED),
    ],
)
def test_controller_rejects_incomplete_shape(output: dict[str, object], problem: FactProblemKind) -> None:
    """Malformed roots are not absence."""
    fact = IpsecKeyControllerFact.derive(OfflineAntaDevice("test"), (command(IpsecKeyControllerFact, output),))
    assert isinstance(fact, UnavailableFact)
    assert fact.problem is problem


@pytest.mark.parametrize(
    ("policies", "state"),
    [
        ({}, FeatureState.DISABLED),
        ({"dynamic-sa": SA_POLICY}, FeatureState.ENABLED),
        ({"BLAH": {**SA_POLICY, "replayWindowSize": 0}}, FeatureState.DISABLED),
        ({"dynamic-sa": SA_POLICY, "BLAH": {**SA_POLICY, "replayWindowSize": 0}}, FeatureState.ENABLED),
        ({"BLAH": {**SA_POLICY, "replayWindowSize": 0}, "dynamic-sa": SA_POLICY}, FeatureState.ENABLED),
        ({"tiny": {"replayWindowSize": 1}}, FeatureState.ENABLED),
    ],
)
def test_any_policy_with_positive_window(policies: dict[str, object], state: FeatureState) -> None:
    """Policy names and selection do not narrow the deliberate any-policy observation."""
    fact = IpsecSaAntiReplayFact.derive(OfflineAntaDevice("test"), (command(IpsecSaAntiReplayFact, {"ipsecSecurityAssociations": policies}),))
    assert isinstance(fact, AvailableFact)
    assert fact.value.state is state


@pytest.mark.parametrize("incomplete", [{}, None, {"replayWindowSize": -1}, {"replayWindowSize": "16384"}])
@pytest.mark.parametrize("witness_first", [False, True])
def test_positive_policy_survives_unrelated_bad_policy(incomplete: object, witness_first: bool) -> None:
    """Keep an existential witness in both iteration orders."""
    items = [("positive", SA_POLICY), ("incomplete", incomplete)]
    output = {"ipsecSecurityAssociations": dict(items if witness_first else reversed(items))}
    fact = IpsecSaAntiReplayFact.derive(OfflineAntaDevice("test"), (command(IpsecSaAntiReplayFact, output),))
    assert isinstance(fact, AvailableFact)
    assert fact.value.state is FeatureState.ENABLED


@pytest.mark.parametrize(
    ("output", "problem"),
    [
        ({}, FactProblemKind.MISSING),
        ({"ipsecSecurityAssociations": None}, FactProblemKind.MISSING),
        ({"ipsecSecurityAssociations": []}, FactProblemKind.MALFORMED),
        ({"ipsecSecurityAssociations": {"bad": {}}}, FactProblemKind.MISSING),
        ({"ipsecSecurityAssociations": {"off": {"replayWindowSize": 0}, "bad": {}}}, FactProblemKind.MISSING),
        ({"ipsecSecurityAssociations": {"bad": None}}, FactProblemKind.MALFORMED),
        ({"ipsecSecurityAssociations": {"bad": {"replayWindowSize": True}}}, FactProblemKind.MALFORMED),
        ({"ipsecSecurityAssociations": {"bad": {"replayWindowSize": 0.5}}}, FactProblemKind.MALFORMED),
        ({"ipsecSecurityAssociations": {"bad": {"replayWindowSize": -1}}}, FactProblemKind.MALFORMED),
        ({"ipsecSecurityAssociations": {"bad": {"replayWindowSize": "0"}}}, FactProblemKind.MALFORMED),
        ({"ipsecSecurityAssociations": {"": SA_POLICY, "valid": SA_POLICY}}, FactProblemKind.MALFORMED),
    ],
)
def test_no_positive_requires_complete_negative_evidence(output: dict[str, object], problem: FactProblemKind) -> None:
    """Relevant missing policy data prevents a safe negative result."""
    fact = IpsecSaAntiReplayFact.derive(OfflineAntaDevice("test"), (command(IpsecSaAntiReplayFact, output),))
    assert isinstance(fact, UnavailableFact)
    assert fact.problem is problem


@pytest.mark.parametrize("definition", [IpsecKeyControllerFact, IpsecSaAntiReplayFact])
@pytest.mark.parametrize(("output", "problem"), [(None, FactProblemKind.MISSING), ("", FactProblemKind.MALFORMED)])
def test_missing_or_wrong_format(definition, output: object, problem: FactProblemKind) -> None:  # noqa: ANN001
    """Require successfully collected JSON."""
    fact = definition.derive(OfflineAntaDevice("test"), (command(definition, output),))
    assert isinstance(fact, UnavailableFact)
    assert fact.problem is problem
    assert fact.source.name == definition.commands[0].command


@pytest.mark.parametrize("definition", [IpsecKeyControllerFact, IpsecSaAntiReplayFact])
@pytest.mark.parametrize(
    ("errors", "problem"),
    [
        (["This command is not supported on this hardware platform"], FactProblemKind.UNSUPPORTED),
        (["transport failed"], FactProblemKind.COLLECTION_FAILED),
    ],
)
def test_command_errors_are_not_absence(definition, errors: list[str], problem: FactProblemKind) -> None:  # noqa: ANN001
    """Preserve unsupported and failed observation sources."""
    value = command(definition, {})
    value.errors = errors
    fact = definition.derive(OfflineAntaDevice("test"), (value,))
    assert isinstance(fact, UnavailableFact)
    assert fact.problem is problem
    assert fact.source.name == value.command


def test_command_identity_is_checked() -> None:
    """Do not feed SA output into the controller parser."""
    fact = IpsecKeyControllerFact.derive(OfflineAntaDevice("test"), (command(IpsecSaAntiReplayFact, {}),))
    assert isinstance(fact, UnavailableFact)
    assert fact.problem is FactProblemKind.COLLECTION_FAILED
