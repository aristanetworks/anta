# Copyright (c) 2026 Arista Networks, Inc.
# Use of this source code is governed by the Apache License 2.0
# that can be found in the LICENSE file.
"""802.1X configuration normalization and typed fact views."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from enum import Enum
from typing import TYPE_CHECKING, ClassVar

from anta._advisory.facts.models import (
    CommandsFactDefinition,
    ConfigurationFact,
    ConfigurationState,
    Fact,
    FactProblemKind,
    FactSource,
    FactSourceKind,
    FeatureFact,
    FeatureName,
    FeatureRef,
    FeatureState,
    SubFeature,
    UnavailableFact,
)
from anta._advisory.optional_commands import OptionalAntaCommand, is_unsupported_optional_command
from anta._eos.parsing import ParseFail, ParseFailureReason, ParseResult, ParseSuccessful

if TYPE_CHECKING:
    from anta.models import AntaCommand

DOT1X_COMMAND = OptionalAntaCommand(command="show dot1x all", revision=1)


# Scoped consumers defer command errors; summary commands retain their existing contract.
DOT1X_ALL_COMMAND = DOT1X_COMMAND.model_copy(update={"defer_errors": True})


DOT1X_CONFIG_COMMAND = OptionalAntaCommand(command="show running-config section dot1x", ofmt="text", defer_errors=True)


_DOT1X_CHILD_INDENT = "   "


_DHCP_PROFILING_PREFIX = "radius av-pair dhcp "


class Dot1xPortControl(str, Enum):
    """Configured 802.1X port-control mode of an authenticator interface."""

    AUTO = "auto"
    FORCE_AUTHORIZED = "force-authorized"
    FORCE_UNAUTHORIZED = "force-unauthorized"


_PORT_CONTROL = {
    "controlled": Dot1xPortControl.AUTO,
    "forceAuth": Dot1xPortControl.FORCE_AUTHORIZED,
    "forceUnauth": Dot1xPortControl.FORCE_UNAUTHORIZED,
}


@dataclass(frozen=True, slots=True)
class Dot1xAuthenticatorInterface:
    """One configured authenticator and its port-control mode."""

    name: str
    port_control: Dot1xPortControl


@dataclass(frozen=True, slots=True)
class _InterfaceProblem:
    """A neutral parse failure with interface identity when known."""

    interface: str | None
    failure: ParseFail


@dataclass(frozen=True, slots=True)
class _AuthenticatorInventory:
    """Normalized authenticator records and explicit partial coverage."""

    interfaces: tuple[Dot1xAuthenticatorInterface, ...] = ()
    problems: tuple[_InterfaceProblem, ...] = ()


@dataclass(frozen=True, slots=True)
class Dot1xInterfaceProblem:
    """An incomplete observation retaining its interface identity when known."""

    interface: str | None
    fact: UnavailableFact[Dot1xControlledAuthenticatorInterfacesFact]


@dataclass(frozen=True, slots=True)
class Dot1xAuthenticatorInterfaceProblem:
    """One reported authenticator interface whose record could not be interpreted."""

    name: str | None
    problem: FactProblemKind


def _source(command: AntaCommand) -> FactSource:
    """Return the source for one command-derived fact."""
    return FactSource(command.command, FactSourceKind.COMMAND)


def _command_problem(command: AntaCommand) -> FactProblemKind | None:
    """Keep failed or unsupported collection distinct from observed configuration."""
    if is_unsupported_optional_command(command):
        return FactProblemKind.UNSUPPORTED
    return FactProblemKind.COLLECTION_FAILED if command.errors else None


def _parse_field(output: object, key: str) -> ParseResult[object]:
    """Distinguish a missing field from an explicitly malformed value."""
    if output is None:
        return ParseFail(ParseFailureReason.MISSING, "command output is missing")
    if not isinstance(output, Mapping):
        return ParseFail(ParseFailureReason.MALFORMED, "command output is not a mapping")
    if key not in output:
        return ParseFail(ParseFailureReason.MISSING, f"{key} is missing")
    return ParseSuccessful(output[key])


def _parse_boolean(output: object, key: str) -> ParseResult[bool]:
    """Decode one required boolean without inspecting unrelated fields."""
    parsed = _parse_field(output, key)
    if isinstance(parsed, ParseFail):
        return parsed
    if not isinstance(parsed.value, bool):
        return ParseFail(ParseFailureReason.MALFORMED, f"{key} is not a boolean")
    return ParseSuccessful(parsed.value)


def _parse_system_auth_control(output: object) -> ParseResult[bool]:
    """Normalize the global control prerequisite independently of interface data."""
    return _parse_boolean(output, "systemAuthControl")


def _parse_dynamic_authorization(output: object) -> ParseResult[bool]:
    """Normalize the global dynamic-authorization flag."""
    return _parse_boolean(output, "dynAuth")


def _parse_port_control(interface: object) -> ParseResult[Dot1xPortControl]:
    """Decode the required EOS mode once for every authenticator view."""
    if not isinstance(interface, Mapping):
        return ParseFail(ParseFailureReason.MALFORMED, "interface record is not a mapping")
    parsed = _parse_field(interface, "portControl")
    if isinstance(parsed, ParseFail):
        return parsed
    if not isinstance(parsed.value, str):
        return ParseFail(ParseFailureReason.MALFORMED, "portControl is not a string")
    mode = _PORT_CONTROL.get(parsed.value)
    if mode is None:
        return ParseFail(ParseFailureReason.INVALID, "portControl is not a recognized EOS mode")
    return ParseSuccessful(mode)


def _parse_authenticator_inventory(output: object) -> ParseResult[_AuthenticatorInventory]:
    """Decode all authenticators while preserving independent interface failures."""
    parsed = _parse_field(output, "interfaces")
    if isinstance(parsed, ParseFail):
        return parsed
    if not isinstance(parsed.value, Mapping):
        return ParseFail(ParseFailureReason.MALFORMED, "interfaces is not a mapping")
    interfaces: list[Dot1xAuthenticatorInterface] = []
    problems: list[_InterfaceProblem] = []
    for name, entry in parsed.value.items():
        if not isinstance(name, str) or not name or name.strip() != name:
            problems.append(_InterfaceProblem(None, ParseFail(ParseFailureReason.MALFORMED, "interface name is invalid")))
            continue
        mode = _parse_port_control(entry)
        if isinstance(mode, ParseFail):
            failure = ParseFail(mode.reason, f"show dot1x all interface {name!r}: {mode.detail}")
            problems.append(_InterfaceProblem(name, failure))
        else:
            interfaces.append(Dot1xAuthenticatorInterface(name, mode.value))
    return ParseSuccessful(_AuthenticatorInventory(tuple(interfaces), tuple(problems)))


def _parse_controlled_authenticator_inventory(output: object) -> ParseResult[_AuthenticatorInventory]:
    """Project controlled interfaces without discarding scoped uncertainty."""
    control = _parse_system_auth_control(output)
    if isinstance(control, ParseFail):
        return control
    if not control.value:
        return ParseSuccessful(_AuthenticatorInventory())
    parsed = _parse_authenticator_inventory(output)
    if isinstance(parsed, ParseFail):
        return parsed
    interfaces = tuple(interface for interface in parsed.value.interfaces if interface.port_control is Dot1xPortControl.AUTO)
    return ParseSuccessful(_AuthenticatorInventory(interfaces, parsed.value.problems))


def _representative_failure(problems: tuple[_InterfaceProblem, ...]) -> ParseFail:
    """Select a stable problem when no complete observation proves presence."""
    return min(problems, key=lambda item: (item.interface or "", item.failure.reason.value, item.failure.detail)).failure


def _parse_dot1x_controlled_authenticator(output: object) -> ParseResult[bool]:
    """Summarize controlled presence before relevant uncertainty or absence."""
    parsed = _parse_controlled_authenticator_inventory(output)
    if isinstance(parsed, ParseFail):
        return parsed
    if parsed.value.interfaces:
        return ParseSuccessful(value=True)
    if parsed.value.problems:
        return _representative_failure(parsed.value.problems)
    return ParseSuccessful(value=False)


@dataclass(frozen=True, slots=True)
class Dot1xSystemAuthControlFact(FeatureFact, CommandsFactDefinition["Dot1xSystemAuthControlFact"]):
    """Global 802.1X system authentication control."""

    feature: ClassVar[FeatureRef] = SubFeature(FeatureName.DOT1X, "system authentication control")
    key: ClassVar[str] = "feature.dot1x.system_auth_control"
    label: ClassVar[str] = "802.1X system authentication control state"
    commands: ClassVar[tuple[AntaCommand, ...]] = (DOT1X_ALL_COMMAND,)

    @classmethod
    def parse(cls, commands: tuple[AntaCommand, ...]) -> Fact[Dot1xSystemAuthControlFact]:
        """Project the shared global-control decoder into feature state."""
        (command,) = commands
        source = _source(command)
        problem = _command_problem(command)
        if problem is FactProblemKind.UNSUPPORTED:
            return cls(FeatureState.UNSUPPORTED).available(source)
        if problem is not None:
            return cls.unavailable(problem, source)
        parsed = _parse_system_auth_control(command.output)
        if isinstance(parsed, ParseFail):
            return cls.unavailable(FactProblemKind(parsed.reason.value), source)
        return cls(FeatureState.ENABLED if parsed.value else FeatureState.DISABLED).available(source)


@dataclass(frozen=True, slots=True)
class Dot1xAuthenticatorInterfacesFact(ConfigurationFact, CommandsFactDefinition["Dot1xAuthenticatorInterfacesFact"]):
    """Interfaces configured with the 802.1X authenticator PAE role.

    EOS lists an interface in ``show dot1x all`` exactly when ``dot1x pae authenticator``
    is configured on it, independently of global system authentication control, link
    state, current supplicants, and port-control mode. Each interface retains its
    configured port-control mode.

    One valid interface establishes the configured state despite other uninterpretable
    records, which are retained in ``problems``; ``interfaces`` is then incomplete.
    Without a valid interface, any such record leaves the fact unavailable.
    """

    feature: ClassVar[FeatureRef] = SubFeature(FeatureName.DOT1X, "authenticator interface")
    key: ClassVar[str] = "configuration.dot1x.authenticator_interfaces"
    label: ClassVar[str] = "802.1X authenticator interfaces"
    interfaces: tuple[Dot1xAuthenticatorInterface, ...] = ()
    problems: tuple[Dot1xAuthenticatorInterfaceProblem, ...] = ()
    commands: ClassVar[tuple[AntaCommand, ...]] = (DOT1X_ALL_COMMAND,)

    @classmethod
    def parse(cls, commands: tuple[AntaCommand, ...]) -> Fact[Dot1xAuthenticatorInterfacesFact]:
        """Project every normalized authenticator into configured evidence."""
        (command,) = commands
        source = _source(command)
        problem = _command_problem(command)
        if problem is not None:
            return cls.unavailable(problem, source)
        parsed = _parse_authenticator_inventory(command.output)
        if isinstance(parsed, ParseFail):
            return cls.unavailable(FactProblemKind(parsed.reason.value), source)
        inventory = parsed.value
        if not inventory.interfaces and inventory.problems:
            return cls.unavailable(FactProblemKind(_representative_failure(inventory.problems).reason.value), source)
        problems = tuple(Dot1xAuthenticatorInterfaceProblem(item.interface, FactProblemKind(item.failure.reason.value)) for item in inventory.problems)
        state = ConfigurationState.CONFIGURED if inventory.interfaces else ConfigurationState.NOT_CONFIGURED
        return cls(state, inventory.interfaces, problems).available(source)


@dataclass(frozen=True, slots=True)
class Dot1xControlledAuthenticatorInterfacesFact(CommandsFactDefinition["Dot1xControlledAuthenticatorInterfacesFact"]):
    """Globally enabled auto authenticators with interface-specific coverage.

    This scoped view uses the same effective control criteria as
    Dot1xControlledAuthenticatorFact, retaining partial evidence for correlation.
    Link state and live authentication sessions do not gate configured control.
    """

    key: ClassVar[str] = "configuration.dot1x.controlled_authenticator_interfaces"
    label: ClassVar[str] = "802.1X controlled authenticator interfaces"
    commands: ClassVar[tuple[AntaCommand, ...]] = (DOT1X_ALL_COMMAND,)
    interfaces: tuple[Dot1xAuthenticatorInterface, ...] = ()
    problems: tuple[Dot1xInterfaceProblem, ...] = ()

    @classmethod
    def parse(cls, commands: tuple[AntaCommand, ...]) -> Fact[Dot1xControlledAuthenticatorInterfacesFact]:
        """Project the shared inventory into controlled, scoped evidence."""
        (command,) = commands
        source = _source(command)
        problem = _command_problem(command)
        if problem is not None:
            return cls.unavailable(problem, source)
        parsed = _parse_controlled_authenticator_inventory(command.output)
        if isinstance(parsed, ParseFail):
            return cls.unavailable(FactProblemKind(parsed.reason.value), source)
        problems = tuple(
            Dot1xInterfaceProblem(item.interface, cls.unavailable(FactProblemKind(item.failure.reason.value), source)) for item in parsed.value.problems
        )
        return cls(parsed.value.interfaces, problems).available(source)


@dataclass(frozen=True, slots=True)
class Dot1xControlledAuthenticatorFact(FeatureFact, CommandsFactDefinition["Dot1xControlledAuthenticatorFact"]):
    """Effective 802.1X authenticator with controlled port state."""

    feature: ClassVar[FeatureRef] = SubFeature(FeatureName.DOT1X, "controlled authenticator")
    key: ClassVar[str] = "feature.dot1x.controlled_authenticator"
    label: ClassVar[str] = "802.1X controlled authenticator state"
    commands: ClassVar[tuple[AntaCommand, ...]] = (DOT1X_COMMAND,)

    @classmethod
    def parse(cls, commands: tuple[AntaCommand, ...]) -> Fact[Dot1xControlledAuthenticatorFact]:
        """Project the shared controlled inventory into a device-wide summary."""
        (command,) = commands
        source = _source(command)
        problem = _command_problem(command)
        if problem is FactProblemKind.UNSUPPORTED:
            return cls(FeatureState.UNSUPPORTED).available(source)
        if problem is not None:
            return cls.unavailable(problem, source)
        parsed = _parse_dot1x_controlled_authenticator(command.output)
        if isinstance(parsed, ParseFail):
            return cls.unavailable(FactProblemKind(parsed.reason.value), source)
        return cls(FeatureState.ENABLED if parsed.value else FeatureState.DISABLED).available(source)


@dataclass(frozen=True, slots=True)
class Dot1xDynamicAuthorizationFact(FeatureFact, CommandsFactDefinition["Dot1xDynamicAuthorizationFact"]):
    """Effective 802.1X dynamic authorization with an authenticator interface."""

    feature: ClassVar[FeatureRef] = SubFeature(FeatureName.DOT1X, "dynamic authorization authenticator")
    key: ClassVar[str] = "feature.dot1x.dynamic_authorization"
    label: ClassVar[str] = "802.1X dynamic-authorization state"
    commands: ClassVar[tuple[AntaCommand, ...]] = (DOT1X_COMMAND,)

    @classmethod
    def parse(cls, commands: tuple[AntaCommand, ...]) -> Fact[Dot1xDynamicAuthorizationFact]:
        """Require dynamic authorization and controlled-authenticator presence."""
        (command,) = commands
        source = _source(command)
        problem = _command_problem(command)
        if problem is FactProblemKind.UNSUPPORTED:
            return cls(FeatureState.UNSUPPORTED).available(source)
        if problem is not None:
            return cls.unavailable(problem, source)
        dynamic = _parse_dynamic_authorization(command.output)
        if isinstance(dynamic, ParseSuccessful) and not dynamic.value:
            return cls(FeatureState.DISABLED).available(source)
        controlled = _parse_dot1x_controlled_authenticator(command.output)
        if isinstance(controlled, ParseSuccessful) and not controlled.value:
            return cls(FeatureState.DISABLED).available(source)
        for parsed in (dynamic, controlled):
            if isinstance(parsed, ParseFail):
                return cls.unavailable(FactProblemKind(parsed.reason.value), source)
        return cls(FeatureState.ENABLED).available(source)


@dataclass(frozen=True, slots=True)
class Dot1xSupplicantInterface:
    """An interface enumerated by the configured supplicant observation."""

    name: str


@dataclass(frozen=True, slots=True)
class Dot1xSupplicantProblem:
    """A supplicant record whose interface scope is known or unavailable."""

    interface: str | None
    fact: UnavailableFact[Dot1xSupplicantInterfacesFact]


@dataclass(frozen=True, slots=True)
class Dot1xSupplicantInterfacesFact(CommandsFactDefinition["Dot1xSupplicantInterfacesFact"]):
    """Configured supplicant interfaces, independent of session and SSL state.

    The command enumerates configured bindings even with an unused supplicant
    and no SSL profile. Identity strings and TLS/session data are not retained.
    """

    key: ClassVar[str] = "configuration.dot1x.supplicant_interfaces"
    label: ClassVar[str] = "802.1X supplicant interfaces"
    commands: ClassVar[tuple[AntaCommand, ...]] = (OptionalAntaCommand(command="show dot1x supplicant", revision=1, defer_errors=True),)
    interfaces: tuple[Dot1xSupplicantInterface, ...] = ()
    problems: tuple[Dot1xSupplicantProblem, ...] = ()

    @classmethod
    # The command boundary and individual records retain distinct failures.
    # pylint: disable-next=too-many-return-statements
    def parse(cls, commands: tuple[AntaCommand, ...]) -> Fact[Dot1xSupplicantInterfacesFact]:  # noqa: PLR0911
        """Keep configured identities without interpreting authentication progress."""
        # Collection guards match the independent authenticator observation.
        # pylint: disable=duplicate-code
        (command,) = commands
        source = FactSource(command.command, FactSourceKind.COMMAND)
        if is_unsupported_optional_command(command):
            return cls.unavailable(FactProblemKind.UNSUPPORTED, source)
        if command.errors:
            return cls.unavailable(FactProblemKind.COLLECTION_FAILED, source)
        output = command.output
        if output is None:
            return cls.unavailable(FactProblemKind.MISSING, source)
        if not isinstance(output, Mapping):
            return cls.unavailable(FactProblemKind.MALFORMED, source)
        if "interfaces" not in output:
            return cls.unavailable(FactProblemKind.MISSING, source)
        entries = output["interfaces"]
        if not isinstance(entries, Mapping):
            return cls.unavailable(FactProblemKind.MALFORMED, source)
        interfaces: list[Dot1xSupplicantInterface] = []
        problems: list[Dot1xSupplicantProblem] = []
        for name, entry in entries.items():
            if not isinstance(name, str) or not name or name.strip() != name:
                problems.append(Dot1xSupplicantProblem(None, cls.unavailable(FactProblemKind.MALFORMED, source)))
            elif not isinstance(entry, Mapping):
                problems.append(Dot1xSupplicantProblem(name, cls.unavailable(FactProblemKind.MALFORMED, source)))
            else:
                interfaces.append(Dot1xSupplicantInterface(name))
        return cls(tuple(interfaces), tuple(problems)).available(source)


class Dot1xDhcpProfilingOption(str, Enum):
    """DHCP option forwarded to RADIUS by 802.1X device profiling."""

    HOSTNAME = "hostname"
    PARAMETER_REQUEST_LIST = "parameter-request-list"
    VENDOR_CLASS_ID = "vendor-class-id"


_DHCP_PROFILING_OPTIONS = {option.value: option for option in Dot1xDhcpProfilingOption}


def _dhcp_profiling_options(output: str) -> tuple[frozenset[Dot1xDhcpProfilingOption], frozenset[str]] | FactProblemKind:
    """Return the recognized and unrecognized DHCP profiling options configured directly under the global ``dot1x`` block.

    Unexpected indentation leaves the block boundaries unknown, so no option can be trusted.
    """
    options: set[Dot1xDhcpProfilingOption] = set()
    unrecognized: set[str] = set()
    in_dot1x = False
    for line in output.splitlines():
        if not line.strip() or line.strip() == "!":
            continue
        if not line.startswith((" ", "\t")):
            in_dot1x = line.rstrip() == "dot1x"
            continue
        if not in_dot1x:
            continue
        indent = line[: len(line) - len(line.lstrip())]
        if "\t" in indent or len(indent) % len(_DOT1X_CHILD_INDENT):
            return FactProblemKind.MALFORMED
        if indent != _DOT1X_CHILD_INDENT:
            continue
        statement = line.strip()
        if statement.startswith(_DHCP_PROFILING_PREFIX):
            value = statement.removeprefix(_DHCP_PROFILING_PREFIX)
            option = _DHCP_PROFILING_OPTIONS.get(value)
            if option is None:
                unrecognized.add(value)
            else:
                options.add(option)
    return frozenset(options), frozenset(unrecognized)


@dataclass(frozen=True, slots=True)
class Dot1xDhcpProfilingFact(ConfigurationFact, CommandsFactDefinition["Dot1xDhcpProfilingFact"]):
    """DHCP device-profiling options forwarded by 802.1X as RADIUS attributes.

    No structured EOS command reports these statements, so the fact reads the persistent
    ``radius av-pair dhcp`` statements of the global ``dot1x`` configuration block.

    One recognized option establishes the configured state despite unrecognized options,
    which are retained in ``unrecognized``. Without a recognized option, any unrecognized
    option leaves the fact unavailable.
    """

    feature: ClassVar[FeatureRef] = SubFeature(FeatureName.DOT1X, "DHCP profiling")
    key: ClassVar[str] = "configuration.dot1x.dhcp_profiling"
    label: ClassVar[str] = "802.1X DHCP profiling configuration"
    options: frozenset[Dot1xDhcpProfilingOption] = frozenset()
    unrecognized: frozenset[str] = frozenset()
    commands: ClassVar[tuple[AntaCommand, ...]] = (DOT1X_CONFIG_COMMAND,)

    @classmethod
    def parse(cls, commands: tuple[AntaCommand, ...]) -> Fact[Dot1xDhcpProfilingFact]:
        """Normalize every configured DHCP profiling option."""
        (command,) = commands
        source = _source(command)
        problem = _command_problem(command)
        if problem is not None:
            return cls.unavailable(problem, source)
        if command.output is None:
            return cls.unavailable(FactProblemKind.MISSING, source)
        if not isinstance(command.output, str):
            return cls.unavailable(FactProblemKind.MALFORMED, source)
        observations = _dhcp_profiling_options(command.output)
        if isinstance(observations, FactProblemKind):
            return cls.unavailable(observations, source)
        options, unrecognized = observations
        if not options and unrecognized:
            return cls.unavailable(FactProblemKind.INVALID, source)
        state = ConfigurationState.CONFIGURED if options else ConfigurationState.NOT_CONFIGURED
        return cls(state, options, unrecognized).available(source)
