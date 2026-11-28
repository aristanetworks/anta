# Copyright (c) 2026 Arista Networks, Inc.
# Use of this source code is governed by the Apache License 2.0
# that can be found in the LICENSE file.
"""Sanitized native event-handler evidence for SA229."""

from __future__ import annotations

import json
from copy import deepcopy
from pathlib import Path

_FIXTURES = Path(__file__).parents[3] / "data" / "advisories" / "sa229"
BOOT_ENABLED = json.loads((_FIXTURES / "boot-handler.json").read_text())
BOOT_ABSENT = {"eventHandlers": {}}

# Synthetic mutation: outer double quotes expand substitutions before the loop.
BOOT_REQUOTED = deepcopy(BOOT_ENABLED)
next(iter(BOOT_REQUOTED["eventHandlers"].values()))["action"] = (
    'sudo ip -all netns exec bash -c "for i in /sys/class/net/ma*; do '
    r'ethtool -L \"$(basename \"$i\")\" rx 1; ethtool -L \"$(basename \"$i\")\" combined 1; done" &> /dev/null'
)
