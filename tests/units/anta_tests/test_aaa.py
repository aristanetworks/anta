# Copyright (c) 2023-2025 Arista Networks, Inc.
# Use of this source code is governed by the Apache License 2.0
# that can be found in the LICENSE file.
"""Tests for anta.tests.aaa.py."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from anta.tests.aaa import VerifyTacacsSourceIntf
from tests.units.anta_tests import test

if TYPE_CHECKING:
    from anta.models import AntaTest, AntaUnitTest

DATA: dict[tuple[type[AntaTest], str], AntaUnitTest] = {
    (VerifyTacacsSourceIntf, "success"): {
        "eos_data": [
            {
                "tacacsServers": [
                    {
                        "serverInfo": {"hostname": "10.22.10.91", "authport": 49, "vrf": "MGMT"},
                    },
                ],
                "groups": {"GROUP1": {"serverGroup": "TACACS+", "members": [{"hostname": "SERVER1", "authport": 49, "vrf": "MGMT"}]}},
                "srcIntf": {"MGMT": "Management0"},
            },
        ],
        "inputs": {"intf": "Management0", "vrf": "MGMT"},
        "expected": {"result": "success"},
    },
    (VerifyTacacsSourceIntf, "failed"): {
        "eos_data": [
            {
                "tacacsServers": [],
                "groups": {},
                "srcIntf": {},
            },
        ],
        "inputs": {"intf": "Management0", "vrf": "MGMT"},
        "expected": {"result": "failure", "messages": ["VRF: MGMT Source Interface: Management0 - Not configured"]},
    },
}
