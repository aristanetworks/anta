# Copyright (c) 2023-2025 Arista Networks, Inc.
# Use of this source code is governed by the Apache License 2.0
# that can be found in the LICENSE file.
"""Tests for anta.tests.profiles.py."""

from __future__ import annotations

from typing import TYPE_CHECKING

from anta.tests.profiles import VerifyTcamProfile, VerifyUnifiedForwardingTableMode
from tests.units.anta_tests import test

if TYPE_CHECKING:
    from tests.units.anta_tests import AntaUnitTest

DATA: list[AntaUnitTest] = [
    {
        "name": "success",
        "test": VerifyUnifiedForwardingTableMode,
        "eos_data": [{"uftMode": "2", "urpfEnabled": False, "chipModel": "bcm56870", "l2TableSize": 163840, "l3TableSize": 147456, "lpmTableSize": 32768}],
        "inputs": {"mode": 2},
        "expected": {"result": "success"},
    },
    {
        "name": "failure",
        "test": VerifyUnifiedForwardingTableMode,
        "eos_data": [{"uftMode": "2", "urpfEnabled": False, "chipModel": "bcm56870", "l2TableSize": 163840, "l3TableSize": 147456, "lpmTableSize": 32768}],
        "inputs": {"mode": 3},
        "expected": {"result": "failure", "messages": ["Device is not running correct UFT mode (expected: 3 / running: 2)"]},
    },
    {
        "name": "success",
        "test": VerifyTcamProfile,
        "eos_data": [
            {"pmfProfiles": {"FixedSystem": {"config": "test", "configType": "System Profile", "status": "test", "mode": "tcam"}}, "lastProgrammingStatus": {}},
        ],
        "inputs": {"profile": "test"},
        "expected": {"result": "success"},
    },
    {
        "name": "failure",
        "test": VerifyTcamProfile,
        "eos_data": [
            {"pmfProfiles": {"FixedSystem": {"config": "test", "configType": "System Profile", "status": "default", "mode": "tcam"}}, "lastProgrammingStatus": {}},
        ],
        "inputs": {"profile": "test"},
        "expected": {"result": "failure", "messages": ["Incorrect profile running on device: default"]},
    },
]
