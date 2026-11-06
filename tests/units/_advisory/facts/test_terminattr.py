# Copyright (c) 2026 Arista Networks, Inc.
# Use of this source code is governed by the Apache License 2.0
# that can be found in the LICENSE file.
"""Tests for persistent TerminAttr TLS client configuration facts."""

from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

from anta._advisory.facts.models import AvailableFact, FactProblemKind, FeatureState, UnavailableFact
from anta._advisory.facts.terminattr import TerminAttrDefaultCaTlsFact, TerminAttrTlsConnection
from tests.units.anta_tests.advisories import OfflineAntaDevice

if TYPE_CHECKING:
    from anta.models import AntaCommand


def config(arguments: str, lifecycle: str = "no shutdown") -> str:
    """Build the running-configuration shape shown in the public advisory."""
    return f"daemon TerminAttr\n   exec /usr/bin/TerminAttr {arguments}\n   {lifecycle}\n"


def command(output: str | dict[str, object] | None, errors: list[str] | None = None) -> AntaCommand:
    """Populate the fact-owned command without changing its declaration."""
    collected = TerminAttrDefaultCaTlsFact.commands[0].model_copy()
    collected.output = output
    collected.errors = errors or []
    return collected


@pytest.mark.parametrize(
    ("authentication", "ca_file"),
    [
        ("token-secure,/mnt/flash/token.json", None),
        ("certs,/mnt/flash/cert.pem,/mnt/flash/key.pem", None),
        ("token-secure,/mnt/flash/token.json,/mnt/flash/ca.pem", "/mnt/flash/ca.pem"),
        ("certs,/mnt/flash/cert.pem,/mnt/flash/key.pem,/mnt/flash/ca.pem", "/mnt/flash/ca.pem"),
    ],
)
@pytest.mark.parametrize("separator", ["=", " "])
def test_tls_authentication_and_ca_context(authentication: str, ca_file: str | None, separator: str) -> None:
    """Apply the advisory's explicit-CA exclusion without retaining credentials."""
    output = config(f"-cvaddr{separator}apiserver.arista.io:443 -cvcompression=gzip -cvvrf=management -taillogs -cvauth{separator}{authentication}")
    fact = TerminAttrDefaultCaTlsFact.derive(OfflineAntaDevice("test"), (command(output),))

    assert isinstance(fact, AvailableFact)
    assert fact.value.state is (FeatureState.ENABLED if ca_file is None else FeatureState.DISABLED)
    assert fact.value.connections == (TerminAttrTlsConnection("primary", ("apiserver.arista.io:443",), ca_file),)
    assert fact.source.name == "show running-configuration | section TerminAttr"
    assert "token.json" not in repr(fact.value)
    assert "key.pem" not in repr(fact.value)


@pytest.mark.parametrize(
    "output",
    ["", "\n!\n", "daemon TerminAttr\n   shutdown", config("-cvauth=broken", "shutdown"), config("-grpcaddr=0.0.0.0:6042")],
)
def test_decisively_absent_client(output: str) -> None:
    """Daemon absence, explicit shutdown, and server-only configuration close the client path."""
    fact = TerminAttrDefaultCaTlsFact.parse((command(output),))

    assert isinstance(fact, AvailableFact)
    assert fact.value.state is FeatureState.DISABLED
    assert fact.value.connections == ()


def test_scoped_ca_correlation() -> None:
    """An on-premises cluster's CA must not cover a different cluster's default trust store."""
    output = config(
        "-cvopt onprem.addr=192.0.2.1:9910,192.0.2.2:9910 -cvopt onprem.auth=certs,cert,key,private-ca.pem "
        "-cvopt=cloud.addr=apiserver.arista.io:443 -cvopt=cloud.auth=token-secure,token.json "
        "-cvopt cloud.vrf=management"
    )
    fact = TerminAttrDefaultCaTlsFact.parse((command(output),))

    assert isinstance(fact, AvailableFact)
    assert fact.value.state is FeatureState.ENABLED
    assert fact.value.connections == (
        TerminAttrTlsConnection("cloud", ("apiserver.arista.io:443",), None),
        TerminAttrTlsConnection("onprem", ("192.0.2.1:9910", "192.0.2.2:9910"), "private-ca.pem"),
    )


def test_flat_and_scoped_connections_are_both_retained() -> None:
    """A flat client must not disappear when a separate scoped client is present."""
    output = config(
        '-cvaddr=apiserver.arista.io:443 -cvauth="token-secure,token.json,ca with spaces.pem" '
        "-cvopt backup.addr=backup.example:443 -cvopt backup.auth=certs,cert,key"
    )
    fact = TerminAttrDefaultCaTlsFact.parse((command(output),))

    assert isinstance(fact, AvailableFact)
    assert fact.value.connections == (
        TerminAttrTlsConnection("backup", ("backup.example:443",), None),
        TerminAttrTlsConnection("primary", ("apiserver.arista.io:443",), "ca with spaces.pem"),
    )
    assert fact.value.state is FeatureState.ENABLED


@pytest.mark.parametrize("global_first", [True, False])
@pytest.mark.parametrize(
    ("global_arguments", "scoped_arguments", "ca_file"),
    [
        (
            "-cvaddr=apiserver.arista.io:443 -cvauth=token-secure,token,private-ca.pem",
            "-cvopt primary.addr=ignored.example:443 -cvopt primary.auth=token-secure,token",
            "private-ca.pem",
        ),
        ("-cvaddr=apiserver.arista.io:443", "-cvopt primary.auth=token-secure,token", None),
        ("-cvauth=token-secure,token,private-ca.pem", "-cvopt primary.addr=apiserver.arista.io:443", "private-ca.pem"),
        (
            "-cvaddr= -cvauth=",
            "-cvopt primary.addr=apiserver.arista.io:443 -cvopt primary.auth=token-secure,token,private-ca.pem",
            "private-ca.pem",
        ),
    ],
)
def test_primary_options_merge_with_global_precedence(global_arguments: str, scoped_arguments: str, ca_file: str | None, *, global_first: bool) -> None:
    """Global flags override only nonempty primary fields, independently of argument order."""
    arguments = (global_arguments, scoped_arguments) if global_first else (scoped_arguments, global_arguments)
    fact = TerminAttrDefaultCaTlsFact.parse((command(config(" ".join(arguments))),))

    assert isinstance(fact, AvailableFact)
    assert fact.value.connections == (TerminAttrTlsConnection("primary", ("apiserver.arista.io:443",), ca_file),)
    assert fact.value.state is (FeatureState.ENABLED if ca_file is None else FeatureState.DISABLED)


@pytest.mark.parametrize("scoped_argument", ["backup.addr=backup.example:443", "backup.auth=token-secure,token"])
def test_secondary_cluster_does_not_inherit_global_options(scoped_argument: str) -> None:
    """Globals complete primary only; a secondary cluster still needs its own address and authentication."""
    output = config(f"-cvaddr=apiserver.arista.io:443 -cvauth=token-secure,token -cvopt {scoped_argument}")
    fact = TerminAttrDefaultCaTlsFact.parse((command(output),))

    assert isinstance(fact, UnavailableFact)
    assert fact.problem is FactProblemKind.MISSING


@pytest.mark.parametrize("option", ["-cvconfig", "-cvconfig=true", "--cvconfig", "--cvconfig=false"])
@pytest.mark.parametrize("ca_file", [None, "private-ca.pem"])
def test_cvconfig_preserves_tls_client_selection(option: str, ca_file: str | None) -> None:
    """Dynamic segmentation subscriptions leave the client's destination and CA selection unchanged."""
    authentication = "token-secure,token" if ca_file is None else f"token-secure,token,{ca_file}"
    output = config(f"-cvaddr=apiserver.arista.io:443 {option} -cvauth={authentication}")
    fact = TerminAttrDefaultCaTlsFact.parse((command(output),))

    assert isinstance(fact, AvailableFact)
    assert fact.value.connections == (TerminAttrTlsConnection("primary", ("apiserver.arista.io:443",), ca_file),)
    assert fact.value.state is (FeatureState.ENABLED if ca_file is None else FeatureState.DISABLED)


@pytest.mark.parametrize(
    ("output", "problem"),
    [
        (None, FactProblemKind.MISSING),
        ({}, FactProblemKind.MALFORMED),
        ("unexpected output", FactProblemKind.MALFORMED),
        ("daemon TerminAttr", FactProblemKind.MISSING),
        ("daemon TerminAttr\n   no shutdown", FactProblemKind.MISSING),
        (config("-cvaddr=apiserver.arista.io:443").replace("   no shutdown\n", ""), FactProblemKind.MISSING),
        (config("-cvaddr=apiserver.arista.io:443"), FactProblemKind.MISSING),
        (config("-cvauth=token-secure,token.json"), FactProblemKind.MISSING),
        (config("-cvaddr -cvauth=token-secure,token.json"), FactProblemKind.MISSING),
        (config("-cvaddr"), FactProblemKind.MISSING),
        (config("-cvaddr="), FactProblemKind.MISSING),
        (config("-cvaddr=host:443 -cvauth=token-secure"), FactProblemKind.MALFORMED),
        (config("-cvaddr=host:443 -cvauth=certs,cert"), FactProblemKind.MALFORMED),
        (config("-cvaddr=host:443 -cvauth=token-secure,token,"), FactProblemKind.MALFORMED),
        (config("-cvaddr=host:443, -cvauth=certs,cert,key,ca"), FactProblemKind.MALFORMED),
        (config("-cvaddr=host:443 -cvauth=certs,cert,key,ca,extra"), FactProblemKind.MALFORMED),
        (config("-cvaddr=host:443 -cvauth=unknown,credential"), FactProblemKind.UNSUPPORTED),
        (config("-cvaddr=host:443 -cvauth=token,token"), FactProblemKind.UNSUPPORTED),
        (config("-cvopt addr=host:443"), FactProblemKind.MALFORMED),
        (config("-cvopt .addr=host:443"), FactProblemKind.MALFORMED),
        (config("-cvopt cloud.addr"), FactProblemKind.MALFORMED),
        (config("-cvopt cloud.addr="), FactProblemKind.MISSING),
        (config("-cvopt cloud.addr=host:443"), FactProblemKind.MISSING),
        (config("-cvopt cloud.auth=token-secure,token"), FactProblemKind.MISSING),
        (config("-cvopt foo.bar.addr=apiserver.arista.io:443 -cvopt foo.bar.auth=token-secure,token"), FactProblemKind.MALFORMED),
        (config("-cvaddr=host:443 -cvaddr=other:443 -cvauth=certs,cert,key"), FactProblemKind.INVALID),
        (config("-cvopt cloud.addr=host:443 -cvopt cloud.addr=other:443"), FactProblemKind.INVALID),
        (config('-cvaddr="unterminated'), FactProblemKind.MALFORMED),
        (config("-cvaddr=host:443").replace("/usr/bin/TerminAttr", "/mnt/flash/wrapper"), FactProblemKind.UNSUPPORTED),
        (config("") + "   shutdown\n", FactProblemKind.INVALID),
        (config("") + "   exec /usr/bin/TerminAttr\n", FactProblemKind.INVALID),
        (config("") + "daemon TerminAttr\n", FactProblemKind.INVALID),
    ],
)
def test_invalid_or_incomplete_configuration(output: str | dict[str, object] | None, problem: FactProblemKind) -> None:
    """Malformed, unsupported, contradictory, and incomplete inputs must never prove absence."""
    fact = TerminAttrDefaultCaTlsFact.parse((command(output),))

    assert isinstance(fact, UnavailableFact)
    assert fact.problem is problem
    assert fact.source.name == "show running-configuration | section TerminAttr"


@pytest.mark.parametrize(
    ("errors", "problem"),
    [
        (["This command is not supported on this hardware platform"], FactProblemKind.UNSUPPORTED),
        (["Permission denied"], FactProblemKind.COLLECTION_FAILED),
        (["This command is not supported on this hardware platform", "Permission denied"], FactProblemKind.COLLECTION_FAILED),
    ],
)
def test_command_failures(errors: list[str], problem: FactProblemKind) -> None:
    """Preserve the actual command failure even if stale output resembles absence."""
    fact = TerminAttrDefaultCaTlsFact.parse((command("", errors),))

    assert isinstance(fact, UnavailableFact)
    assert fact.problem is problem
    assert fact.source.name == "show running-configuration | section TerminAttr"
