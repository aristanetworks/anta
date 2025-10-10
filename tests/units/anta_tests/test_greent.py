# Copyright (c) 2023-2025 Arista Networks, Inc.
# Use of this source code is governed by the Apache License 2.0
# that can be found in the LICENSE file.
"""Data for testing anta.tests.configuration."""

from __future__ import annotations

import sys
from typing import TYPE_CHECKING, Any

from anta.models import AntaTest
from anta.result_manager.models import AntaTestStatus
from anta.tests.greent import VerifyGreenT, VerifyGreenTCounters
from tests.units.anta_tests import test

if TYPE_CHECKING:
    from tests.units.anta_tests import AntaUnitTestData

DATA: AntaUnitTestData = {
    (VerifyGreenTCounters, "success"): {
        "eos_data": [{"sampleRcvd": 0, "sampleDiscarded": 0, "multiDstSampleRcvd": 0, "grePktSent": 1, "sampleSent": 0}],
        "expected": {"result": AntaTestStatus.SUCCESS},
    },
    (VerifyGreenTCounters, "failure"): {
        "eos_data": [{"sampleRcvd": 0, "sampleDiscarded": 0, "multiDstSampleRcvd": 0, "grePktSent": 0, "sampleSent": 0}],
        "expected": {"result": AntaTestStatus.FAILURE, "messages": ["GreenT counters are not incremented"]},
    },
    (VerifyGreenT, "success"): {
        "eos_data": [
            {
                "profiles": {
                    "default": {"interfaces": [], "appliedInterfaces": [], "samplePolicy": "default", "failures": {}, "appliedInterfaces6": [], "failures6": {}},
                    "testProfile": {"interfaces": [], "appliedInterfaces": [], "samplePolicy": "default", "failures": {}, "appliedInterfaces6": [], "failures6": {}},
                }
            }
        ],
        "expected": {"result": AntaTestStatus.SUCCESS},
    },
    (VerifyGreenT, "failure"): {
        "eos_data": [
            {
                "profiles": {
                    "default": {"interfaces": [], "appliedInterfaces": [], "samplePolicy": "default", "failures": {}, "appliedInterfaces6": [], "failures6": {}}
                }
            }
        ],
        "expected": {"result": AntaTestStatus.FAILURE, "messages": ["No GreenT policy is created"]},
    },
}
