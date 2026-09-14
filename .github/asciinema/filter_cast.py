#!/usr/bin/env python3

# Copyright (c) 2026 Arista Networks, Inc.
# Use of this source code is governed by the Apache License 2.0
# that can be found in the LICENSE file.
"""Shape README animation casts while preserving their meaningful output."""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path

OSC_HYPERLINK = re.compile(r"\x1b]8;.*?\x1b\\")
ANSI_CONTROL = re.compile(r"\x1b(?:\[[0-?]*[ -/]*[@-~]|\].*?\x1b\\)")


def plain_text(value: str) -> str:
    """Remove terminal control sequences used while inspecting cast output."""
    return ANSI_CONTROL.sub("", value)


def normalize_nrfu_progress(events: list[dict[str, object] | list[object]], duration: float = 4) -> None:
    """Normalize progress timing so lab performance does not control GIF duration."""
    progress_events = [event for event in events if isinstance(event, list) and event[1] == "o" and "Running Tests" in event[2]]
    actual_duration = sum(event[0] for event in progress_events)
    if actual_duration > duration:
        factor = duration / actual_duration
        for event in progress_events:
            event[0] = round(event[0] * factor, 3)


def validate_psirt_recording(events: list[dict[str, object] | list[object]]) -> None:
    """Require the successful report outcome before replacing the committed cast."""
    success_message = "Security advisory Markdown report saved to psirt.md"
    if not any(
        isinstance(event, list)
        and len(event) == 3
        and event[1] == "o"
        and isinstance(event[2], str)
        and success_message in event[2]
        for event in events
    ):
        msg = "PSIRT Markdown report success message was not found in the recording"
        raise RuntimeError(msg)


# pylint: disable=too-many-locals
def animate_nrfu_table(events: list[dict[str, object] | list[object]]) -> list[dict[str, object] | list[object]]:
    """Pause on two representative NRFU rows, then rapidly print the rest."""
    start = next(
        (index for index, event in enumerate(events) if isinstance(event, list) and event[1] == "o" and "All tests results" in event[2]),
        None,
    )
    if start is None:
        raise RuntimeError("NRFU result table was not found in the recording")

    end = None
    bottom_started = False
    for index, event in enumerate(events[start:], start):
        if not isinstance(event, list) or event[1] != "o":
            continue
        output = plain_text(event[2])
        bottom_started = bottom_started or "└" in output
        if bottom_started and "┘" in output:
            end = index
            break
    if end is None:
        raise RuntimeError("NRFU result table bottom border was not found in the recording")

    table_events = events[start : end + 1]
    table_text = "".join(event[2] for event in table_events if isinstance(event, list) and event[1] == "o")
    lines = table_text.splitlines(keepends=True)
    header_separator = next((index for index, line in enumerate(lines) if plain_text(line).lstrip().startswith("┡")), None)
    row_boundaries = [index for index, line in enumerate(lines) if plain_text(line).lstrip().startswith(("├", "└"))]
    if header_separator is None or len(row_boundaries) < 2:
        raise RuntimeError("NRFU result table rows were not found after joining cast events")

    rows: list[list[str]] = []
    row_start = header_separator + 1
    for boundary in row_boundaries:
        rows.append(lines[row_start:boundary])
        row_start = boundary + 1

    status_pattern = re.compile(r"│\s*(?:success|failure|error|skipped)\s*│")
    display_rows = [row for row in rows if status_pattern.search(plain_text(row[0]))]
    successes = [index for index, row in enumerate(display_rows) if re.search(r"│\s*success\s*│", plain_text(row[0]))]
    failures = [index for index, row in enumerate(display_rows) if re.search(r"│\s*failure\s*│", plain_text(row[0]))]
    if not successes or not failures:
        raise RuntimeError("NRFU result table does not contain both a success and a failure row")
    success = min(successes, key=lambda index: len(display_rows[index]))
    failure = min(failures, key=lambda index: len(display_rows[index]))

    separator = lines[row_boundaries[0]]
    bottom = lines[row_boundaries[-1]]
    if not bottom.endswith(("\r", "\n")):
        bottom += "\r\n"
    initial_table = "".join([*lines[: header_separator + 1], *display_rows[success], bottom])
    reveal_failure = "".join(["\x1b[1A\r\x1b[2K", separator, *display_rows[failure], bottom])
    delay = round(sum(event[0] for event in table_events if isinstance(event, list)), 3)
    animation: list[dict[str, object] | list[object]] = [
        [delay, "o", initial_table],
        [0.5, "o", reveal_failure],
        [0.45, "o", "\x1b[0m"],
    ]

    remaining_rows = [row for index, row in enumerate(display_rows) if index not in {success, failure}]
    for index in range(0, len(remaining_rows), 4):
        row_delay = 0.45 if index == 0 else 0.02
        resume_table = "\x1b[1A\r\x1b[2K" if index == 0 else ""
        rows = "".join(f"{separator}{''.join(row)}" for row in remaining_rows[index : index + 4])
        animation.append([row_delay, "o", f"{resume_table}{rows}"])
    animation.append([0.01, "o", bottom])

    return [*events[:start], *animation, *events[end + 1 :]]


def main() -> None:
    """Filter and retime an asciinema cast for a concise README animation."""
    source = Path(sys.argv[1])
    destination = Path(sys.argv[2])
    recording = sys.argv[3]
    public_command = "anta nrfu" if recording == "nrfu" else "anta psirt md-report --md-output psirt.md"

    events = [json.loads(line) for line in source.read_text(encoding="utf-8").splitlines()]
    filtered_events: list[dict[str, object] | list[object]] = []

    for event in events:
        if isinstance(event, dict):
            event["command"] = public_command
        elif isinstance(event, list) and len(event) == 3 and event[1] == "o":
            if recording == "nrfu":
                if "WARNING " in event[2] or "ERROR   " in event[2]:
                    progress_start = event[2].rfind("\x1b[32m(")
                    if progress_start == -1:
                        continue
                    event[2] = "\r\x1b[2K" + event[2][progress_start:]
            event[2] = OSC_HYPERLINK.sub("", event[2])
        filtered_events.append(event)

    if recording == "nrfu":
        normalize_nrfu_progress(filtered_events)
        filtered_events = animate_nrfu_table(filtered_events)
    else:
        validate_psirt_recording(filtered_events)
        normalize_nrfu_progress(filtered_events, duration=4.5)

    with destination.open("w", encoding="utf-8") as output_stream:
        for event in filtered_events:
            output_stream.write(json.dumps(event, ensure_ascii=False, separators=(",", ":")))
            output_stream.write("\n")


if __name__ == "__main__":
    main()
