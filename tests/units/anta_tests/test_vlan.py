# Copyright (c) 2023-2025 Arista Networks, Inc.
# Use of this source code is governed by the Apache License 2.0
# that can be found in the LICENSE file.
"""Tests for anta.tests.vlan.py."""

from __future__ import annotations

from typing import TYPE_CHECKING

from anta.tests.vlan import VerifyVlanInternalPolicy
from tests.units.anta_tests import test

if TYPE_CHECKING:
    from tests.units.anta_tests import AntaUnitTest

DATA: list[AntaUnitTest] = [
    {
        "name": "success",
        "test": VerifyVlanInternalPolicy,
        "eos_data": [{"policy": "ascending", "startVlanId": 1006, "endVlanId": 4094}],
        "inputs": {"policy": "ascending", "start_vlan_id": 1006, "end_vlan_id": 4094},
        "expected": {"result": "success"},
    },
    {
        "name": "failure-incorrect-policy",
        "test": VerifyVlanInternalPolicy,
        "eos_data": [{"policy": "descending", "startVlanId": 4094, "endVlanId": 1006}],
        "inputs": {"policy": "ascending", "start_vlan_id": 1006, "end_vlan_id": 4094},
        "expected": {
            "result": "failure",
            "messages": [
                "The VLAN internal allocation policy is not configured properly:\n"
                "Expected `ascending` as the policy, but found `descending` instead.\n"
                "Expected `1006` as the startVlanId, but found `4094` instead.\n"
                "Expected `4094` as the endVlanId, but found `1006` instead."
            ],
        },
    },
]
