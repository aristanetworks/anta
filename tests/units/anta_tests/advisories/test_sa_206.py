# Copyright (c) 2026 Arista Networks, Inc.
# Use of this source code is governed by the Apache License 2.0
# that can be found in the LICENSE file.
"""Unit tests for Arista Security Advisory 206."""

from __future__ import annotations

from datetime import date
from functools import partial
from typing import TYPE_CHECKING
from unittest.mock import patch

import pytest

from anta._advisory.eos_versions import AffectedStatus, evaluate_version
from anta._advisory.facts.bfd import BfdKeyedAuthenticationFact
from anta._advisory.facts.eos import EosVersionFact
from anta._advisory.facts.models import FactProblemKind, FactSource, FactSourceKind, FeatureState
from anta._advisory.findings.models import ErrorResult, NotAffectedResult
from anta._advisory.remediation import FixedRelease, software_version_plan
from anta._advisory.results import _get_atomic_vulnerability_ids
from anta._eos.version import EOSVersion, parse_eos_version
from anta.models import AntaCommand
from anta.result_manager.models import AntaTestStatus
from anta.tests.advisories.sa_154 import SA154
from anta.tests.advisories.sa_206 import ADVISORY, AFFECTED_VERSION_MATRIX, SA206, _assess_sa206
from tests.units.anta_tests import build_eos_version, test  # noqa: F401 - Parameterized advisory harness.
from tests.units.anta_tests.advisories import OfflineAntaDevice, build_expected_advisory_result

if TYPE_CHECKING:
    from tests.units.anta_tests import AntaUnitTestData

SOURCE = FactSource("unit test", FactSourceKind.DEVICE_METADATA)
VULNERABILITY_ID = "CVE-2026-121368"
KEYED = "router bfd\n   authentication mode md5 shared-secret profile TEST\n"
EXPECTED_REMEDIATION = software_version_plan(
    (
        FixedRelease(EOSVersion(4, 37, 0, suffix="F")),
        FixedRelease(EOSVersion(4, 36, 3, suffix="M")),
        FixedRelease(EOSVersion(4, 35, 7, suffix="M")),
        FixedRelease(EOSVersion(4, 34, 9, suffix="M")),
        FixedRelease(EOSVersion(4, 33, 11, suffix="M")),
    ),
    current_version=EOSVersion(4, 35, 6, suffix="M"),
)
expected = partial(build_expected_advisory_result, VULNERABILITY_ID)
_DATA: AntaUnitTestData = {
    (SA206, "keyed-global"): {
        "version": build_eos_version("4.35.6M"),
        "eos_data": [KEYED, ""],
        "expected": expected(
            AntaTestStatus.FAILURE,
            "The device is affected because EOS version '4.35.6M' is affected and the BFD keyed MD5/SHA1 authentication is enabled",
            EXPECTED_REMEDIATION,
        ),
    },
    (SA206, "absent"): {
        "version": None,
        "eos_data": ["", ""],
        "expected": expected(
            AntaTestStatus.SUCCESS,
            "The device is not affected because the BFD keyed MD5/SHA1 authentication is disabled",
            None,
        ),
    },
    (SA206, "simple"): {
        "version": build_eos_version("4.35.6M"),
        "eos_data": ["router bfd\n   authentication mode simple shared-secret profile TEST\n", ""],
        "expected": expected(
            AntaTestStatus.SUCCESS,
            "The device is not affected because the BFD keyed MD5/SHA1 authentication is disabled",
            None,
        ),
    },
    (SA206, "fixed"): {
        "version": build_eos_version("4.37.0F"),
        "eos_data": [KEYED, ""],
        "expected": expected(AntaTestStatus.SUCCESS, "The device is not affected because EOS version '4.37.0F' is outside the affected releases", None),
    },
}

for label, global_configuration, interface_configuration, _scope in (
    (
        "global-despite-all-interface-overrides",
        KEYED,
        ("interface Ethernet1\n   bfd authentication mode disabled\ninterface Ethernet2\n   bfd authentication mode simple shared-secret profile TEST\n"),
        "global/peer",
    ),
    ("shutdown-still-configured", "router bfd\n   shutdown\n   authentication mode md5 shared-secret profile TEST\n", "", "global/peer"),
    ("meticulous-interface", "", "interface Ethernet1\n   bfd authentication mode sha1 shared-secret profile TEST meticulous\n", "interface"),
    ("incomplete-interface-sibling", KEYED, "interface Ethernet1\n   bfd authentication mode\n", "global/peer"),
    (
        "incomplete-global-sibling",
        "router bfd\n   authentication mode\n",
        "interface Ethernet1\n   bfd authentication mode md5 shared-secret profile TEST\n",
        "interface",
    ),
):
    _DATA[(SA206, label)] = {
        "version": build_eos_version("4.35.6M"),
        "eos_data": [global_configuration, interface_configuration],
        "expected": expected(
            AntaTestStatus.FAILURE,
            "The device is affected because EOS version '4.35.6M' is affected and the BFD keyed MD5/SHA1 authentication is enabled",
            EXPECTED_REMEDIATION,
        ),
    }


for case in _DATA.values():
    case["eos_data"].insert(0, {"adminDown": False})
_DATA[(SA206, "shutdown-still-configured")]["eos_data"][0] = {"adminDown": True}
_DATA[(SA206, "shutdown-still-configured")]["expected"] = expected(
    AntaTestStatus.SUCCESS, "The device is not affected because the BFD keyed MD5/SHA1 authentication is disabled", None
)


@pytest.mark.parametrize(
    ("version", "affected"),
    [
        ("4.21.99M", False),
        ("4.22.0F", True),
        ("4.22.0.1F", True),
        ("4.23.99M", True),
        ("4.31.99M", True),
        ("4.32.0F", True),
        ("4.32.99M", True),
        ("4.33.0F", True),
        ("4.33.10M", True),
        ("4.33.10.99M", True),
        ("4.33.11M", False),
        ("4.34.8M", True),
        ("4.34.8.99M", True),
        ("4.34.9M", False),
        ("4.35.6M", True),
        ("4.35.6.99M", True),
        ("4.35.7M", False),
        ("4.36.2F", True),
        ("4.36.2.99F", True),
        ("4.36.3M", False),
        ("4.37.0F", False),
        ("4.38.0F", False),
        ("5.0.0F", False),
    ],
)
def test_source_boundaries(version: str, affected: bool) -> None:
    """Spell out introductions, fixed patches and open-ended older trains."""
    result = evaluate_version(parse_eos_version(version).unwrap(), AFFECTED_VERSION_MATRIX)
    assert (result.affected_status is AffectedStatus.AFFECTED) is affected


def test_metadata_and_commands() -> None:
    """Keep assigned identity and the persistent observation contract explicit."""
    assert ADVISORY.sa_number == "0206"
    assert ADVISORY.last_updated == date(2026, 11, 10)
    assert ADVISORY.vulnerabilities[0].id == VULNERABILITY_ID
    assert all(isinstance(command, AntaCommand) for command in SA206.commands)
    assert [command.command for command in SA206.commands if isinstance(command, AntaCommand)] == [
        "show bfd peers summary",
        r"show running-config sanitized section ^router\sbfd$",
        r"show running-config sanitized section ^\s+bfd\sauthentication\smode\s",
    ]


def test_independent_absence_and_error_aggregation() -> None:
    """Complete absence excludes scope; otherwise report every required failure."""
    version = EosVersionFact.unavailable(FactProblemKind.MISSING, SOURCE)
    disabled = BfdKeyedAuthenticationFact(FeatureState.DISABLED).available(SOURCE)
    assert isinstance(_assess_sa206(version, disabled), NotAffectedResult)
    unavailable = BfdKeyedAuthenticationFact.unavailable(FactProblemKind.MISSING, SOURCE)
    result = _assess_sa206(version, unavailable)
    assert isinstance(result, ErrorResult)
    assert len(result.problems) == 2


@pytest.mark.asyncio
@pytest.mark.parametrize("version", ["4.35.6M", "4.37.0F"])
@pytest.mark.parametrize("error", ["Permission denied", "This command is not supported on this hardware platform"])
async def test_wrapper_collection_failure(version: str, error: str) -> None:
    """Actual collection failures reach the numbered CVE assessment and exclusions."""
    device = OfflineAntaDevice("unit-test")
    device.version = parse_eos_version(version).unwrap()
    await device.refresh()

    async def fail_collection(self: OfflineAntaDevice, command: AntaCommand, *, collection_id: str | None = None) -> None:
        del self, collection_id
        if command.command == "show bfd peers summary":
            command.output = {"adminDown": False}
            command.errors = []
        else:
            command.output = None
            command.errors = [error]

    instance = SA206(device=device)
    with patch.object(OfflineAntaDevice, "_collect", fail_collection):
        await instance.test()
    assert instance.result.result is (AntaTestStatus.SUCCESS if version == "4.37.0F" else AntaTestStatus.ERROR)
    assert len(instance.result.atomic_results) == 1
    atomic = instance.result.atomic_results[0]
    assert atomic.result == instance.result.result
    assert _get_atomic_vulnerability_ids(atomic) == (VULNERABILITY_ID,)
    if version == "4.35.6M":
        assert r"show running-config sanitized section ^router\sbfd$" in instance.result.messages[0]


@pytest.mark.asyncio
@pytest.mark.parametrize("positive_scope", ["global", "interface"])
@pytest.mark.parametrize("positive", [False, True])
async def test_wrapper_independent_collection(positive_scope: str, positive: bool) -> None:
    """One failed command cannot defeat an independent positive witness."""
    device = OfflineAntaDevice("unit-test")
    device.version = parse_eos_version("4.35.6M").unwrap()
    await device.refresh()

    async def collect(self: OfflineAntaDevice, command: AntaCommand, *, collection_id: str | None = None) -> None:
        del self, collection_id
        if command.command == "show bfd peers summary":
            command.output = {"adminDown": False}
            command.errors = []
            return
        global_command = command.command == BfdKeyedAuthenticationFact.commands[1].command
        if global_command == (positive_scope == "global"):
            command.output = (KEYED if global_command else "interface Ethernet1\n   bfd authentication mode sha1 shared-secret profile TEST\n") if positive else ""
            command.errors = []
        else:
            command.output = None
            command.errors = ["Permission denied"]

    instance = SA206(device=device)
    with patch.object(OfflineAntaDevice, "_collect", collect):
        await instance.test()
    assert instance.result.result is (AntaTestStatus.FAILURE if positive else AntaTestStatus.ERROR)
    assert _get_atomic_vulnerability_ids(instance.result.atomic_results[0]) == (VULNERABILITY_ID,)


@pytest.mark.asyncio
@pytest.mark.parametrize("positive", [False, True])
async def test_wrapper_summary_failure(positive: bool) -> None:
    """Failed administrative collection cannot hide complete absence or prove enabled BFD."""
    device = OfflineAntaDevice("unit-test")
    device.version = parse_eos_version("4.35.6M").unwrap()
    await device.refresh()

    async def collect(self: OfflineAntaDevice, command: AntaCommand, *, collection_id: str | None = None) -> None:
        del self, collection_id
        if command.command == "show bfd peers summary":
            command.output = None
            command.errors = ["Permission denied"]
        else:
            command.output = KEYED if positive and command.command == BfdKeyedAuthenticationFact.commands[1].command else ""
            command.errors = []

    instance = SA206(device=device)
    with patch.object(OfflineAntaDevice, "_collect", collect):
        await instance.test()
    assert instance.result.result is (AntaTestStatus.ERROR if positive else AntaTestStatus.SUCCESS)
    if positive:
        assert "show bfd peers summary" in instance.result.messages[0]


@pytest.mark.asyncio
@pytest.mark.parametrize("test_class", [SA154, SA206])
@pytest.mark.parametrize(
    ("scenario", "required_sources", "status"),
    [
        ("both-config-fail", (1, 2), AntaTestStatus.ERROR),
        ("all-fail", (0, 1, 2), AntaTestStatus.ERROR),
        ("malformed-summary", (0, 1, 2), AntaTestStatus.ERROR),
        ("mixed-problems", (0, 1, 2), AntaTestStatus.ERROR),
        ("positive-global-summary-fails", (0,), AntaTestStatus.ERROR),
        ("positive-interface-summary-fails", (0,), AntaTestStatus.ERROR),
        ("positive-global", (), AntaTestStatus.FAILURE),
        ("positive-interface", (), AntaTestStatus.FAILURE),
        ("shutdown", (), AntaTestStatus.SUCCESS),
        ("absent", (), AntaTestStatus.SUCCESS),
    ],
)
async def test_wrapper_required_failure_sources(test_class: type[SA154 | SA206], scenario: str, required_sources: tuple[int, ...], status: AntaTestStatus) -> None:
    """Injected collection/parser failures retain all and only still-required sources."""
    device = OfflineAntaDevice("unit-test")
    device.version = parse_eos_version("4.35.0F").unwrap()
    await device.refresh()
    commands = BfdKeyedAuthenticationFact.commands
    outputs: list[dict[str, object] | str | None] = [{"adminDown": False}, None, None]
    errors = [[], ["Permission denied"], ["Permission denied"]]
    if scenario in {"all-fail", "absent"} or scenario.endswith("summary-fails"):
        outputs[0], errors[0] = None, ["Permission denied"]
    elif scenario == "malformed-summary":
        outputs[0] = {"adminDown": "invalid"}
    elif scenario == "mixed-problems":
        outputs = [{}, None, {}]
        errors = [[], [], []]
    elif scenario == "shutdown":
        outputs[0] = {"adminDown": True}
    if scenario.startswith("positive-global"):
        outputs[1], errors[1] = KEYED, []
    elif scenario.startswith("positive-interface"):
        outputs[2], errors[2] = "interface Ethernet1\n   bfd authentication mode sha1 shared-secret profile TEST\n", []
    elif scenario == "absent":
        outputs[1:], errors[1:] = ["", ""], [[], []]

    async def collect(self: OfflineAntaDevice, command: AntaCommand, *, collection_id: str | None = None) -> None:
        del self, collection_id
        index = next(i for i, declared in enumerate(commands) if declared.command == command.command)
        command.output, command.errors = outputs[index], errors[index]

    instance = test_class(device=device)
    with patch.object(OfflineAntaDevice, "_collect", collect):
        await instance.test()
    assert instance.result.result is status
    assert len(instance.result.atomic_results) == 1
    if status is AntaTestStatus.ERROR:
        message = " ".join(instance.result.messages)
        assert tuple(index for index, command in enumerate(commands) if command.command in message) == required_sources
