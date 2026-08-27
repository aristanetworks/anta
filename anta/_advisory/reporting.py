# Copyright (c) 2026 Arista Networks, Inc.
# Use of this source code is governed by the Apache License 2.0
# that can be found in the LICENSE file.
"""Shared helpers for security advisory reports."""

from __future__ import annotations

from typing import TYPE_CHECKING

from anta._advisory.results import get_advisory_metadata

if TYPE_CHECKING:
    from collections.abc import Sequence

    from anta._advisory.models import AdvisoryMetadata
    from anta.result_manager.models import TestResult


def validate_advisory_results(results: Sequence[TestResult]) -> list[tuple[TestResult, AdvisoryMetadata]]:
    """Return results paired with metadata, rejecting empty or mixed result sets."""
    if not results:
        msg = "Security advisory reports require at least one test result."
        raise ValueError(msg)

    advisory_results: list[tuple[TestResult, AdvisoryMetadata]] = []
    non_advisory_results: list[str] = []
    for result in results:
        advisory = get_advisory_metadata(result)
        if advisory is None:
            non_advisory_results.append(f"{result.name}/{result.test}")
        else:
            advisory_results.append((result, advisory))

    if non_advisory_results:
        msg = f"Security advisory reports only support advisory test results. Found non-advisory results: {', '.join(non_advisory_results)}."
        raise ValueError(msg)

    return advisory_results
