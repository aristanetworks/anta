# Copyright (c) 2023-2026 Arista Networks, Inc.
# Use of this source code is governed by the Apache License 2.0
# that can be found in the LICENSE file.
"""Tests for anta.tests.vlan.py."""

from __future__ import annotations

import sys
from typing import TYPE_CHECKING, Any

from anta.models import AntaTest
from anta.result_manager.models import AntaTestStatus
from anta.tests.vlan import VerifyDynamicVlanSource, VerifyVlanInternalPolicy, VerifyVlanStatus
from tests.units.anta_tests import test

if TYPE_CHECKING:
    from tests.units.anta_tests import AntaUnitTestData

DATA: AntaUnitTestData = {
    (VerifyVlanInternalPolicy, "success"): {
        "eos_data": [{"policy": "ascending", "startVlanId": 1006, "endVlanId": 4094}],
        "inputs": {"policy": "ascending", "start_vlan_id": 1006, "end_vlan_id": 4094},
        "expected": {"result": AntaTestStatus.SUCCESS},
    },
    (VerifyVlanInternalPolicy, "failure-incorrect-policy"): {
        "eos_data": [{"policy": "descending", "startVlanId": 4094, "endVlanId": 1006}],
        "inputs": {"policy": "ascending", "start_vlan_id": 1006, "end_vlan_id": 4094},
        "expected": {
            "result": AntaTestStatus.FAILURE,
            "messages": ["Incorrect VLAN internal allocation policy configured - Expected: ascending Actual: descending"],
        },
    },
    (VerifyVlanInternalPolicy, "failure-incorrect-start-end-id"): {
        "eos_data": [{"policy": "ascending", "startVlanId": 4094, "endVlanId": 1006}],
        "inputs": {"policy": "ascending", "start_vlan_id": 1006, "end_vlan_id": 4094},
        "expected": {
            "result": AntaTestStatus.FAILURE,
            "messages": [
                "VLAN internal allocation policy: ascending - Incorrect start VLAN id configured - Expected: 1006 Actual: 4094",
                "VLAN internal allocation policy: ascending - Incorrect end VLAN id configured - Expected: 4094 Actual: 1006",
            ],
        },
    },
    (VerifyDynamicVlanSource, "success"): {
        "eos_data": [{"dynamicVlans": {"evpn": {"vlanIds": [1199]}, "mlagsync": {"vlanIds": [1401]}, "vccbfd": {"vlanIds": [1501]}}}],
        "inputs": {"sources": ["evpn", "mlagsync"], "strict": False},
        "expected": {"result": AntaTestStatus.SUCCESS},
    },
    (VerifyDynamicVlanSource, "failure-no-dynamic-vlan-sources"): {
        "eos_data": [{"dynamicVlans": {}}],
        "inputs": {"sources": ["evpn", "mlagsync"], "strict": False},
        "expected": {"result": AntaTestStatus.FAILURE, "messages": ["Dynamic VLAN source(s) not found in configuration: evpn, mlagsync"]},
    },
    (VerifyDynamicVlanSource, "failure-dynamic-vlan-sources-mismatch"): {
        "eos_data": [{"dynamicVlans": {"vccbfd": {"vlanIds": [1500]}, "mlagsync": {"vlanIds": [1501]}}}],
        "inputs": {"sources": ["evpn", "mlagsync"], "strict": False},
        "expected": {"result": AntaTestStatus.FAILURE, "messages": ["Dynamic VLAN source(s) not found in configuration: evpn"]},
    },
    (VerifyDynamicVlanSource, "success-strict-mode"): {
        "eos_data": [{"dynamicVlans": {"evpn": {"vlanIds": [1199]}, "mlagsync": {"vlanIds": [1502], "vccbfd": {"vlanIds": []}}}}],
        "inputs": {"sources": ["evpn", "mlagsync"], "strict": True},
        "expected": {"result": AntaTestStatus.SUCCESS},
    },
    (VerifyDynamicVlanSource, "failure-all-sources-exact-match-additional-source-found"): {
        "eos_data": [{"dynamicVlans": {"evpn": {"vlanIds": [1199]}, "mlagsync": {"vlanIds": [1500]}, "vccbfd": {"vlanIds": [1500]}}}],
        "inputs": {"sources": ["evpn", "mlagsync"], "strict": True},
        "expected": {"result": AntaTestStatus.FAILURE, "messages": ["Strict mode enabled: Unexpected sources have VLANs allocated: vccbfd"]},
    },
    (VerifyDynamicVlanSource, "failure-all-sources-exact-match-expected-source-not-found"): {
        "eos_data": [{"dynamicVlans": {"evpn": {"vlanIds": [1199]}, "mlagsync": {"vlanIds": []}}}],
        "inputs": {"sources": ["evpn", "mlagsync"], "strict": True},
        "expected": {"result": AntaTestStatus.FAILURE, "messages": ["Dynamic VLAN source(s) exist but have no VLANs allocated: mlagsync"]},
    },
    (VerifyVlanStatus, "success"): {
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
        "expected": {"result": AntaTestStatus.SUCCESS},
    },
    (VerifyVlanStatus, "failure-vlan-not-conifgured"): {
        "eos_data": [{"vlans": {"1": {"name": "default", "dynamic": False, "status": "active", "interfaces": {}}}, "sourceDetail": ""}],
        "inputs": {"vlans": [{"vlan_id": 4092, "status": "active"}, {"vlan_id": 4094, "status": "active"}]},
        "expected": {"result": AntaTestStatus.FAILURE, "messages": ["VLAN: Vlan4092 - Not configured", "VLAN: Vlan4094 - Not configured"]},
    },
    (VerifyVlanStatus, "failure-incorrect-status"): {
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
            "result": AntaTestStatus.FAILURE,
            "messages": [
                "VLAN: Vlan4092 - Incorrect administrative status - Expected: active Actual: suspended",
                "VLAN: Vlan4094 - Incorrect administrative status - Expected: suspended Actual: active",
            ],
        },
    },
}
