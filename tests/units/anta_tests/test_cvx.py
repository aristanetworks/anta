# Copyright (c) 2023-2024 Arista Networks, Inc.
# Use of this source code is governed by the Apache License 2.0
# that can be found in the LICENSE file.
"""Data for testing anta.tests.cvx."""

from __future__ import annotations

from typing import Any

from anta.tests.cvx import VerifyCVXClusterStatus, VerifyManagementCVX, VerifyMcsClientMounts
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
    {
        "name": "success-all",
        "test": VerifyCVXClusterStatus,
        "eos_data": [
            {
                "enabled": True,
                "clusterMode": True,
                "clusterStatus": {
                    "role": "Master",
                    "peerStatus": {
                        "cvx-red-2": {"peerName": "cvx-red-2", "registrationState": "Registration complete"},
                        "cvx-red-3": {"peerName": "cvx-red-3", "registrationState": "Registration complete"},
                    },
                },
            }
        ],
        "inputs": {
            "enabled": True,
            "cluster_mode": True,
            "role": "Master",
            "peer_status": [
                {"peer_name": "cvx-red-2", "registrationState": "Registration complete"},
                {"peer_name": "cvx-red-3", "registrationState": "Registration complete"},
            ],
        },
        "expected": {"result": "success"},
    },
    {
        "name": "failure-invalid-role",
        "test": VerifyCVXClusterStatus,
        "eos_data": [
            {
                "enabled": True,
                "clusterMode": True,
                "clusterStatus": {
                    "role": "Standby",
                    "peerStatus": {
                        "cvx-red-2": {"peerName": "cvx-red-2", "registrationState": "Registration complete"},
                        "cvx-red-3": {"peerName": "cvx-red-3", "registrationState": "Registration complete"},
                    },
                },
            }
        ],
        "inputs": {
            "enabled": True,
            "cluster_mode": True,
            "role": "Master",
            "peer_status": [
                {"peer_name": "cvx-red-2", "registrationState": "Registration complete"},
                {"peer_name": "cvx-red-3", "registrationState": "Registration complete"},
            ],
        },
        "expected": {"result": "failure", "messages": ["CVX Role is not valid: Standby"]},
    },
    {
        "name": "failure-cvx-enabled",
        "test": VerifyCVXClusterStatus,
        "eos_data": [
            {
                "enabled": False,
                "clusterMode": True,
                "clusterStatus": {
                    "role": "Master",
                    "peerStatus": {},
                },
            }
        ],
        "inputs": {
            "enabled": True,
            "cluster_mode": True,
            "role": "Master",
            "peer_status": [],
        },
        "expected": {"result": "failure", "messages": ["CVX Server status is not enabled"]},
    },
    {
        "name": "failure-cluster-enabled",
        "test": VerifyCVXClusterStatus,
        "eos_data": [
            {
                "enabled": True,
                "clusterMode": False,
                "clusterStatus": {},
            }
        ],
        "inputs": {
            "enabled": True,
            "cluster_mode": True,
            "role": "Master",
            "peer_status": [],
        },
        "expected": {"result": "failure", "messages": ["CVX Server is not a cluster"]},
    },
    {
        "name": "failure-missing-peers",
        "test": VerifyCVXClusterStatus,
        "eos_data": [
            {
                "enabled": True,
                "clusterMode": True,
                "clusterStatus": {
                    "role": "Master",
                    "peerStatus": {
                        "cvx-red-2": {"peerName": "cvx-red-2", "registrationState": "Registration complete"},
                    },
                },
            }
        ],
        "inputs": {
            "enabled": True,
            "cluster_mode": True,
            "role": "Master",
            "peer_status": [
                {"peer_name": "cvx-red-2", "registrationState": "Registration complete"},
                {"peer_name": "cvx-red-3", "registrationState": "Registration complete"},
            ],
        },
        "expected": {"result": "failure", "messages": ["Unexpected number of peers", "cvx-red-3 is not present"]},
    },
    {
        "name": "failure-invalid-peers",
        "test": VerifyCVXClusterStatus,
        "eos_data": [
            {
                "enabled": True,
                "clusterMode": True,
                "clusterStatus": {
                    "role": "Master",
                    "peerStatus": {},
                },
            }
        ],
        "inputs": {
            "enabled": True,
            "cluster_mode": True,
            "role": "Master",
            "peer_status": [
                {"peer_name": "cvx-red-2", "registrationState": "Registration complete"},
                {"peer_name": "cvx-red-3", "registrationState": "Registration complete"},
            ],
        },
        "expected": {"result": "failure", "messages": ["Peer status data is invalid"]},
    },
    {
        "name": "failure-registration-error",
        "test": VerifyCVXClusterStatus,
        "eos_data": [
            {
                "enabled": True,
                "clusterMode": True,
                "clusterStatus": {
                    "role": "Master",
                    "peerStatus": {
                        "cvx-red-2": {"peerName": "cvx-red-2", "registrationState": "Registration error"},
                        "cvx-red-3": {"peerName": "cvx-red-3", "registrationState": "Registration complete"},
                    },
                },
            }
        ],
        "inputs": {
            "enabled": True,
            "cluster_mode": True,
            "role": "Master",
            "peer_status": [
                {"peer_name": "cvx-red-2", "registrationState": "Registration complete"},
                {"peer_name": "cvx-red-3", "registrationState": "Registration complete"},
            ],
        },
        "expected": {"result": "failure", "messages": ["cvx-red-2 registration state is not complete: Registration error"]},
    },
]
