# Copyright (c) 2026 Arista Networks, Inc.
# Use of this source code is governed by the Apache License 2.0
# that can be found in the LICENSE file.
"""Observed eAPI enablement and explicit HTTP default-service configuration."""

from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

from anta._advisory.facts.http import EapiEnabledFact, HttpDefaultServicesFact
from anta._advisory.facts.models import AvailableFact, FactProblemKind, FeatureState, UnavailableFact
from tests.units.anta_tests.advisories import OfflineAntaDevice

if TYPE_CHECKING:
    from anta.models import AntaCommand

LEGACY_ENABLED = """management api http-commands
   protocol https port 443
   no protocol http port 80
   no protocol http localhost port 8080
   no protocol unix-socket
   qos dscp 0
   no log-level
   default-services
   no header csp frame-ancestors
   no cors allowed-origin
   no protocol https ssl profile
   no shutdown
   session timeout 1440 minutes
"""
SHARED_DISABLED = """management api http-commands
   no shutdown
   session timeout 1440 minutes
   !
   vrf default
      no shutdown
management http-server
   protocol https port 443
   no protocol http port 80
   no protocol http localhost port 8080
   no protocol unix-socket
   qos dscp 0
   no log-level
   no default-services
   no header csp frame-ancestors
   no protocol https ssl profile
   !
   vrf default
      default shutdown
"""


def command_with(fact: type[EapiEnabledFact | HttpDefaultServicesFact], output: object) -> AntaCommand:
    """Attach a payload to the declared command, including intentionally invalid shapes."""
    return fact.required_commands()[0].model_copy(update={"output": output})


def test_command_contracts() -> None:
    """Pin API JSON revision one and inspect explicit full-default flags in both carriers."""
    (api,) = EapiEnabledFact.required_commands()
    assert api.command == "show management api http-commands"
    assert api.revision == 1
    assert api.ofmt == "json"
    (config,) = HttpDefaultServicesFact.required_commands()
    assert config.command == "show running-config all | section ^management (api http-commands|http-server)"
    assert config.ofmt == "text"


@pytest.mark.parametrize(
    ("output", "state"),
    [
        ({"enabled": True}, FeatureState.ENABLED),
        ({"enabled": False}, FeatureState.DISABLED),
        ({"enabled": True, "httpsServer": {"configured": True, "running": False}}, FeatureState.ENABLED),
        ({"enabled": True, "vrfs": [], "httpServer": {"configured": False}, "unixSocketServer": {"configured": False}}, FeatureState.ENABLED),
        ({"enabled": False, "httpsServer": "unrelated malformed listener"}, FeatureState.DISABLED),
    ],
)
def test_configured_eapi_enablement(output: dict[str, object], state: FeatureState) -> None:
    """The neutral configured-service fact does not infer listener or runtime policy."""
    fact = EapiEnabledFact.derive(OfflineAntaDevice("unit-test"), (command_with(EapiEnabledFact, output),))
    assert isinstance(fact, AvailableFact)
    assert fact.value.state is state
    assert fact.source.name == "show management api http-commands"


@pytest.mark.parametrize(
    ("output", "problem"),
    [
        (None, FactProblemKind.MISSING),
        ({}, FactProblemKind.MISSING),
        ({"enabled": None}, FactProblemKind.MISSING),
        ("Enabled: Yes", FactProblemKind.MALFORMED),
        ([], FactProblemKind.MALFORMED),
        ({"enabled": "true"}, FactProblemKind.MALFORMED),
        ({"enabled": 0}, FactProblemKind.MALFORMED),
        ({"enabled": 1}, FactProblemKind.MALFORMED),
    ],
)
def test_eapi_unavailable_evidence(output: object, problem: FactProblemKind) -> None:
    """Missing or malformed service flags never imply disablement."""
    fact = EapiEnabledFact.derive(OfflineAntaDevice("unit-test"), (command_with(EapiEnabledFact, output),))
    assert isinstance(fact, UnavailableFact)
    assert fact.problem is problem


@pytest.mark.parametrize(
    ("output", "state"),
    [
        (LEGACY_ENABLED, FeatureState.ENABLED),
        (LEGACY_ENABLED.replace("   default-services", "   no default-services"), FeatureState.DISABLED),
        (SHARED_DISABLED, FeatureState.DISABLED),
        (SHARED_DISABLED.replace("   no default-services", "   default-services"), FeatureState.ENABLED),
        ("management http-server\n   default-services\n", FeatureState.ENABLED),
        ("management http-server\n   no default-services\n", FeatureState.DISABLED),
        ("management api http-commands\n   default-services\nmanagement http-server\n   default-services\n", FeatureState.ENABLED),
        (LEGACY_ENABLED + "   vrf default-services\n      no shutdown\n", FeatureState.ENABLED),
        (LEGACY_ENABLED + "   protocol https ssl profile default-services\n", FeatureState.ENABLED),
    ],
)
def test_explicit_default_service_settings(output: str, state: FeatureState) -> None:
    """Read the actual carrier while ignoring unrelated protocols and VRF names."""
    fact = HttpDefaultServicesFact.derive(OfflineAntaDevice("unit-test"), (command_with(HttpDefaultServicesFact, output),))
    assert isinstance(fact, AvailableFact)
    assert fact.value.state is state
    assert fact.source.name == "show running-config all | section ^management (api http-commands|http-server)"


@pytest.mark.parametrize(
    ("output", "problem"),
    [
        (None, FactProblemKind.MISSING),
        ("", FactProblemKind.MISSING),
        ("\n!\n", FactProblemKind.MISSING),
        ({"defaultServices": False}, FactProblemKind.MALFORMED),
        ([], FactProblemKind.MALFORMED),
        ("management api http-commands\n   no shutdown\n", FactProblemKind.MISSING),
        ("management api http-commands\n   no shutdown\nmanagement http-server\n   protocol https port 443\n", FactProblemKind.MISSING),
        ("management ssh\n   default-services\n", FactProblemKind.MALFORMED),
        ("   default-services\n", FactProblemKind.MALFORMED),
        ("management http-server\n      no default-services\n", FactProblemKind.INVALID),
        ("management http-server\n   no default-services extra\n", FactProblemKind.INVALID),
        ("management http-server\n   default default-services\n", FactProblemKind.INVALID),
        ("management http-server\n   default-services\n   default-services\n", FactProblemKind.MALFORMED),
        ("management http-server\n   default-services\nmanagement http-server\n", FactProblemKind.MALFORMED),
    ],
)
def test_default_service_unavailable_evidence(output: object, problem: FactProblemKind) -> None:
    """Omission, wrong scope, malformed headings and incomplete clauses cannot prove safety."""
    fact = HttpDefaultServicesFact.derive(OfflineAntaDevice("unit-test"), (command_with(HttpDefaultServicesFact, output),))
    assert isinstance(fact, UnavailableFact)
    assert fact.problem is problem


@pytest.mark.parametrize("reverse", [False, True])
def test_conflicting_carrier_settings(reverse: bool) -> None:
    """Conflicting reports of one global setting invalidate that setting in either order."""
    sections = ["management api http-commands\n   default-services\n", "management http-server\n   no default-services\n"]
    if reverse:
        sections.reverse()
    fact = HttpDefaultServicesFact.derive(OfflineAntaDevice("unit-test"), (command_with(HttpDefaultServicesFact, "".join(sections)),))
    assert isinstance(fact, UnavailableFact)
    assert fact.problem is FactProblemKind.CONTRADICTORY
    assert {observation.state for observation in fact.observations} == {FeatureState.ENABLED, FeatureState.DISABLED}


@pytest.mark.parametrize("definition", [EapiEnabledFact, HttpDefaultServicesFact])
@pytest.mark.parametrize(
    ("errors", "problem"),
    [
        (["could not run command"], FactProblemKind.COLLECTION_FAILED),
        (["This command is not supported on this hardware platform"], FactProblemKind.UNSUPPORTED),
        (["This command is not supported on this hardware platform", "could not run command"], FactProblemKind.COLLECTION_FAILED),
    ],
)
def test_command_failures(definition: type[EapiEnabledFact | HttpDefaultServicesFact], errors: list[str], problem: FactProblemKind) -> None:
    """Collection errors take precedence over a stale valid payload."""
    payload = {"enabled": True} if definition is EapiEnabledFact else LEGACY_ENABLED
    command = command_with(definition, payload).model_copy(update={"errors": errors})
    fact = definition.derive(OfflineAntaDevice("unit-test"), (command,))
    assert isinstance(fact, UnavailableFact)
    assert fact.problem is problem
    assert fact.source.name == command.command


@pytest.mark.parametrize("definition", [EapiEnabledFact, HttpDefaultServicesFact])
def test_missing_command(definition: type[EapiEnabledFact | HttpDefaultServicesFact]) -> None:
    """An absent command response is a collection failure, not a default setting."""
    fact = definition.derive(OfflineAntaDevice("unit-test"))
    assert isinstance(fact, UnavailableFact)
    assert fact.problem is FactProblemKind.COLLECTION_FAILED
