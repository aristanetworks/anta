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
def test_published_tls_configurations(authentication: str, ca_file: str | None, separator: str) -> None:
    """Cover both impacted and non-impacted configurations without retaining credentials."""
    output = config(f"-cvaddr{separator}apiserver.arista.io:443 -cvcompression=gzip -cvvrf=management -taillogs -cvauth{separator}{authentication}")
    fact = TerminAttrDefaultCaTlsFact.derive(OfflineAntaDevice("test"), (command(output),))

    assert isinstance(fact, AvailableFact)
    assert fact.value.state is (FeatureState.ENABLED if ca_file is None else FeatureState.DISABLED)
    assert fact.value.connections == (TerminAttrTlsConnection("default", ("apiserver.arista.io:443",), ca_file),)
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
        TerminAttrTlsConnection("default", ("apiserver.arista.io:443",), "ca with spaces.pem"),
    )
    assert fact.value.state is FeatureState.ENABLED


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
        (config("-cvconfig"), FactProblemKind.UNSUPPORTED),
        (config("-cvconfig=true"), FactProblemKind.UNSUPPORTED),
        (config("-cvopt addr=host:443"), FactProblemKind.MALFORMED),
        (config("-cvopt .addr=host:443"), FactProblemKind.MALFORMED),
        (config("-cvopt cloud.addr"), FactProblemKind.MALFORMED),
        (config("-cvopt cloud.addr="), FactProblemKind.MISSING),
        (config("-cvopt cloud.addr=host:443"), FactProblemKind.MISSING),
        (config("-cvopt cloud.auth=token-secure,token"), FactProblemKind.MISSING),
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
