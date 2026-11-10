# Copyright (c) 2026 Arista Networks, Inc.
# Use of this source code is governed by the Apache License 2.0
# that can be found in the LICENSE file.
"""Unit tests for normalized EOS PTP facts."""

from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

from anta._advisory.facts.models import AvailableFact, FactProblemKind, FeatureState, UnavailableFact
from anta._advisory.facts.ptp import PtpGlobalFact
from tests.units.anta_tests.advisories import OfflineAntaDevice

if TYPE_CHECKING:
    from anta.models import AntaCommand


def command(output: dict[str, object] | str | None) -> AntaCommand:
    """Populate the declared revision-2 command."""
    populated = PtpGlobalFact.commands[0].model_copy()
    populated.output = output
    return populated


@pytest.mark.parametrize(
    ("output", "state"),
    [
        ({"ptpMode": "ptpBoundaryClock", "ptpIntfSummaries": {}}, FeatureState.ENABLED),
        ({"ptpMode": "ptpOneStepBoundaryClock", "ptpIntfSummaries": {}}, FeatureState.ENABLED),
        ({"ptpMode": "ptpEndToEndTransparentClock", "ptpIntfSummaries": {}}, FeatureState.ENABLED),
        ({"ptpMode": "ptpPeerToPeerTransparentClock", "ptpIntfSummaries": {}}, FeatureState.ENABLED),
        ({"ptpMode": "ptpOrdinaryMasterClock", "ptpIntfSummaries": {}}, FeatureState.ENABLED),
        ({"ptpMode": "ptpGeneralized", "ptpIntfSummaries": {}}, FeatureState.ENABLED),
        ({"ptpMode": "ptpOneStepEndToEndTransparentClock", "ptpIntfSummaries": {}}, FeatureState.ENABLED),
        ({"ptpMode": "ptpOneStepPeerToPeerTransparentClock", "ptpIntfSummaries": {}}, FeatureState.ENABLED),
        ({"ptpMode": "ptpFutureMode", "ptpIntfSummaries": {}}, FeatureState.ENABLED),
        ({"ptpMode": "unknown", "ptpIntfSummaries": {}}, FeatureState.ENABLED),
        ({"ptpMode": "ptpDisabled", "ptpIntfSummaries": {}}, FeatureState.DISABLED),
        ({"ptpIntfSummaries": {}}, FeatureState.DISABLED),
    ],
)
def test_ptp_global_states(output: dict[str, object], state: FeatureState) -> None:
    """Distinguish global enablement from the presence of interface summaries."""
    fact = PtpGlobalFact.derive(OfflineAntaDevice("unit-test"), (command(output),))
    assert isinstance(fact, AvailableFact)
    assert fact.value.state is state
    assert fact.source.name == "show ptp"


@pytest.mark.parametrize(
    ("output", "problem"),
    [
        (None, FactProblemKind.MISSING),
        ("PTP Mode: Disabled", FactProblemKind.MALFORMED),
        ({}, FactProblemKind.MISSING),
        ({"ptpMode": "ptpBoundaryClock"}, FactProblemKind.MISSING),
        ({"ptpIntfSummaries": None}, FactProblemKind.MALFORMED),
        ({"ptpIntfSummaries": []}, FactProblemKind.MALFORMED),
        ({"ptpMode": None, "ptpIntfSummaries": {}}, FactProblemKind.MALFORMED),
        ({"ptpMode": True, "ptpIntfSummaries": {}}, FactProblemKind.MALFORMED),
        ({"ptpMode": "", "ptpIntfSummaries": {}}, FactProblemKind.INVALID),
        ({"ptpMode": "   ", "ptpIntfSummaries": {}}, FactProblemKind.INVALID),
        ({"ptpIntfSummaries": {"Ethernet1": {}}}, FactProblemKind.MISSING),
    ],
)
def test_ptp_global_invalid_output(output: dict[str, object] | str | None, problem: FactProblemKind) -> None:
    """Keep incomplete or malformed JSON distinct from disabled PTP."""
    fact = PtpGlobalFact.derive(OfflineAntaDevice("unit-test"), (command(output),))
    assert isinstance(fact, UnavailableFact)
    assert fact.problem is problem


def test_ptp_global_unsupported() -> None:
    """Keep unsupported collection distinct from explicit disabled PTP."""
    populated = command(None)
    populated.errors = ["This command is not supported on this hardware platform"]
    fact = PtpGlobalFact.derive(OfflineAntaDevice("unit-test"), (populated,))
    assert isinstance(fact, UnavailableFact)
    assert fact.problem is FactProblemKind.UNSUPPORTED


def test_ptp_global_collection_failure() -> None:
    """Preserve a command failure without interpreting it as disabled PTP."""
    populated = command(None)
    populated.errors = ["unavailable"]
    fact = PtpGlobalFact.derive(OfflineAntaDevice("unit-test"), (populated,))
    assert isinstance(fact, UnavailableFact)
    assert fact.problem is FactProblemKind.COLLECTION_FAILED


def test_ptp_global_ignores_operational_port_state() -> None:
    """Global mode remains enabled for a disabled or idle port."""
    output = {
        "ptpMode": "ptpBoundaryClock",
        "ptpClockSummary": {"numberOfSlavePorts": 0, "numberOfMasterPorts": 0},
        "ptpIntfSummaries": {
            "Ethernet53": {
                "interface": "Ethernet53",
                "ptpIntfVlanSummaries": [
                    {"vlanId": 0, "portState": "psDisabled", "delayMechanism": "e2e", "transportMode": "ipv4"},
                ],
            },
        },
    }
    fact = PtpGlobalFact.derive(OfflineAntaDevice("unit-test"), (command(output),))
    assert isinstance(fact, AvailableFact)
    assert fact.value.state is FeatureState.ENABLED


def test_ptp_global_mixed_command_errors() -> None:
    """Do not mistake mixed errors for unsupported or disabled PTP."""
    populated = command(None)
    populated.errors = ["This command is not supported on this hardware platform", "permission denied"]
    fact = PtpGlobalFact.derive(OfflineAntaDevice("unit-test"), (populated,))
    assert isinstance(fact, UnavailableFact)
    assert fact.problem is FactProblemKind.COLLECTION_FAILED


def test_ptp_global_requires_declared_command() -> None:
    """Reject missing command collection independently of output parsing."""
    fact = PtpGlobalFact.derive(OfflineAntaDevice("unit-test"))
    assert isinstance(fact, UnavailableFact)
    assert fact.problem is FactProblemKind.COLLECTION_FAILED
