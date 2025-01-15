# Copyright (c) 2023-2025 Arista Networks, Inc.
# Use of this source code is governed by the Apache License 2.0
# that can be found in the LICENSE file.
"""Data for testing anta.tests.configuration."""

from __future__ import annotations

from typing import TYPE_CHECKING

from anta.tests.configuration import VerifyRunningConfigDiffs, VerifyRunningConfigLines, VerifyZeroTouch
from tests.units.anta_tests import test

if TYPE_CHECKING:
    from tests.units.anta_tests import AntaUnitTest

DATA: list[AntaUnitTest] = [
    {
        "name": "success",
        "test": VerifyZeroTouch,
        "eos_data": [{"mode": "disabled"}],
        "expected": {"result": "success"},
    },
    {
        "name": "failure",
        "test": VerifyZeroTouch,
        "eos_data": [{"mode": "enabled"}],
        "expected": {"result": "failure", "messages": ["ZTP is NOT disabled"]},
    },
    {
        "name": "success",
        "test": VerifyRunningConfigDiffs,
        "eos_data": [""],
        "expected": {"result": "success"},
    },
    {
        "name": "failure",
        "test": VerifyRunningConfigDiffs,
        "eos_data": ["blah blah"],
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
]
