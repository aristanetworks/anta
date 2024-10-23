# Copyright (c) 2023-2024 Arista Networks, Inc.
# Use of this source code is governed by the Apache License 2.0
# that can be found in the LICENSE file.
"""Data for testing anta.tests.configuration."""

from __future__ import annotations

from typing import Any

from anta.tests.configuration import VerifyMcsClientMounts, VerifyRunningConfigDiffs, VerifyRunningConfigLines, VerifyZeroTouch
from tests.units.anta_tests import test

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
    {
        "name": "failure",
        "test": VerifyRunningConfigDiffs,
        "eos_data": ["blah blah"],
        "inputs": None,
        "expected": {"result": "failure", "messages": ["blah blah"]},
    },
    {
        "name": "success",
        "test": VerifyRunningConfigLines,
        "eos_data": ["blah blah"],
        "inputs": {"regex_patterns": ["blah"]},
        "expected": {"result": "success"},
    },
    {
        "name": "success",
        "test": VerifyRunningConfigLines,
        "eos_data": ["enable password something\nsome other line"],
        "inputs": {"regex_patterns": ["^enable password .*$", "^.*other line$"]},
        "expected": {"result": "success"},
    },
    {
        "name": "failure",
        "test": VerifyRunningConfigLines,
        "eos_data": ["enable password something\nsome other line"],
        "inputs": {"regex_patterns": ["bla", "bleh"]},
        "expected": {"result": "failure", "messages": ["Following patterns were not found: 'bla','bleh'"]},
    },
    {
        "name": "success",
        "test": VerifyMcsClientMounts,
        "eos_data": [{"mountStates": [{"path": "mcs/v1/toSwitch/28-99-3a-8f-93-7b", "type": "Mcs::DeviceConfigV1", "state": "mountStateMountComplete"}]}],
        "inputs": None,
        "expected": {"result": "success"},
    },
    {
        "name": "success-haclient",
        "test": VerifyMcsClientMounts,
        "eos_data": [
            {
                "mountStates": [
                    {"path": "mcs/v1/apiCfgRedState", "type": "Mcs::ApiConfigRedundancyState", "state": "mountStateMountComplete"},
                    {"path": "mcs/v1/toSwitch/00-1c-73-74-c0-8b", "type": "Mcs::DeviceConfigV1", "state": "mountStateMountComplete"},
                ]
            },
        ],
        "inputs": None,
        "expected": {"result": "success"},
    },
]
