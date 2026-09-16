# Copyright (c) 2026 Arista Networks, Inc.
# Use of this source code is governed by the Apache License 2.0
# that can be found in the LICENSE file.
"""Builders for passing normalized facts directly to advisory assessments."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, TypeVar, cast

from anta._advisory.eos_versions import AffectedStatus, VersionRule, evaluate_version
from anta._advisory.facts.eos import EosVersionFact
from anta._advisory.facts.models import AvailableFact, FactDefinition, FactProblemKind, FactSource, FactSourceKind, UnavailableFact
from anta._eos.version import parse_eos_version

if TYPE_CHECKING:
    from collections.abc import Sequence

FactT = TypeVar("FactT", bound=FactDefinition[Any])
SOURCE = FactSource("unit test", FactSourceKind.DEVICE_METADATA)


def available_fact(definition: type[FactT], value: FactT) -> AvailableFact[FactT]:
    """Build an available fact with a stable unit-test source."""
    if type(value) is not definition:
        msg = "Fact value must use the requested definition class"
        raise TypeError(msg)
    return value.available(SOURCE)


def unavailable_fact(definition: type[FactT], problem: FactProblemKind = FactProblemKind.MISSING) -> UnavailableFact[FactT]:
    """Build an unavailable fact with a stable unit-test source."""
    return cast("UnavailableFact[FactT]", definition.unavailable(problem, SOURCE))


def eos_version_fact(version: str) -> AvailableFact[EosVersionFact]:
    """Build a normalized EOS version fact."""
    parsed = parse_eos_version(version).unwrap()
    return available_fact(EosVersionFact, EosVersionFact.from_version(parsed))


def assert_version_statuses(matrix: Sequence[VersionRule], cases: Sequence[tuple[str, AffectedStatus]]) -> None:
    """Assert independent source-boundary expectations against one version matrix."""
    for version, expected in cases:
        actual = evaluate_version(parse_eos_version(version).unwrap(), matrix).affected_status
        assert actual is expected, f"Expected {version} to be {expected.name}, got {actual.name}"
