# Copyright (c) 2023-2025 Arista Networks, Inc.
# Use of this source code is governed by the Apache License 2.0
# that can be found in the LICENSE file.
"""Data for testing anta.tests.configuration."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from anta.tests.greent import VerifyGreenT, VerifyGreenTCounters
from tests.units.anta_tests import test

if TYPE_CHECKING:
    from anta.models import AntaTest
    from tests.units.anta_tests import AntaUnitTest

DATA: dict[tuple[type[AntaTest], str], AntaUnitTest] = {
    (VerifyGreenTCounters, "success"): {
        "eos_data": [{"sampleRcvd": 0, "sampleDiscarded": 0, "multiDstSampleRcvd": 0, "grePktSent": 1, "sampleSent": 0}],
        "inputs": None,
        "expected": {"result": "success"},
    },
    (VerifyGreenTCounters, "failure"): {
        "eos_data": [{"sampleRcvd": 0, "sampleDiscarded": 0, "multiDstSampleRcvd": 0, "grePktSent": 0, "sampleSent": 0}],
        "inputs": None,
        "expected": {"result": "failure", "messages": ["GreenT counters are not incremented"]},
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
        "inputs": None,
        "expected": {"result": "success"},
    },
    (VerifyGreenT, "failure"): {
        "eos_data": [
            {
                "profiles": {
                    "default": {"interfaces": [], "appliedInterfaces": [], "samplePolicy": "default", "failures": {}, "appliedInterfaces6": [], "failures6": {}}
                }
            }
        ],
        "inputs": None,
        "expected": {"result": "failure", "messages": ["No GreenT policy is created"]},
    },
}
