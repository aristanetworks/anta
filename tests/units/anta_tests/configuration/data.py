# Copyright (c) 2023 Arista Networks, Inc.
# Use of this source code is governed by the Apache License 2.0
# that can be found in the LICENSE file.
"""Data for testing anta.tests.configuration"""

from typing import Any, Dict, List

INPUT_ZEROTOUCH: List[Dict[str, Any]] = [
    {
        "name": "success",
        "eos_data": [{"mode": "disabled"}],
        "inputs": None,
        "expected": {"result": "success"},
    },
    {
        "name": "failure",
        "eos_data": [{"mode": "enabled"}],
        "inputs": None,
        "expected": {"result": "failure", "messages": ["ZTP is NOT disabled"]}
    },
]


INPUT_RUNNING_CONFIG: List[Dict[str, Any]] = [
    {
        "name": "success",
        "eos_data": [''],
        "inputs": None,
        "expected": {"result": "success"},
    },
    {
        "name": "failure",
        "eos_data": ["blah blah"],
        "inputs": None,
        "expected": {"result": "failure", "messages": ["blah blah"]}
    },
]
