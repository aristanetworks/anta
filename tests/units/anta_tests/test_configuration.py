# Copyright (c) 2023-2025 Arista Networks, Inc.
# Use of this source code is governed by the Apache License 2.0
# that can be found in the LICENSE file.
"""Data for testing anta.tests.configuration."""

from __future__ import annotations

import sys
from typing import TYPE_CHECKING, Any

from anta.models import AntaTest
from anta.result_manager.models import AntaTestStatus
from anta.tests.configuration import VerifyRunningConfigDiffs, VerifyRunningConfigLines, VerifyZeroTouch
from tests.units.anta_tests import AntaUnitTest, test

if sys.version_info >= (3, 10):
    from typing import TypeAlias
else:
    TypeAlias = type


AntaUnitTestDataDict: TypeAlias = dict[tuple[type[AntaTest], str], AntaUnitTest]

DATA: AntaUnitTestDataDict = {
    (VerifyZeroTouch, "success"): {"eos_data": [{"mode": "disabled"}], "inputs": None, "expected": {"result": AntaTestStatus.SUCCESS}},
    (VerifyZeroTouch, "failure"): {
        "eos_data": [{"mode": "enabled"}],
        "inputs": None,
        "expected": {"result": AntaTestStatus.FAILURE, "messages": ["ZTP is NOT disabled"]},
    },
    (VerifyRunningConfigDiffs, "success"): {"eos_data": [""], "inputs": None, "expected": {"result": AntaTestStatus.SUCCESS}},
    (VerifyRunningConfigDiffs, "failure"): {"eos_data": ["blah blah"], "inputs": None, "expected": {"result": AntaTestStatus.FAILURE, "messages": ["blah blah"]}},
    (VerifyRunningConfigLines, "success"): {"eos_data": ["blah blah"], "inputs": {"regex_patterns": ["blah"]}, "expected": {"result": AntaTestStatus.SUCCESS}},
    (VerifyRunningConfigLines, "success-patterns"): {
        "eos_data": ["enable password something\nsome other line"],
        "inputs": {"regex_patterns": ["^enable password .*$", "^.*other line$"]},
        "expected": {"result": AntaTestStatus.SUCCESS},
    },
    (VerifyRunningConfigLines, "failure"): {
        "eos_data": ["enable password something\nsome other line"],
        "inputs": {"regex_patterns": ["bla", "bleh"]},
        "expected": {"result": AntaTestStatus.FAILURE, "messages": ["Following patterns were not found: 'bla', 'bleh"]},
    },
}
