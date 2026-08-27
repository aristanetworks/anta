# Copyright (c) 2026 Arista Networks, Inc.
# Use of this source code is governed by the Apache License 2.0
# that can be found in the LICENSE file.
"""Test inputs for anta.tests.advisories.sa_117."""

from __future__ import annotations

import sys
from typing import TYPE_CHECKING, Any

from anta.models import AntaTest
from anta.result_manager.models import AntaTestStatus
from anta.tests.advisories.sa_117 import VerifySA117, _evaluate_risky_trace_configuration
from tests.units.anta_tests import test

if TYPE_CHECKING:
    from tests.units.anta_tests import AntaUnitTestData

DATA: AntaUnitTestData = {
    (VerifySA117, "failure-accounting-enabled"): {
        "eos_data": [
            {"transports": {"default": {"enabled": True, "accounting": True}}},
            {"cmds": {}},
            {"version": "4.32.4M"},
        ],
        "expected": {
            "result": AntaTestStatus.FAILURE,
            "messages": ["OpenConfig gNMI has accounting requests enabled."],
        },
    },
    (VerifySA117, "failure-risky-trace-configured"): {
        "eos_data": [
            {"transports": {"default": {"enabled": True, "accounting": False}}},
            {"cmds": {"trace OpenConfig setting service/9": None}},
            {"version": "4.32.4M"},
        ],
        "expected": {
            "result": AntaTestStatus.FAILURE,
            "messages": ["OpenConfig tracing includes one of the risky selectors from the advisory."],
        },
    },
    (VerifySA117, "success-risky-trace-with-transport-disabled"): {
        "eos_data": [
            {"transports": {}},
            {"cmds": {"trace OpenConfig setting service/9": None}},
            {"version": "4.32.4M"},
        ],
        "expected": {
            "result": AntaTestStatus.SUCCESS,
            "messages": ["The device configuration is not affected by this advisory."],
        },
    },
    (VerifySA117, "success-not-exposed"): {
        "eos_data": [
            {"transports": {"default": {"enabled": False, "accounting": True}}},
            {"cmds": {}},
            {"version": "4.32.4M"},
        ],
        "expected": {
            "result": AntaTestStatus.SUCCESS,
            "messages": ["The device configuration is not affected by this advisory."],
        },
    },
    (VerifySA117, "success-accounting-and-tracing-disabled"): {
        "eos_data": [
            {"transports": {"default": {"enabled": True, "accounting": False}}},
            {"cmds": {"hostname switch": None, "trace OpenConfig setting harmless/1": None}},
            {"version": "4.32.4M"},
        ],
        "expected": {
            "result": AntaTestStatus.SUCCESS,
            "messages": ["The device configuration is not affected by this advisory."],
        },
    },
    (VerifySA117, "success-fixed-version"): {
        "eos_data": [{}, {}, {"version": "4.32.5M"}],
        "expected": {
            "result": AntaTestStatus.SUCCESS,
            "messages": ["The EOS version '4.32.5M' is not affected by this advisory."],
        },
    },
    (VerifySA117, "success-excluded-version-suffix"): {
        "eos_data": [{}, {}, {"version": "4.33.1FX-wbb"}],
        "expected": {
            "result": AntaTestStatus.SUCCESS,
            "messages": ["The EOS version '4.33.1FX-wbb' is not affected by this advisory."],
        },
    },
}


def test_evaluate_risky_trace_configuration_rejects_non_string_command() -> None:
    """Verify malformed command keys return an unknown evaluation."""
    assert _evaluate_risky_trace_configuration({"cmds": {1: None}}) is None
