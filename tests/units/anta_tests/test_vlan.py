# Copyright (c) 2023-2025 Arista Networks, Inc.
# Use of this source code is governed by the Apache License 2.0
# that can be found in the LICENSE file.
"""Tests for anta.tests.vlan.py."""

from __future__ import annotations

from typing import Any

from anta.tests.vlan import VerifyDynamicVlanSource, VerifyVlanInternalPolicy
from tests.units.anta_tests import test

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
    {
        "name": "success-any-source-match",
        "test": VerifyDynamicVlanSource,
        "eos_data": [{"dynamicVlans": {"evpn": {"vlanIds": [1199]}, "mlagsync": {"vlanIds": []}}}],
        "inputs": {"source": ["evpn", "mlagsync"], "strict": False},
        "expected": {"result": "success"},
    },
    {
        "name": "success-all-source-match",
        "test": VerifyDynamicVlanSource,
        "eos_data": [{"dynamicVlans": {"evpn": {"vlanIds": [1199]}, "mlagsync": {"vlanIds": [1500]}}}],
        "inputs": {"source": ["evpn", "mlagsync"], "strict": False},
        "expected": {"result": "success"},
    },
    {
        "name": "failure-no-dynamic-vlans",
        "test": VerifyDynamicVlanSource,
        "eos_data": [{"dynamicVlans": {}}],
        "inputs": {"source": ["evpn", "mlagsync"], "strict": False},
        "expected": {"result": "skipped", "messages": ["Dynamic VLANs are not configured"]},
    },
    {
        "name": "failure-dynamic-vlan-source-invalid",
        "test": VerifyDynamicVlanSource,
        "eos_data": [{"dynamicVlans": {"vccbfd": {"vlanIds": [1500]}, "mlagsync": {"vlanIds": [1501]}}}],
        "inputs": {"source": ["evpn", "mlagsync"], "strict": False},
        "expected": {"result": "failure", "messages": ["Dynamic VLAN(s) source mismatch - vccbfd, mlagsync are not in the expected sources: evpn, mlagsync."]},
    },
    {
        "name": "failure-any-source-match-additional-source-found",
        "test": VerifyDynamicVlanSource,
        "eos_data": [{"dynamicVlans": {"evpn": {"vlanIds": [1199]}, "mlagsync": {"vlanIds": [1501]}, "vccbfd": {"vlanIds": [1500]}}}],
        "inputs": {"source": ["evpn", "mlagsync"], "strict": False},
        "expected": {"result": "failure", "messages": ["Dynamic VLAN(s) source mismatch - evpn, mlagsync, vccbfd are not in the expected sources: evpn, mlagsync."]},
    },
    {
        "name": "success-all-source-exact-match",
        "test": VerifyDynamicVlanSource,
        "eos_data": [{"dynamicVlans": {"evpn": {"vlanIds": [1199]}, "mlagsync": {"vlanIds": [1502]}}}],
        "inputs": {"source": ["evpn", "mlagsync"], "strict": True},
        "expected": {"result": "success"},
    },
    {
        "name": "failure-all-source-exact-match-additional-source-found",
        "test": VerifyDynamicVlanSource,
        "eos_data": [{"dynamicVlans": {"evpn": {"vlanIds": [1199]}, "mlagsync": {"vlanIds": [1500]}, "vccbfd": {"vlanIds": [1500]}}}],
        "inputs": {"source": ["evpn", "mlagsync"], "strict": True},
        "expected": {"result": "failure", "messages": ["Dynamic VLAN(s) source mismatch - Expected: evpn, mlagsync Actual: evpn, mlagsync, vccbfd"]},
    },
    {
        "name": "failure-all-source-exact-match-expected-source-not-found",
        "test": VerifyDynamicVlanSource,
        "eos_data": [{"dynamicVlans": {"evpn": {"vlanIds": [1199]}, "mlagsync": {"vlanIds": []}}}],
        "inputs": {"source": ["evpn", "mlagsync"], "strict": True},
        "expected": {"result": "failure", "messages": ["Dynamic VLAN(s) source mismatch - Expected: evpn, mlagsync Actual: evpn"]},
    },
]
