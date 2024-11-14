# Copyright (c) 2023-2024 Arista Networks, Inc.
# Use of this source code is governed by the Apache License 2.0
# that can be found in the LICENSE file.
"""Data for testing anta.tests.configuration."""

from __future__ import annotations

from typing import Any

from anta.tests.configuration import VerifyCVXClusterStatus, VerifyManagementCVX, VerifyRunningConfigDiffs, VerifyRunningConfigLines, VerifyZeroTouch
from tests.units.anta_tests import test

DATA: list[dict[str, Any]] = [
    {
        "name": "success",
        "test": VerifyZeroTouch,
        "eos_data": [{"mode": "disabled"}],
        "inputs": None,
        "expected": {"result": "success"},
    },
    {
        "name": "failure",
        "test": VerifyZeroTouch,
        "eos_data": [{"mode": "enabled"}],
        "inputs": None,
        "expected": {"result": "failure", "messages": ["ZTP is NOT disabled"]},
    },
    {
        "name": "success",
        "test": VerifyRunningConfigDiffs,
        "eos_data": [""],
        "inputs": None,
        "expected": {"result": "success"},
    },
    {
        "name": "failure",
        "test": VerifyRunningConfigDiffs,
        "eos_data": ["blah blah"],
        "inputs": None,
        "expected": {"result": "failure", "messages": ["blah blah"]},
    },
    {
        "name": "success",
        "test": VerifyRunningConfigLines,
        "eos_data": ["blah blah"],
        "inputs": {"regex_patterns": ["blah"]},
        "expected": {"result": "success"},
    },
    {
        "name": "success",
        "test": VerifyRunningConfigLines,
        "eos_data": ["enable password something\nsome other line"],
        "inputs": {"regex_patterns": ["^enable password .*$", "^.*other line$"]},
        "expected": {"result": "success"},
    },
    {
        "name": "failure",
        "test": VerifyRunningConfigLines,
        "eos_data": ["enable password something\nsome other line"],
        "inputs": {"regex_patterns": ["bla", "bleh"]},
        "expected": {"result": "failure", "messages": ["Following patterns were not found: 'bla','bleh'"]},
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
        "name": "success-enabled",
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
]
