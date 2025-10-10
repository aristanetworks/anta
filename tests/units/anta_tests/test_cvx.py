# Copyright (c) 2023-2025 Arista Networks, Inc.
# Use of this source code is governed by the Apache License 2.0
# that can be found in the LICENSE file.
"""Data for testing anta.tests.cvx."""

from __future__ import annotations

import sys
from typing import TYPE_CHECKING, Any

from anta.models import AntaTest
from anta.result_manager.models import AntaTestStatus
from anta.tests.cvx import VerifyActiveCVXConnections, VerifyCVXClusterStatus, VerifyManagementCVX, VerifyMcsClientMounts, VerifyMcsServerMounts
from tests.units.anta_tests import test

if TYPE_CHECKING:
    from tests.units.anta_tests import AntaUnitTestData

DATA: AntaUnitTestData = {
    (VerifyMcsClientMounts, "success"): {
        "eos_data": [{"mountStates": [{"path": "mcs/v1/toSwitch/28-99-3a-8f-93-7b", "type": "Mcs::DeviceConfigV1", "state": "mountStateMountComplete"}]}],
        "expected": {"result": AntaTestStatus.SUCCESS},
    },
    (VerifyMcsClientMounts, "success-haclient"): {
        "eos_data": [
            {
                "mountStates": [
                    {"path": "mcs/v1/apiCfgRedState", "type": "Mcs::ApiConfigRedundancyState", "state": "mountStateMountComplete"},
                    {"path": "mcs/v1/toSwitch/00-1c-73-74-c0-8b", "type": "Mcs::DeviceConfigV1", "state": "mountStateMountComplete"},
                ]
            }
        ],
        "expected": {"result": AntaTestStatus.SUCCESS},
    },
    (VerifyMcsClientMounts, "success-partial-non-mcs"): {
        "eos_data": [
            {
                "mountStates": [
                    {"path": "blah/blah/blah", "type": "blah::blah", "state": "mountStatePreservedUnmounted"},
                    {"path": "mcs/v1/toSwitch/00-1c-73-74-c0-8b", "type": "Mcs::DeviceConfigV1", "state": "mountStateMountComplete"},
                ]
            }
        ],
        "expected": {"result": AntaTestStatus.SUCCESS},
    },
    (VerifyMcsClientMounts, "failure-nomounts"): {
        "eos_data": [{"mountStates": []}],
        "expected": {"result": AntaTestStatus.FAILURE, "messages": ["MCS Client mount states are not present"]},
    },
    (VerifyMcsClientMounts, "failure-mountStatePreservedUnmounted"): {
        "eos_data": [{"mountStates": [{"path": "mcs/v1/toSwitch/28-99-3a-8f-93-7b", "type": "Mcs::DeviceConfigV1", "state": "mountStatePreservedUnmounted"}]}],
        "expected": {
            "result": AntaTestStatus.FAILURE,
            "messages": ["MCS Client mount states are not valid - Expected: mountStateMountComplete Actual: mountStatePreservedUnmounted"],
        },
    },
    (VerifyMcsClientMounts, "failure-partial-haclient"): {
        "eos_data": [
            {
                "mountStates": [
                    {"path": "mcs/v1/apiCfgRedState", "type": "Mcs::ApiConfigRedundancyState", "state": "mountStateMountComplete"},
                    {"path": "mcs/v1/toSwitch/00-1c-73-74-c0-8b", "type": "Mcs::DeviceConfigV1", "state": "mountStatePreservedUnmounted"},
                ]
            }
        ],
        "expected": {
            "result": AntaTestStatus.FAILURE,
            "messages": ["MCS Client mount states are not valid - Expected: mountStateMountComplete Actual: mountStatePreservedUnmounted"],
        },
    },
    (VerifyMcsClientMounts, "failure-full-haclient"): {
        "eos_data": [
            {
                "mountStates": [
                    {"path": "blah/blah/blah", "type": "blah::blahState", "state": "mountStatePreservedUnmounted"},
                    {"path": "mcs/v1/toSwitch/00-1c-73-74-c0-8b", "type": "Mcs::DeviceConfigV1", "state": "mountStatePreservedUnmounted"},
                ]
            }
        ],
        "expected": {
            "result": AntaTestStatus.FAILURE,
            "messages": ["MCS Client mount states are not valid - Expected: mountStateMountComplete Actual: mountStatePreservedUnmounted"],
        },
    },
    (VerifyMcsClientMounts, "failure-non-mcs-client"): {
        "eos_data": [{"mountStates": [{"path": "blah/blah/blah", "type": "blah::blahState", "state": "mountStatePreservedUnmounted"}]}],
        "expected": {"result": AntaTestStatus.FAILURE, "messages": ["MCS Client mount states are not present"]},
    },
    (VerifyMcsClientMounts, "failure-partial-mcs-client"): {
        "eos_data": [
            {
                "mountStates": [
                    {"path": "blah/blah/blah", "type": "blah::blahState", "state": "mountStatePreservedUnmounted"},
                    {"path": "blah/blah/blah", "type": "Mcs::DeviceConfigV1", "state": "mountStatePreservedUnmounted"},
                ]
            }
        ],
        "expected": {
            "result": AntaTestStatus.FAILURE,
            "messages": ["MCS Client mount states are not valid - Expected: mountStateMountComplete Actual: mountStatePreservedUnmounted"],
        },
    },
    (VerifyManagementCVX, "success-enabled"): {
        "eos_data": [{"clusterStatus": {"enabled": True}}],
        "inputs": {"enabled": True},
        "expected": {"result": AntaTestStatus.SUCCESS},
    },
    (VerifyManagementCVX, "success-disabled"): {
        "eos_data": [{"clusterStatus": {"enabled": False}}],
        "inputs": {"enabled": False},
        "expected": {"result": AntaTestStatus.SUCCESS},
    },
    (VerifyManagementCVX, "failure-invalid-state"): {
        "eos_data": [{"clusterStatus": {"enabled": False}}],
        "inputs": {"enabled": True},
        "expected": {"result": AntaTestStatus.FAILURE, "messages": ["Management CVX status is not valid: Expected: enabled Actual: disabled"]},
    },
    (VerifyManagementCVX, "failure-no-enabled state"): {
        "eos_data": [{"clusterStatus": {}}],
        "inputs": {"enabled": False},
        "expected": {"result": AntaTestStatus.FAILURE, "messages": ["Management CVX status - Not configured"]},
    },
    (VerifyManagementCVX, "failure - no clusterStatus"): {
        "eos_data": [{}],
        "inputs": {"enabled": False},
        "expected": {"result": AntaTestStatus.FAILURE, "messages": ["Management CVX status - Not configured"]},
    },
    (VerifyMcsServerMounts, "success"): {
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
        "expected": {"result": AntaTestStatus.SUCCESS},
    },
    (VerifyMcsServerMounts, "failure-no-mounts"): {
        "eos_data": [{"connections": [{"hostname": "media-leaf-1", "mounts": []}]}],
        "inputs": {"connections_count": 1},
        "expected": {
            "result": AntaTestStatus.FAILURE,
            "messages": ["Host: media-leaf-1 - No mount status found", "Incorrect CVX successful connections count - Expected: 1 Actual: 0"],
        },
    },
    (VerifyMcsServerMounts, "failure-unexpected-number-paths"): {
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
            "result": AntaTestStatus.FAILURE,
            "messages": [
                "Host: media-leaf-1 - Incorrect number of mount path states - Expected: 3 Actual: 2",
                "Host: media-leaf-1 - Unexpected MCS path type - Expected: Mcs::ApiConfigRedundancyStatus, "
                "Mcs::ActiveFlows, Mcs::Client::Status Actual: Mcs::ApiStatus",
            ],
        },
    },
    (VerifyMcsServerMounts, "failure-unexpected-path-type"): {
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
        "expected": {
            "result": AntaTestStatus.FAILURE,
            "messages": [
                "Host: media-leaf-1 - Unexpected MCS path type - Expected: Mcs::ApiConfigRedundancyStatus, Mcs::ActiveFlows, "
                "Mcs::Client::Status Actual: Mcs::ApiStatus"
            ],
        },
    },
    (VerifyMcsServerMounts, "failure-invalid-mount-state"): {
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
            "result": AntaTestStatus.FAILURE,
            "messages": [
                "Host: media-leaf-1 Path Type: Mcs::ApiConfigRedundancyStatus - MCS server mount state is not valid - "
                "Expected: mountStateMountComplete Actual:mountStateMountFailed"
            ],
        },
    },
    (VerifyMcsServerMounts, "failure-no-mcs-mount"): {
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
        "expected": {
            "result": AntaTestStatus.FAILURE,
            "messages": ["MCS mount state not detected", "Incorrect CVX successful connections count - Expected: 1 Actual: 0"],
        },
    },
    (VerifyMcsServerMounts, "failure-connections"): {
        "eos_data": [{}],
        "inputs": {"connections_count": 1},
        "expected": {"result": AntaTestStatus.FAILURE, "messages": ["CVX connections are not available"]},
    },
    (VerifyActiveCVXConnections, "success"): {
        "eos_data": [
            {
                "connections": [
                    {"switchId": "fc:bd:67:c3:16:55", "hostname": "lyv563", "oobConnectionActive": True},
                    {"switchId": "00:1c:73:3c:e3:9e", "hostname": "tg264", "oobConnectionActive": True},
                ]
            }
        ],
        "inputs": {"connections_count": 2},
        "expected": {"result": AntaTestStatus.SUCCESS},
    },
    (VerifyActiveCVXConnections, "failure"): {
        "eos_data": [
            {
                "connections": [
                    {"switchId": "fc:bd:67:c3:16:55", "hostname": "lyv563", "oobConnectionActive": False},
                    {"switchId": "00:1c:73:3c:e3:9e", "hostname": "tg264", "oobConnectionActive": True},
                ]
            }
        ],
        "inputs": {"connections_count": 2},
        "expected": {"result": AntaTestStatus.FAILURE, "messages": ["CVX active connections count - Expected: 2 Actual: 1"]},
    },
    (VerifyActiveCVXConnections, "failure-no-connections"): {
        "eos_data": [{}],
        "inputs": {"connections_count": 2},
        "expected": {"result": AntaTestStatus.FAILURE, "messages": ["CVX connections are not available"]},
    },
    (VerifyCVXClusterStatus, "success-all"): {
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
        "expected": {"result": AntaTestStatus.SUCCESS},
    },
    (VerifyCVXClusterStatus, "failure-invalid-role"): {
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
        "expected": {"result": AntaTestStatus.FAILURE, "messages": ["CVX Role is not valid: Expected: Master Actual: Standby"]},
    },
    (VerifyCVXClusterStatus, "failure-cvx-enabled"): {
        "eos_data": [{"enabled": False, "clusterMode": True, "clusterStatus": {"role": "Master", "peerStatus": {}}}],
        "inputs": {"role": "Master", "peer_status": []},
        "expected": {"result": AntaTestStatus.FAILURE, "messages": ["CVX Server status is not enabled"]},
    },
    (VerifyCVXClusterStatus, "failure-cluster-enabled"): {
        "eos_data": [{"enabled": True, "clusterMode": False, "clusterStatus": {}}],
        "inputs": {"role": "Master", "peer_status": []},
        "expected": {"result": AntaTestStatus.FAILURE, "messages": ["CVX Server is not a cluster"]},
    },
    (VerifyCVXClusterStatus, "failure-missing-peers"): {
        "eos_data": [
            {
                "enabled": True,
                "clusterMode": True,
                "clusterStatus": {"role": "Master", "peerStatus": {"cvx-red-2": {"peerName": "cvx-red-2", "registrationState": "Registration complete"}}},
            }
        ],
        "inputs": {
            "role": "Master",
            "peer_status": [
                {"peer_name": "cvx-red-2", "registrationState": "Registration complete"},
                {"peer_name": "cvx-red-3", "registrationState": "Registration complete"},
            ],
        },
        "expected": {"result": AntaTestStatus.FAILURE, "messages": ["Unexpected number of peers - Expected: 2 Actual: 1", "cvx-red-3 - Not present"]},
    },
    (VerifyCVXClusterStatus, "failure-invalid-peers"): {
        "eos_data": [{"enabled": True, "clusterMode": True, "clusterStatus": {"role": "Master", "peerStatus": {}}}],
        "inputs": {
            "role": "Master",
            "peer_status": [
                {"peer_name": "cvx-red-2", "registrationState": "Registration complete"},
                {"peer_name": "cvx-red-3", "registrationState": "Registration complete"},
            ],
        },
        "expected": {
            "result": AntaTestStatus.FAILURE,
            "messages": ["Unexpected number of peers - Expected: 2 Actual: 0", "cvx-red-2 - Not present", "cvx-red-3 - Not present"],
        },
    },
    (VerifyCVXClusterStatus, "failure-registration-error"): {
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
        "expected": {
            "result": AntaTestStatus.FAILURE,
            "messages": ["cvx-red-2 - Invalid registration state - Expected: Registration complete Actual: Registration error"],
        },
    },
}
