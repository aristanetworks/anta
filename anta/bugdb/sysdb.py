# Copyright (c) 2023-2026 Arista Networks, Inc.
# Use of this source code is governed by the Apache License 2.0
# that can be found in the LICENSE file.
"""SysDB client for querying device state via Acons.

Uses ``bash python -m Acons Sysdb`` via eAPI to read SysDB paths on EOS devices.
The ``ls -l /ar/Sysdb/...`` command is used with full absolute paths to avoid
the empty client-side mount profile that prevents ``cd`` from resolving paths
in subprocess Acons sessions.

The Acons text output is parsed **on the device** by a Python wrapper script
that returns JSON, avoiding fragile regex parsing on the ANTA side.
"""

from __future__ import annotations

import base64
import json
import logging
from typing import TYPE_CHECKING, Any

from anta.models import AntaCommand

if TYPE_CHECKING:
    from anta.device import AntaDevice

logger = logging.getLogger(__name__)

ACONS_TIMEOUT = 30

# Python script executed on-device to parse Acons output into JSON.
# Spawns Acons, sends ls -l commands, parses the text output, and prints a
# JSON dict mapping each SysDB path to its attributes.
# Written to a temp file on the device to stay within eAPI command length limits.
_DEVICE_SCRIPT = """\
import subprocess,sys,base64,json,re
c=base64.b64decode(sys.argv[1])
p=subprocess.Popen(["python","-m","Acons","Sysdb"],stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=subprocess.DEVNULL)
o,_=p.communicate(c)
K=("Connecting to agent","Connected to process","Connection closed")
R={}
P=None
A={}
for l in o.decode().splitlines():
 s=l.strip().lstrip("$ ").strip()
 if not s or s=="$" or s.startswith(K):
  continue
 if " is " in s and s.startswith(("/ar/Sysdb/","/ar/Eos/","/Sysdb/","/Eos/")):
  if P is not None and A:
   R[P]=A
  x=s.split(" is ")[0].strip()
  P=x[3:] if x.startswith("/ar") else x
  A={}
  continue
 if "not found" in s:
  if P is not None and A:
   R[P]=A
  P=None
  A={}
  continue
 if P is not None:
  m=re.match(r"\\s*(\\S+?)\\s*:\\s+(.*)",s)
  if m:
   n,v=m.group(1),m.group(2).strip()
   if v in("True","true"):
    v=True
   elif v in("False","false"):
    v=False
   elif v in("None","[]",""):
    v=None
   else:
    try:
     v=int(v)
    except ValueError:
     try:
      v=float(v)
     except ValueError:
      pass
   A[n]=v
if P is not None and A:
 R[P]=A
json.dump(R,sys.stdout)
"""


async def fetch_sysdb_paths(device: AntaDevice, paths: set[str]) -> dict[str, Any]:
    """Fetch multiple SysDB paths from a device via Acons.

    Sends a single eAPI ``bash`` command that writes a parser script
    to a temp file, spawns Acons with ``ls -l`` queries, parses
    the text output on-device, and returns a JSON dict.

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

    sorted_paths = sorted(paths)
    bash_cmd = _build_bash_command(sorted_paths)

    cmd = AntaCommand(
        command=f"bash timeout {ACONS_TIMEOUT} {bash_cmd}",
        ofmt="text",
    )
    await device.collect_commands([cmd])

    if not cmd.collected or cmd.error:
        logger.warning("SysDB collection via Acons failed on %s — feature-tag resolution will be incomplete", device.name)
        return {}

    output = cmd.text_output.strip()
    if not output:
        return {}

    try:
        return json.loads(output)  # type: ignore[no-any-return]
    except json.JSONDecodeError:
        logger.warning("Failed to parse SysDB JSON output from %s", device.name)
        return {}


def _build_acons_commands(paths: list[str]) -> str:
    """Build Acons stdin commands for a list of SysDB paths.

    Uses ``ls -l /ar/Sysdb/...`` to list entity attributes directly.
    Unlike ``cd``, the ``ls`` command with a full path does not
    require client-side mount profiles and works in subprocess
    Acons sessions spawned via eAPI ``bash``.
    """
    lines = []
    for p in paths:
        ar = f"/ar{p[:-2]}" if p.endswith("/*") else f"/ar{p}"
        lines.append(f"ls -l {ar}")
    lines.append("exit")
    return "\n".join(lines) + "\n"


def _build_bash_command(paths: list[str]) -> str:
    """Build a bash command that runs the on-device parser script.

    Writes the parser script to a temp file on the device, runs it
    with the base64-encoded Acons commands as an argument, and cleans up.
    """
    acons_cmds = _build_acons_commands(paths)
    encoded_cmds = base64.b64encode(acons_cmds.encode()).decode()
    encoded_script = base64.b64encode(_DEVICE_SCRIPT.encode()).decode()
    return f"bash -c 'F=$(mktemp);base64 -d<<<{encoded_script}>$F;python $F {encoded_cmds};rm -f $F'"
