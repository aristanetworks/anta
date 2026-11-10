# Copyright (c) 2026 Arista Networks, Inc.
# Use of this source code is governed by the Apache License 2.0
# that can be found in the LICENSE file.
"""Unit tests for facts normalized from persistent 802.1X configuration."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, cast

import pytest

from anta._advisory.facts.dot1x import (
    Dot1xAuthenticatorInterface,
    Dot1xAuthenticatorInterfaceProblem,
    Dot1xAuthenticatorInterfacesFact,
    Dot1xControlledAuthenticatorFact,
    Dot1xControlledAuthenticatorInterfacesFact,
    Dot1xDhcpProfilingFact,
    Dot1xDhcpProfilingOption,
    Dot1xDynamicAuthorizationFact,
    Dot1xPortControl,
    Dot1xSystemAuthControlFact,
)
from anta._advisory.facts.models import AvailableFact, ConfigurationState, Fact, FactProblemKind, FeatureState, UnavailableFact
from anta._advisory.optional_commands import OptionalAntaCommand
from tests.units.anta_tests.advisories import OfflineAntaDevice
from tests.units.anta_tests.advisories.dot1x_outputs import dot1x_all, dot1x_interface

if TYPE_CHECKING:
    from anta.models import AntaCommand

UNSUPPORTED = "This command is not supported on this hardware platform"

Dot1xFactDefinition = type[
    Dot1xSystemAuthControlFact
    | Dot1xAuthenticatorInterfacesFact
    | Dot1xDhcpProfilingFact
    | Dot1xControlledAuthenticatorFact
    | Dot1xControlledAuthenticatorInterfacesFact
    | Dot1xDynamicAuthorizationFact
]

SECTION_PREFIX = "aaa accounting dot1x default start-stop group radius\ndot1x\n   captive-portal start limit infinite\n"

SECTION_SUFFIX = "interface Ethernet20\n   dot1x pae authenticator\n   dot1x port-control auto\ndot1x system-auth-control\n"


def command_for(definition: Dot1xFactDefinition, output: object) -> AntaCommand:
    """Copy the fact command with one test response."""
    command = definition.commands[0].model_copy()
    command.output = cast("dict[str, Any] | str | None", output)
    return command


def failed(definition: Dot1xFactDefinition, error: str) -> AntaCommand:
    """Copy the fact command with one command error."""
    command = command_for(definition, None)
    command.errors = [error]
    return command


def unsupported(definition: Dot1xFactDefinition) -> AntaCommand:
    """Copy the fact command with an unsupported-platform error."""
    return failed(definition, UNSUPPORTED)


def controlled_interfaces_fact(output: object, *, errors: list[str] | None = None) -> Fact[Dot1xControlledAuthenticatorInterfacesFact]:
    """Exercise the real declared command and derivation path."""
    command = command_for(Dot1xControlledAuthenticatorInterfacesFact, output)
    command.errors = errors or []
    return Dot1xControlledAuthenticatorInterfacesFact.derive(OfflineAntaDevice("unit-test"), (command,))


@pytest.mark.parametrize(
    ("output", "state"),
    [
        ({"systemAuthControl": False, "interfaces": {}}, FeatureState.DISABLED),
        ({"systemAuthControl": True, "interfaces": {"Ethernet1": {"portControl": "forceAuth"}}}, FeatureState.DISABLED),
        ({"systemAuthControl": True, "interfaces": {"Ethernet1": {"portControl": "controlled"}}}, FeatureState.ENABLED),
    ],
)
def test_dot1x_controlled_authenticator_states(output: dict[str, object], state: FeatureState) -> None:
    """Normalize effective controlled 802.1X state."""
    command = command_for(Dot1xControlledAuthenticatorFact, output)

    fact = Dot1xControlledAuthenticatorFact.derive(OfflineAntaDevice("unit-test"), (command,))

    assert isinstance(fact, AvailableFact)
    assert fact.value.state is state


@pytest.mark.parametrize(
    ("output", "state"),
    [
        ({"systemAuthControl": False, "dynAuth": False, "interfaces": {}}, FeatureState.DISABLED),
        (
            {"systemAuthControl": True, "dynAuth": True, "interfaces": {"Ethernet1": {"portControl": "controlled"}}},
            FeatureState.ENABLED,
        ),
        ({"systemAuthControl": True, "dynAuth": False, "interfaces": {"Ethernet1": {"portControl": "controlled"}}}, FeatureState.DISABLED),
        ({"systemAuthControl": True, "dynAuth": True, "interfaces": {"Ethernet1": {"portControl": "forceAuth"}}}, FeatureState.DISABLED),
    ],
)
def test_dot1x_dynamic_authorization_states(output: dict[str, object], state: FeatureState) -> None:
    """Require effective global dynamic authorization and a controlled authenticator interface."""
    fact = Dot1xDynamicAuthorizationFact.derive(OfflineAntaDevice("unit-test"), (command_for(Dot1xDynamicAuthorizationFact, output),))
    assert isinstance(fact, AvailableFact)
    assert fact.value.state is state


@pytest.mark.parametrize(
    "definition",
    [
        Dot1xSystemAuthControlFact,
        Dot1xAuthenticatorInterfacesFact,
        Dot1xControlledAuthenticatorInterfacesFact,
        Dot1xDhcpProfilingFact,
    ],
)
def test_collection_failure_is_unavailable(definition: Dot1xFactDefinition) -> None:
    """Every command error is deferred to the fact and retained with its own source, never read as absent configuration."""
    command = failed(definition, "invalid command")
    assert command.errors_deferred
    fact = definition.derive(OfflineAntaDevice("unit-test"), (command,))
    assert isinstance(fact, UnavailableFact)
    assert fact.problem is FactProblemKind.COLLECTION_FAILED
    assert fact.source.name == definition.commands[0].command


@pytest.mark.parametrize(("value", "state"), [(True, FeatureState.ENABLED), (False, FeatureState.DISABLED)])
def test_system_auth_control_states(value: bool, state: FeatureState) -> None:
    """Global system authentication control is reported independently of authenticator interfaces."""
    output = dot1x_all(system_auth_control=value, interfaces={"Ethernet20": dot1x_interface("controlled")})
    fact = Dot1xSystemAuthControlFact.derive(OfflineAntaDevice("unit-test"), (command_for(Dot1xSystemAuthControlFact, output),))
    assert isinstance(fact, AvailableFact)
    assert fact.value.state is state
    assert fact.source.name == "show dot1x all"


@pytest.mark.parametrize(
    ("output", "problem"),
    [
        (None, FactProblemKind.MISSING),
        ("System authentication control: enabled", FactProblemKind.MALFORMED),
        ({"interfaces": {}}, FactProblemKind.MISSING),
        (dot1x_all(system_auth_control="enabled"), FactProblemKind.MALFORMED),
        (dot1x_all(system_auth_control=None), FactProblemKind.MALFORMED),
    ],
)
def test_system_auth_control_unavailable(output: object, problem: FactProblemKind) -> None:
    """A missing or non-boolean flag is not disabled control."""
    fact = Dot1xSystemAuthControlFact.derive(OfflineAntaDevice("unit-test"), (command_for(Dot1xSystemAuthControlFact, output),))
    assert isinstance(fact, UnavailableFact)
    assert fact.problem is problem


@pytest.mark.parametrize("definition", [Dot1xSystemAuthControlFact, Dot1xControlledAuthenticatorFact, Dot1xDynamicAuthorizationFact])
def test_feature_summaries_unsupported(
    definition: type[Dot1xSystemAuthControlFact | Dot1xControlledAuthenticatorFact | Dot1xDynamicAuthorizationFact],
) -> None:
    """Feature summaries preserve the unsupported state through normalization."""
    fact = definition.derive(OfflineAntaDevice("unit-test"), (unsupported(definition),))
    assert isinstance(fact, AvailableFact)
    assert fact.value.state is FeatureState.UNSUPPORTED


@pytest.mark.parametrize(
    ("raw", "port_control"),
    [
        ("controlled", Dot1xPortControl.AUTO),
        ("forceAuth", Dot1xPortControl.FORCE_AUTHORIZED),
        ("forceUnauth", Dot1xPortControl.FORCE_UNAUTHORIZED),
    ],
)
@pytest.mark.parametrize("system_auth_control", [True, False])
def test_authenticator_port_control_modes(raw: str, port_control: Dot1xPortControl, *, system_auth_control: bool) -> None:
    """Every port-control mode is an authenticator, including with system authentication control disabled.

    EOS 4.32.0F, 4.33.3.1F, and 4.35.3F report ``controlled`` for ``dot1x port-control auto`` and ``forceAuth`` for both the
    default and an explicit ``force-authorized`` on an interface with ``dot1x pae authenticator``.
    """
    output = dot1x_all(system_auth_control=system_auth_control, interfaces={"Ethernet20": dot1x_interface(raw)})
    fact = Dot1xAuthenticatorInterfacesFact.derive(OfflineAntaDevice("unit-test"), (command_for(Dot1xAuthenticatorInterfacesFact, output),))
    assert isinstance(fact, AvailableFact)
    assert fact.value.state is ConfigurationState.CONFIGURED
    assert fact.value.interfaces == (Dot1xAuthenticatorInterface("Ethernet20", port_control),)


def test_authenticator_interfaces_preserve_identity() -> None:
    """Each authenticator retains its interface name and own port-control mode."""
    output = dot1x_all(interfaces={"Ethernet20": dot1x_interface("controlled"), "Ethernet21": dot1x_interface("forceAuth")})
    fact = Dot1xAuthenticatorInterfacesFact.derive(OfflineAntaDevice("unit-test"), (command_for(Dot1xAuthenticatorInterfacesFact, output),))
    assert isinstance(fact, AvailableFact)
    assert fact.value.interfaces == (
        Dot1xAuthenticatorInterface("Ethernet20", Dot1xPortControl.AUTO),
        Dot1xAuthenticatorInterface("Ethernet21", Dot1xPortControl.FORCE_AUTHORIZED),
    )


def test_no_authenticator_interfaces() -> None:
    """Interfaces with only port-control or a supplicant role are not listed, so an empty mapping is no authenticator."""
    fact = Dot1xAuthenticatorInterfacesFact.derive(OfflineAntaDevice("unit-test"), (command_for(Dot1xAuthenticatorInterfacesFact, dot1x_all()),))
    assert isinstance(fact, AvailableFact)
    assert fact.value.state is ConfigurationState.NOT_CONFIGURED
    assert fact.value.interfaces == ()


@pytest.mark.parametrize(
    ("output", "problem"),
    [
        (None, FactProblemKind.MISSING),
        ({"systemAuthControl": True}, FactProblemKind.MISSING),
        (dot1x_all(interfaces=["Ethernet20"]), FactProblemKind.MALFORMED),
        (dot1x_all(interfaces={"Ethernet20": "controlled"}), FactProblemKind.MALFORMED),
        (dot1x_all(interfaces={"Ethernet20": {"hostMode": "multiHost"}}), FactProblemKind.MISSING),
        (dot1x_all(interfaces={"Ethernet20": {"portControl": 1}}), FactProblemKind.MALFORMED),
        (dot1x_all(interfaces={"Ethernet20": dot1x_interface("auto")}), FactProblemKind.INVALID),
        (dot1x_all(interfaces={"": dot1x_interface("controlled")}), FactProblemKind.MALFORMED),
    ],
)
def test_authenticator_interfaces_unavailable(output: object, problem: FactProblemKind) -> None:
    """Without a valid authenticator, incomplete interface evidence cannot prove absence."""
    fact = Dot1xAuthenticatorInterfacesFact.derive(OfflineAntaDevice("unit-test"), (command_for(Dot1xAuthenticatorInterfacesFact, output),))
    assert isinstance(fact, UnavailableFact)
    assert fact.problem is problem
    assert fact.source.name == "show dot1x all"


@pytest.mark.parametrize("reverse", [False, True])
@pytest.mark.parametrize(
    ("broken", "problem"),
    [
        ({}, FactProblemKind.MISSING),
        ("controlled", FactProblemKind.MALFORMED),
        ({"portControl": 1}, FactProblemKind.MALFORMED),
        (dot1x_interface("auto"), FactProblemKind.INVALID),
    ],
)
def test_valid_authenticator_survives_uninterpretable_interface(broken: object, problem: FactProblemKind, *, reverse: bool) -> None:
    """A valid authenticator proves the configured state in either order, and the other record stays explicit."""
    records = [("Ethernet20", dot1x_interface("controlled")), ("Ethernet21", broken)]
    output = dot1x_all(interfaces=dict(reversed(records) if reverse else records))
    fact = Dot1xAuthenticatorInterfacesFact.derive(OfflineAntaDevice("unit-test"), (command_for(Dot1xAuthenticatorInterfacesFact, output),))
    assert isinstance(fact, AvailableFact)
    assert fact.value.state is ConfigurationState.CONFIGURED
    assert fact.value.interfaces == (Dot1xAuthenticatorInterface("Ethernet20", Dot1xPortControl.AUTO),)
    assert fact.value.problems == (Dot1xAuthenticatorInterfaceProblem("Ethernet21", problem),)


@pytest.mark.parametrize("reverse", [False, True])
def test_uninterpretable_authenticators_without_valid_interface(*, reverse: bool) -> None:
    """Without a valid authenticator, the representative problem does not depend on traversal order."""
    records = [("Ethernet20", {}), ("Ethernet21", dot1x_interface("auto"))]
    output = dot1x_all(interfaces=dict(reversed(records) if reverse else records))
    fact = Dot1xAuthenticatorInterfacesFact.derive(OfflineAntaDevice("unit-test"), (command_for(Dot1xAuthenticatorInterfacesFact, output),))
    assert isinstance(fact, UnavailableFact)
    assert fact.problem is FactProblemKind.MISSING
    assert fact.source.name == "show dot1x all"


def test_authenticator_interfaces_unsupported() -> None:
    """An unsupported 802.1X command cannot enumerate authenticators."""
    fact = Dot1xAuthenticatorInterfacesFact.derive(OfflineAntaDevice("unit-test"), (unsupported(Dot1xAuthenticatorInterfacesFact),))
    assert isinstance(fact, UnavailableFact)
    assert fact.problem is FactProblemKind.UNSUPPORTED


@pytest.mark.parametrize(
    ("statements", "options"),
    [
        (("hostname",), {Dot1xDhcpProfilingOption.HOSTNAME}),
        (("parameter-request-list",), {Dot1xDhcpProfilingOption.PARAMETER_REQUEST_LIST}),
        (("vendor-class-id",), {Dot1xDhcpProfilingOption.VENDOR_CLASS_ID}),
        (
            ("hostname", "parameter-request-list", "vendor-class-id"),
            {Dot1xDhcpProfilingOption.HOSTNAME, Dot1xDhcpProfilingOption.PARAMETER_REQUEST_LIST, Dot1xDhcpProfilingOption.VENDOR_CLASS_ID},
        ),
    ],
)
def test_dhcp_profiling_options(statements: tuple[str, ...], options: set[Dot1xDhcpProfilingOption]) -> None:
    """Each option is retained exactly as configured, alone or combined (captured on EOS 4.32.0F)."""
    output = SECTION_PREFIX + "".join(f"   radius av-pair dhcp {statement}\n" for statement in statements) + SECTION_SUFFIX
    fact = Dot1xDhcpProfilingFact.derive(OfflineAntaDevice("unit-test"), (command_for(Dot1xDhcpProfilingFact, output),))
    assert isinstance(fact, AvailableFact)
    assert fact.value.state is ConfigurationState.CONFIGURED
    assert fact.value.options == frozenset(options)
    assert fact.source.name == "show running-config section dot1x"


@pytest.mark.parametrize(
    "output",
    [
        pytest.param("", id="no-dot1x-configuration"),
        pytest.param(SECTION_PREFIX + SECTION_SUFFIX, id="dot1x-without-profiling"),
        pytest.param(
            "dot1x\n   no radius av-pair dhcp hostname\n   radius av-pair service-type\n   radius av-pair lldp system-name\n"
            "   radius av-pair framed-mtu 1400\n   mac-based-auth radius av-pair user-name delimiter colon lowercase\n",
            id="other-attributes",
        ),
        pytest.param("dot1x\n   supplicant profile P1\n      radius av-pair dhcp hostname\n", id="nested-statement"),
        pytest.param("interface Ethernet20\n   radius av-pair dhcp hostname\n", id="other-block"),
    ],
)
def test_dhcp_profiling_not_configured(output: str) -> None:
    """Only the three option statements directly under the global block count."""
    fact = Dot1xDhcpProfilingFact.derive(OfflineAntaDevice("unit-test"), (command_for(Dot1xDhcpProfilingFact, output),))
    assert isinstance(fact, AvailableFact)
    assert fact.value.state is ConfigurationState.NOT_CONFIGURED
    assert fact.value.options == frozenset()


def test_dhcp_profiling_after_other_block() -> None:
    """A later global block is still evaluated after other top-level sections."""
    output = "interface Ethernet20\n   dot1x pae authenticator\n!\ndot1x\n   radius av-pair dhcp vendor-class-id\n"
    fact = Dot1xDhcpProfilingFact.derive(OfflineAntaDevice("unit-test"), (command_for(Dot1xDhcpProfilingFact, output),))
    assert isinstance(fact, AvailableFact)
    assert fact.value.options == frozenset({Dot1xDhcpProfilingOption.VENDOR_CLASS_ID})


@pytest.mark.parametrize(
    ("output", "problem"),
    [
        pytest.param(None, FactProblemKind.MISSING, id="missing"),
        pytest.param({"dot1x": {}}, FactProblemKind.MALFORMED, id="non-text"),
        pytest.param("dot1x\n   radius av-pair dhcp client-identifier\n", FactProblemKind.INVALID, id="unrecognized-option"),
        pytest.param("dot1x\n  radius av-pair dhcp hostname\n", FactProblemKind.MALFORMED, id="uneven-indentation"),
        pytest.param("dot1x\n\tradius av-pair dhcp hostname\n", FactProblemKind.MALFORMED, id="tab-indentation"),
    ],
)
def test_dhcp_profiling_unavailable(output: object, problem: FactProblemKind) -> None:
    """Missing, non-text, or unrecognized configuration output is not an unconfigured profiling state."""
    fact = Dot1xDhcpProfilingFact.derive(OfflineAntaDevice("unit-test"), (command_for(Dot1xDhcpProfilingFact, output),))
    assert isinstance(fact, UnavailableFact)
    assert fact.problem is problem


def test_dhcp_profiling_unsupported() -> None:
    """An unsupported configuration command cannot establish absent profiling."""
    fact = Dot1xDhcpProfilingFact.derive(OfflineAntaDevice("unit-test"), (unsupported(Dot1xDhcpProfilingFact),))
    assert isinstance(fact, UnavailableFact)
    assert fact.problem is FactProblemKind.UNSUPPORTED


@pytest.mark.parametrize("reverse", [False, True])
def test_recognized_profiling_option_survives_unrecognized_option(*, reverse: bool) -> None:
    """A recognized option proves the configured state in either order, and the unrecognized option stays explicit."""
    statements = ["   radius av-pair dhcp hostname\n", "   radius av-pair dhcp client-identifier\n"]
    output = "dot1x\n" + "".join(reversed(statements) if reverse else statements)
    fact = Dot1xDhcpProfilingFact.derive(OfflineAntaDevice("unit-test"), (command_for(Dot1xDhcpProfilingFact, output),))
    assert isinstance(fact, AvailableFact)
    assert fact.value.state is ConfigurationState.CONFIGURED
    assert fact.value.options == frozenset({Dot1xDhcpProfilingOption.HOSTNAME})
    assert fact.value.unrecognized == frozenset({"client-identifier"})


@pytest.mark.parametrize("reverse", [False, True])
def test_malformed_dot1x_block_overrides_recognized_option(*, reverse: bool) -> None:
    """Unexpected indentation leaves the block boundaries unknown, so a recognized option cannot be trusted in either order."""
    statements = ["   radius av-pair dhcp hostname\n", "  radius av-pair dhcp vendor-class-id\n"]
    output = "dot1x\n" + "".join(reversed(statements) if reverse else statements)
    fact = Dot1xDhcpProfilingFact.derive(OfflineAntaDevice("unit-test"), (command_for(Dot1xDhcpProfilingFact, output),))
    assert isinstance(fact, UnavailableFact)
    assert fact.problem is FactProblemKind.MALFORMED


def test_command_contract() -> None:
    """Require explicit revision one and retain failures for independent exclusions."""
    (command,) = Dot1xControlledAuthenticatorInterfacesFact.required_commands()
    assert isinstance(command, OptionalAntaCommand)
    assert (command.command, command.ofmt, command.revision, command.defer_errors) == ("show dot1x all", "json", 1, True)


@pytest.mark.parametrize(
    ("mode", "raw"),
    [(Dot1xPortControl.AUTO, "controlled"), (Dot1xPortControl.FORCE_AUTHORIZED, "forceAuth"), (Dot1xPortControl.FORCE_UNAUTHORIZED, "forceUnauth")],
)
@pytest.mark.parametrize("system_control", [False, True])
def test_controlled_interfaces_require_global_control_and_auto(mode: Dot1xPortControl, raw: str, system_control: bool) -> None:
    """The scoped view shares the legacy summary's effective control criteria."""
    fact = controlled_interfaces_fact({"systemAuthControl": system_control, "interfaces": {"Ethernet3": {"portControl": raw, "hostMode": "multiHost"}}})
    assert isinstance(fact, AvailableFact)
    expected = (Dot1xAuthenticatorInterface("Ethernet3", mode),) if system_control and mode is Dot1xPortControl.AUTO else ()
    assert fact.value.interfaces == expected
    assert not fact.value.problems
    assert fact.source.name == "show dot1x all"


def test_empty_interfaces_and_unrelated_fields() -> None:
    """The command's explicit empty interface map establishes empty configured scope."""
    fact = controlled_interfaces_fact({"interfaces": {}, "systemAuthControl": True})
    assert isinstance(fact, AvailableFact)
    assert fact.value.interfaces == ()
    assert fact.value.problems == ()


@pytest.mark.parametrize(
    ("output", "problem"),
    [
        (None, FactProblemKind.MISSING),
        ({}, FactProblemKind.MISSING),
        ([], FactProblemKind.MALFORMED),
        ({"systemAuthControl": True}, FactProblemKind.MISSING),
        ({"systemAuthControl": "true", "interfaces": {}}, FactProblemKind.MALFORMED),
        ({"systemAuthControl": None, "interfaces": {}}, FactProblemKind.MALFORMED),
        ({"systemAuthControl": True, "interfaces": None}, FactProblemKind.MALFORMED),
        ({"systemAuthControl": True, "interfaces": []}, FactProblemKind.MALFORMED),
    ],
)
def test_unreliable_command_or_scope_shape(output: object, problem: FactProblemKind) -> None:
    """Broken scope boundaries cannot silently become empty configuration."""
    fact = controlled_interfaces_fact(output)
    assert isinstance(fact, UnavailableFact)
    assert fact.problem is problem


@pytest.mark.parametrize("name", ["", 1, " Ethernet2"])
@pytest.mark.parametrize("reverse", [False, True])
def test_invalid_sibling_identity_preserves_valid_interface(name: object, reverse: bool) -> None:
    """An unusable sibling identity cannot discard a trustworthy interface."""
    entries = [("Ethernet3", {"portControl": "controlled"}), (name, {"portControl": "controlled"})]
    fact = controlled_interfaces_fact({"systemAuthControl": True, "interfaces": dict(reversed(entries) if reverse else entries)})
    assert isinstance(fact, AvailableFact)
    assert fact.value.interfaces == (Dot1xAuthenticatorInterface("Ethernet3", Dot1xPortControl.AUTO),)
    assert len(fact.value.problems) == 1
    assert fact.value.problems[0].interface is None
    assert fact.value.problems[0].fact.problem is FactProblemKind.MALFORMED


@pytest.mark.parametrize("reverse", [False, True])
@pytest.mark.parametrize(
    ("broken", "problem"),
    [
        ({}, FactProblemKind.MISSING),
        (None, FactProblemKind.MALFORMED),
        ({"portControl": None}, FactProblemKind.MALFORMED),
        ({"portControl": "future"}, FactProblemKind.INVALID),
    ],
)
def test_scoped_problem_preserves_other_interfaces(reverse: bool, broken: object, problem: FactProblemKind) -> None:
    """Traversal order cannot erase a valid observation from another scope."""
    entries = [("Ethernet3", {"portControl": "controlled"}), ("Ethernet2", broken)]
    fact = controlled_interfaces_fact({"systemAuthControl": True, "interfaces": dict(reversed(entries) if reverse else entries)})
    assert isinstance(fact, AvailableFact)
    assert fact.value.interfaces == (Dot1xAuthenticatorInterface("Ethernet3", Dot1xPortControl.AUTO),)
    assert len(fact.value.problems) == 1
    assert fact.value.problems[0].interface == "Ethernet2"
    assert fact.value.problems[0].fact.problem is problem


def test_command_failures_are_not_absence() -> None:
    """A failed collection cannot establish an empty authenticator list."""
    fact = controlled_interfaces_fact({"interfaces": {}}, errors=["transport failure"])
    assert isinstance(fact, UnavailableFact)
    assert fact.problem is FactProblemKind.COLLECTION_FAILED


def test_unsupported_command_is_not_absence() -> None:
    """Unsupported collection remains unavailable on otherwise applicable devices."""
    command = Dot1xControlledAuthenticatorInterfacesFact.required_commands()[0].model_copy(update={"errors": ["not supported on this hardware platform"]})
    fact = Dot1xControlledAuthenticatorInterfacesFact.derive(OfflineAntaDevice("unit-test"), (command,))
    assert isinstance(fact, UnavailableFact)
    assert fact.problem is FactProblemKind.UNSUPPORTED


@pytest.mark.parametrize("entries", [None, {}, {"Ethernet2": None}])
def test_disabled_global_control_decisively_excludes_interface_errors(entries: object) -> None:
    """Interface parsing is unnecessary when the global prerequisite is disabled."""
    fact = controlled_interfaces_fact({"systemAuthControl": False, "interfaces": entries})
    assert isinstance(fact, AvailableFact)
    assert fact.value.interfaces == ()
    assert fact.value.problems == ()


@pytest.mark.parametrize("definition", [Dot1xControlledAuthenticatorFact, Dot1xDynamicAuthorizationFact])
@pytest.mark.parametrize("reverse", [False, True])
@pytest.mark.parametrize("broken", [{}, None, {"portControl": None}, {"portControl": "future"}])
def test_summary_presence_survives_unrelated_interface_failures(
    definition: type[Dot1xControlledAuthenticatorFact | Dot1xDynamicAuthorizationFact],
    reverse: bool,
    broken: object,
) -> None:
    """A valid auto authenticator wins over independent failures in either order."""
    records = [("Ethernet3", dot1x_interface("controlled")), ("Ethernet2", broken)]
    output = dot1x_all(interfaces=dict(reversed(records) if reverse else records))
    output["dynAuth"] = True
    fact = definition.derive(OfflineAntaDevice("unit-test"), (command_for(definition, output),))
    assert isinstance(fact, AvailableFact)
    assert fact.value.state is FeatureState.ENABLED
    assert fact.source.name == "show dot1x all"


@pytest.mark.parametrize("reverse", [False, True])
@pytest.mark.parametrize("name", ["", 1, " Ethernet2"])
def test_general_inventory_preserves_presence_with_unknown_sibling_scope(name: object, reverse: bool) -> None:
    """An unusable sibling name cannot erase a trustworthy configured authenticator."""
    records = [("Ethernet3", dot1x_interface("controlled")), (name, dot1x_interface("forceAuth"))]
    output = dot1x_all(interfaces=dict(reversed(records) if reverse else records))
    fact = Dot1xAuthenticatorInterfacesFact.derive(OfflineAntaDevice("unit-test"), (command_for(Dot1xAuthenticatorInterfacesFact, output),))
    assert isinstance(fact, AvailableFact)
    assert fact.value.state is ConfigurationState.CONFIGURED
    assert fact.value.interfaces == (Dot1xAuthenticatorInterface("Ethernet3", Dot1xPortControl.AUTO),)
    assert fact.value.problems == (Dot1xAuthenticatorInterfaceProblem(None, FactProblemKind.MALFORMED),)


@pytest.mark.parametrize(
    "definition",
    [
        Dot1xControlledAuthenticatorFact,
        Dot1xDynamicAuthorizationFact,
        Dot1xControlledAuthenticatorInterfacesFact,
        Dot1xAuthenticatorInterfacesFact,
    ],
)
@pytest.mark.parametrize(
    ("fields", "problem"),
    [
        ({}, FactProblemKind.MISSING),
        ({"interfaces": None}, FactProblemKind.MALFORMED),
        ({"interfaces": []}, FactProblemKind.MALFORMED),
        ({"interfaces": {"Ethernet3": {}}}, FactProblemKind.MISSING),
        ({"interfaces": {"Ethernet3": {"portControl": None}}}, FactProblemKind.MALFORMED),
        ({"interfaces": {"Ethernet3": {"portControl": 1}}}, FactProblemKind.MALFORMED),
        ({"interfaces": {"Ethernet3": {"portControl": "future"}}}, FactProblemKind.INVALID),
    ],
)
def test_authenticator_views_share_required_field_classification(
    definition: type[
        Dot1xControlledAuthenticatorFact | Dot1xDynamicAuthorizationFact | Dot1xControlledAuthenticatorInterfacesFact | Dot1xAuthenticatorInterfacesFact
    ],
    fields: dict[str, object],
    problem: FactProblemKind,
) -> None:
    """Every view assigns the same reason while the scoped view retains partial evidence."""
    output = {"systemAuthControl": True, "dynAuth": True, **fields}
    fact = definition.derive(OfflineAntaDevice("unit-test"), (command_for(definition, output),))
    if isinstance(fact, UnavailableFact):
        assert fact.problem is problem
    else:
        assert isinstance(fact.value, Dot1xControlledAuthenticatorInterfacesFact)
        assert fact.value.interfaces == ()
        assert len(fact.value.problems) == 1
        assert fact.value.problems[0].interface == "Ethernet3"
        assert fact.value.problems[0].fact.problem is problem
    assert fact.source.name == "show dot1x all"


@pytest.mark.parametrize("definition", [Dot1xControlledAuthenticatorFact, Dot1xDynamicAuthorizationFact])
@pytest.mark.parametrize("reverse", [False, True])
def test_summary_without_presence_keeps_stable_uncertainty(
    definition: type[Dot1xControlledAuthenticatorFact | Dot1xDynamicAuthorizationFact],
    reverse: bool,
) -> None:
    """No positive means a required failure, selected independently of traversal order."""
    records = [("Ethernet2", {}), ("Ethernet3", dot1x_interface("future"))]
    output = dot1x_all(interfaces=dict(reversed(records) if reverse else records))
    output["dynAuth"] = True
    fact = definition.derive(OfflineAntaDevice("unit-test"), (command_for(definition, output),))
    assert isinstance(fact, UnavailableFact)
    assert fact.problem is FactProblemKind.MISSING
    assert fact.source.name == "show dot1x all"


@pytest.mark.parametrize("definition", [Dot1xControlledAuthenticatorFact, Dot1xDynamicAuthorizationFact])
def test_disabled_control_excludes_unusable_interface_and_dynamic_fields(
    definition: type[Dot1xControlledAuthenticatorFact | Dot1xDynamicAuthorizationFact],
) -> None:
    """A disabled global prerequisite establishes absence without unrelated evidence."""
    output = {"systemAuthControl": False, "interfaces": None}
    fact = definition.derive(OfflineAntaDevice("unit-test"), (command_for(definition, output),))
    assert isinstance(fact, AvailableFact)
    assert fact.value.state is FeatureState.DISABLED


def test_global_control_ignores_unrelated_interface_and_dynamic_failures() -> None:
    """The global view depends solely on its own normalized flag."""
    output = {"systemAuthControl": True, "dynAuth": None, "interfaces": None}
    fact = Dot1xSystemAuthControlFact.derive(OfflineAntaDevice("unit-test"), (command_for(Dot1xSystemAuthControlFact, output),))
    assert isinstance(fact, AvailableFact)
    assert fact.value.state is FeatureState.ENABLED
