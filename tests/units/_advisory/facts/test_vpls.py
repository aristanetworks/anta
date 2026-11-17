# Copyright (c) 2026 Arista Networks, Inc.
# Use of this source code is governed by the Apache License 2.0
# that can be found in the LICENSE file.
"""Tests for point-in-time BGP VPLS signaling instance observations."""

from __future__ import annotations

from typing import Any

import pytest

from anta._advisory.facts.models import AvailableFact, FactProblemKind, FeatureState, UnavailableFact
from anta._advisory.facts.vpls import BgpVplsSignalingInstanceFact
from tests.units.anta_tests.advisories import OfflineAntaDevice

# Local-only shape qualified on EOS 4.35.1F, with zero BGP peers.
LOCAL_ONLY = {
    "instances": {
        "PR88_TEST4351": {
            "groups": {
                "PR88_TEST4351_GROUP": {
                    "rd": "192.0.2.214:3942",
                    "importRts": [843041950666598],
                    "exportRts": [843041950666598],
                    "vplsVeIdLocal": 214,
                    "vplsVeIdsRemote": {},
                }
            }
        }
    }
}


def commands(output: dict[str, Any] | str | None) -> tuple:
    """Populate a copy of the single signaling command."""
    command = BgpVplsSignalingInstanceFact.commands[0].model_copy()
    command.output = output
    return (command,)


@pytest.mark.parametrize("output", [LOCAL_ONLY, {"instances": {"CUSTOMER": {}}}, {"instances": {"CUSTOMER": {"groups": "opaque"}}}])
def test_any_reported_instance_is_present(output: dict[str, Any]) -> None:
    """Only local instance presence is required; group details and peers are opaque."""
    fact = BgpVplsSignalingInstanceFact.derive(OfflineAntaDevice("test"), commands(output))
    assert isinstance(fact, AvailableFact)
    assert fact.value.state is FeatureState.ENABLED
    assert fact.source.name == "show bgp vpls signaling"


def test_successful_empty_instances_are_absent() -> None:
    """An empty snapshot is absent even when convergence may explain it."""
    fact = BgpVplsSignalingInstanceFact.derive(OfflineAntaDevice("test"), commands({"instances": {}}))
    assert isinstance(fact, AvailableFact)
    assert fact.value.state is FeatureState.DISABLED


@pytest.mark.parametrize("reverse", [False, True])
def test_instance_witness_survives_independent_malformed_entry(reverse: bool) -> None:
    """A malformed sibling cannot discard an independently reported instance."""
    entries = [("GOOD", {}), ("BROKEN", [])]
    output = {"instances": dict(reversed(entries) if reverse else entries)}
    fact = BgpVplsSignalingInstanceFact.derive(OfflineAntaDevice("test"), commands(output))
    assert isinstance(fact, AvailableFact)
    assert fact.value.state is FeatureState.ENABLED


@pytest.mark.parametrize(
    ("output", "problem"),
    [
        ({}, FactProblemKind.MISSING),
        ({"instances": None}, FactProblemKind.MISSING),
        ({"instances": []}, FactProblemKind.MALFORMED),
        ({"instances": {"A": []}}, FactProblemKind.MALFORMED),
        ({"instances": {"": {}}}, FactProblemKind.MALFORMED),
        ({"instances": {1: {}}}, FactProblemKind.MALFORMED),
        ("invalid JSON", FactProblemKind.MALFORMED),
        (None, FactProblemKind.MISSING),
    ],
)
def test_invalid_signaling_cannot_establish_absence(output: dict[str, Any] | str | None, problem: FactProblemKind) -> None:
    """Unavailable or malformed instance evidence retains its command source."""
    fact = BgpVplsSignalingInstanceFact.derive(OfflineAntaDevice("test"), commands(output))
    assert isinstance(fact, UnavailableFact)
    assert fact.problem is problem
    assert fact.source.name == "show bgp vpls signaling"


@pytest.mark.parametrize("error", ["permission denied", "BGP inactive", "% BGP inactive"])
def test_signaling_errors_do_not_infer_bgp_disablement(error: str) -> None:
    """BGP disablement belongs to the independent shared BGP fact."""
    values = commands(None)
    values[0].errors = [error]
    fact = BgpVplsSignalingInstanceFact.derive(OfflineAntaDevice("test"), values)
    assert isinstance(fact, UnavailableFact)
    assert fact.problem is FactProblemKind.COLLECTION_FAILED
    assert fact.source.name == "show bgp vpls signaling"


def test_unsupported_is_unavailable_instead_of_absence() -> None:
    """An unsupported command is not successful empty signaling output."""
    values = commands(None)
    values[0].errors = ["This command is not supported on this hardware platform"]
    fact = BgpVplsSignalingInstanceFact.derive(OfflineAntaDevice("test"), values)
    assert isinstance(fact, UnavailableFact)
    assert fact.problem is FactProblemKind.UNSUPPORTED
