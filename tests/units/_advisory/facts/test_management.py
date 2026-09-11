# Copyright (c) 2026 Arista Networks, Inc.
# Use of this source code is governed by the Apache License 2.0
# that can be found in the LICENSE file.
"""Unit tests for facts normalized from EOS management-service output."""

from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

from anta._advisory.facts.management import (
    Dot1xControlledAuthenticatorFact,
    Dot1xDynamicAuthorizationFact,
    GnmiAuthorizationFact,
    GnmiMtlsAuthorizationFact,
    GnmiTransportFact,
    GnpsiAuthenticationExposureFact,
    GnpsiEosRpcAuthTraceFact,
    GnpsiMutualTlsSpiffeMitigationFact,
    GnpsiTransportFact,
    GnsiAuthzFact,
    GnsiCertzFact,
    GnsiCredentialzFact,
    GnsiMultipleTransportsFact,
    GnsiPathzFact,
    GnsiPathzPolicyOverlapFact,
    GnsiTransportFact,
    NetconfTransportFact,
    RadiusProxyDynamicAuthorizationFact,
    RestconfTransportFact,
    SnmpAgentFact,
    SnmpV3AuthenticationFact,
    SnmpV3CredentialSyntaxFact,
    _parse_dot1x_controlled_authenticator,
)
from anta._advisory.facts.models import AvailableFact, CredentialSyntaxState, FactProblemKind, FeatureState, MitigationState, UnavailableFact
from anta._eos.parsing import ParseFail, ParseFailureReason, ParseSuccessful
from tests.units.anta_tests.advisories import OfflineAntaDevice

if TYPE_CHECKING:
    from anta.models import AntaCommand


@pytest.fixture(name="device")
def fact_device_fixture() -> OfflineAntaDevice:
    """Return an offline device suitable for fact derivation."""
    return OfflineAntaDevice("unit-test")


def gnsi_command(output: dict[str, object]) -> AntaCommand:
    """Return the shared gNSI command populated with structured output."""
    command = GnsiTransportFact.commands[0].model_copy()
    command.output = output
    return command


def pathz_policy_command(output: str) -> AntaCommand:
    """Return the persisted Pathz policy command populated with text output."""
    command = GnsiPathzPolicyOverlapFact.commands[0].model_copy()
    command.output = output
    return command


def snmp_command(output: dict[str, object]) -> AntaCommand:
    """Return the SNMP command populated with structured output."""
    command = SnmpAgentFact.commands[0].model_copy()
    command.output = output
    return command


def snmpv3_config_command(output: str) -> AntaCommand:
    """Return the narrow SNMPv3 user configuration command populated with text."""
    command = SnmpV3CredentialSyntaxFact.commands[0].model_copy()
    command.output = output
    return command


def json_command(definition: type, output: dict[str, object]) -> AntaCommand:
    """Return the first command from a fact definition populated with structured output."""
    command = definition.commands[0].model_copy()
    command.output = output
    return command


def text_command(definition: type, output: str) -> AntaCommand:
    """Return the first command from a fact definition populated with text output."""
    command = definition.commands[0].model_copy()
    command.output = output
    return command


@pytest.mark.parametrize(
    "definition",
    [
        Dot1xDynamicAuthorizationFact,
        SnmpV3AuthenticationFact,
        RestconfTransportFact,
        NetconfTransportFact,
        GnpsiTransportFact,
        GnpsiAuthenticationExposureFact,
    ],
)
def test_optional_feature_command_unsupported(device: OfflineAntaDevice, definition: type) -> None:
    """Treat a feature-specific unsupported command as feature absence."""
    command = definition.commands[0].model_copy()
    command.output = None
    command.errors = ["This command is not supported on this hardware platform"]

    fact = definition.derive(device, (command,))

    assert isinstance(fact, AvailableFact)
    assert fact.value.state is FeatureState.UNSUPPORTED


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
def test_dot1x_dynamic_authorization_states(device: OfflineAntaDevice, output: dict[str, object], state: FeatureState) -> None:
    """Require effective global dynamic authorization and a controlled authenticator interface."""
    fact = Dot1xDynamicAuthorizationFact.derive(device, (json_command(Dot1xDynamicAuthorizationFact, output),))
    assert isinstance(fact, AvailableFact)
    assert fact.value.state is state


def test_dot1x_dynamic_authorization_rejects_malformed_interface(device: OfflineAntaDevice) -> None:
    """Reject enabled 802.1X output without effective interface state."""
    output = {"systemAuthControl": True, "dynAuth": True, "interfaces": {"Ethernet1": {}}}
    fact = Dot1xDynamicAuthorizationFact.derive(device, (json_command(Dot1xDynamicAuthorizationFact, output),))
    assert isinstance(fact, UnavailableFact)
    assert fact.problem is FactProblemKind.MALFORMED


@pytest.mark.parametrize(
    ("output", "controlled"),
    [
        ({"systemAuthControl": False, "interfaces": {}}, False),
        ({"systemAuthControl": True, "interfaces": {"Ethernet1": {"portControl": "forceAuth"}}}, False),
        ({"systemAuthControl": True, "interfaces": {"Ethernet1": {"portControl": "controlled"}}}, True),
    ],
)
def test_parse_dot1x_controlled_authenticator(output: dict[str, object], controlled: bool) -> None:
    """Return a typed successful result for observed EOS controlled-authenticator states."""
    parsed = _parse_dot1x_controlled_authenticator(output)

    assert isinstance(parsed, ParseSuccessful)
    assert parsed.value is controlled


def test_parse_dot1x_controlled_authenticator_failure() -> None:
    """Return a typed parsing failure for malformed EOS interface state."""
    parsed = _parse_dot1x_controlled_authenticator({"systemAuthControl": True, "interfaces": {"Ethernet1": {}}})

    assert isinstance(parsed, ParseFail)
    assert parsed.reason is ParseFailureReason.MALFORMED
    assert parsed.detail == "show dot1x all interface 'Ethernet1' portControl is not a string"


@pytest.mark.parametrize(
    ("output", "state"),
    [
        ("", FeatureState.DISABLED),
        ("radius proxy\n   dynamic-authorization\n   client group CG1\n      client ipv4 192.0.2.0/24 vrf default", FeatureState.ENABLED),
        ("radius proxy\n   client group CG1", FeatureState.DISABLED),
    ],
)
def test_radius_proxy_dynamic_authorization_states(device: OfflineAntaDevice, output: str, state: FeatureState) -> None:
    """Require proxy mode, dynamic authorization, and a client group."""
    fact = RadiusProxyDynamicAuthorizationFact.derive(device, (text_command(RadiusProxyDynamicAuthorizationFact, output),))
    assert isinstance(fact, AvailableFact)
    assert fact.value.state is state


@pytest.mark.parametrize(("enabled", "state"), [(True, FeatureState.ENABLED), (False, FeatureState.DISABLED)])
def test_gnsi_credentialz_states(device: OfflineAntaDevice, enabled: bool, state: FeatureState) -> None:
    """Normalize structured gNSI Credentialz state."""
    fact = GnsiCredentialzFact.derive(device, (gnsi_command({"credentialzEnabled": enabled}),))
    assert isinstance(fact, AvailableFact)
    assert fact.value.state is state


@pytest.mark.parametrize(
    ("output", "state"),
    [
        ({"enabled": False}, FeatureState.DISABLED),
        ({"enabled": True, "authorization": False}, FeatureState.DISABLED),
        ({"enabled": True, "authorization": True}, FeatureState.ENABLED),
        ({"transports": {"default": {"enabled": True, "authorization": True}}}, FeatureState.ENABLED),
    ],
)
def test_gnmi_authorization_states(device: OfflineAntaDevice, output: dict[str, object], state: FeatureState) -> None:
    """Normalize authorization across flat and multi-transport gNMI schemas."""
    command = GnmiAuthorizationFact.commands[0].model_copy()
    command.output = output
    fact = GnmiAuthorizationFact.derive(device, (command,))
    assert isinstance(fact, AvailableFact)
    assert fact.value.state is state


def test_gnmi_authorization_rejects_contradictory_service_state(device: OfflineAntaDevice) -> None:
    """Reject an enabled transport beneath an explicitly disabled service."""
    command = GnmiAuthorizationFact.commands[0].model_copy()
    command.output = {"enabled": False, "transports": {"default": {"enabled": True, "authorization": True}}}
    fact = GnmiAuthorizationFact.derive(device, (command,))
    assert isinstance(fact, UnavailableFact)
    assert fact.problem is FactProblemKind.MALFORMED


@pytest.mark.parametrize(
    ("definition", "output", "state"),
    [
        (RestconfTransportFact, {"enabled": False}, FeatureState.DISABLED),
        (RestconfTransportFact, {"enabled": True}, FeatureState.ENABLED),
        (NetconfTransportFact, {"enabled": False}, FeatureState.DISABLED),
        (NetconfTransportFact, {"enabled": True}, FeatureState.ENABLED),
    ],
)
def test_openconfig_transport_states(device: OfflineAntaDevice, definition: type, output: dict[str, object], state: FeatureState) -> None:
    """Normalize structured RESTCONF and NETCONF transport state."""
    fact = definition.derive(device, (json_command(definition, output),))
    assert isinstance(fact, AvailableFact)
    assert fact.value.state is state


@pytest.mark.parametrize("definition", [RestconfTransportFact, NetconfTransportFact])
@pytest.mark.parametrize(("output", "problem"), [({}, FactProblemKind.MISSING), ({"enabled": "yes"}, FactProblemKind.MALFORMED)])
def test_openconfig_transport_rejects_invalid_output(device: OfflineAntaDevice, definition: type, output: dict[str, object], problem: FactProblemKind) -> None:
    """Reject missing and malformed structured service state."""
    fact = definition.derive(device, (json_command(definition, output),))
    assert isinstance(fact, UnavailableFact)
    assert fact.problem is problem


GNPSI_DISABLED: dict[str, object] = {
    "enabled": False,
    "transports": {"t2": {"enabled": False, "securityType": "unknown", "authnUsernamePriority": []}},
}
GNPSI_TLS_METADATA: dict[str, object] = {
    "enabled": True,
    "transports": {"t2": {"enabled": True, "securityType": "tls", "authnUsernamePriority": ["x509-spiffe", "metadata", "x509-common-name"]}},
}
GNPSI_MTLS_COMMON_NAME: dict[str, object] = {
    "enabled": True,
    "transports": {"t2": {"enabled": True, "securityType": "mtls", "authnUsernamePriority": ["x509-spiffe", "x509-common-name"]}},
}
GNPSI_MTLS_SPIFFE: dict[str, object] = {
    "enabled": True,
    "transports": {"t2": {"enabled": True, "securityType": "mtls", "authnUsernamePriority": ["x509-spiffe"]}},
}


@pytest.mark.parametrize(
    ("output", "transport_state", "exposure_state"),
    [
        (GNPSI_DISABLED, FeatureState.DISABLED, FeatureState.DISABLED),
        (GNPSI_TLS_METADATA, FeatureState.ENABLED, FeatureState.ENABLED),
        (GNPSI_MTLS_COMMON_NAME, FeatureState.ENABLED, FeatureState.ENABLED),
        (GNPSI_MTLS_SPIFFE, FeatureState.ENABLED, FeatureState.DISABLED),
    ],
)
def test_gnpsi_transport_and_authentication_states(
    device: OfflineAntaDevice,
    output: dict[str, object],
    transport_state: FeatureState,
    exposure_state: FeatureState,
) -> None:
    """Normalize gNPSI transport state and both vulnerable authentication paths."""
    transport = GnpsiTransportFact.derive(device, (json_command(GnpsiTransportFact, output),))
    exposure = GnpsiAuthenticationExposureFact.derive(device, (json_command(GnpsiAuthenticationExposureFact, output),))
    assert isinstance(transport, AvailableFact)
    assert isinstance(exposure, AvailableFact)
    assert transport.value.state is transport_state
    assert exposure.value.state is exposure_state


def test_gnpsi_disabled_service_ignores_stale_transport_state(device: OfflineAntaDevice) -> None:
    """Trust the disabled service flag while nested operational transport state converges."""
    output = {
        "enabled": False,
        "transports": {"t2": {"enabled": True, "securityType": "tls", "authnUsernamePriority": ["metadata"]}},
    }

    transport = GnpsiTransportFact.derive(device, (json_command(GnpsiTransportFact, output),))
    exposure = GnpsiAuthenticationExposureFact.derive(device, (json_command(GnpsiAuthenticationExposureFact, output),))
    mitigation = GnpsiMutualTlsSpiffeMitigationFact.derive(device, (json_command(GnpsiMutualTlsSpiffeMitigationFact, output),))

    assert isinstance(transport, AvailableFact)
    assert transport.value.state is FeatureState.DISABLED
    assert isinstance(exposure, AvailableFact)
    assert exposure.value.state is FeatureState.DISABLED
    assert isinstance(mitigation, AvailableFact)
    assert mitigation.value.state is MitigationState.INEFFECTIVE


def test_gnpsi_exposure_short_circuits_incomplete_transport(device: OfflineAntaDevice) -> None:
    """Preserve a confirmed vulnerable transport when another transport is incomplete."""
    output = {
        "enabled": True,
        "transports": {
            "incomplete": {"enabled": True},
            "exposed": {"enabled": True, "securityType": "tls", "authnUsernamePriority": ["metadata"]},
        },
    }

    fact = GnpsiAuthenticationExposureFact.derive(device, (json_command(GnpsiAuthenticationExposureFact, output),))

    assert isinstance(fact, AvailableFact)
    assert fact.value.state is FeatureState.ENABLED


def test_gnpsi_mitigation_short_circuits_ineffective_transport(device: OfflineAntaDevice) -> None:
    """Preserve a confirmed ineffective mitigation when another transport is incomplete."""
    output = {
        "enabled": True,
        "transports": {
            "incomplete": {"enabled": True},
            "exposed": {"enabled": True, "securityType": "tls", "authnUsernamePriority": ["metadata"]},
        },
    }

    fact = GnpsiMutualTlsSpiffeMitigationFact.derive(device, (json_command(GnpsiMutualTlsSpiffeMitigationFact, output),))

    assert isinstance(fact, AvailableFact)
    assert fact.value.state is MitigationState.INEFFECTIVE


@pytest.mark.parametrize(
    ("output", "state"),
    [
        (GNPSI_MTLS_SPIFFE, MitigationState.EFFECTIVE),
        (GNPSI_TLS_METADATA, MitigationState.INEFFECTIVE),
        (GNPSI_MTLS_COMMON_NAME, MitigationState.INEFFECTIVE),
        (
            {
                "enabled": True,
                "transports": {
                    "t2": {"enabled": True, "securityType": "mtls", "authnUsernamePriority": ["x509-spiffe"]},
                    "t3": {"enabled": True, "securityType": "mtls", "authnUsernamePriority": ["x509-common-name"]},
                },
            },
            MitigationState.INEFFECTIVE,
        ),
    ],
)
def test_gnpsi_mutual_tls_spiffe_mitigation(device: OfflineAntaDevice, output: dict[str, object], state: MitigationState) -> None:
    """Require mutual TLS and exclusively x509-spiffe authentication on every enabled transport."""
    fact = GnpsiMutualTlsSpiffeMitigationFact.derive(device, (json_command(GnpsiMutualTlsSpiffeMitigationFact, output),))
    assert isinstance(fact, AvailableFact)
    assert fact.value.state is state


def test_gnpsi_mutual_tls_spiffe_mitigation_rejects_missing_authentication(device: OfflineAntaDevice) -> None:
    """Keep incomplete enabled-transport output unavailable."""
    output = {"enabled": True, "transports": {"t2": {"enabled": True, "securityType": "mtls"}}}
    fact = GnpsiMutualTlsSpiffeMitigationFact.derive(device, (json_command(GnpsiMutualTlsSpiffeMitigationFact, output),))
    assert isinstance(fact, UnavailableFact)
    assert fact.problem is FactProblemKind.MISSING


@pytest.mark.parametrize(
    ("output", "state"),
    [("", FeatureState.DISABLED), ("EosRpcAuth           enabled  0123456789", FeatureState.ENABLED), ("EosRpcAuth disabled", FeatureState.DISABLED)],
)
def test_gnpsi_trace_states(device: OfflineAntaDevice, output: str, state: FeatureState) -> None:
    """Normalize the explicit EosRpcAuth trace facility."""
    fact = GnpsiEosRpcAuthTraceFact.derive(device, (text_command(GnpsiEosRpcAuthTraceFact, output),))
    assert isinstance(fact, AvailableFact)
    assert fact.value.state is state


@pytest.mark.parametrize("error", ["Agent 'Gnpsi' is not running", "Invalid input (at token 2: 'Gnpsi')"])
def test_gnpsi_trace_preserves_collection_failure(device: OfflineAntaDevice, error: str) -> None:
    """Keep unavailable gNPSI trace output as a collection failure for assessment."""
    command = GnpsiEosRpcAuthTraceFact.commands[0].model_copy()
    command.errors = [error]

    fact = GnpsiEosRpcAuthTraceFact.derive(device, (command,))

    assert isinstance(fact, UnavailableFact)
    assert fact.problem is FactProblemKind.COLLECTION_FAILED


@pytest.mark.parametrize(
    ("output", "state"),
    [
        ({"usersByVersion": {}}, FeatureState.DISABLED),
        ({"usersByVersion": {"v3": {}}}, FeatureState.DISABLED),
        ({"usersByVersion": {"v3": {"users": {"alice": {"v3Params": {"authType": "None"}}}}}}, FeatureState.DISABLED),
        ({"usersByVersion": {"v3": {"users": {"alice": {"v3Params": {"privType": "AES-128"}}}}}}, FeatureState.DISABLED),
        ({"usersByVersion": {"v3": {"users": {"alice": {"v3Params": {"authType": "SHA-256"}}}}}}, FeatureState.ENABLED),
    ],
)
def test_snmpv3_authentication_key_states(device: OfflineAntaDevice, output: dict[str, object], state: FeatureState) -> None:
    """Normalize authentication-key presence without reading configured values."""
    fact = SnmpV3AuthenticationFact.derive(device, (json_command(SnmpV3AuthenticationFact, output),))

    assert isinstance(fact, AvailableFact)
    assert fact.definition is SnmpV3AuthenticationFact
    assert fact.value.state is state


def test_snmpv3_authentication_key_rejects_malformed_output(device: OfflineAntaDevice) -> None:
    """Reject malformed structured SNMPv3 user output."""
    fact = SnmpV3AuthenticationFact.derive(device, (json_command(SnmpV3AuthenticationFact, {"usersByVersion": {"v3": {"users": []}}}),))

    assert isinstance(fact, UnavailableFact)
    assert fact.problem is FactProblemKind.MALFORMED


@pytest.mark.parametrize(("enabled", "state"), [(True, FeatureState.ENABLED), (False, FeatureState.DISABLED)])
def test_snmp_agent_states(device: OfflineAntaDevice, enabled: bool, state: FeatureState) -> None:
    """Normalize the structured SNMP agent state."""
    fact = SnmpAgentFact.derive(device, (snmp_command({"enabled": enabled}),))

    assert isinstance(fact, AvailableFact)
    assert fact.definition is SnmpAgentFact
    assert fact.value.state is state


@pytest.mark.parametrize(
    ("output", "problem"),
    [({}, FactProblemKind.MISSING), ({"enabled": "true"}, FactProblemKind.MALFORMED)],
)
def test_snmp_agent_invalid_output(device: OfflineAntaDevice, output: dict[str, object], problem: FactProblemKind) -> None:
    """Reject missing and malformed SNMP agent state."""
    fact = SnmpAgentFact.derive(device, (snmp_command(output),))

    assert isinstance(fact, UnavailableFact)
    assert fact.problem is problem


@pytest.mark.parametrize(
    ("output", "state"),
    [
        ("", CredentialSyntaxState.NOT_CONFIGURED),
        ("snmp-server user alice operators v3", CredentialSyntaxState.NOT_CONFIGURED),
        ("snmp-server user legacy operators v3 localized 80000001 auth sha A1B2 priv aes C3D4", CredentialSyntaxState.LEGACY),
        (
            "snmp-server user remote operators remote 192.0.2.1 v3 localized 80000002 auth sha A1B2",
            CredentialSyntaxState.LEGACY,
        ),
        ("snmp-server user encrypted operators v3 localized 80000001 auth sha256 key 7 A1B2", CredentialSyntaxState.ENCRYPTED),
        ("snmp-server user auth priv v3 auth sha256 key 7 A1B2", CredentialSyntaxState.ENCRYPTED),
        (
            "snmp-server user mixed operators v3 localized 80000001 auth sha key 7 A1B2 priv aes C3D4",
            CredentialSyntaxState.MIXED,
        ),
        (
            (
                "snmp-server user encrypted operators v3 localized 80000001 auth sha key 7 A1B2\n"
                "snmp-server user legacy operators v3 localized 80000002 auth sha C3D4"
            ),
            CredentialSyntaxState.MIXED,
        ),
    ],
)
def test_snmpv3_credential_syntax_states(device: OfflineAntaDevice, output: str, state: CredentialSyntaxState) -> None:
    """Normalize absent, local, remote, encrypted, legacy, and mixed credential syntax."""
    fact = SnmpV3CredentialSyntaxFact.derive(device, (snmpv3_config_command(output),))

    assert isinstance(fact, AvailableFact)
    assert fact.definition is SnmpV3CredentialSyntaxFact
    assert fact.value.state is state


@pytest.mark.parametrize(
    "output",
    [
        "snmp-server community public ro",
        "snmp-server user alice operators v3 auth sha",
        "snmp-server user alice operators v3 auth sha key 5 A1B2",
        "snmp-server user alice operators v3 auth sha key 7",
        "snmp-server user 'alice operators v3 auth sha A1B2",
    ],
)
def test_snmpv3_credential_syntax_rejects_malformed_output(device: OfflineAntaDevice, output: str) -> None:
    """Reject output outside the established SNMPv3 user grammar."""
    fact = SnmpV3CredentialSyntaxFact.derive(device, (snmpv3_config_command(output),))

    assert isinstance(fact, UnavailableFact)
    assert fact.problem is FactProblemKind.MALFORMED


@pytest.mark.parametrize(
    ("output", "state"),
    [
        ({"transports": {"default": {"enabled": True}}}, FeatureState.ENABLED),
        ({"transports": {"disabled": {"enabled": False}, "other": {"enabled": True}}}, FeatureState.ENABLED),
        ({"transports": {"default": {"enabled": False}}}, FeatureState.DISABLED),
        ({"transports": {}}, FeatureState.DISABLED),
    ],
)
def test_gnsi_transport_states(device: OfflineAntaDevice, output: dict[str, object], state: FeatureState) -> None:
    """Normalize one or many structured gNSI transport states."""
    fact = GnsiTransportFact.derive(device, (gnsi_command(output),))

    assert isinstance(fact, AvailableFact)
    assert fact.definition is GnsiTransportFact
    assert fact.value.state is state
    assert fact.source.name == "show management api gnsi"


@pytest.mark.parametrize(
    ("output", "problem"),
    [
        ({}, FactProblemKind.MISSING),
        ({"transports": []}, FactProblemKind.MALFORMED),
        ({"transports": {"default": {}}}, FactProblemKind.MALFORMED),
        ({"transports": {"default": {"enabled": "yes"}}}, FactProblemKind.MALFORMED),
    ],
)
def test_gnsi_transport_invalid_output(device: OfflineAntaDevice, output: dict[str, object], problem: FactProblemKind) -> None:
    """Reject missing and malformed transport structures."""
    fact = GnsiTransportFact.derive(device, (gnsi_command(output),))

    assert isinstance(fact, UnavailableFact)
    assert fact.problem is problem


@pytest.mark.parametrize(
    ("output", "state"),
    [
        ({"transports": {}}, FeatureState.DISABLED),
        ({"transports": {"default": {"enabled": True}}}, FeatureState.DISABLED),
        ({"transports": {"one": {"enabled": True}, "two": {"enabled": True}}}, FeatureState.ENABLED),
        ({"transports": {"one": {"enabled": True}, "two": {"enabled": False}}}, FeatureState.DISABLED),
    ],
)
def test_gnsi_multiple_transport_states(device: OfflineAntaDevice, output: dict[str, object], state: FeatureState) -> None:
    """Normalize whether at least two gNSI transports are enabled."""
    fact = GnsiMultipleTransportsFact.derive(device, (gnsi_command(output),))

    assert isinstance(fact, AvailableFact)
    assert fact.definition is GnsiMultipleTransportsFact
    assert fact.value.state is state


@pytest.mark.parametrize(
    "output",
    [
        {},
        {"transports": []},
        {"transports": {"default": {}}},
        {"transports": {"default": {"enabled": "yes"}}},
    ],
)
def test_gnsi_multiple_transport_rejects_invalid_output(device: OfflineAntaDevice, output: dict[str, object]) -> None:
    """Reject missing and malformed gNSI transport cardinality."""
    fact = GnsiMultipleTransportsFact.derive(device, (gnsi_command(output),))

    assert isinstance(fact, UnavailableFact)
    assert fact.problem in {FactProblemKind.MISSING, FactProblemKind.MALFORMED}


@pytest.mark.parametrize(("enabled", "state"), [(True, FeatureState.ENABLED), (False, FeatureState.DISABLED)])
def test_gnsi_certz_states(device: OfflineAntaDevice, enabled: bool, state: FeatureState) -> None:
    """Normalize the structured gNSI Certz state."""
    fact = GnsiCertzFact.derive(device, (gnsi_command({"certzEnabled": enabled}),))

    assert isinstance(fact, AvailableFact)
    assert fact.definition is GnsiCertzFact
    assert fact.value.state is state


@pytest.mark.parametrize(
    ("output", "problem"),
    [({}, FactProblemKind.MISSING), ({"certzEnabled": "yes"}, FactProblemKind.MALFORMED)],
)
def test_gnsi_certz_invalid_output(device: OfflineAntaDevice, output: dict[str, object], problem: FactProblemKind) -> None:
    """Reject missing and malformed Certz state."""
    fact = GnsiCertzFact.derive(device, (gnsi_command(output),))

    assert isinstance(fact, UnavailableFact)
    assert fact.problem is problem


def test_gnsi_unsupported_command_proves_feature_absence(device: OfflineAntaDevice) -> None:
    """Normalize the established feature-specific unsupported response."""
    command = gnsi_command({})
    command.output = None
    command.errors = ["This command is not supported on this hardware platform"]

    transport = GnsiTransportFact.derive(device, (command,))
    certz = GnsiCertzFact.derive(device, (command,))
    authz = GnsiAuthzFact.derive(device, (command,))

    assert isinstance(transport, AvailableFact)
    assert transport.value.state is FeatureState.UNSUPPORTED
    assert isinstance(certz, AvailableFact)
    assert certz.value.state is FeatureState.UNSUPPORTED
    assert isinstance(authz, AvailableFact)
    assert authz.value.state is FeatureState.UNSUPPORTED


@pytest.mark.parametrize(("enabled", "state"), [(True, FeatureState.ENABLED), (False, FeatureState.DISABLED)])
def test_gnsi_authz_states(device: OfflineAntaDevice, enabled: bool, state: FeatureState) -> None:
    """Normalize the structured gNSI Authz state."""
    fact = GnsiAuthzFact.derive(device, (gnsi_command({"authzEnabled": enabled}),))

    assert isinstance(fact, AvailableFact)
    assert fact.definition is GnsiAuthzFact
    assert fact.value.state is state


@pytest.mark.parametrize(
    ("output", "problem"),
    [({}, FactProblemKind.MISSING), ({"authzEnabled": "yes"}, FactProblemKind.MALFORMED)],
)
def test_gnsi_authz_invalid_output(device: OfflineAntaDevice, output: dict[str, object], problem: FactProblemKind) -> None:
    """Reject missing and malformed Authz state."""
    fact = GnsiAuthzFact.derive(device, (gnsi_command(output),))

    assert isinstance(fact, UnavailableFact)
    assert fact.problem is problem


@pytest.mark.parametrize(("enabled", "state"), [(True, FeatureState.ENABLED), (False, FeatureState.DISABLED)])
def test_gnsi_pathz_states(device: OfflineAntaDevice, enabled: bool, state: FeatureState) -> None:
    """Normalize the structured gNSI Pathz state."""
    fact = GnsiPathzFact.derive(device, (gnsi_command({"pathzEnabled": enabled}),))

    assert isinstance(fact, AvailableFact)
    assert fact.definition is GnsiPathzFact
    assert fact.value.state is state


@pytest.mark.parametrize(
    ("output", "problem"),
    [({}, FactProblemKind.MISSING), ({"pathzEnabled": "yes"}, FactProblemKind.MALFORMED)],
)
def test_gnsi_pathz_invalid_output(device: OfflineAntaDevice, output: dict[str, object], problem: FactProblemKind) -> None:
    """Reject missing and malformed Pathz state."""
    fact = GnsiPathzFact.derive(device, (gnsi_command(output),))

    assert isinstance(fact, UnavailableFact)
    assert fact.problem is problem


@pytest.mark.parametrize(
    ("output", "state"),
    [
        ("null", FeatureState.DISABLED),
        ('{"rules": []}', FeatureState.DISABLED),
        (
            '{"rules": [{"user": "alice", "path": {"elem": [{"name": "interfaces"}]}}, {"group": "operators", "path": {"elem": [{"name": "interfaces"}]}}]}',
            FeatureState.ENABLED,
        ),
        (
            '{"rules": [{"user": "alice", "path": {"elem": [{"name": "interfaces"}]}}, {"group": "operators", "path": {"elem": [{"name": "system"}]}}]}',
            FeatureState.DISABLED,
        ),
    ],
)
def test_gnsi_pathz_policy_overlap_states(device: OfflineAntaDevice, output: str, state: FeatureState) -> None:
    """Normalize absent, overlapping, and disjoint Pathz policy rules."""
    fact = GnsiPathzPolicyOverlapFact.derive(device, (pathz_policy_command(output),))

    assert isinstance(fact, AvailableFact)
    assert fact.definition is GnsiPathzPolicyOverlapFact
    assert fact.value.state is state


@pytest.mark.parametrize(("output", "problem"), [("", FactProblemKind.MISSING), ("{", FactProblemKind.MALFORMED), ("[]", FactProblemKind.MALFORMED)])
def test_gnsi_pathz_policy_overlap_rejects_invalid_output(device: OfflineAntaDevice, output: str, problem: FactProblemKind) -> None:
    """Reject missing or malformed persisted Pathz policy output."""
    fact = GnsiPathzPolicyOverlapFact.derive(device, (pathz_policy_command(output),))

    assert isinstance(fact, UnavailableFact)
    assert fact.problem is problem


def test_gnsi_pathz_policy_overlap_preserves_collection_failure(device: OfflineAntaDevice) -> None:
    """Report a failed persisted-policy command as unavailable collection evidence."""
    command = pathz_policy_command("")
    command.errors = ["policy could not be read"]

    fact = GnsiPathzPolicyOverlapFact.derive(device, (command,))

    assert isinstance(fact, UnavailableFact)
    assert fact.problem is FactProblemKind.COLLECTION_FAILED


@pytest.mark.parametrize(
    ("output", "state"),
    [
        ({"transports": {"default": {"enabled": True}}}, FeatureState.ENABLED),
        ({"transports": {"disabled": {"enabled": False}, "other": {"enabled": True}}}, FeatureState.ENABLED),
        ({"transports": {"default": {"enabled": False}}}, FeatureState.DISABLED),
        ({"transports": {}}, FeatureState.DISABLED),
    ],
)
def test_gnmi_transport_states(device: OfflineAntaDevice, output: dict[str, object], state: FeatureState) -> None:
    """Normalize structured gNMI transport states used by advisory facts."""
    command = GnmiTransportFact.commands[0].model_copy()
    command.output = output

    fact = GnmiTransportFact.derive(device, (command,))

    assert isinstance(fact, AvailableFact)
    assert fact.value.state is state


@pytest.mark.parametrize(
    ("output", "problem"),
    [({}, FactProblemKind.MALFORMED), ({"transports": []}, FactProblemKind.MALFORMED), ({"transports": {"default": {}}}, FactProblemKind.MALFORMED)],
)
def test_gnmi_transport_invalid_output(device: OfflineAntaDevice, output: dict[str, object], problem: FactProblemKind) -> None:
    """Reject missing and malformed gNMI transport structures."""
    command = GnmiTransportFact.commands[0].model_copy()
    command.output = output

    fact = GnmiTransportFact.derive(device, (command,))

    assert isinstance(fact, UnavailableFact)
    assert fact.problem is problem


def valid_ssl_profile(*, trusted: bool = True) -> dict[str, object]:
    """Return a valid SSL profile with optional client trust."""
    return {
        "profileStatus": {
            "oc": {
                "profileState": "valid",
                "profileError": [],
                "certName": "server.crt",
                "keyName": "server.key",
                "trustedCertificates": ["shared_ca.crt"] if trusted else [],
            },
            "plain": {
                "profileState": "valid",
                "profileError": [],
                "certName": "server.crt",
                "keyName": "server.key",
                "trustedCertificates": [],
            },
        }
    }


def test_gnmi_mtls_authorization_requires_one_transport_to_meet_both_conditions(device: OfflineAntaDevice) -> None:
    """Do not combine mutual TLS and authorization from different transports."""
    gnmi = GnmiMtlsAuthorizationFact.commands[0].model_copy()
    gnmi.output = {
        "transports": {
            "authorized": {"enabled": True, "authorization": True, "sslProfile": "plain"},
            "trusted": {"enabled": True, "authorization": False, "sslProfile": "oc"},
        }
    }
    ssl = GnmiMtlsAuthorizationFact.commands[1].model_copy()
    ssl.output = valid_ssl_profile()

    fact = GnmiMtlsAuthorizationFact.derive(device, (gnmi, ssl))

    assert isinstance(fact, AvailableFact)
    assert fact.value.state is FeatureState.DISABLED
    assert fact.source.name == GnmiMtlsAuthorizationFact.commands[1].command


def test_gnmi_mtls_authorization_detects_exposed_transport(device: OfflineAntaDevice) -> None:
    """Detect one enabled transport with authorization and mutual TLS."""
    gnmi = GnmiMtlsAuthorizationFact.commands[0].model_copy()
    gnmi.output = {"transports": {"default": {"enabled": True, "authorization": True, "sslProfile": "oc"}}}
    ssl = GnmiMtlsAuthorizationFact.commands[1].model_copy()
    ssl.output = valid_ssl_profile()

    fact = GnmiMtlsAuthorizationFact.derive(device, (gnmi, ssl))

    assert isinstance(fact, AvailableFact)
    assert fact.value.state is FeatureState.ENABLED
    assert fact.source.name == GnmiMtlsAuthorizationFact.commands[1].command


def test_gnmi_mtls_authorization_unsupported_gnmi_proves_feature_absence(device: OfflineAntaDevice) -> None:
    """Normalize unsupported gNMI as absence without requiring SSL-profile state."""
    gnmi, ssl = (command.model_copy() for command in GnmiMtlsAuthorizationFact.commands)
    gnmi.output = None
    gnmi.errors = ["This command is not supported on this hardware platform"]
    ssl.output = None

    fact = GnmiMtlsAuthorizationFact.derive(device, (gnmi, ssl))

    assert isinstance(fact, AvailableFact)
    assert fact.value.state is FeatureState.UNSUPPORTED
    assert fact.source.name == GnmiMtlsAuthorizationFact.commands[0].command


def test_gnmi_mtls_authorization_requires_ssl_output_for_authorized_transport(device: OfflineAntaDevice) -> None:
    """Keep mTLS exposure unavailable when an authorized transport lacks observable SSL state."""
    gnmi, ssl = (command.model_copy() for command in GnmiMtlsAuthorizationFact.commands)
    gnmi.output = {"transports": {"default": {"enabled": True, "authorization": True, "sslProfile": "oc"}}}
    ssl.output = None
    ssl.errors = ["This command is not supported on this hardware platform"]

    fact = GnmiMtlsAuthorizationFact.derive(device, (gnmi, ssl))

    assert isinstance(fact, UnavailableFact)
    assert fact.problem is FactProblemKind.UNSUPPORTED
    assert fact.source.name == GnmiMtlsAuthorizationFact.commands[1].command


def test_gnmi_mtls_authorization_ignores_unsupported_ssl_for_unauthorized_transport(device: OfflineAntaDevice) -> None:
    """Do not require SSL evidence after request authorization closes the exposure path."""
    gnmi, ssl = (command.model_copy() for command in GnmiMtlsAuthorizationFact.commands)
    gnmi.output = {"transports": {"default": {"enabled": True, "authorization": False, "sslProfile": "oc"}}}
    ssl.output = None
    ssl.errors = ["This command is not supported on this hardware platform"]

    fact = GnmiMtlsAuthorizationFact.derive(device, (gnmi, ssl))

    assert isinstance(fact, AvailableFact)
    assert fact.value.state is FeatureState.DISABLED
    assert fact.source.name == GnmiMtlsAuthorizationFact.commands[0].command


@pytest.mark.parametrize(
    ("output", "state"),
    [
        ({"systemAuthControl": False, "interfaces": {}}, FeatureState.DISABLED),
        ({"systemAuthControl": True, "interfaces": {"Ethernet1": {"portControl": "forceAuth"}}}, FeatureState.DISABLED),
        ({"systemAuthControl": True, "interfaces": {"Ethernet1": {"portControl": "controlled"}}}, FeatureState.ENABLED),
    ],
)
def test_dot1x_controlled_authenticator_states(device: OfflineAntaDevice, output: dict[str, object], state: FeatureState) -> None:
    """Normalize effective controlled 802.1X state."""
    command = Dot1xControlledAuthenticatorFact.commands[0].model_copy()
    command.output = output

    fact = Dot1xControlledAuthenticatorFact.derive(device, (command,))

    assert isinstance(fact, AvailableFact)
    assert fact.value.state is state


def test_dot1x_controlled_authenticator_malformed(device: OfflineAntaDevice) -> None:
    """Reject incomplete effective 802.1X state."""
    command = Dot1xControlledAuthenticatorFact.commands[0].model_copy()
    command.output = {"systemAuthControl": True, "interfaces": {"Ethernet1": {}}}

    fact = Dot1xControlledAuthenticatorFact.derive(device, (command,))

    assert isinstance(fact, UnavailableFact)
    assert fact.problem is FactProblemKind.MALFORMED


def test_dot1x_controlled_authenticator_unsupported(device: OfflineAntaDevice) -> None:
    """Treat feature-specific unsupported output as 802.1X absence."""
    command = Dot1xControlledAuthenticatorFact.commands[0].model_copy()
    command.output = None
    command.errors = ["This command is not supported on this hardware platform"]

    fact = Dot1xControlledAuthenticatorFact.derive(device, (command,))

    assert isinstance(fact, AvailableFact)
    assert fact.value.state is FeatureState.UNSUPPORTED
