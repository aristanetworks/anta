# Copyright (c) 2026 Arista Networks, Inc.
# Use of this source code is governed by the Apache License 2.0
# that can be found in the LICENSE file.
"""Builders for passing normalized facts directly to advisory assessments."""

from __future__ import annotations

from typing import TYPE_CHECKING

from anta._advisory.eos_versions import AffectedStatus, VersionRule, evaluate_version
from anta._advisory.facts.eos import EosVersionFact
from anta._advisory.facts.models import AvailableFact, FactSource, FactSourceKind
from anta._eos.version import parse_eos_version

if TYPE_CHECKING:
    from collections.abc import Sequence

SOURCE = FactSource("unit test", FactSourceKind.DEVICE_METADATA)


def eos_version_fact(version: str) -> AvailableFact[EosVersionFact]:
    """Build a normalized EOS version fact."""
    parsed = parse_eos_version(version).unwrap()
    return EosVersionFact.from_version(parsed).available(SOURCE)


def assert_version_statuses(matrix: Sequence[VersionRule], cases: Sequence[tuple[str, AffectedStatus]]) -> None:
    """Assert independent source-boundary expectations against one version matrix."""
    for version, expected in cases:
        actual = evaluate_version(parse_eos_version(version).unwrap(), matrix).affected_status
        assert actual is expected, f"Expected {version} to be {expected.name}, got {actual.name}"
