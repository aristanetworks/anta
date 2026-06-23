# Copyright (c) 2023-2026 Arista Networks, Inc.
# Use of this source code is governed by the Apache License 2.0
# that can be found in the LICENSE file.
"""SysDB client for querying device state via Acons.

Uses ``bash python3 -m Acons Sysdb`` via eAPI to read SysDB paths on EOS devices.
The output is parsed into Python dicts for use by the AQL evaluator.
"""

from __future__ import annotations

import json
import logging
from typing import TYPE_CHECKING, Any

from anta.models import AntaCommand

if TYPE_CHECKING:
    from anta.device import AntaDevice

logger = logging.getLogger(__name__)

ACONS_TIMEOUT = 10


async def fetch_sysdb_paths(device: AntaDevice, paths: set[str]) -> dict[str, Any]:
    """Fetch multiple SysDB paths from a device via Acons.

    Parameters
    ----------
    device
        The ANTA device to query.
    paths
        Set of SysDB paths to fetch (e.g. ``/Sysdb/routing/bgp/config``).

    Returns
    -------
    dict[str, Any]
        Dict mapping each path to its fetched data. Paths that failed
        to fetch are omitted.
    """
    if not paths:
        return {}

    result: dict[str, Any] = {}
    commands: list[tuple[str, AntaCommand]] = []

    for path in paths:
        # Build a single Acons command that outputs JSON for the path
        acons_script = _build_acons_script(path)
        cmd = AntaCommand(
            command=f"bash timeout {ACONS_TIMEOUT} python3 -c {_shell_quote(acons_script)}",
            ofmt="text",
        )
        commands.append((path, cmd))

    # Collect all commands on the device
    await device.collect_commands([cmd for _, cmd in commands])

    for path, cmd in commands:
        if cmd.collected and not cmd.error:
            try:
                parsed = _parse_acons_output(cmd.text_output)
                if parsed is not None:
                    result[path] = parsed
            except Exception:  # noqa: BLE001
                logger.debug("Failed to parse Acons output for %s on %s", path, device.name)

    return result


def _build_acons_script(path: str) -> str:
    """Build a Python script that queries a SysDB path via Acons and outputs JSON."""
    # Handle wildcard paths: /Sysdb/path/* -> list children
    if path.endswith("/*"):
        base_path = path[:-2]
        return (
            "import json, sys\n"
            "try:\n"
            "    from Acons import Sysdb\n"
            f"    node = Sysdb.get('{base_path}')\n"
            "    if node is None:\n"
            "        print('null')\n"
            "    else:\n"
            "        result = {}\n"
            "        for child in node:\n"
            "            try:\n"
            "                result[str(child)] = dict(node[child])\n"
            "            except Exception:\n"
            "                result[str(child)] = str(node[child])\n"
            "        print(json.dumps(result))\n"
            "except Exception as e:\n"
            "    print(json.dumps({'_error': str(e)}))\n"
        )
    return (
        "import json, sys\n"
        "try:\n"
        "    from Acons import Sysdb\n"
        f"    node = Sysdb.get('{path}')\n"
        "    if node is None:\n"
        "        print('null')\n"
        "    else:\n"
        "        print(json.dumps(dict(node)))\n"
        "except Exception as e:\n"
        "    print(json.dumps({'_error': str(e)}))\n"
    )


def _parse_acons_output(output: str) -> Any:  # noqa: ANN401
    """Parse the JSON output from an Acons query."""
    output = output.strip()
    if not output:
        return None
    try:
        data = json.loads(output)
    except json.JSONDecodeError:
        return None
    else:
        if isinstance(data, dict) and "_error" in data:
            logger.debug("Acons error: %s", data["_error"])
            return None
        return data


def _shell_quote(script: str) -> str:
    """Quote a Python script for use in a bash command."""
    escaped = script.replace("'", "'\"'\"'")
    return f"'{escaped}'"


def extract_path_filters(query_rules: list[dict[str, Any]]) -> set[str]:
    """Extract all unique SysDB path filters from a set of query rules.

    Parameters
    ----------
    query_rules
        List of QueryRule-like dicts with ``pathFilters`` fields.

    Returns
    -------
    set[str]
        All unique SysDB paths that need to be fetched.
    """
    paths: set[str] = set()
    for rule in query_rules:
        for pf in rule.get("pathFilters", []) if isinstance(rule, dict) else rule.path_filters:
            paths.add(pf)
    return paths
