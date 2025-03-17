# Copyright (c) 2023-2025 Arista Networks, Inc.
# Use of this source code is governed by the Apache License 2.0
# that can be found in the LICENSE file.
"""Tests for anta.tests.vlan.py."""

from __future__ import annotations

from typing import Any

from anta.tests.vlan import VerifyDynamicVlanSource, VerifyVlanInternalPolicy, VerifyVlanStatus
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
            "messages": ["Incorrect VLAN internal allocation policy configured - Expected: ascending Actual: descending"],
        },
    },
    {
        "name": "failure-incorrect-start-end-id",
        "test": VerifyVlanInternalPolicy,
        "eos_data": [{"policy": "ascending", "startVlanId": 4094, "endVlanId": 1006}],
        "inputs": {"policy": "ascending", "start_vlan_id": 1006, "end_vlan_id": 4094},
        "expected": {
            "result": "failure",
            "messages": [
                "VLAN internal allocation policy: ascending - Incorrect start VLAN id configured - Expected: 1006 Actual: 4094",
                "VLAN internal allocation policy: ascending - Incorrect end VLAN id configured - Expected: 4094 Actual: 1006",
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
    {
        "name": "success",
        "test": VerifyVlanStatus,
        "eos_data": [
            {
                "vlans": {
                    "1": {"name": "default", "dynamic": False, "status": "active", "interfaces": {}},
                    "4092": {"name": "VLAN4092", "dynamic": True, "status": "active", "interfaces": {}},
                    "4094": {"name": "VLAN4094", "dynamic": True, "status": "active", "interfaces": {}},
                },
                "sourceDetail": "",
            }
        ],
        "inputs": {"vlans": [{"vlan_id": 4092, "status": "active"}, {"vlan_id": 4094, "status": "active"}]},
        "expected": {"result": "success"},
    },
    {
        "name": "failure-not-conifgure",
        "test": VerifyVlanStatus,
        "eos_data": [
            {
                "vlans": {
                    "1": {"name": "default", "dynamic": False, "status": "active", "interfaces": {}},
                },
                "sourceDetail": "",
            }
        ],
        "inputs": {"vlans": [{"vlan_id": 4092, "status": "active"}, {"vlan_id": 4094, "status": "active"}]},
        "expected": {
            "result": "failure",
            "messages": [
                "VLAN: Vlan4092 - Not configured",
                "VLAN: Vlan4094 - Not configured",
            ],
        },
    },
    {
        "name": "failure-incorrect-status",
        "test": VerifyVlanStatus,
        "eos_data": [
            {
                "vlans": {
                    "1": {"name": "default", "dynamic": False, "status": "active", "interfaces": {}},
                    "4092": {"name": "VLAN4092", "dynamic": True, "status": "suspended", "interfaces": {}},
                    "4094": {"name": "VLAN4094", "dynamic": True, "status": "active", "interfaces": {}},
                },
                "sourceDetail": "",
            }
        ],
        "inputs": {"vlans": [{"vlan_id": 4092, "status": "active"}, {"vlan_id": 4094, "status": "suspended"}]},
        "expected": {
            "result": "failure",
            "messages": [
                "VLAN: Vlan4092 - Incorrect administrative status - Expected: active Actual: suspended",
                "VLAN: Vlan4094 - Incorrect administrative status - Expected: suspended Actual: active",
            ],
        },
    },
]
