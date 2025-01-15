# Copyright (c) 2023-2025 Arista Networks, Inc.
# Use of this source code is governed by the Apache License 2.0
# that can be found in the LICENSE file.
"""Tests for anta.tests.vlan.py."""

from __future__ import annotations

from typing import TYPE_CHECKING

from anta.tests.vlan import VerifyDynamicVlanSource, VerifyVlanInternalPolicy
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
    {
        "name": "success",
        "test": VerifyDynamicVlanSource,
        "eos_data": [{"dynamicVlans": {"evpn": {"vlanIds": [1199]}, "mlagsync": {"vlanIds": [1401]}, "vccbfd": {"vlanIds": [1501]}}}],
        "inputs": {"sources": ["evpn", "mlagsync"], "strict": False},
        "expected": {"result": "success"},
    },
    {
        "name": "failure-no-dynamic-vlan-sources",
        "test": VerifyDynamicVlanSource,
        "eos_data": [{"dynamicVlans": {}}],
        "inputs": {"sources": ["evpn", "mlagsync"], "strict": False},
        "expected": {"result": "failure", "messages": ["Dynamic VLAN source(s) not found in configuration: evpn, mlagsync"]},
    },
    {
        "name": "failure-dynamic-vlan-sources-mismatch",
        "test": VerifyDynamicVlanSource,
        "eos_data": [{"dynamicVlans": {"vccbfd": {"vlanIds": [1500]}, "mlagsync": {"vlanIds": [1501]}}}],
        "inputs": {"sources": ["evpn", "mlagsync"], "strict": False},
        "expected": {
            "result": "failure",
            "messages": ["Dynamic VLAN source(s) not found in configuration: evpn"],
        },
    },
    {
        "name": "success-strict-mode",
        "test": VerifyDynamicVlanSource,
        "eos_data": [{"dynamicVlans": {"evpn": {"vlanIds": [1199]}, "mlagsync": {"vlanIds": [1502], "vccbfd": {"vlanIds": []}}}}],
        "inputs": {"sources": ["evpn", "mlagsync"], "strict": True},
        "expected": {"result": "success"},
    },
    {
        "name": "failure-all-sources-exact-match-additional-source-found",
        "test": VerifyDynamicVlanSource,
        "eos_data": [{"dynamicVlans": {"evpn": {"vlanIds": [1199]}, "mlagsync": {"vlanIds": [1500]}, "vccbfd": {"vlanIds": [1500]}}}],
        "inputs": {"sources": ["evpn", "mlagsync"], "strict": True},
        "expected": {
            "result": "failure",
            "messages": ["Strict mode enabled: Unexpected sources have VLANs allocated: vccbfd"],
        },
    },
    {
        "name": "failure-all-sources-exact-match-expected-source-not-found",
        "test": VerifyDynamicVlanSource,
        "eos_data": [{"dynamicVlans": {"evpn": {"vlanIds": [1199]}, "mlagsync": {"vlanIds": []}}}],
        "inputs": {"sources": ["evpn", "mlagsync"], "strict": True},
        "expected": {"result": "failure", "messages": ["Dynamic VLAN source(s) exist but have no VLANs allocated: mlagsync"]},
    },
]
