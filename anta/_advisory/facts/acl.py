# Copyright (c) 2026 Arista Networks, Inc.
# Use of this source code is governed by the Apache License 2.0
# that can be found in the LICENSE file.
"""Facts derived from EOS access-control-list state."""

from __future__ import annotations

import re
from typing import TYPE_CHECKING

from anta._advisory.facts.models import (
    CommandsFactDefinition,
    ConfigurationState,
    ConfigurationValue,
    Fact,
    FactProblemKind,
    FactSource,
    FactSourceKind,
    FeatureName,
    SubFeature,
)
from anta._advisory.optional_commands import OptionalAntaCommand, is_unsupported_optional_command

if TYPE_CHECKING:
    from anta.models import AntaCommand

ACL_COMMAND = OptionalAntaCommand(command="show platform trident tcam acl", ofmt="text")
ACL_SECTION = re.compile(r"^=== (?P<family>IP|MAC|IPv6) ACLs on switch (?P<switchcard>\S+) ===$")
INGRESS_ACL = re.compile(r"^INGRESS ACL (?P<name>.+?) uses \d+ entries$")
VLAN_ASSIGNMENT = re.compile(r"^Assigned to VLANs: (?P<vlans>.+)$")
RACLID = re.compile(r"^Shared ACL Identifier \(RACLID\): (?P<raclid>.+)$")
REQUIRED_SWITCH_CARD_COUNT = 2


def _shared_svi_acl_state(output: str) -> ConfigurationState | None:  # noqa: C901
    """Return whether a well-formed dual-switch-card output contains a shared SVI ACL."""
    family: str | None = None
    switchcard: str | None = None
    entry: dict[str, str] | None = None
    switchcards: set[str] = set()
    assignments: dict[tuple[str, str, str, str], set[str]] = {}
    malformed = False

    def finish_entry() -> None:
        nonlocal entry, malformed
        current = entry
        if current is None:
            return
        if family is None or switchcard is None or "vlans" not in current or "raclid" not in current:
            malformed = True
            entry = None
            return
        vlans = re.sub(r"\s+", "", current["vlans"])
        raclid = current["raclid"].strip()
        if vlans.lower() != "none" and raclid.lower() != "none":
            if not raclid.isdigit():
                malformed = True
            else:
                assignments.setdefault((family, current["name"], vlans, raclid), set()).add(switchcard)
        entry = None

    for raw_line in output.splitlines():
        line = raw_line.strip()
        if match := ACL_SECTION.fullmatch(line):
            finish_entry()
            family = match.group("family")
            section_switchcard = match.group("switchcard")
            switchcard = section_switchcard
            if family == "MAC":
                family = None
                switchcard = None
            else:
                switchcards.add(section_switchcard)
            continue
        if match := INGRESS_ACL.fullmatch(line):
            if family is None or switchcard is None:
                continue
            finish_entry()
            entry = {"name": match.group("name")}
            continue
        if entry is None:
            continue
        if match := VLAN_ASSIGNMENT.fullmatch(line):
            entry["vlans"] = match.group("vlans")
        elif match := RACLID.fullmatch(line):
            entry["raclid"] = match.group("raclid")
    finish_entry()

    if any(len(assigned) >= REQUIRED_SWITCH_CARD_COUNT for assigned in assignments.values()):
        return ConfigurationState.CONFIGURED
    if malformed or len(switchcards) < REQUIRED_SWITCH_CARD_COUNT or assignments:
        return None
    return ConfigurationState.NOT_CONFIGURED


class SharedSviIngressAclFact(CommandsFactDefinition[ConfigurationValue]):
    """Shared IPv4 or IPv6 ingress ACL configuration on an SVI across switch cards."""

    key = "configuration.acl.shared_svi_ingress"
    label = "shared SVI ingress ACL configuration"
    commands = (ACL_COMMAND,)

    @classmethod
    def parse(cls, commands: tuple[AntaCommand, ...]) -> Fact[ConfigurationValue]:
        """Normalize the unconverted Trident ACL output without retaining ACL inventories."""
        (command,) = commands
        source = FactSource(command.command, FactSourceKind.COMMAND)
        if is_unsupported_optional_command(command):
            return cls.unavailable(FactProblemKind.UNSUPPORTED, source)
        state = _shared_svi_acl_state(command.text_output)
        if state is None:
            return cls.unavailable(FactProblemKind.MALFORMED, source)
        return cls.available(ConfigurationValue(SubFeature(FeatureName.ACL, "shared SVI ingress"), state), source)
