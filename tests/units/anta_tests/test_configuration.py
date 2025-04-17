# Copyright (c) 2023-2025 Arista Networks, Inc.
# Use of this source code is governed by the Apache License 2.0
# that can be found in the LICENSE file.
"""Data for testing anta.tests.configuration."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from anta.tests.configuration import VerifyRunningConfigDiffs, VerifyRunningConfigLines, VerifyZeroTouch
from tests.units.anta_tests import test

if TYPE_CHECKING:
    from anta.models import AntaTest
    from tests.units.anta_tests import AntaUnitTest

DATA: dict[tuple[type[AntaTest], str], AntaUnitTest] = {
    (VerifyZeroTouch, "success"): {"eos_data": [{"mode": "disabled"}], "inputs": None, "expected": {"result": "success"}},
    (VerifyZeroTouch, "failure"): {"eos_data": [{"mode": "enabled"}], "inputs": None, "expected": {"result": "failure", "messages": ["ZTP is NOT disabled"]}},
    (VerifyRunningConfigDiffs, "success"): {"eos_data": [""], "inputs": None, "expected": {"result": "success"}},
    (VerifyRunningConfigDiffs, "failure"): {"eos_data": ["blah blah"], "inputs": None, "expected": {"result": "failure", "messages": ["blah blah"]}},
    (VerifyRunningConfigLines, "success"): {"eos_data": ["blah blah"], "inputs": {"regex_patterns": ["blah"]}, "expected": {"result": "success"}},
    (VerifyRunningConfigLines, "success-patterns"): {
        "eos_data": ["enable password something\nsome other line"],
        "inputs": {"regex_patterns": ["^enable password .*$", "^.*other line$"]},
        "expected": {"result": "success"},
    },
    (VerifyRunningConfigLines, "failure"): {
        "eos_data": ["enable password something\nsome other line"],
        "inputs": {"regex_patterns": ["bla", "bleh"]},
        "expected": {"result": "failure", "messages": ["Following patterns were not found: 'bla', 'bleh"]},
    },
}
