# Copyright (c) 2023-2025 Arista Networks, Inc.
# Use of this source code is governed by the Apache License 2.0
# that can be found in the LICENSE file.
"""Tests for anta.tests.profiles.py."""

from __future__ import annotations

import sys
from typing import TYPE_CHECKING, Any

from anta.models import AntaTest
from anta.result_manager.models import AntaTestStatus
from anta.tests.profiles import VerifyTcamProfile, VerifyUnifiedForwardingTableMode
from tests.units.anta_tests import test

if TYPE_CHECKING:
    from tests.units.anta_tests import AntaUnitTestDataDict

DATA: AntaUnitTestDataDict = {
    (VerifyUnifiedForwardingTableMode, "success"): {
        "eos_data": [{"uftMode": "2", "urpfEnabled": False, "chipModel": "bcm56870", "l2TableSize": 163840, "l3TableSize": 147456, "lpmTableSize": 32768}],
        "inputs": {"mode": 2},
        "expected": {"result": AntaTestStatus.SUCCESS},
    },
    (VerifyUnifiedForwardingTableMode, "failure"): {
        "eos_data": [{"uftMode": "2", "urpfEnabled": False, "chipModel": "bcm56870", "l2TableSize": 163840, "l3TableSize": 147456, "lpmTableSize": 32768}],
        "inputs": {"mode": 3},
        "expected": {"result": AntaTestStatus.FAILURE, "messages": ["Not running the correct UFT mode - Expected: 3 Actual: 2"]},
    },
    (VerifyTcamProfile, "success"): {
        "eos_data": [
            {"pmfProfiles": {"FixedSystem": {"config": "test", "configType": "System Profile", "status": "test", "mode": "tcam"}}, "lastProgrammingStatus": {}}
        ],
        "inputs": {"profile": "test"},
        "expected": {"result": AntaTestStatus.SUCCESS},
    },
    (VerifyTcamProfile, "failure-pmf-profiles-not-found"): {
        "eos_data": [{"pmfProfiles": {}, "lastProgrammingStatus": {}}],
        "inputs": {"profile": "test"},
        "expected": {"result": AntaTestStatus.FAILURE, "messages": ["No TCAM profile found"]},
    },
    (VerifyTcamProfile, "failure"): {
        "eos_data": [
            {
                "pmfProfiles": {
                    "Linecard3": {"config": "default", "configType": "System Profile", "status": "default", "mode": "tcam"},
                    "Linecard4": {"config": "default", "configType": "System Profile", "status": "default", "mode": "tcam"},
                    "FixedSystem": {"config": "default", "configType": "System Profile", "status": "default", "mode": "tcam"},
                },
            }
        ],
        "inputs": {"profile": "test"},
        "expected": {
            "result": AntaTestStatus.FAILURE,
            "messages": [
                "Linecard3 - Incorrect profile running on device - Expected: test Actual: default",
                "Linecard4 - Incorrect profile running on device - Expected: test Actual: default",
                "FixedSystem - Incorrect profile running on device - Expected: test Actual: default",
            ],
        },
    },
}
