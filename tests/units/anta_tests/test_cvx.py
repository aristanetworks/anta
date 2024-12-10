# Copyright (c) 2023-2024 Arista Networks, Inc.
# Use of this source code is governed by the Apache License 2.0
# that can be found in the LICENSE file.
"""Data for testing anta.tests.cvx."""

from __future__ import annotations

from typing import Any

from anta.tests.cvx import VerifyManagementCVX, VerifyMcsClientMounts, VerifyMcsServerMounts
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
        "inputs": {"expected_connection_count": 1},
        "expected": {"result": "success"},
    },
    {
        "name": "failure-no-mounts",
        "test": VerifyMcsServerMounts,
        "eos_data": [{"connections": [{"hostname": "media-leaf-1", "mounts": []}]}],
        "inputs": {"expected_connection_count": 1},
        "expected": {"result": "failure", "messages": ["No mount status for media-leaf-1", "Only 0 successful connections"]},
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
        "inputs": {"expected_connection_count": 1},
        "expected": {"result": "failure", "messages": ["Unexpected number of mount path states: 2"]},
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
        "inputs": {"expected_connection_count": 1},
        "expected": {"result": "failure", "messages": ["Unexpected MCS path type: Mcs::ApiStatus"]},
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
        "inputs": {"expected_connection_count": 1},
        "expected": {"result": "failure", "messages": ["MCS server mount state is not valid: mountStateMountFailed"]},
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
        "inputs": {"expected_connection_count": 1},
        "expected": {"result": "failure", "messages": ["MCS mount state not detected", "Only 0 successful connections"]},
    },
]
