# Copyright (c) 2026 Arista Networks, Inc.
# Use of this source code is governed by the Apache License 2.0
# that can be found in the LICENSE file.
"""Unit tests for facts normalized from EOS AAA output."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, cast

import pytest

from anta._advisory.facts.aaa import Dot1xRadiusAccountingFact, LevelZeroCommandAuthorizationFact, LoginAuthenticationFact
from anta._advisory.facts.models import AvailableFact, FactProblemKind, FeatureState, MitigationState, UnavailableFact
from tests.units.anta_tests.advisories import OfflineAntaDevice

if TYPE_CHECKING:
    from anta.models import AntaCommand


def aaa_command(output: str) -> AntaCommand:
    """Return the narrow AAA command populated with text output."""
    command = LevelZeroCommandAuthorizationFact.commands[0].model_copy()
    command.output = output
    return command


@pytest.mark.parametrize(
    ("output", "state"),
    [
        ("", MitigationState.INEFFECTIVE),
        ("aaa authorization commands 0 default local none", MitigationState.INEFFECTIVE),
        ("aaa authorization commands 0 default local", MitigationState.EFFECTIVE),
        ("aaa authorization commands 0-2 default group tacacs+", MitigationState.EFFECTIVE),
        ("aaa authorization commands all default local group tacacs+", MitigationState.EFFECTIVE),
        ("aaa authorization commands 1-15 default none", MitigationState.INEFFECTIVE),
    ],
)
def test_level_zero_command_authorization_states(output: str, state: MitigationState) -> None:
    """Normalize implicit, explicit unsafe, safe, ranged, and all-level method lists."""
    fact = LevelZeroCommandAuthorizationFact.derive(OfflineAntaDevice("unit-test"), (aaa_command(output),))

    assert isinstance(fact, AvailableFact)
    assert fact.value.state is state


def test_level_zero_command_authorization_rejects_malformed_expression() -> None:
    """Reject an invalid level expression in an applicable command."""
    fact = LevelZeroCommandAuthorizationFact.derive(
        OfflineAntaDevice("unit-test"),
        (aaa_command("aaa authorization commands 2-0 default local"),),
    )

    assert isinstance(fact, UnavailableFact)
    assert fact.problem is FactProblemKind.MALFORMED


def test_level_zero_command_authorization_unsupported() -> None:
    """Keep unsupported AAA configuration unavailable."""
    command = aaa_command("")
    command.output = None
    command.errors = ["This command is not supported on this hardware platform"]

    fact = LevelZeroCommandAuthorizationFact.derive(OfflineAntaDevice("unit-test"), (command,))

    assert isinstance(fact, UnavailableFact)
    assert fact.problem is FactProblemKind.UNSUPPORTED


@pytest.mark.parametrize(
    ("methods", "state"),
    [
        (["local"], FeatureState.ENABLED),
        (["group tacacs+", "local"], FeatureState.ENABLED),
        (["none"], FeatureState.DISABLED),
        (["none", "local"], FeatureState.DISABLED),
    ],
)
def test_login_authentication_states(methods: list[str], state: FeatureState) -> None:
    """Normalize enabled and explicitly disabled default login method lists."""
    command = LoginAuthenticationFact.commands[0].model_copy()
    command.output = {"loginAuthenMethods": {"default": {"methods": methods}}}

    fact = LoginAuthenticationFact.derive(OfflineAntaDevice("unit-test"), (command,))

    assert isinstance(fact, AvailableFact)
    assert fact.value.state is state


def test_login_authentication_rejects_missing_default_list() -> None:
    """Reject missing default login methods."""
    command = LoginAuthenticationFact.commands[0].model_copy()
    command.output = {"loginAuthenMethods": {}}

    fact = LoginAuthenticationFact.derive(OfflineAntaDevice("unit-test"), (command,))

    assert isinstance(fact, UnavailableFact)
    assert fact.problem is FactProblemKind.MISSING


def test_login_authentication_unsupported() -> None:
    """Keep unsupported AAA method output unavailable."""
    command = LoginAuthenticationFact.commands[0].model_copy()
    command.output = None
    command.errors = ["This command is not supported on this hardware platform"]

    fact = LoginAuthenticationFact.derive(OfflineAntaDevice("unit-test"), (command,))

    assert isinstance(fact, UnavailableFact)
    assert fact.problem is FactProblemKind.UNSUPPORTED


UNSUPPORTED = "This command is not supported on this hardware platform"
NO_RADIUS_GROUPS: dict[str, object] = {"radiusServers": [], "groups": {}, "srcIntf": {}, "lastCounterClearTime": 0.0}
NAMED_RADIUS_GROUP: dict[str, object] = {
    "radiusServers": [],
    "groups": {"ACCT": {"serverGroup": "RADIUS", "members": []}},
    "srcIntf": {},
    "lastCounterClearTime": 0.0,
}


def accounting_methods(methods: object, action: str | None = "startStop") -> dict[str, object]:
    """Return ``show aaa methods accounting`` output with one default 802.1X method list."""
    dot1x: dict[str, object] = {"defaultMethods": methods, "consoleMethods": []}
    if action is not None:
        dot1x["defaultAction"] = action
    return {
        "commandsAcctMethods": {"privilege0-15": {"defaultMethods": [], "consoleMethods": []}},
        "execAcctMethods": {"exec": {"defaultMethods": [], "consoleMethods": []}},
        "systemAcctMethods": {"system": {"defaultMethods": [], "consoleMethods": []}},
        "dot1xAcctMethods": {"dot1x": dot1x},
    }


def radius_accounting_fact(accounting: object, radius: object, *, accounting_errors: list[str] | None = None, radius_errors: list[str] | None = None) -> object:
    """Derive the 802.1X RADIUS accounting fact from both command responses."""
    accounting_command, radius_command = (command.model_copy() for command in Dot1xRadiusAccountingFact.commands)
    accounting_command.output = cast("dict[str, Any] | str | None", accounting)
    accounting_command.errors = accounting_errors or []
    radius_command.output = cast("dict[str, Any] | str | None", radius)
    radius_command.errors = radius_errors or []
    return Dot1xRadiusAccountingFact.derive(OfflineAntaDevice("unit-test"), (accounting_command, radius_command))


@pytest.mark.parametrize(
    ("methods", "action", "radius", "state", "source"),
    [
        pytest.param([], None, NO_RADIUS_GROUPS, FeatureState.DISABLED, "show aaa methods accounting", id="no-accounting"),
        pytest.param(["group radius"], "startStop", NO_RADIUS_GROUPS, FeatureState.ENABLED, "show aaa methods accounting", id="4.32-builtin-start-stop"),
        pytest.param(["group radius"], "stopOnly", NO_RADIUS_GROUPS, FeatureState.ENABLED, "show aaa methods accounting", id="4.32-builtin-stop-only"),
        pytest.param(["radius"], "startStop", NO_RADIUS_GROUPS, FeatureState.ENABLED, "show aaa methods accounting", id="4.35-builtin"),
        pytest.param(["group ACCT"], "startStop", NAMED_RADIUS_GROUP, FeatureState.ENABLED, "show radius", id="4.32-named-empty-group"),
        pytest.param(["ACCT"], "stopOnly", NAMED_RADIUS_GROUP, FeatureState.ENABLED, "show radius", id="4.35-named-group"),
        pytest.param(["logging", "group ACCT"], "startStop", NAMED_RADIUS_GROUP, FeatureState.ENABLED, "show radius", id="named-group-after-logging"),
        pytest.param(["group ACCT", "group radius", "logging"], "stopOnly", None, FeatureState.ENABLED, "show aaa methods accounting", id="builtin-without-radius"),
        pytest.param(["logging"], "startStop", NAMED_RADIUS_GROUP, FeatureState.DISABLED, "show radius", id="logging-only"),
        pytest.param(["group ACCT"], "startStop", NO_RADIUS_GROUPS, FeatureState.DISABLED, "show radius", id="undefined-group"),
        pytest.param(
            ["group ACCT"],
            "startStop",
            {"radiusServers": [], "groups": {"OTHER": {"serverGroup": "RADIUS", "members": []}}},
            FeatureState.DISABLED,
            "show radius",
            id="other-radius-group",
        ),
    ],
)
def test_dot1x_radius_accounting_states(methods: list[str], action: str | None, radius: object, state: FeatureState, source: str) -> None:
    """Built-in and named RADIUS groups count with either action; logging and unresolved names do not.

    EOS 4.32.0F and 4.33.3.1F report ``group NAME`` methods and EOS 4.35.3F reports ``NAME``. A named group referenced by
    accounting can be deleted, or recreated as a TACACS+ group, without changing the accounting list.
    """
    fact = radius_accounting_fact(accounting_methods(methods, action), radius)
    assert isinstance(fact, AvailableFact)
    assert fact.value.state is state
    assert fact.source.name == source


@pytest.mark.parametrize(
    ("accounting", "problem"),
    [
        (None, FactProblemKind.MISSING),
        ([], FactProblemKind.MALFORMED),
        ({"execAcctMethods": {}}, FactProblemKind.MISSING),
        ({"dot1xAcctMethods": []}, FactProblemKind.MALFORMED),
        ({"dot1xAcctMethods": {}}, FactProblemKind.MISSING),
        ({"dot1xAcctMethods": {"dot1x": "startStop"}}, FactProblemKind.MALFORMED),
        ({"dot1xAcctMethods": {"dot1x": {"defaultAction": "startStop"}}}, FactProblemKind.MISSING),
        (accounting_methods("group radius"), FactProblemKind.MALFORMED),
        (accounting_methods(["group radius", 1]), FactProblemKind.MALFORMED),
        (accounting_methods([""]), FactProblemKind.MALFORMED),
    ],
)
def test_dot1x_radius_accounting_accounting_unavailable(accounting: object, problem: FactProblemKind) -> None:
    """Incomplete accounting output is never read as disabled accounting."""
    fact = radius_accounting_fact(accounting, NO_RADIUS_GROUPS)
    assert isinstance(fact, UnavailableFact)
    assert fact.problem is problem
    assert fact.source.name == "show aaa methods accounting"


@pytest.mark.parametrize(
    ("radius", "problem"),
    [
        (None, FactProblemKind.MISSING),
        ({"radiusServers": []}, FactProblemKind.MISSING),
        ({"groups": []}, FactProblemKind.MALFORMED),
        ({"groups": {"ACCT": "RADIUS"}}, FactProblemKind.MALFORMED),
        ({"groups": {"ACCT": {"members": []}}}, FactProblemKind.MALFORMED),
        ({"groups": {"ACCT": {"serverGroup": 1}, "OTHER": {"serverGroup": "RADIUS"}}}, FactProblemKind.MALFORMED),
        ({"groups": {"": {"serverGroup": "RADIUS"}}}, FactProblemKind.MALFORMED),
    ],
)
def test_dot1x_radius_accounting_radius_unavailable(radius: object, problem: FactProblemKind) -> None:
    """A named method cannot be resolved without valid RADIUS server-group evidence, which keeps its own source."""
    fact = radius_accounting_fact(accounting_methods(["group ACCT"]), radius)
    assert isinstance(fact, UnavailableFact)
    assert fact.problem is problem
    assert fact.source.name == "show radius"


@pytest.mark.parametrize("reverse", [False, True])
@pytest.mark.parametrize(
    ("methods", "state"),
    [
        pytest.param(["group ACCT"], FeatureState.ENABLED, id="referenced-radius-group"),
        pytest.param(["group BROKEN", "group ACCT"], FeatureState.ENABLED, id="referenced-radius-and-malformed-groups"),
        pytest.param(["group OTHER"], FeatureState.DISABLED, id="referenced-tacacs-group"),
    ],
)
def test_dot1x_radius_accounting_ignores_irrelevant_malformed_group(methods: list[str], state: FeatureState, *, reverse: bool) -> None:
    """A malformed group cannot hide a referenced RADIUS group or matter when unreferenced, in either order."""
    groups = [("BROKEN", {"members": []}), ("ACCT", {"serverGroup": "RADIUS", "members": []}), ("OTHER", {"serverGroup": "TACACS+", "members": []})]
    radius = {"radiusServers": [], "groups": dict(reversed(groups) if reverse else groups)}
    fact = radius_accounting_fact(accounting_methods(methods), radius)
    assert isinstance(fact, AvailableFact)
    assert fact.value.state is state
    assert fact.source.name == "show radius"


@pytest.mark.parametrize("reverse", [False, True])
def test_dot1x_radius_accounting_referenced_malformed_group(*, reverse: bool) -> None:
    """Without a referenced RADIUS group, a referenced malformed group prevents disabled accounting in either order."""
    groups = [("BROKEN", {"members": []}), ("ACCT", {"serverGroup": "RADIUS", "members": []})]
    radius = {"radiusServers": [], "groups": dict(reversed(groups) if reverse else groups)}
    fact = radius_accounting_fact(accounting_methods(["group BROKEN", "logging"]), radius)
    assert isinstance(fact, UnavailableFact)
    assert fact.problem is FactProblemKind.MALFORMED
    assert fact.source.name == "show radius"


@pytest.mark.parametrize(
    ("methods", "accounting_errors", "radius_errors", "result"),
    [
        pytest.param(["group ACCT"], ["invalid command"], [], ("show aaa methods accounting", FactProblemKind.COLLECTION_FAILED), id="accounting-failed"),
        pytest.param(["group ACCT"], [], ["invalid command"], ("show radius", FactProblemKind.COLLECTION_FAILED), id="radius-failed-named-group"),
        pytest.param(["group radius"], [], ["invalid command"], FeatureState.ENABLED, id="radius-failed-builtin-group"),
        pytest.param([], [], ["invalid command"], FeatureState.DISABLED, id="radius-failed-no-accounting"),
    ],
)
def test_dot1x_radius_accounting_collection_failures(
    methods: list[str], accounting_errors: list[str], radius_errors: list[str], result: tuple[str, FactProblemKind] | FeatureState
) -> None:
    """Every command error is deferred to the fact, keeps its own source, and only matters when that command is needed."""
    assert all(command.model_copy(update={"errors": ["invalid command"]}).errors_deferred for command in Dot1xRadiusAccountingFact.commands)
    fact = radius_accounting_fact(accounting_methods(methods), NAMED_RADIUS_GROUP, accounting_errors=accounting_errors, radius_errors=radius_errors)
    if isinstance(result, FeatureState):
        assert isinstance(fact, AvailableFact)
        assert fact.value.state is result
    else:
        assert isinstance(fact, UnavailableFact)
        assert (fact.source.name, fact.problem) == result


def test_dot1x_radius_accounting_unsupported_accounting() -> None:
    """Unsupported accounting methods output is unavailable rather than absent accounting."""
    fact = radius_accounting_fact(None, NO_RADIUS_GROUPS, accounting_errors=[UNSUPPORTED])
    assert isinstance(fact, UnavailableFact)
    assert fact.problem is FactProblemKind.UNSUPPORTED
    assert fact.source.name == "show aaa methods accounting"


def test_dot1x_radius_accounting_unsupported_radius() -> None:
    """Unsupported RADIUS output is only needed, and reported, when a named method must be resolved."""
    fact = radius_accounting_fact(accounting_methods(["group ACCT"]), None, radius_errors=[UNSUPPORTED])
    assert isinstance(fact, UnavailableFact)
    assert fact.problem is FactProblemKind.UNSUPPORTED
    assert fact.source.name == "show radius"

    disabled = radius_accounting_fact(accounting_methods([], None), None, radius_errors=[UNSUPPORTED])
    assert isinstance(disabled, AvailableFact)
    assert disabled.value.state is FeatureState.DISABLED
