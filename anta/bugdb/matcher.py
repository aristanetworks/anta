# Copyright (c) 2023-2026 Arista Networks, Inc.
# Use of this source code is governed by the Apache License 2.0
# that can be found in the LICENSE file.
"""Bug matching engine.

Determines which bugs from the AlertBase database affect a given device
based on its EOS version and resolved tags.
"""

from __future__ import annotations

import logging

from anta.bugdb.models import Bug, BugMatch
from anta.bugdb.version import EOSVersion, is_version_affected

logger = logging.getLogger(__name__)


def match_bug(bug: Bug, device_version: EOSVersion, device_tags: set[str]) -> BugMatch | None:
    """Check if a bug affects a device given its version and tags.

    Parameters
    ----------
    bug
        The bug entry to evaluate.
    device_version
        Parsed EOS version of the device.
    device_tags
        Set of resolved tags for the device (hardware + feature).

    Returns
    -------
    BugMatch | None
        A ``BugMatch`` if the bug affects the device, ``None`` otherwise.
    """
    if bug.product != "eos":
        return None

    if not is_version_affected(device_version, bug.version_introduced, bug.version_fixed):
        return None

    # No conjunction = applies unconditionally to affected versions
    if not bug.conjunction:
        return BugMatch(bug=bug, matched_by="version-only (no tag conditions)")

    # Evaluate conjunction: OR of ANDs
    for clause_idx, and_clause in enumerate(bug.conjunction):
        clause_tags = {cond.tag for cond in and_clause}
        if clause_tags.issubset(device_tags):
            matched_tags = ", ".join(sorted(clause_tags))
            return BugMatch(bug=bug, matched_by=f"clause {clause_idx}: {matched_tags}")

    return None


def match_bugs(
    bugs: list[Bug],
    device_version: EOSVersion,
    device_tags: set[str],
    *,
    min_severity: str | None = None,
) -> list[BugMatch]:
    """Match all bugs against a device's version and tags.

    Parameters
    ----------
    bugs
        List of bugs to evaluate.
    device_version
        Parsed EOS version of the device.
    device_tags
        Set of resolved tags for the device.
    min_severity
        Optional minimum severity filter (e.g. ``"sev2"``).
        Only bugs with severity <= this value are included (sev1 is highest).

    Returns
    -------
    list[BugMatch]
        List of matching bugs, sorted by severity then bug ID.
    """
    severity_order = {"sev1": 1, "sev2": 2, "sev3": 3, "sev4": 4}
    min_sev_num = severity_order.get(min_severity, 4) if min_severity else 4

    matches: list[BugMatch] = []
    for bug in bugs:
        bug_sev_num = severity_order.get(bug.severity, 4)
        if bug_sev_num > min_sev_num:
            continue

        result = match_bug(bug, device_version, device_tags)
        if result is not None:
            matches.append(result)

    matches.sort(key=lambda m: (severity_order.get(m.bug.severity, 4), m.bug.bug_id))
    return matches
