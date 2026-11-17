# Copyright (c) 2026 Arista Networks, Inc.
# Use of this source code is governed by the Apache License 2.0
# that can be found in the LICENSE file.
"""Configured keyed BFD authentication observations."""

from __future__ import annotations

from typing import Any, cast

import pytest

from anta._advisory.facts.bfd import BfdAuthenticationFact, BfdKeyedAuthenticationFact
from anta._advisory.facts.models import AvailableFact, Fact, FactProblemKind, FeatureState, UnavailableFact


def fact(output: object, *, interface: bool = False) -> Fact[BfdKeyedAuthenticationFact]:
    """Parse one sanitized configuration scope while BFD is enabled."""
    commands = tuple(command.model_copy() for command in BfdKeyedAuthenticationFact.commands)
    commands[0].output = {"adminDown": False}
    commands[1].output = "" if interface else cast("Any", output)
    commands[2].output = cast("Any", output) if interface else ""
    return BfdKeyedAuthenticationFact.parse(commands)


@pytest.mark.parametrize("mode", ["md5", "sha1"])
@pytest.mark.parametrize("meticulous", ["", " meticulous"])
@pytest.mark.parametrize(
    ("header", "prefix"),
    [
        ("router bfd\n", "   "),
        ("interface Ethernet1\n", "   bfd "),
        ("router bfd\n   peer 192.0.2.1\n", "      "),
        ("router bfd\n   vrf BLUE\n      peer 192.0.2.1\n", "         "),
    ],
)
def test_configured_modes(header: str, prefix: str, mode: str, meticulous: str) -> None:
    """Parse configured keyed modes without requiring a live peer."""
    interface = header.startswith("interface")
    result = fact(f"{header}{prefix}authentication mode {mode} shared-secret profile TEST{meticulous}\n", interface=interface)
    assert isinstance(result, AvailableFact)
    assert result.value.state is FeatureState.ENABLED
    assert result.source.name == (
        r"show running-config sanitized section ^\s+bfd\sauthentication\smode\s" if interface else r"show running-config sanitized section ^router\sbfd$"
    )


@pytest.mark.parametrize(
    ("config", "interface"),
    [
        ("", False),
        ("", True),
        ("router bfd\n   shutdown\n", False),
        ("router bfd\n   authentication mode simple shared-secret profile TEST\n", False),
        ("interface Ethernet1\n   bfd authentication mode simple shared-secret profile TEST\n", True),
        ("interface Ethernet1\n   description bfd authentication mode md5 shared-secret profile TEST\n", True),
        ("router bgp 65000\n   authentication mode md5 shared-secret profile TEST\n", True),
        ("router bfd\n   sbfd\n      reflector local-discriminator 1000 proxy\n", False),
        ("management security\n   shared-secret profile bfd\n      secret **MASKED**\n", True),
    ],
)
def test_no_keyed_authentication(config: str, interface: bool) -> None:
    """Simple modes, absent authentication and unrelated matches establish absence."""
    result = fact(config, interface=interface)
    assert isinstance(result, AvailableFact)
    assert result.value.state is FeatureState.DISABLED


def test_overrides_do_not_erase_global_configuration() -> None:
    """Configured global authentication is independent of interface overrides."""
    result = fact(
        "router bfd\n   authentication mode md5 shared-secret profile ABSENT\n"
        "interface Ethernet1\n   bfd authentication mode disabled\n"
        "interface Ethernet2\n   bfd authentication mode simple shared-secret profile TEST\n"
    )
    assert isinstance(result, AvailableFact)
    assert result.value.state is FeatureState.ENABLED


@pytest.mark.parametrize(
    "config",
    [
        "router bfd\n   authentication mode\n",
        "interface Ethernet1\n   bfd authentication mode\n",
        "   bfd authentication mode md5 shared-secret profile TEST\n",
        "authentication mode md5 shared-secret profile TEST\n",
        "interface Ethernet1 extra\n   bfd authentication mode md5 shared-secret profile TEST\n",
    ],
)
def test_incomplete_required_configuration(config: str) -> None:
    """Synthetic malformed collection text cannot establish safe absence."""
    result = fact(config, interface="bfd authentication" in config)
    assert isinstance(result, UnavailableFact)
    assert result.problem is FactProblemKind.MALFORMED


@pytest.mark.parametrize("reverse", [False, True])
def test_complete_witness_survives_unrelated_error(reverse: bool) -> None:
    """Record ordering cannot erase independently established keyed authentication."""
    parts = [
        "interface Ethernet1\n   bfd authentication mode md5 shared-secret profile TEST\n",
        "interface Ethernet2\n   bfd authentication mode\n",
    ]
    result = fact("".join(reversed(parts) if reverse else parts), interface=True)
    assert isinstance(result, AvailableFact)
    assert result.value.state is FeatureState.ENABLED


@pytest.mark.parametrize(("output", "problem"), [(None, FactProblemKind.MISSING), ({}, FactProblemKind.MALFORMED)])
def test_response_failures(output: object, problem: FactProblemKind) -> None:
    """Missing/text-type failures cannot be interpreted as absence."""
    result = fact(output)
    assert isinstance(result, UnavailableFact)
    assert result.problem is problem


@pytest.mark.parametrize(
    ("error", "problem"),
    [
        ("Permission denied", FactProblemKind.COLLECTION_FAILED),
        ("This command is not supported on this hardware platform", FactProblemKind.UNSUPPORTED),
    ],
)
def test_collection_failure(error: str, problem: FactProblemKind) -> None:
    """Preserve the failed command and reason."""
    commands = tuple(command.model_copy() for command in BfdKeyedAuthenticationFact.commands)
    commands[0].output = {"adminDown": False}
    commands[1].output = None
    commands[1].errors = [error]
    commands[2].output = ""
    result = BfdKeyedAuthenticationFact.parse(commands)
    assert isinstance(result, UnavailableFact)
    assert result.problem is problem


@pytest.mark.parametrize(
    ("config", "error"),
    [
        ("router bgp 65000\n   bfd authentication mode md5 shared-secret profile TEST\n", False),
        ("management security\n   bfd authentication mode md5 shared-secret profile TEST\n", False),
        ("interface Ethernet1\n   description bfd authentication mode md5 shared-secret profile TEST\n", False),
        ("interface\n   bfd authentication mode md5 shared-secret profile TEST\n", True),
        ("   interface Ethernet1\n      bfd authentication mode md5 shared-secret profile TEST\n", True),
        ("interface Ethernet1\n   unrelated-submode\n      bfd authentication mode md5 shared-secret profile TEST\n", True),
        ("bfd authentication mode md5 shared-secret profile TEST\n", True),
    ],
)
def test_interface_parent_is_required(config: str, error: bool) -> None:
    """Synthetic misplaced directives cannot prove interface authentication."""
    result = fact(config, interface=True)
    if error:
        assert isinstance(result, UnavailableFact)
        assert result.problem is FactProblemKind.MALFORMED
    else:
        assert isinstance(result, AvailableFact)
        assert result.value.state is FeatureState.DISABLED


@pytest.mark.parametrize("indent", [" ", "   ", "\t"])
def test_authentication_requires_horizontal_indentation(indent: str) -> None:
    """Raw directive matches require actual leading whitespace and complete tokens."""
    result = fact(f"interface Ethernet1\n{indent}bfd authentication mode sha1 shared-secret profile TEST\n", interface=True)
    assert isinstance(result, AvailableFact)
    assert result.value.state is FeatureState.ENABLED


@pytest.mark.parametrize("separator", ["  ", "\t"])
def test_horizontal_token_separators(separator: str) -> None:
    """Synthetic whitespace variants preserve token and interface boundaries."""
    directive = separator.join(("bfd", "authentication", "mode", "md5", "shared-secret", "profile", "TEST"))
    result = fact(f"interface{separator}Ethernet1\n   {directive}\n", interface=True)
    assert isinstance(result, AvailableFact)
    assert result.value.state is FeatureState.ENABLED


@pytest.mark.parametrize("definition", [BfdAuthenticationFact, BfdKeyedAuthenticationFact])
@pytest.mark.parametrize("admin_down", [False, True])
def test_shared_administrative_gate(definition: type[BfdAuthenticationFact | BfdKeyedAuthenticationFact], admin_down: bool) -> None:
    """Both facts exclude administrative shutdown without requiring live peers."""
    commands = tuple(command.model_copy() for command in definition.commands)
    commands[0].output = {"adminDown": admin_down}
    commands[1].output = "router bfd\n   authentication mode md5 shared-secret profile TEST\n"
    commands[2].output = ""
    result = definition.parse(commands)
    assert isinstance(result, AvailableFact)
    assert result.value.state is (FeatureState.DISABLED if admin_down else FeatureState.ENABLED)


@pytest.mark.parametrize("summary", [None, {"adminDown": "unknown"}])
def test_complete_absence_does_not_require_summary(summary: object) -> None:
    """Complete persistent absence independently excludes authentication scope."""
    commands = tuple(command.model_copy() for command in BfdKeyedAuthenticationFact.commands)
    commands[0].output = cast("Any", summary)
    commands[1].output = ""
    commands[2].output = ""
    result = BfdKeyedAuthenticationFact.parse(commands)
    assert isinstance(result, AvailableFact)
    assert result.value.state is FeatureState.DISABLED


@pytest.mark.parametrize("definition", [BfdAuthenticationFact, BfdKeyedAuthenticationFact])
@pytest.mark.parametrize(("mode", "keyed_state"), [("simple", FeatureState.DISABLED), ("md5", FeatureState.ENABLED), ("sha1", FeatureState.ENABLED)])
@pytest.mark.parametrize("interface", [False, True])
def test_shared_mode_filter_keeps_legacy_simple(
    definition: type[BfdAuthenticationFact | BfdKeyedAuthenticationFact], keyed_state: FeatureState, mode: str, interface: bool
) -> None:
    """The default accepts any non-disabled mode; the keyed fact restricts modes."""
    commands = tuple(command.model_copy() for command in definition.commands)
    commands[0].output = {"adminDown": False}
    commands[1].output = "" if interface else f"router bfd\n   authentication mode {mode} shared-secret profile TEST\n"
    commands[2].output = f"interface Ethernet1\n   bfd authentication mode {mode} shared-secret profile TEST\n" if interface else ""
    result = definition.parse(commands)
    assert isinstance(result, AvailableFact)
    assert result.value.state is (FeatureState.ENABLED if definition is BfdAuthenticationFact else keyed_state)


@pytest.mark.parametrize("definition", [BfdAuthenticationFact, BfdKeyedAuthenticationFact])
def test_peer_disabled_does_not_enable_authentication(definition: type[BfdAuthenticationFact | BfdKeyedAuthenticationFact]) -> None:
    """Captured peer-level disablement is not configured authentication."""
    commands = tuple(command.model_copy() for command in definition.commands)
    commands[0].output = {"adminDown": False}
    commands[1].output = "router bfd\n   peer 198.51.100.206\n      authentication mode disabled\n"
    commands[2].output = ""
    result = definition.parse(commands)
    assert isinstance(result, AvailableFact)
    assert result.value.state is FeatureState.DISABLED


@pytest.mark.parametrize("positive", [False, True])
def test_summary_permission_failure(positive: bool) -> None:
    """Administrative evidence is required only when authentication is present."""
    commands = tuple(command.model_copy() for command in BfdKeyedAuthenticationFact.commands)
    commands[0].errors = ["Permission denied"]
    commands[1].output = "router bfd\n   authentication mode md5 shared-secret profile TEST\n" if positive else ""
    commands[2].output = ""
    result = BfdKeyedAuthenticationFact.parse(commands)
    if positive:
        assert isinstance(result, UnavailableFact)
        assert result.problem is FactProblemKind.COLLECTION_FAILED
        assert result.source.name == "show bfd peers summary"
    else:
        assert isinstance(result, AvailableFact)
        assert result.value.state is FeatureState.DISABLED


def test_summary_unsupported_excludes_feature() -> None:
    """The shared legacy unsupported-summary contract also applies to the keyed fact."""
    commands = tuple(command.model_copy() for command in BfdKeyedAuthenticationFact.commands)
    commands[0].errors = ["This command is not supported on this hardware platform"]
    commands[1].output = "router bfd\n   authentication mode md5 shared-secret profile TEST\n"
    commands[2].output = ""
    result = BfdKeyedAuthenticationFact.parse(commands)
    assert isinstance(result, AvailableFact)
    assert result.value.state is FeatureState.UNSUPPORTED
