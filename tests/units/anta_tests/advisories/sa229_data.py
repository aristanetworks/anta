# Copyright (c) 2026 Arista Networks, Inc.
# Use of this source code is governed by the Apache License 2.0
# that can be found in the LICENSE file.
"""Sanitized native event-handler evidence for SA229."""

from __future__ import annotations

import json
from pathlib import Path

_FIXTURES = Path(__file__).parents[3] / "data" / "advisories" / "sa229"
BOOT_ENABLED = json.loads((_FIXTURES / "boot-handler.json").read_text())
BOOT_ABSENT = {"eventHandlers": {}}
