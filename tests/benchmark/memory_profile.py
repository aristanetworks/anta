# Copyright (c) 2023-2026 Arista Networks, Inc.
# Use of this source code is governed by the Apache License 2.0
# that can be found in the LICENSE file.
"""Reconstruct a sample's allocation peak without downloading its captured stack bytes."""

from __future__ import annotations

import importlib
import re
from collections import Counter
from itertools import pairwise
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from pathlib import Path

LARGE_ALLOCATION_BYTES = 128 * 1024


def sample_window(timestamps: dict[str, Any], target: str) -> tuple[int, int]:
    """Require one target and ordered, complete native sample boundaries."""
    uris = timestamps["uri_by_ts"]
    markers = timestamps["markers"]
    matches = [index for index, (_timestamp, uri) in enumerate(uris) if uri == target]
    if len(matches) != 1 or [list(marker) for marker in markers] != [[kind] for _ in uris for kind in ("SampleStart", "SampleEnd")]:
        msg = "Missing target or inconsistent native measurement markers"
        raise ValueError(msg)
    windows = [(markers[2 * index]["SampleStart"], markers[2 * index + 1]["SampleEnd"]) for index in range(len(uris))]
    if any(start >= end or uris[index][0] < end for index, (start, end) in enumerate(windows)) or any(left[1] >= right[0] for left, right in pairwise(windows)):
        msg = "Native measurement timestamps are inconsistent"
        raise ValueError(msg)
    return windows[matches[0]]


def summarize_profile(directory: Path, target: str) -> dict[str, Any]:  # noqa: C901  # pylint: disable=too-many-locals,too-many-branches
    """Count live requested bytes originating inside one native measurement window.

    This is an independent allocation-cohort metric, not RSS or a CodSpeed dashboard export.
    A realloc contributes its full new requested size, including for a pre-window pointer.
    """
    # These optional analysis dependencies are installed by the diagnostic workflow.
    # Ordinary ANTA benchmark/type-check environments do not need them.
    msgpack = importlib.import_module("msgpack")
    zstandard = importlib.import_module("zstandard")

    results = directory / "profile/results"
    with (results / "ExecutionTimestamps.msgpack").open("rb") as stream:
        start, end = sample_window(msgpack.unpack(stream, raw=False), target)
    profiles = list(results.glob("*MemtrackArtifact.msgpack"))
    if len(profiles) != 1:
        msg = "Expected exactly one native allocation artifact"
        raise ValueError(msg)
    count = 0
    events = []
    with profiles[0].open("rb") as compressed, zstandard.ZstdDecompressor().stream_reader(compressed) as stream:
        for event in msgpack.Unpacker(stream, raw=False):
            count += 1
            if start <= event["timestamp"] <= end and event["type"] in {"Malloc", "Calloc", "AlignedAlloc", "Realloc", "Free"}:
                if event["type"] == "Realloc" and (not event["addr"] or "old_addr" not in event):
                    msg = "Unsupported failed realloc or missing source pointer"
                    raise ValueError(msg)
                events.append(event)
    logged = re.search(r"Wrote (\d+) memtrack events to disk", (directory / "run.log").read_text(encoding="utf-8"))
    if logged is None or count != int(logged[1]):
        msg = "Decoded native event count does not match the tracker log"
        raise ValueError(msg)
    live: dict[tuple[int, int], int] = {}
    current = peak = cumulative = 0
    large: Counter[int] = Counter()
    for event in sorted(events, key=lambda event: event["timestamp"]):
        kind = event["type"]
        key = (event["pid"], event["addr"])
        if kind in {"Free", "Realloc"}:
            current -= live.pop((event["pid"], event.get("old_addr", event["addr"])), 0)
        if kind != "Free" and event["addr"]:
            size = event["size"]
            current -= live.pop(key, 0)
            live[key] = size
            current += size
            cumulative += size
            if size >= LARGE_ALLOCATION_BYTES:
                large[size] += 1
        peak = max(peak, current)
    if not events:
        msg = "No allocation events inside the target sample"
        raise ValueError(msg)
    return {
        "peak_sample_allocations_bytes": peak,
        "cumulative_sample_allocations_bytes": cumulative,
        "large_allocations": dict(large),
        "decoded_events": count,
    }
