# Copyright (c) 2026 Arista Networks, Inc.
# Use of this source code is governed by the Apache License 2.0
# that can be found in the LICENSE file.
"""Facts derived from EOS and component software metadata."""

from __future__ import annotations

from collections.abc import Mapping
from typing import ClassVar

from anta._advisory.facts.models import (
    CommandsFactDefinition,
    ComponentSoftwareVersion,
    Fact,
    FactProblemKind,
    FactSource,
    FactSourceKind,
    MitigationState,
    MitigationValue,
)
from anta._advisory.optional_commands import OptionalAntaCommand, is_unsupported_optional_command
from anta.models import AntaCommand


class PackageVersionFact(CommandsFactDefinition[ComponentSoftwareVersion]):
    """Base fact for one package reported by ``show version detail``."""

    key = "software.package.version"
    label = "package version"
    commands = (AntaCommand(command="show version detail", revision=1),)
    package_name: ClassVar[str]
    component_name: ClassVar[str]

    @classmethod
    # pylint: disable-next=too-many-return-statements
    def parse(cls, commands: tuple[AntaCommand, ...]) -> Fact[ComponentSoftwareVersion]:  # noqa: PLR0911
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
        return cls.available(ComponentSoftwareVersion(cls.component_name, version.strip()), source)


class TerminAttrVersionFact(PackageVersionFact):
    """TerminAttr package version."""

    key = "software.terminattr.version"
    label = "TerminAttr version"
    package_name = "TerminAttr-core"
    component_name = "TerminAttr"


class OpenSshClientVersionFact(PackageVersionFact):
    """OpenSSH client package version."""

    key = "software.openssh_clients.version"
    label = "OpenSSH client version"
    package_name = "openssh-clients"
    component_name = "openssh-clients"


class OpenSshServerVersionFact(PackageVersionFact):
    """OpenSSH server package version."""

    key = "software.openssh_server.version"
    label = "OpenSSH server version"
    package_name = "openssh-server"
    component_name = "openssh-server"


class PersistentHotfixFact(CommandsFactDefinition[MitigationValue]):
    """Base fact for one installed and boot-persistent advisory SWIX hotfix."""

    key = "mitigation.hotfix"
    label = "persistent SWIX hotfix"
    extension_name: ClassVar[str]
    commands = (
        OptionalAntaCommand(command="show extensions", revision=2),
        OptionalAntaCommand(command="show boot-extensions", revision=1),
    )

    @classmethod
    def _installed_extension(cls, command: AntaCommand) -> Fact[MitigationValue] | Mapping[str, object]:
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
            return cls.available(MitigationValue(MitigationState.INEFFECTIVE), source)
        if not isinstance(extension, Mapping) or not isinstance(extension.get("status"), str):
            return cls.unavailable(FactProblemKind.MALFORMED, source)
        return extension

    @classmethod
    def _boot_state(cls, command: AntaCommand) -> Fact[MitigationValue]:
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
        return cls.available(MitigationValue(state), source)

    @classmethod
    def parse(cls, commands: tuple[AntaCommand, ...]) -> Fact[MitigationValue]:
        """Verify that the advisory SWIX is installed and enabled for boot."""
        extensions_command, boot_extensions_command = commands
        extension = cls._installed_extension(extensions_command)
        if not isinstance(extension, Mapping):
            return extension
        if extension["status"] != "installed":
            source = FactSource(extensions_command.command, FactSourceKind.COMMAND)
            return cls.available(MitigationValue(MitigationState.INEFFECTIVE), source)
        return cls._boot_state(boot_extensions_command)


class SA173HotfixFact(PersistentHotfixFact):
    """Installed and boot-persistent SA173 SWIX hotfix."""

    key = "mitigation.hotfix.sa173"
    label = "SA173 SWIX hotfix"
    extension_name = "sa173-SecurityAdvisory173_CVE-2026-73455.swix"


class SA171HotfixFact(PersistentHotfixFact):
    """Installed and boot-persistent SA171 CVE-2026-73435 SWIX hotfix."""

    key = "mitigation.hotfix.sa171_cve_2026_73435"
    label = "SA171 CVE-2026-73435 SWIX hotfix"
    extension_name = "sa171-SecurityAdvisory171_CVE-2026-73435.swix"
