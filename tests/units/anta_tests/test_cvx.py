# Copyright (c) 2023-2025 Arista Networks, Inc.
# Use of this source code is governed by the Apache License 2.0
# that can be found in the LICENSE file.
"""Data for testing anta.tests.cvx."""

from __future__ import annotations

from typing import Any

from anta.tests.cvx import VerifyActiveCVXConnections, VerifyCVXClusterStatus, VerifyManagementCVX, VerifyMcsClientMounts, VerifyMcsServerMounts
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
        "name": "failure - no enabled state",
        "test": VerifyManagementCVX,
        "eos_data": [{"clusterStatus": {}}],
        "inputs": {"enabled": False},
        "expected": {"result": "failure", "messages": ["Management CVX status is not valid: None"]},
    },
    {
        "name": "failure - no clusterStatus",
        "test": VerifyManagementCVX,
        "eos_data": [{}],
        "inputs": {"enabled": False},
        "expected": {"result": "failure", "messages": ["Management CVX status is not valid: None"]},
    },
    {
        "name": "success",
        "test": VerifyMcsServerMounts,
        "eos_data": [
            {
                "connections": [
                    {
                        "hostname": "media-leaf-1",
                        "mounts": [
                            {
                                "service": "Mcs",
                                "mountStates": [
                                    {
                                        "pathStates": [
                                            {"path": "mcs/v1/apiCfgRedStatus", "type": "Mcs::ApiConfigRedundancyStatus", "state": "mountStateMountComplete"},
                                            {"path": "mcs/v1/activeflows", "type": "Mcs::ActiveFlows", "state": "mountStateMountComplete"},
                                            {"path": "mcs/switch/status", "type": "Mcs::Client::Status", "state": "mountStateMountComplete"},
                                        ]
                                    }
                                ],
                            }
                        ],
                    }
                ]
            }
        ],
        "inputs": {"connections_count": 1},
        "expected": {"result": "success"},
    },
    {
        "name": "failure-no-mounts",
        "test": VerifyMcsServerMounts,
        "eos_data": [{"connections": [{"hostname": "media-leaf-1", "mounts": []}]}],
        "inputs": {"connections_count": 1},
        "expected": {
            "result": "failure",
            "messages": ["No mount status for media-leaf-1", "Incorrect CVX successful connections count. Expected: 1, Actual : 0"],
        },
    },
    {
        "name": "failure-unexpected-number-paths",
        "test": VerifyMcsServerMounts,
        "eos_data": [
            {
                "connections": [
                    {
                        "hostname": "media-leaf-1",
                        "mounts": [
                            {
                                "service": "Mcs",
                                "mountStates": [
                                    {
                                        "pathStates": [
                                            {"path": "mcs/v1/apiCfgRedStatus", "type": "Mcs::ApiStatus", "state": "mountStateMountComplete"},
                                            {"path": "mcs/v1/activeflows", "type": "Mcs::ActiveFlows", "state": "mountStateMountComplete"},
                                        ]
                                    }
                                ],
                            }
                        ],
                    }
                ]
            }
        ],
        "inputs": {"connections_count": 1},
        "expected": {
            "result": "failure",
            "messages": [
                "Incorrect number of mount path states for media-leaf-1 - Expected: 3, Actual: 2",
                "Unexpected MCS path type for media-leaf-1: 'Mcs::ApiStatus'.",
            ],
        },
    },
    {
        "name": "failure-unexpected-path-type",
        "test": VerifyMcsServerMounts,
        "eos_data": [
            {
                "connections": [
                    {
                        "hostname": "media-leaf-1",
                        "mounts": [
                            {
                                "service": "Mcs",
                                "mountStates": [
                                    {
                                        "pathStates": [
                                            {"path": "mcs/v1/apiCfgRedStatus", "type": "Mcs::ApiStatus", "state": "mountStateMountComplete"},
                                            {"path": "mcs/v1/activeflows", "type": "Mcs::ActiveFlows", "state": "mountStateMountComplete"},
                                            {"path": "mcs/switch/status", "type": "Mcs::Client::Status", "state": "mountStateMountComplete"},
                                        ]
                                    }
                                ],
                            }
                        ],
                    }
                ]
            }
        ],
        "inputs": {"connections_count": 1},
        "expected": {"result": "failure", "messages": ["Unexpected MCS path type for media-leaf-1: 'Mcs::ApiStatus'"]},
    },
    {
        "name": "failure-invalid-mount-state",
        "test": VerifyMcsServerMounts,
        "eos_data": [
            {
                "connections": [
                    {
                        "hostname": "media-leaf-1",
                        "mounts": [
                            {
                                "service": "Mcs",
                                "mountStates": [
                                    {
                                        "pathStates": [
                                            {"path": "mcs/v1/apiCfgRedStatus", "type": "Mcs::ApiConfigRedundancyStatus", "state": "mountStateMountFailed"},
                                            {"path": "mcs/v1/activeflows", "type": "Mcs::ActiveFlows", "state": "mountStateMountComplete"},
                                            {"path": "mcs/switch/status", "type": "Mcs::Client::Status", "state": "mountStateMountComplete"},
                                        ]
                                    }
                                ],
                            }
                        ],
                    }
                ]
            }
        ],
        "inputs": {"connections_count": 1},
        "expected": {
            "result": "failure",
            "messages": ["MCS server mount state for path 'Mcs::ApiConfigRedundancyStatus' is not valid is for media-leaf-1: 'mountStateMountFailed'"],
        },
    },
    {
        "name": "failure-no-mcs-mount",
        "test": VerifyMcsServerMounts,
        "eos_data": [
            {
                "connections": [
                    {
                        "hostname": "media-leaf-1",
                        "mounts": [
                            {
                                "service": "blah-blah",
                                "mountStates": [{"pathStates": [{"path": "blah-blah-path", "type": "blah-blah-type", "state": "blah-blah-state"}]}],
                            }
                        ],
                    }
                ]
            }
        ],
        "inputs": {"connections_count": 1},
        "expected": {"result": "failure", "messages": ["MCS mount state not detected", "Incorrect CVX successful connections count. Expected: 1, Actual : 0"]},
    },
    {
        "name": "failure-connections",
        "test": VerifyMcsServerMounts,
        "eos_data": [{}],
        "inputs": {"connections_count": 1},
        "expected": {"result": "failure", "messages": ["CVX connections are not available."]},
    },
    {
        "name": "success",
        "test": VerifyActiveCVXConnections,
        "eos_data": [
            {
                "connections": [
                    {
                        "switchId": "fc:bd:67:c3:16:55",
                        "hostname": "lyv563",
                        "oobConnectionActive": True,
                    },
                    {
                        "switchId": "00:1c:73:3c:e3:9e",
                        "hostname": "tg264",
                        "oobConnectionActive": True,
                    },
                ]
            }
        ],
        "inputs": {"connections_count": 2},
        "expected": {"result": "success"},
    },
    {
        "name": "failure",
        "test": VerifyActiveCVXConnections,
        "eos_data": [
            {
                "connections": [
                    {
                        "switchId": "fc:bd:67:c3:16:55",
                        "hostname": "lyv563",
                        "oobConnectionActive": False,
                    },
                    {
                        "switchId": "00:1c:73:3c:e3:9e",
                        "hostname": "tg264",
                        "oobConnectionActive": True,
                    },
                ]
            }
        ],
        "inputs": {"connections_count": 2},
        "expected": {"result": "failure", "messages": ["CVX active connections count. Expected: 2, Actual : 1"]},
    },
    {
        "name": "failure-no-connections",
        "test": VerifyActiveCVXConnections,
        "eos_data": [{}],
        "inputs": {"connections_count": 2},
        "expected": {"result": "failure", "messages": ["CVX connections are not available"]},
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
            "role": "Master",
            "peer_status": [
                {"peer_name": "cvx-red-2", "registrationState": "Registration complete"},
                {"peer_name": "cvx-red-3", "registrationState": "Registration complete"},
            ],
        },
        "expected": {"result": "failure", "messages": ["Unexpected number of peers 1 vs 2", "cvx-red-3 is not present"]},
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
            "role": "Master",
            "peer_status": [
                {"peer_name": "cvx-red-2", "registrationState": "Registration complete"},
                {"peer_name": "cvx-red-3", "registrationState": "Registration complete"},
            ],
        },
        "expected": {"result": "failure", "messages": ["Unexpected number of peers 0 vs 2", "cvx-red-2 is not present", "cvx-red-3 is not present"]},
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
            "role": "Master",
            "peer_status": [
                {"peer_name": "cvx-red-2", "registrationState": "Registration complete"},
                {"peer_name": "cvx-red-3", "registrationState": "Registration complete"},
            ],
        },
        "expected": {"result": "failure", "messages": ["cvx-red-2 registration state is not complete: Registration error"]},
    },
]
