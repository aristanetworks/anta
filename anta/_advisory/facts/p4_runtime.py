# Copyright (c) 2026 Arista Networks, Inc.
# Use of this source code is governed by the Apache License 2.0
# that can be found in the LICENSE file.
"""Facts derived from EOS P4Runtime state."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from typing import TYPE_CHECKING

from anta._advisory.facts.models import (
    CommandsFactDefinition,
    Fact,
    FactProblemKind,
    FactSource,
    FactSourceKind,
    FeatureName,
    FeatureState,
    FeatureValue,
    SubFeature,
)
from anta._advisory.optional_commands import OptionalAntaCommand, is_unsupported_optional_command

if TYPE_CHECKING:
    from anta.models import AntaCommand

P4_RUNTIME_COMMAND = OptionalAntaCommand(command="show p4-runtime", revision=1)
SSL_PROFILE_COMMAND = OptionalAntaCommand(command="show management security ssl profile", revision=1)


def _source(command: AntaCommand) -> FactSource:
    """Return a command fact source."""
    return FactSource(command.command, FactSourceKind.COMMAND)


class P4RuntimeFact(CommandsFactDefinition[FeatureValue]):
    """Effective P4Runtime service state."""

    key = "feature.p4_runtime"
    label = "P4Runtime state"
    commands = (P4_RUNTIME_COMMAND,)

    @classmethod
    def parse(cls, commands: tuple[AntaCommand, ...]) -> Fact[FeatureValue]:
        """Normalize the P4Runtime enablement flag."""
        (command,) = commands
        source = _source(command)
        if is_unsupported_optional_command(command):
            return cls.available(FeatureValue(FeatureName.P4_RUNTIME, FeatureState.UNSUPPORTED), source)
        enabled = command.json_output.get("enabled")
        if not isinstance(enabled, bool):
            return cls.unavailable(FactProblemKind.MISSING if enabled is None else FactProblemKind.MALFORMED, source)
        return cls.available(FeatureValue(FeatureName.P4_RUNTIME, FeatureState.ENABLED if enabled else FeatureState.DISABLED), source)


class P4RuntimeAccountingFact(CommandsFactDefinition[FeatureValue]):
    """P4Runtime request-accounting state."""

    key = "feature.p4_runtime.accounting"
    label = "P4Runtime accounting state"
    commands = (P4_RUNTIME_COMMAND,)

    @classmethod
    def parse(cls, commands: tuple[AntaCommand, ...]) -> Fact[FeatureValue]:
        """Normalize request accounting on the effective P4Runtime transport."""
        (command,) = commands
        source = _source(command)
        feature = SubFeature(FeatureName.P4_RUNTIME, "accounting")
        if is_unsupported_optional_command(command):
            return cls.available(FeatureValue(feature, FeatureState.UNSUPPORTED), source)
        transport = command.json_output.get("transport")
        if not isinstance(transport, Mapping):
            return cls.unavailable(FactProblemKind.MISSING if transport is None else FactProblemKind.MALFORMED, source)
        enabled = transport.get("accountingRequests")
        if not isinstance(enabled, bool):
            return cls.unavailable(FactProblemKind.MISSING if enabled is None else FactProblemKind.MALFORMED, source)
        return cls.available(FeatureValue(feature, FeatureState.ENABLED if enabled else FeatureState.DISABLED), source)


class P4RuntimeMtlsFact(CommandsFactDefinition[FeatureValue]):
    """mTLS state of the effective P4Runtime transport."""

    key = "feature.p4_runtime.mtls"
    label = "P4Runtime mTLS state"
    commands = (P4_RUNTIME_COMMAND, SSL_PROFILE_COMMAND)

    @classmethod
    # pylint: disable-next=too-many-return-statements
    def parse(cls, commands: tuple[AntaCommand, ...]) -> Fact[FeatureValue]:  # noqa: PLR0911
        """Normalize whether P4Runtime uses an SSL profile with trusted certificates."""
        p4, ssl = commands
        p4_source = _source(p4)
        feature = SubFeature(FeatureName.P4_RUNTIME, "mTLS")
        if is_unsupported_optional_command(p4):
            return cls.available(FeatureValue(feature, FeatureState.UNSUPPORTED), p4_source)
        transport = p4.json_output.get("transport")
        if not isinstance(transport, Mapping):
            return cls.unavailable(FactProblemKind.MISSING if transport is None else FactProblemKind.MALFORMED, p4_source)
        profile_name = transport.get("sslProfile")
        if profile_name in (None, ""):
            return cls.available(FeatureValue(feature, FeatureState.DISABLED), p4_source)
        if not isinstance(profile_name, str):
            return cls.unavailable(FactProblemKind.MALFORMED, p4_source)

        ssl_source = _source(ssl)
        if is_unsupported_optional_command(ssl):
            return cls.unavailable(FactProblemKind.UNSUPPORTED, ssl_source)
        profiles = ssl.json_output.get("profileStatus")
        if not isinstance(profiles, Mapping):
            return cls.unavailable(FactProblemKind.MISSING if profiles is None else FactProblemKind.MALFORMED, ssl_source)
        profile = profiles.get(profile_name)
        if not isinstance(profile, Mapping):
            return cls.unavailable(FactProblemKind.MISSING, ssl_source)
        trusted = profile.get("trustedCertificates")
        if trusted is None or trusted == []:
            return cls.available(FeatureValue(feature, FeatureState.DISABLED), ssl_source)
        if (
            not isinstance(trusted, Sequence)
            or isinstance(trusted, str | bytes)
            or not all(isinstance(certificate, str) and certificate.strip() for certificate in trusted)
        ):
            return cls.unavailable(FactProblemKind.MALFORMED, ssl_source)
        return cls.available(FeatureValue(feature, FeatureState.ENABLED), ssl_source)
