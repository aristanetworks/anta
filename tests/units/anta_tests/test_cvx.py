# Copyright (c) 2023-2024 Arista Networks, Inc.
# Use of this source code is governed by the Apache License 2.0
# that can be found in the LICENSE file.
"""Data for testing anta.tests.cvx."""

from __future__ import annotations

from typing import Any

from anta.tests.cvx import VerifyManagementCVX, VerifyMcsClientMounts
from tests.units.anta_tests import test

DATA: list[dict[str, Any]] = [
    {
        "name": "success",
        "test": VerifyMcsClientMounts,
        "eos_data": [{"mountStates": [{"path": "mcs/v1/toSwitch/28-99-3a-8f-93-7b", "type": "Mcs::DeviceConfigV1", "state": "mountStateMountComplete"}]}],
        "inputs": None,
        "expected": {"result": "success"},
    },
    {
        "name": "success-haclient",
        "test": VerifyMcsClientMounts,
        "eos_data": [
            {
                "mountStates": [
                    {"path": "mcs/v1/apiCfgRedState", "type": "Mcs::ApiConfigRedundancyState", "state": "mountStateMountComplete"},
                    {"path": "mcs/v1/toSwitch/00-1c-73-74-c0-8b", "type": "Mcs::DeviceConfigV1", "state": "mountStateMountComplete"},
                ]
            },
        ],
        "inputs": None,
        "expected": {"result": "success"},
    },
    {
        "name": "success-partial-non-mcs",
        "test": VerifyMcsClientMounts,
        "eos_data": [
            {
                "mountStates": [
                    {"path": "blah/blah/blah", "type": "blah::blah", "state": "mountStatePreservedUnmounted"},
                    {"path": "mcs/v1/toSwitch/00-1c-73-74-c0-8b", "type": "Mcs::DeviceConfigV1", "state": "mountStateMountComplete"},
                ]
            },
        ],
        "inputs": None,
        "expected": {"result": "success"},
    },
    {
        "name": "failure-nomounts",
        "test": VerifyMcsClientMounts,
        "eos_data": [
            {"mountStates": []},
        ],
        "inputs": None,
        "expected": {"result": "failure", "messages": ["MCS Client mount states are not present"]},
    },
    {
        "name": "failure-mountStatePreservedUnmounted",
        "test": VerifyMcsClientMounts,
        "eos_data": [{"mountStates": [{"path": "mcs/v1/toSwitch/28-99-3a-8f-93-7b", "type": "Mcs::DeviceConfigV1", "state": "mountStatePreservedUnmounted"}]}],
        "inputs": None,
        "expected": {"result": "failure", "messages": ["MCS Client mount states are not valid: mountStatePreservedUnmounted"]},
    },
    {
        "name": "failure-partial-haclient",
        "test": VerifyMcsClientMounts,
        "eos_data": [
            {
                "mountStates": [
                    {"path": "mcs/v1/apiCfgRedState", "type": "Mcs::ApiConfigRedundancyState", "state": "mountStateMountComplete"},
                    {"path": "mcs/v1/toSwitch/00-1c-73-74-c0-8b", "type": "Mcs::DeviceConfigV1", "state": "mountStatePreservedUnmounted"},
                ]
            },
        ],
        "inputs": None,
        "expected": {"result": "failure", "messages": ["MCS Client mount states are not valid: mountStatePreservedUnmounted"]},
    },
    {
        "name": "failure-full-haclient",
        "test": VerifyMcsClientMounts,
        "eos_data": [
            {
                "mountStates": [
                    {"path": "blah/blah/blah", "type": "blah::blahState", "state": "mountStatePreservedUnmounted"},
                    {"path": "mcs/v1/toSwitch/00-1c-73-74-c0-8b", "type": "Mcs::DeviceConfigV1", "state": "mountStatePreservedUnmounted"},
                ]
            },
        ],
        "inputs": None,
        "expected": {"result": "failure", "messages": ["MCS Client mount states are not valid: mountStatePreservedUnmounted"]},
    },
    {
        "name": "failure-non-mcs-client",
        "test": VerifyMcsClientMounts,
        "eos_data": [
            {"mountStates": [{"path": "blah/blah/blah", "type": "blah::blahState", "state": "mountStatePreservedUnmounted"}]},
        ],
        "inputs": None,
        "expected": {"result": "failure", "messages": ["MCS Client mount states are not present"]},
    },
    {
        "name": "failure-partial-mcs-client",
        "test": VerifyMcsClientMounts,
        "eos_data": [
            {
                "mountStates": [
                    {"path": "blah/blah/blah", "type": "blah::blahState", "state": "mountStatePreservedUnmounted"},
                    {"path": "blah/blah/blah", "type": "Mcs::DeviceConfigV1", "state": "mountStatePreservedUnmounted"},
                ]
            },
        ],
        "inputs": None,
        "expected": {"result": "failure", "messages": ["MCS Client mount states are not valid: mountStatePreservedUnmounted"]},
    },
    {
        "name": "success-enabled",
        "test": VerifyManagementCVX,
        "eos_data": [
            {
                "clusterStatus": {
                    "enabled": True,
                }
            }
        ],
        "inputs": {"enabled": True},
        "expected": {"result": "success"},
    },
    {
        "name": "success-disabled",
        "test": VerifyManagementCVX,
        "eos_data": [
            {
                "clusterStatus": {
                    "enabled": False,
                }
            }
        ],
        "inputs": {"enabled": False},
        "expected": {"result": "success"},
    },
    {
        "name": "failure",
        "test": VerifyManagementCVX,
        "eos_data": [{"clusterStatus": {}}],
        "inputs": {"enabled": False},
        "expected": {"result": "failure", "messages": ["Management CVX status is not valid: None"]},
    },
]
