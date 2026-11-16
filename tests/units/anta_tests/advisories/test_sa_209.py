# Copyright (c) 2026 Arista Networks, Inc.
# Use of this source code is governed by the Apache License 2.0
# that can be found in the LICENSE file.
# pylint: disable=duplicate-code
"""Unit tests for Arista Security Advisory 209."""

from __future__ import annotations

from datetime import date
from functools import partial
from typing import TYPE_CHECKING, cast
from unittest.mock import AsyncMock

import pytest

from anta._advisory.eos_versions import AffectedStatus, evaluate_version
from anta._advisory.facts.bgp import BgpListenPort, BgpNonDefaultListenPortFact, MultiAgentRoutingFact
from anta._advisory.facts.eos import EosVersionFact
from anta._advisory.facts.models import ConfigurationState, FactProblemKind, FactsBase, FactSource, FactSourceKind, FeatureState
from anta._advisory.findings.models import AffectedResult, ErrorResult, NotAffectedResult
from anta._advisory.models import _AdvisoryVulnerabilitySeverity
from anta._advisory.remediation import (
    AnyOf,
    ChangeSoftwareVersion,
    ConditionalAction,
    FixedRelease,
    KnownFixedReleases,
    OperationalAction,
    RemediationPlan,
    SoftwareTarget,
)
from anta._eos.version import EOSVersion, parse_eos_version
from anta.result_manager.models import AntaTestStatus
from anta.tests.advisories.sa_209 import ADVISORY, AFFECTED_VERSION_MATRIX, SA209, _assess_sa209
from tests.units.anta_tests import (
    AntaUnitTestData,
    build_eos_version,
    test,  # noqa: F401 - Pytest collects this imported test function.
)
from tests.units.anta_tests.advisories import OfflineAntaDevice, build_expected_advisory_result
from tests.units.anta_tests.advisories.bgp_captures import bgp_instances, route_summary

if TYPE_CHECKING:
    from typing import Any

SOURCE = FactSource("unit-test", FactSourceKind.DEVICE_METADATA)
VERSION = EosVersionFact.from_version(EOSVersion(4, 35, 3, suffix="F")).available(SOURCE)
MULTI = MultiAgentRoutingFact(FeatureState.ENABLED).available(SOURCE)
RIBD = MultiAgentRoutingFact(FeatureState.DISABLED).available(SOURCE)
MISSING_VERSION = EosVersionFact.unavailable(FactProblemKind.MISSING, SOURCE)
MISSING_PORT = BgpNonDefaultListenPortFact.unavailable(FactProblemKind.MALFORMED, SOURCE)
MISSING_MODEL = MultiAgentRoutingFact.unavailable(FactProblemKind.MISSING, SOURCE)
FIXED = KnownFixedReleases(
    (
        FixedRelease(EOSVersion(4, 37, 0, suffix="F")),
        FixedRelease(EOSVersion(4, 36, 3, suffix="M")),
        FixedRelease(EOSVersion(4, 35, 7, suffix="M")),
        FixedRelease(EOSVersion(4, 34, 9, suffix="M")),
        FixedRelease(EOSVersion(4, 33, 11, suffix="M")),
    )
)
CONDITION = "removing the non-default BGP listen port is operationally feasible"


def remediation(version: EOSVersion, vrfs: str, *, complete: bool = True) -> RemediationPlan:
    """Return fixed software or, where feasible, removal of the listen port from each reporting VRF."""
    scope = f"VRFs: {vrfs}" if complete else f"every VRF using a non-default port, including: {vrfs}"
    removal = OperationalAction(f"Remove 'bgp transport listen-port' from the BGP configuration of {scope}.")
    return RemediationPlan(AnyOf((ChangeSoftwareVersion(SoftwareTarget.EOS, version, FIXED), ConditionalAction(CONDITION, removal))))


@pytest.mark.parametrize(
    ("version", "affected"),
    [
        ("3.9.1", False),
        ("4.0.1F", True),
        ("4.25.0F", True),
        ("4.31.2F", True),
        ("4.32.0F", True),
        ("4.32.99M", True),
        ("4.33.0F", True),
        ("4.33.10M", True),
        ("4.33.10.1M", True),
        ("4.33.11M", False),
        ("4.34.1F", True),
        ("4.34.8M", True),
        ("4.34.9M", False),
        ("4.35.6M", True),
        ("4.35.6.1M", True),
        ("4.35.7M", False),
        ("4.36.2F", True),
        ("4.36.2.1F", True),
        ("4.36.3M", False),
        ("4.37.0F", False),
        ("4.38.0F", False),
        ("5.0.0F", False),
    ],
)
def test_source_software_boundaries(version: str, affected: bool) -> None:
    """4.32 and all older 4.x trains have no floor; named fixes close their own trains."""
    actual = evaluate_version(parse_eos_version(version).unwrap(), AFFECTED_VERSION_MATRIX)
    assert actual.affected_status is (AffectedStatus.AFFECTED if affected else AffectedStatus.NOT_AFFECTED)


def test_affected_with_vrf_remediation() -> None:
    """Removal names each VRF reporting a non-default port once, in reported order."""
    ports = BgpNonDefaultListenPortFact(
        ConfigurationState.CONFIGURED,
        (BgpListenPort("default", "IPv4", 1179), BgpListenPort("default", "IPv6", 1179), BgpListenPort("RED", "IPv4", 2179)),
    ).available(SOURCE)
    result = _assess_sa209(VERSION, ports, MULTI)
    assert isinstance(result, AffectedResult)
    assert result.vulnerability_id == "CVE-2026-121290"
    assert result.conditions == (ports, MULTI)
    assert result.remediation == remediation(EOSVersion(4, 35, 3, suffix="F"), "default, RED")


def test_partial_inventory_does_not_claim_complete_removal() -> None:
    """With an unreadable sibling, removal covers every non-default VRF while fixed software stays a complete alternative."""
    ports = BgpNonDefaultListenPortFact(ConfigurationState.CONFIGURED, (BgpListenPort("default", "IPv4", 1179),), FactProblemKind.MISSING).available(SOURCE)
    result = _assess_sa209(VERSION, ports, MULTI)
    assert isinstance(result, AffectedResult)
    assert result.remediation == remediation(EOSVersion(4, 35, 3, suffix="F"), "default", complete=False)


def test_decisive_absence_ignores_unrelated_errors() -> None:
    """Default ports, ribd in both models, or fixed software each close exposure alone."""
    default = BgpNonDefaultListenPortFact(ConfigurationState.NOT_CONFIGURED).available(SOURCE)
    assert _assess_sa209(MISSING_VERSION, default, MISSING_MODEL) == NotAffectedResult(vulnerability_id="CVE-2026-121290", decisive=(default,))
    assert _assess_sa209(MISSING_VERSION, MISSING_PORT, RIBD) == NotAffectedResult(vulnerability_id="CVE-2026-121290", decisive=(RIBD,))
    fixed = _assess_sa209(EosVersionFact.from_version(EOSVersion(4, 36, 3, suffix="M")).available(SOURCE), MISSING_PORT, MISSING_MODEL)
    assert isinstance(fixed, NotAffectedResult)


def test_all_required_unavailable_inputs_are_retained() -> None:
    """An unreadable listen port is an error, never the default port."""
    result = _assess_sa209(MISSING_VERSION, MISSING_PORT, MISSING_MODEL)
    assert isinstance(result, ErrorResult)
    assert result.problems == (MISSING_VERSION, MISSING_PORT, MISSING_MODEL)
    assert _assess_sa209(VERSION, MISSING_PORT, MULTI) == ErrorResult(vulnerability_id="CVE-2026-121290", problems=(MISSING_PORT,))


def test_metadata_and_collection() -> None:
    """No ACL, iptables, or shell evidence is collected."""
    assert ADVISORY.sa_number == "0209"
    assert ADVISORY.title == "Security Advisory 0209"
    assert ADVISORY.last_updated == date(2026, 11, 10)
    assert [(item.id, item.severity) for item in ADVISORY.vulnerabilities] == [("CVE-2026-121290", _AdvisoryVulnerabilitySeverity.HIGH)]
    facts = cast("type[FactsBase]", SA209.__dict__["Facts"])
    assert tuple(facts.definitions()) == ("version", "listen_port", "multi_agent")
    instance = SA209(OfflineAntaDevice("unit-test"))
    assert [(command.command, command.ofmt, command.revision) for command in instance.instance_commands] == [
        ("show bgp instance vrf all", "json", 3),
        ("show ip route summary", "json", 3),
    ]


AFFECTED_MESSAGE = (
    "The device is affected because EOS version '{}' is affected, the BGP non-default listen port configuration is configured, "
    "and the routing protocol model multi-agent is enabled."
)
NOT_CONFIGURED_MESSAGE = "The device is not affected because the BGP non-default listen port configuration is not configured."
expected = partial(build_expected_advisory_result, "CVE-2026-121290")

_DATA: AntaUnitTestData = {
    (SA209, "affected-default-and-vrf-ports"): {
        "version": build_eos_version("4.35.3F"),
        "eos_data": [bgp_instances(("default", 1179, 1179), ("PROBE", 2179, 2179)), route_summary()],
        "expected": expected(AntaTestStatus.FAILURE, AFFECTED_MESSAGE.format("4.35.3F"), remediation(EOSVersion(4, 35, 3, suffix="F"), "default, PROBE")),
    },
    (SA209, "affected-vrf-ipv6-port-only-ribd-configured-pending-reload"): {
        "version": build_eos_version("4.31.2F"),
        "eos_data": [bgp_instances(("default", 179, 179), ("PROBE", 179, 2179)), route_summary("ribd", "multi-agent")],
        "expected": expected(AntaTestStatus.FAILURE, AFFECTED_MESSAGE.format("4.31.2F"), remediation(EOSVersion(4, 31, 2, suffix="F"), "PROBE")),
    },
    (SA209, "affected-multi-agent-configured-pending-reload"): {
        "version": build_eos_version("4.31.2F"),
        "eos_data": [bgp_instances(("default", 1179, 1179)), route_summary("multi-agent", "ribd")],
        "expected": expected(AntaTestStatus.FAILURE, AFFECTED_MESSAGE.format("4.31.2F"), remediation(EOSVersion(4, 31, 2, suffix="F"), "default")),
    },
    (SA209, "affected-global-shutdown-vrf-port-still-reported"): {
        "version": build_eos_version("4.34.0F"),
        "eos_data": [bgp_instances(("PROBE", 2179, 2179)), route_summary()],
        "expected": expected(AntaTestStatus.FAILURE, AFFECTED_MESSAGE.format("4.34.0F"), remediation(EOSVersion(4, 34, 0, suffix="F"), "PROBE")),
    },
    (SA209, "affected-valid-port-before-vrf-missing-ports"): {
        "version": build_eos_version("4.35.3F"),
        "eos_data": [{"vrfs": {**bgp_instances(("default", 1179, 179))["vrfs"], "RED": {"localAs": 65010}}}, route_summary()],
        "expected": expected(AntaTestStatus.FAILURE, AFFECTED_MESSAGE.format("4.35.3F"), remediation(EOSVersion(4, 35, 3, suffix="F"), "default", complete=False)),
    },
    (SA209, "affected-valid-port-after-vrf-missing-ports"): {
        "version": build_eos_version("4.35.3F"),
        "eos_data": [{"vrfs": {"RED": {"localAs": 65010}, **bgp_instances(("default", 1179, 179))["vrfs"]}}, route_summary()],
        "expected": expected(AntaTestStatus.FAILURE, AFFECTED_MESSAGE.format("4.35.3F"), remediation(EOSVersion(4, 35, 3, suffix="F"), "default", complete=False)),
    },
    (SA209, "affected-valid-ipv4-port-unreadable-ipv6-port"): {
        "version": build_eos_version("4.35.3F"),
        "eos_data": [{"vrfs": {"default": {"bgpIpv4ListenPort": 1179, "bgpIpv6ListenPort": "1179"}}}, route_summary()],
        "expected": expected(AntaTestStatus.FAILURE, AFFECTED_MESSAGE.format("4.35.3F"), remediation(EOSVersion(4, 35, 3, suffix="F"), "default", complete=False)),
    },
    (SA209, "error-default-ports-with-malformed-vrf"): {
        "version": build_eos_version("4.35.3F"),
        "eos_data": [{"vrfs": {**bgp_instances()["vrfs"], "RED": None}}, route_summary()],
        "expected": expected(
            AntaTestStatus.ERROR,
            "The test could not determine the BGP listen port because the 'show bgp instance vrf all' output is invalid.",
            None,
        ),
    },
    (SA209, "not-affected-default-port-every-vrf"): {
        "version": build_eos_version("4.35.3F"),
        "eos_data": [bgp_instances(("default", 179, 179), ("PROBE", 179, 179)), route_summary()],
        "expected": expected(AntaTestStatus.SUCCESS, NOT_CONFIGURED_MESSAGE, None),
    },
    (SA209, "not-affected-no-running-vrf-missing-router-id"): {
        "version": build_eos_version("4.35.3F"),
        "eos_data": [{"vrfs": {}}, route_summary()],
        "expected": expected(AntaTestStatus.SUCCESS, NOT_CONFIGURED_MESSAGE, None),
    },
    (SA209, "not-affected-ribd"): {
        "version": build_eos_version("4.31.2F"),
        "eos_data": [bgp_instances(("default", 1179, 1179)), route_summary("ribd", "ribd")],
        "expected": expected(AntaTestStatus.SUCCESS, "The device is not affected because the routing protocol model multi-agent is disabled.", None),
    },
    (SA209, "not-affected-fixed-release"): {
        "version": build_eos_version("4.37.0F"),
        "eos_data": [bgp_instances(("default", 1179, 1179)), route_summary()],
        "expected": expected(AntaTestStatus.SUCCESS, "The device is not affected because EOS version '4.37.0F' is outside the affected releases.", None),
    },
    (SA209, "error-vrf-without-listen-port"): {
        "version": build_eos_version("4.35.3F"),
        "eos_data": [{"vrfs": {"default": {"localAs": 65010}}}, route_summary()],
        "expected": expected(
            AntaTestStatus.ERROR,
            "The test could not determine the BGP listen port because the 'show bgp instance vrf all' output is incomplete.",
            None,
        ),
    },
    (SA209, "error-missing-routing-model"): {
        "version": build_eos_version("4.35.3F"),
        "eos_data": [bgp_instances(("default", 1179, 1179)), {"vrfs": {}}],
        "expected": expected(
            AntaTestStatus.ERROR,
            "The test could not determine the multi-agent routing protocol model because the 'show ip route summary' output is incomplete.",
            None,
        ),
    },
}


@pytest.mark.parametrize(
    ("errors", "status"),
    [
        (["BGP inactive"], AntaTestStatus.SUCCESS),
        (["% BGP inactive"], AntaTestStatus.SUCCESS),
        (["BGP inactive", "permission denied"], AntaTestStatus.ERROR),
    ],
)
async def test_inactive_bgp_command_result(errors: list[str], status: AntaTestStatus) -> None:
    """The EOS `BGP inactive` response means no listen port; any other error is retained."""
    device = OfflineAntaDevice("unit-test")
    device.version = EOSVersion(4, 35, 3, suffix="F")
    await device.refresh()
    instance = cast("Any", SA209)(device, eos_data=[{}, route_summary()])
    instance.instance_commands[0].output = None
    instance.instance_commands[0].errors = errors
    instance.collect = AsyncMock()

    await instance.test()

    assert instance.result.result is status
    if status is AntaTestStatus.SUCCESS:
        assert NOT_CONFIGURED_MESSAGE in instance.result.messages[0]
    else:
        assert "show bgp instance vrf all" in instance.result.messages[0]
