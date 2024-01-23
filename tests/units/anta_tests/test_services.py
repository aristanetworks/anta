# Copyright (c) 2023-2024 Arista Networks, Inc.
# Use of this source code is governed by the Apache License 2.0
# that can be found in the LICENSE file.
"""
Tests for anta.tests.security.py
"""
from __future__ import annotations

from typing import Any

from anta.tests.services import VerifyErrdisableRecovery
from tests.lib.anta import test  # noqa: F401; pylint: disable=W0611

DATA: list[dict[str, Any]] = [
    {
        "name": "success",
        "test": VerifyErrdisableRecovery,
        "eos_data": [
            """
                Errdisable Reason              Timer Status   Timer Interval
                ------------------------------ ----------------- --------------
                acl                            Enabled                  300
                bpduguard                      Enabled                  300
                arp-inspection                 Enabled                  30
            """
        ],
        "inputs": {"reasons": [{"reason": "acl", "interval": 300}, {"reason": "bpduguard", "interval": 300}]},
        "expected": {"result": "success"},
    },
    {
        "name": "failure-reason-missing",
        "test": VerifyErrdisableRecovery,
        "eos_data": [
            """
                Errdisable Reason              Timer Status   Timer Interval
                ------------------------------ ----------------- --------------
                acl                            Enabled                  300
                bpduguard                      Enabled                  300
                arp-inspection                 Enabled                  30
            """
        ],
        "inputs": {"reasons": [{"reason": "acl", "interval": 300}, {"reason": "arp-inspection", "interval": 30}, {"reason": "tapagg", "interval": 30}]},
        "expected": {
            "result": "failure",
            "messages": ["`tapagg`: Not found."],
        },
    },
    {
        "name": "failure-reason-disabled",
        "test": VerifyErrdisableRecovery,
        "eos_data": [
            """
                Errdisable Reason              Timer Status   Timer Interval
                ------------------------------ ----------------- --------------
                acl                            Disabled                 300
                bpduguard                      Enabled                  300
                arp-inspection                 Enabled                  30
            """
        ],
        "inputs": {"reasons": [{"reason": "acl", "interval": 300}, {"reason": "arp-inspection", "interval": 30}]},
        "expected": {
            "result": "failure",
            "messages": ["`acl`:\nExpected `Enabled` as the status, but found `Disabled` instead."],
        },
    },
    {
        "name": "failure-interval-not-ok",
        "test": VerifyErrdisableRecovery,
        "eos_data": [
            """
                Errdisable Reason              Timer Status   Timer Interval
                ------------------------------ ----------------- --------------
                acl                            Enabled                  300
                bpduguard                      Enabled                  300
                arp-inspection                 Enabled                  30
            """
        ],
        "inputs": {"reasons": [{"reason": "acl", "interval": 30}, {"reason": "arp-inspection", "interval": 30}]},
        "expected": {
            "result": "failure",
            "messages": ["`acl`:\nExpected `30` as the interval, but found `300` instead."],
        },
    },
    {
        "name": "failure-all-type",
        "test": VerifyErrdisableRecovery,
        "eos_data": [
            """
                Errdisable Reason              Timer Status   Timer Interval
                ------------------------------ ----------------- --------------
                acl                            Disabled                 300
                bpduguard                      Enabled                  300
                arp-inspection                 Enabled                  30
            """
        ],
        "inputs": {"reasons": [{"reason": "acl", "interval": 30}, {"reason": "arp-inspection", "interval": 300}, {"reason": "tapagg", "interval": 30}]},
        "expected": {
            "result": "failure",
            "messages": [
                "`acl`:\nExpected `30` as the interval, but found `300` instead.\nExpected `Enabled` as the status, but found `Disabled` instead.",
                "`arp-inspection`:\nExpected `300` as the interval, but found `30` instead.",
                "`tapagg`: Not found.",
            ],
        },
    },
]
