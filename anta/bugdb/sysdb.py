# Copyright (c) 2023-2026 Arista Networks, Inc.
# Use of this source code is governed by the Apache License 2.0
# that can be found in the LICENSE file.
"""SysDB client for querying device state via PyClient.

Uses ``bash python`` via eAPI to run a PyClient script on the device that
connects to SysDB, reads the requested paths, and returns a JSON dict.

PyClient provides direct Python object access to SysDB entities without
the text parsing overhead of the Acons interactive shell.
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

SYSDB_TIMEOUT = 30

# Python script executed on-device via PyClient to read SysDB paths.
# Connects to SysDB, walks each requested path using EntityProxy.attributes,
# and prints a JSON dict mapping path → {attr: value, ...}.
# Written to a temp file on the device to stay within eAPI command length limits.
_DEVICE_SCRIPT = """\
import sys,base64,json
from PyClient import PyClient
paths=json.loads(base64.b64decode(sys.argv[1]))
pc=PyClient('ar','Sysdb')
root=pc.root()
S={'isNondestructing','entity','name','fullName','parent','parentAttr','parentAttrName','nameInParent'}
def D(o,d=0):
 R={}
 for a in o.attributes:
  if a in S:
   continue
  try:
   v=getattr(o,a)
  except Exception:
   continue
  if callable(v):
   continue
  if hasattr(v,'attributes'):
   if d<2:
    if hasattr(v,'isCollection') and v.isCollection():
     R[a]={str(k):D(w,d+1) for k,w in v.items()}
    else:
     R[a]=D(v,d+1)
  else:
   R[a]=v
 return R
O={}
for p in paths:
 try:
  w=p[:-2] if p.endswith('/*') else p
  e=root.entity['ar'+w]
  if p.endswith('/*') and hasattr(e,'isCollection') and e.isCollection():
   for k,v in e.items():
    O[w+'/'+str(k)]=D(v)
  else:
   O[w]=D(e)
 except Exception:
  pass
json.dump(O,sys.stdout,default=str)
"""


async def fetch_sysdb_paths(device: AntaDevice, paths: set[str]) -> dict[str, Any]:
    """Fetch multiple SysDB paths from a device via PyClient.

    Sends a single eAPI ``bash`` command that writes a PyClient script
    to a temp file, connects to SysDB, reads the requested paths, and
    returns a JSON dict.

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
        command=f"bash timeout {SYSDB_TIMEOUT} {bash_cmd}",
        ofmt="text",
    )
    await device.collect_commands([cmd])

    if not cmd.collected or cmd.error:
        logger.warning("SysDB collection via PyClient failed on %s — feature-tag resolution will be incomplete", device.name)
        return {}

    output = cmd.text_output.strip()
    if not output:
        return {}

    try:
        return json.loads(output)  # type: ignore[no-any-return]
    except json.JSONDecodeError:
        logger.warning("Failed to parse SysDB JSON output from %s", device.name)
        return {}


def _build_bash_command(paths: list[str]) -> str:
    """Build a bash command that runs the on-device PyClient script.

    Writes the script to a temp file on the device, runs it with the
    base64-encoded path list as an argument, and cleans up.
    """
    encoded_paths = base64.b64encode(json.dumps(paths).encode()).decode()
    encoded_script = base64.b64encode(_DEVICE_SCRIPT.encode()).decode()
    return f"bash -c 'F=$(mktemp);trap \"rm -f $F\" EXIT;base64 -d<<<{encoded_script}>$F;python $F {encoded_paths}'"
