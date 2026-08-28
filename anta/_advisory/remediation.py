# Copyright (c) 2026 Arista Networks, Inc.
# Use of this source code is governed by the Apache License 2.0
# that can be found in the LICENSE file.
"""Remediation text helpers for advisory tests."""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from collections.abc import Sequence

PAIR_COUNT = 2


@dataclass(frozen=True)
class FixedRelease:
    """First fixed release published for one software train."""

    version: str
    train: str
    product: str = "EOS"

    def recommendation(self) -> str:
        """Return the bounded upgrade recommendation for this train."""
        return f"{self.product} {self.version} or later in the {self.train} train"


def _join_recommendations(recommendations: Sequence[str]) -> str:
    """Join upgrade targets as concise prose."""
    if len(recommendations) == 1:
        return recommendations[0]
    if len(recommendations) == PAIR_COUNT:
        return f"{recommendations[0]} or {recommendations[1]}"
    return f"{', '.join(recommendations[:-1])}, or {recommendations[-1]}"


def upgrade_remediation(
    fixed_releases: Sequence[FixedRelease],
    *,
    inconclusive: bool = False,
    additional_action: str | None = None,
) -> str:
    """Build source-backed upgrade advice without repeating the advisory URL."""
    if fixed_releases:
        targets = _join_recommendations([release.recommendation() for release in fixed_releases])
        upgrade = f"Upgrade to {targets}."
    else:
        upgrade = "Upgrade to a remediated release when one is published."
    if additional_action is not None:
        upgrade = f"{upgrade} {additional_action}"

    if inconclusive:
        reference = (
            "Refer to the advisory to determine whether the unresolved condition applies, for newly remediated releases, and for current mitigation guidance."
        )
    else:
        reference = "Refer to the advisory for newly remediated releases and current mitigation guidance."
    return f"{upgrade} {reference}"


def no_remediation() -> str:
    """Return an empty remediation value for a not-affected assessment."""
    return ""


def evidence_remediation(evidence: str) -> str:
    """Return an operational action for missing or invalid test evidence."""
    return f"Collect or correct {evidence} and rerun the test."


def mitigated_remediation(
    mitigation: str,
    fixed_releases: Sequence[FixedRelease],
) -> str:
    """Return advice for a verified compensating control."""
    return f"Maintain {mitigation} until upgrading. {upgrade_remediation(fixed_releases)}"
