<<<<<<< HEAD:tests/units/anta_tests/configuration/data.py
# Copyright (c) 2023 Arista Networks, Inc.
# Use of this source code is governed by the Apache License 2.0
# that can be found in the LICENSE file.
"""Data for testing anta.tests.configuration"""
=======
"""
Tests for anta.tests.hardware.py
"""
from __future__ import annotations
>>>>>>> 6bdc890 (anta.tests.configuration: refactor tests):tests/units/anta_tests/test_configuration.py

from typing import Any

from anta.tests.configuration import VerifyRunningConfigDiffs, VerifyZeroTouch
from tests.lib.test_case import test

DATA: list[dict[str, Any]] = [
    {
        "name": "success",
        "test": VerifyZeroTouch,
        "eos_data": [{"mode": "disabled"}],
        "inputs": None,
        "expected": {"result": "success"},
    },
    {
        "name": "failure",
        "test": VerifyZeroTouch,
        "eos_data": [{"mode": "enabled"}],
        "inputs": None,
        "expected": {"result": "failure", "messages": ["ZTP is NOT disabled"]},
    },
    {
        "name": "success",
        "test": VerifyRunningConfigDiffs,
        "eos_data": [""],
        "inputs": None,
        "expected": {"result": "success"},
    },
    {"name": "failure", "test": VerifyRunningConfigDiffs, "eos_data": ["blah blah"], "inputs": None, "expected": {"result": "failure", "messages": ["blah blah"]}},
]
