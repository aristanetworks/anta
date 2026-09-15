# Copyright (c) 2026 Arista Networks, Inc.
# Use of this source code is governed by the Apache License 2.0
# that can be found in the LICENSE file.
"""Facts derived from EOS and component software metadata."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from typing import ClassVar, Generic, TypeVar, cast

from anta._advisory.facts.models import (
    CommandsFactDefinition,
    ComponentSoftwareFact,
    Fact,
    FactProblemKind,
    FactSource,
    FactSourceKind,
    MitigationFact,
    MitigationState,
)
from anta._advisory.optional_commands import OptionalAntaCommand, is_unsupported_optional_command
from anta.models import AntaCommand

PackageFactT = TypeVar("PackageFactT", bound=ComponentSoftwareFact)
HotfixFactT = TypeVar("HotfixFactT", bound=MitigationFact)


class PackageVersionFact(ComponentSoftwareFact, CommandsFactDefinition[PackageFactT], Generic[PackageFactT]):
    """Base fact for one package reported by ``show version detail``."""

    version: str
    key: ClassVar[str] = "software.package.version"
    label: ClassVar[str] = "package version"
    commands: ClassVar[tuple[AntaCommand, ...]] = (AntaCommand(command="show version detail", revision=1),)
    package_name: ClassVar[str]
    component: ClassVar[str]

    @classmethod
    # pylint: disable-next=too-many-return-statements
    def parse(cls, commands: tuple[AntaCommand, ...]) -> Fact[PackageFactT]:  # noqa: PLR0911
        """Extract and normalize the declared package version."""
        (command,) = commands
        source = FactSource(command.command, FactSourceKind.COMMAND)
        details = command.json_output.get("details")
        if details is None:
            return cls.unavailable(FactProblemKind.MISSING, source)
        if not isinstance(details, Mapping):
            return cls.unavailable(FactProblemKind.MALFORMED, source)
        packages = details.get("packages")
        if packages is None:
            return cls.unavailable(FactProblemKind.MISSING, source)
        if not isinstance(packages, Mapping):
            return cls.unavailable(FactProblemKind.MALFORMED, source)
        package = packages.get(cls.package_name)
        if package is None:
            return cls.unavailable(FactProblemKind.MISSING, source)
        if not isinstance(package, Mapping):
            return cls.unavailable(FactProblemKind.MALFORMED, source)
        version = package.get("version")
        if version is None:
            return cls.unavailable(FactProblemKind.MISSING, source)
        if not isinstance(version, str) or not version.strip():
            return cls.unavailable(FactProblemKind.MALFORMED, source)
        return cls.available(cast("PackageFactT", cls(version.strip())), source)


@dataclass(frozen=True, slots=True)
class TerminAttrVersionFact(PackageVersionFact["TerminAttrVersionFact"]):
    """TerminAttr package version."""

    component: ClassVar[str] = "TerminAttr"
    key: ClassVar[str] = "software.terminattr.version"
    label: ClassVar[str] = "TerminAttr version"
    commands: ClassVar[tuple[AntaCommand, ...]] = PackageVersionFact.commands
    package_name: ClassVar[str] = "TerminAttr-core"


@dataclass(frozen=True, slots=True)
class OpenSshClientVersionFact(PackageVersionFact["OpenSshClientVersionFact"]):
    """OpenSSH client package version."""

    component: ClassVar[str] = "openssh-clients"
    key: ClassVar[str] = "software.openssh_clients.version"
    label: ClassVar[str] = "OpenSSH client version"
    commands: ClassVar[tuple[AntaCommand, ...]] = PackageVersionFact.commands
    package_name: ClassVar[str] = "openssh-clients"


@dataclass(frozen=True, slots=True)
class OpenSshServerVersionFact(PackageVersionFact["OpenSshServerVersionFact"]):
    """OpenSSH server package version."""

    component: ClassVar[str] = "openssh-server"
    key: ClassVar[str] = "software.openssh_server.version"
    label: ClassVar[str] = "OpenSSH server version"
    commands: ClassVar[tuple[AntaCommand, ...]] = PackageVersionFact.commands
    package_name: ClassVar[str] = "openssh-server"


class PersistentHotfixFact(MitigationFact, CommandsFactDefinition[HotfixFactT], Generic[HotfixFactT]):
    """Base fact for one installed and boot-persistent advisory SWIX hotfix."""

    state: MitigationState
    key: ClassVar[str] = "mitigation.hotfix"
    label: ClassVar[str] = "persistent SWIX hotfix"
    extension_name: ClassVar[str]
    commands: ClassVar[tuple[AntaCommand, ...]] = (
        OptionalAntaCommand(command="show extensions", revision=2),
        OptionalAntaCommand(command="show boot-extensions", revision=1),
    )

    @classmethod
    def _installed_extension(cls, command: AntaCommand) -> Fact[HotfixFactT] | Mapping[str, object]:
        """Return installed extension data or a result decided by extension state alone."""
        source = FactSource(command.command, FactSourceKind.COMMAND)
        if is_unsupported_optional_command(command):
            return cls.unavailable(FactProblemKind.UNSUPPORTED, source)
        extensions = command.json_output.get("extensions")
        if extensions is None:
            return cls.unavailable(FactProblemKind.MISSING, source)
        if not isinstance(extensions, Mapping):
            return cls.unavailable(FactProblemKind.MALFORMED, source)

        extension = extensions.get(cls.extension_name)
        if extension is None:
            return cls.available(cast("HotfixFactT", cls(MitigationState.INEFFECTIVE)), source)
        if not isinstance(extension, Mapping) or not isinstance(extension.get("status"), str):
            return cls.unavailable(FactProblemKind.MALFORMED, source)
        return extension

    @classmethod
    def _boot_state(cls, command: AntaCommand) -> Fact[HotfixFactT]:
        """Return persistence state from boot-extension output."""
        source = FactSource(command.command, FactSourceKind.COMMAND)
        if is_unsupported_optional_command(command):
            return cls.unavailable(FactProblemKind.UNSUPPORTED, source)
        boot_extensions = command.json_output.get("extensions")
        if boot_extensions is None:
            return cls.unavailable(FactProblemKind.MISSING, source)
        if not isinstance(boot_extensions, list) or not all(isinstance(item, str) for item in boot_extensions):
            return cls.unavailable(FactProblemKind.MALFORMED, source)
        state = MitigationState.EFFECTIVE if cls.extension_name in {item.strip() for item in boot_extensions} else MitigationState.INEFFECTIVE
        return cls.available(cast("HotfixFactT", cls(state)), source)

    @classmethod
    def parse(cls, commands: tuple[AntaCommand, ...]) -> Fact[HotfixFactT]:
        """Verify that the advisory SWIX is installed and enabled for boot."""
        extensions_command, boot_extensions_command = commands
        extension = cls._installed_extension(extensions_command)
        if not isinstance(extension, Mapping):
            return extension
        if extension["status"] != "installed":
            source = FactSource(extensions_command.command, FactSourceKind.COMMAND)
            return cls.available(cast("HotfixFactT", cls(MitigationState.INEFFECTIVE)), source)
        return cls._boot_state(boot_extensions_command)


@dataclass(frozen=True, slots=True)
class SA173HotfixFact(PersistentHotfixFact["SA173HotfixFact"]):
    """Installed and boot-persistent SA173 SWIX hotfix."""

    key: ClassVar[str] = "mitigation.hotfix.sa173"
    label: ClassVar[str] = "SA173 SWIX hotfix"
    commands: ClassVar[tuple[AntaCommand, ...]] = PersistentHotfixFact.commands
    extension_name: ClassVar[str] = "sa173-SecurityAdvisory173_CVE-2026-73455.swix"


@dataclass(frozen=True, slots=True)
class SA171HotfixFact(PersistentHotfixFact["SA171HotfixFact"]):
    """Installed and boot-persistent SA171 CVE-2026-73435 SWIX hotfix."""

    key: ClassVar[str] = "mitigation.hotfix.sa171_cve_2026_73435"
    label: ClassVar[str] = "SA171 CVE-2026-73435 SWIX hotfix"
    commands: ClassVar[tuple[AntaCommand, ...]] = PersistentHotfixFact.commands
    extension_name: ClassVar[str] = "sa171-SecurityAdvisory171_CVE-2026-73435.swix"
