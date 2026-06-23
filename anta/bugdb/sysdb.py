# Copyright (c) 2023-2026 Arista Networks, Inc.
# Use of this source code is governed by the Apache License 2.0
# that can be found in the LICENSE file.
"""SysDB client for querying device state via Acons.

Uses ``bash python -m Acons Sysdb`` via eAPI to read SysDB paths on EOS devices.
Acons is an interactive shell — commands are piped via subprocess stdin and the
text output is parsed into Python dicts for use by the AQL evaluator.
"""

from __future__ import annotations

import logging
import re
from typing import TYPE_CHECKING, Any

from anta.models import AntaCommand

if TYPE_CHECKING:
    from anta.device import AntaDevice

logger = logging.getLogger(__name__)

ACONS_TIMEOUT = 30


async def fetch_sysdb_paths(device: AntaDevice, paths: set[str]) -> dict[str, Any]:
    """Fetch multiple SysDB paths from a device in a single Acons session.

    Builds one bash command that spawns Acons via subprocess, sends
    ``cd -q <path>; ls -l`` for each path, and parses the text output.

    Parameters
    ----------
    device
        The ANTA device to query.
    paths
        Set of SysDB paths to fetch (e.g. ``/Sysdb/routing/bgp/config``).

    Returns
    -------
    dict[str, Any]
        Dict mapping each path to its fetched data as a dict of
        attribute name → value. Paths that could not be read are omitted.
    """
    if not paths:
        return {}

    # Build Acons commands for all paths in a single session
    acons_cmds = _build_acons_commands(sorted(paths))
    bash_script = _build_bash_script(acons_cmds)

    cmd = AntaCommand(
        command=f"bash timeout {ACONS_TIMEOUT} {bash_script}",
        ofmt="text",
    )
    await device.collect_commands([cmd])

    if not cmd.collected or cmd.error:
        logger.debug("Acons batch command failed on %s", device.name)
        return {}

    return _parse_acons_batch_output(cmd.text_output, sorted(paths))


def _build_acons_commands(paths: list[str]) -> str:
    """Build Acons stdin commands for a list of SysDB paths.

    For each path, sends ``cd -q /ar<path>`` then ``ls -l`` to read all attributes.
    Uses a marker line between paths to delimit output sections.
    """
    lines: list[str] = []
    for path in paths:
        sysdb_path = f"/ar{path}" if not path.startswith("/ar") else path
        lines.append(f"cd -q {sysdb_path}")
        lines.append("ls -l")
    lines.append("exit")
    return "\\n".join(lines)


def _build_bash_script(acons_cmds: str) -> str:
    r"""Build a bash command that pipes Acons commands via subprocess.

    Uses ``printf`` to send commands with proper newlines to Acons stdin.
    """
    return (
        "python -c '"
        "import subprocess; "
        'p=subprocess.Popen(["python","-m","Acons","Sysdb"],'
        "stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=subprocess.DEVNULL); "
        f'out,_=p.communicate(b"{acons_cmds}"); '
        "print(out.decode())'"
    )


def _parse_acons_batch_output(output: str, paths: list[str]) -> dict[str, Any]:
    """Parse the text output of a batch Acons session.

    The output contains sections delimited by ``$ `` prompts. Each ``ls -l``
    produces lines like ``attribute_name  : value``.
    """
    result: dict[str, Any] = {}

    # Split by Acons prompt "$ " — each section is the output of one command
    # Skip the connection banner and filter to ls -l output sections
    sections = _extract_ls_sections(output)

    for path_idx, section in enumerate(sections):
        if path_idx >= len(paths):
            break
        path = paths[path_idx]

        parsed = _parse_ls_output(section)
        if parsed is not None:
            result[path] = parsed

    return result


def _extract_ls_sections(output: str) -> list[str]:  # noqa: C901
    """Extract the ls -l output sections from Acons output.

    Acons output looks like:
    ```
    Connecting to agent Sysdb ...
    Connected to process XXXX
    $ $ /path is <entity(...)>
      attr1 : value1
      attr2 : value2
    $ $ ...
    ```

    Each ``ls -l`` output starts after a ``$ `` prompt and contains
    indented ``name : value`` lines.
    """
    sections: list[str] = []
    current_section: list[str] = []
    in_section = False

    for line in output.splitlines():
        stripped = line.strip()

        # Skip connection banner
        if stripped.startswith(("Connecting to agent", "Connected to process")):
            continue

        # Skip "Connection closed" line
        if stripped.startswith("Connection closed"):
            continue

        # Entity header line from cd or ls starts with a path
        if stripped.startswith(("/ar/Sysdb/", "/Sysdb/")):
            if current_section:
                sections.append("\n".join(current_section))
            current_section = []
            in_section = True
            continue

        # "Directory ... not found" means the path doesn't exist
        if "not found" in stripped:
            if current_section:
                sections.append("\n".join(current_section))
            current_section = []
            sections.append("")  # empty section = path not found
            in_section = False
            continue

        # Prompt-only lines
        if stripped in {"$", "$ $"}:
            continue

        if in_section and ":" in line:
            current_section.append(line)

    if current_section:
        sections.append("\n".join(current_section))

    return sections


def _parse_ls_output(section: str) -> dict[str, Any] | None:
    """Parse an ``ls -l`` output section into a dict of attribute → value.

    Lines have the format: ``  attribute_name  : value``
    """
    if not section.strip():
        return None

    result: dict[str, Any] = {}
    for line in section.splitlines():
        match = re.match(r"\s+(\S+)\s+:\s+(.*)", line)
        if match:
            name = match.group(1)
            raw_value = match.group(2).strip()
            result[name] = _coerce_value(raw_value)

    return result or None


def _coerce_value(raw: str) -> Any:  # noqa: ANN401
    """Coerce a string value from Acons ls -l output to a Python type."""
    if raw in ("True", "true"):
        return True
    if raw in ("False", "false"):
        return False
    if raw in {"None", "[]", ""}:
        return None

    # Integer
    try:
        return int(raw)
    except ValueError:
        pass

    # Float
    try:
        return float(raw)
    except ValueError:
        pass

    return raw
