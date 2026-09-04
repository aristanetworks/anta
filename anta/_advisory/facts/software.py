# Copyright (c) 2026 Arista Networks, Inc.
# Use of this source code is governed by the Apache License 2.0
# that can be found in the LICENSE file.
"""Facts derived from EOS and component software metadata."""

from __future__ import annotations

from collections.abc import Mapping
from typing import ClassVar

from anta._advisory.facts.models import CommandsFactDefinition, ComponentSoftwareVersion, Fact, FactProblemKind, FactSource, FactSourceKind
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
