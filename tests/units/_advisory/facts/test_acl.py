# Copyright (c) 2026 Arista Networks, Inc.
# Use of this source code is governed by the Apache License 2.0
# that can be found in the LICENSE file.
"""Unit tests for facts normalized from EOS ACL output."""

from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

from anta._advisory.facts.acl import SharedSviIngressAclFact
from anta._advisory.facts.models import AvailableFact, ConfigurationState, FactProblemKind, UnavailableFact
from tests.units.anta_tests.advisories import OfflineAntaDevice

if TYPE_CHECKING:
    from anta.models import AntaCommand

SHARED_ACL_OUTPUT = """\
=== IP ACLs on switch SwitchcardCes1/0 ===
INGRESS ACL TEST_ACL uses 4 entries
    Assigned to VLANs: 100
    Shared ACL Identifier (RACLID): 1
    Assigned to ports: None
=== MAC ACLs on switch SwitchcardCes1/0 ===
=== IPv6 ACLs on switch SwitchcardCes1/0 ===
=== IP ACLs on switch SwitchcardCes2/0 ===
INGRESS ACL TEST_ACL uses 4 entries
    Assigned to VLANs: 100
    Shared ACL Identifier (RACLID): 1
    Assigned to ports: None
=== MAC ACLs on switch SwitchcardCes2/0 ===
=== IPv6 ACLs on switch SwitchcardCes2/0 ===
"""
EMPTY_ACL_OUTPUT = """\
=== IP ACLs on switch SwitchcardCes1/0 ===
=== MAC ACLs on switch SwitchcardCes1/0 ===
=== IPv6 ACLs on switch SwitchcardCes1/0 ===
=== IP ACLs on switch SwitchcardCes2/0 ===
=== MAC ACLs on switch SwitchcardCes2/0 ===
=== IPv6 ACLs on switch SwitchcardCes2/0 ===
"""


def acl_command(output: str) -> AntaCommand:
    """Return the ACL command populated with text output."""
    command = SharedSviIngressAclFact.commands[0].model_copy()
    command.output = output
    return command


@pytest.mark.parametrize(
    ("output", "state"),
    [(SHARED_ACL_OUTPUT, ConfigurationState.CONFIGURED), (EMPTY_ACL_OUTPUT, ConfigurationState.NOT_CONFIGURED)],
)
def test_shared_svi_acl_states(output: str, state: ConfigurationState) -> None:
    """Normalize shared and empty dual-switch-card ACL output."""
    fact = SharedSviIngressAclFact.derive(OfflineAntaDevice("unit-test"), (acl_command(output),))

    assert isinstance(fact, AvailableFact)
    assert fact.value.state is state


@pytest.mark.parametrize("output", ["", SHARED_ACL_OUTPUT.replace("(RACLID): 1", "(RACLID): 2", 1)])
def test_shared_svi_acl_rejects_incomplete_or_inconsistent_output(output: str) -> None:
    """Reject output that cannot prove a clean negative or shared assignment."""
    fact = SharedSviIngressAclFact.derive(OfflineAntaDevice("unit-test"), (acl_command(output),))

    assert isinstance(fact, UnavailableFact)
    assert fact.problem is FactProblemKind.MALFORMED


def test_shared_svi_acl_ignores_mac_acl_entries() -> None:
    """Do not interpret a MAC ACL in the intervening section as an IP assignment."""
    output = EMPTY_ACL_OUTPUT.replace(
        "=== MAC ACLs on switch SwitchcardCes1/0 ===",
        "=== MAC ACLs on switch SwitchcardCes1/0 ===\nINGRESS ACL TEST_ACL uses 4 entries\n    Assigned to VLANs: 100\n    Shared ACL Identifier (RACLID): 1",
    ).replace(
        "=== MAC ACLs on switch SwitchcardCes2/0 ===",
        "=== MAC ACLs on switch SwitchcardCes2/0 ===\nINGRESS ACL TEST_ACL uses 4 entries\n    Assigned to VLANs: 100\n    Shared ACL Identifier (RACLID): 1",
    )

    fact = SharedSviIngressAclFact.derive(OfflineAntaDevice("unit-test"), (acl_command(output),))

    assert isinstance(fact, AvailableFact)
    assert fact.value.state is ConfigurationState.NOT_CONFIGURED


def test_shared_svi_acl_unsupported_remains_unavailable() -> None:
    """Do not infer ACL absence from an unsupported hardware-specific command."""
    command = acl_command("")
    command.output = None
    command.errors = ["This command is not supported on this hardware platform"]

    fact = SharedSviIngressAclFact.derive(OfflineAntaDevice("unit-test"), (command,))

    assert isinstance(fact, UnavailableFact)
    assert fact.problem is FactProblemKind.UNSUPPORTED
