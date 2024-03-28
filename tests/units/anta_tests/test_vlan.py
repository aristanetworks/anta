# Copyright (c) 2023-2024 Arista Networks, Inc.
# Use of this source code is governed by the Apache License 2.0
# that can be found in the LICENSE file.
"""Tests for anta.tests.vlan.py."""

from __future__ import annotations

from typing import Any

from anta.tests.vlan import VerifyVlanInternalPolicy
from tests.lib.anta import test  # noqa: F401; pylint: disable=W0611

DATA: list[dict[str, Any]] = [
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
