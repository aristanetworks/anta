# Copyright (c) 2026 Arista Networks, Inc.
# Use of this source code is governed by the Apache License 2.0
# that can be found in the LICENSE file.
"""Builders for passing normalized facts directly to advisory assessments."""

from __future__ import annotations

from typing import TYPE_CHECKING, TypeVar

from anta._advisory.eos_versions import AffectedStatus, VersionRule, evaluate_version
from anta._advisory.facts.eos import EosVersionFact
from anta._advisory.facts.models import AvailableFact, FactDefinition, FactProblemKind, FactSource, FactSourceKind, UnavailableFact
from anta._eos.version import EOSVersion, parse_eos_version

if TYPE_CHECKING:
    from collections.abc import Sequence

T = TypeVar("T")
SOURCE = FactSource("unit test", FactSourceKind.DEVICE_METADATA)


def available_fact(definition: type[FactDefinition[T]], value: T) -> AvailableFact[T]:
    """Build an available fact with a stable unit-test source."""
    return definition.available(value, SOURCE)


def unavailable_fact(definition: type[FactDefinition[T]], problem: FactProblemKind = FactProblemKind.MISSING) -> UnavailableFact[T]:
    """Build an unavailable fact with a stable unit-test source."""
    return definition.unavailable(problem, SOURCE)


def eos_version_fact(version: str) -> AvailableFact[EOSVersion]:
    """Build a normalized EOS version fact."""
    return available_fact(EosVersionFact, parse_eos_version(version).unwrap())


def assert_version_statuses(matrix: Sequence[VersionRule], cases: Sequence[tuple[str, AffectedStatus]]) -> None:
    """Assert independent source-boundary expectations against one version matrix."""
    for version, expected in cases:
        actual = evaluate_version(parse_eos_version(version).unwrap(), matrix).affected_status
        assert actual is expected, f"Expected {version} to be {expected.name}, got {actual.name}"
