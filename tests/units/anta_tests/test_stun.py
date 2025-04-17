# Copyright (c) 2023-2025 Arista Networks, Inc.
# Use of this source code is governed by the Apache License 2.0
# that can be found in the LICENSE file.
"""Test inputs for anta.tests.stun.py."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from anta.tests.stun import VerifyStunClientTranslation, VerifyStunServer
from tests.units.anta_tests import test

if TYPE_CHECKING:
    from anta.models import AntaTest
    from tests.units.anta_tests import AntaUnitTest

DATA: dict[tuple[type[AntaTest], str], AntaUnitTest] = {
    (VerifyStunClientTranslation, "success"): {
        "eos_data": [
            {"bindings": {"000000010a64ff0100000000": {"sourceAddress": {"ip": "100.64.3.2", "port": 4500}, "publicAddress": {"ip": "192.64.3.2", "port": 6006}}}},
            {"bindings": {"000000040a64ff0100000000": {"sourceAddress": {"ip": "172.18.3.2", "port": 4500}, "publicAddress": {"ip": "192.18.3.2", "port": 6006}}}},
            {"bindings": {"000000040a64ff0100000000": {"sourceAddress": {"ip": "172.18.4.2", "port": 4500}, "publicAddress": {"ip": "192.18.4.2", "port": 6006}}}},
            {"bindings": {"000000040a64ff0100000000": {"sourceAddress": {"ip": "172.18.6.2", "port": 4500}, "publicAddress": {"ip": "192.18.6.2", "port": 6006}}}},
        ],
        "inputs": {
            "stun_clients": [
                {"source_address": "100.64.3.2", "public_address": "192.64.3.2", "source_port": 4500, "public_port": 6006},
                {"source_address": "172.18.3.2"},
                {"source_address": "172.18.4.2", "source_port": 4500, "public_address": "192.18.4.2"},
                {"source_address": "172.18.6.2", "source_port": 4500, "public_port": 6006},
            ]
        },
        "expected": {"result": "success"},
    },
    (VerifyStunClientTranslation, "failure-incorrect-public-ip"): {
        "eos_data": [
            {"bindings": {"000000010a64ff0100000000": {"sourceAddress": {"ip": "100.64.3.2", "port": 4500}, "publicAddress": {"ip": "192.64.3.2", "port": 6006}}}},
            {"bindings": {"000000040a64ff0100000000": {"sourceAddress": {"ip": "172.18.3.2", "port": 4500}, "publicAddress": {"ip": "192.18.3.2", "port": 6006}}}},
        ],
        "inputs": {
            "stun_clients": [
                {"source_address": "100.64.3.2", "public_address": "192.164.3.2", "source_port": 4500, "public_port": 6006},
                {"source_address": "172.18.3.2", "public_address": "192.118.3.2", "source_port": 4500, "public_port": 6006},
            ]
        },
        "expected": {
            "result": "failure",
            "messages": [
                "Client 100.64.3.2 Port: 4500 - Incorrect public-facing address - Expected: 192.164.3.2 Actual: 192.64.3.2",
                "Client 172.18.3.2 Port: 4500 - Incorrect public-facing address - Expected: 192.118.3.2 Actual: 192.18.3.2",
            ],
        },
    },
    (VerifyStunClientTranslation, "failure-no-client"): {
        "eos_data": [{"bindings": {}}, {"bindings": {}}],
        "inputs": {
            "stun_clients": [
                {"source_address": "100.64.3.2", "public_address": "192.164.3.2", "source_port": 4500, "public_port": 6006},
                {"source_address": "172.18.3.2", "public_address": "192.118.3.2", "source_port": 4500, "public_port": 6006},
            ]
        },
        "expected": {
            "result": "failure",
            "messages": ["Client 100.64.3.2 Port: 4500 - STUN client translation not found", "Client 172.18.3.2 Port: 4500 - STUN client translation not found"],
        },
    },
    (VerifyStunClientTranslation, "failure-incorrect-public-port"): {
        "eos_data": [
            {"bindings": {}},
            {"bindings": {"000000040a64ff0100000000": {"sourceAddress": {"ip": "172.18.3.2", "port": 4500}, "publicAddress": {"ip": "192.18.3.2", "port": 4800}}}},
        ],
        "inputs": {
            "stun_clients": [
                {"source_address": "100.64.3.2", "public_address": "192.164.3.2", "source_port": 4500, "public_port": 6006},
                {"source_address": "172.18.3.2", "public_address": "192.118.3.2", "source_port": 4500, "public_port": 6006},
            ]
        },
        "expected": {
            "result": "failure",
            "messages": [
                "Client 100.64.3.2 Port: 4500 - STUN client translation not found",
                "Client 172.18.3.2 Port: 4500 - Incorrect public-facing address - Expected: 192.118.3.2 Actual: 192.18.3.2",
                "Client 172.18.3.2 Port: 4500 - Incorrect public-facing port - Expected: 6006 Actual: 4800",
            ],
        },
    },
    (VerifyStunClientTranslation, "failure-all-type"): {
        "eos_data": [
            {"bindings": {}},
            {"bindings": {"000000040a64ff0100000000": {"sourceAddress": {"ip": "172.18.3.2", "port": 4500}, "publicAddress": {"ip": "192.18.3.2", "port": 4800}}}},
        ],
        "inputs": {
            "stun_clients": [
                {"source_address": "100.64.3.2", "public_address": "192.164.3.2", "source_port": 4500, "public_port": 6006},
                {"source_address": "172.18.4.2", "public_address": "192.118.3.2", "source_port": 4800, "public_port": 6006},
            ]
        },
        "expected": {
            "result": "failure",
            "messages": [
                "Client 100.64.3.2 Port: 4500 - STUN client translation not found",
                "Client 172.18.4.2 Port: 4800 - Incorrect public-facing address - Expected: 192.118.3.2 Actual: 192.18.3.2",
                "Client 172.18.4.2 Port: 4800 - Incorrect public-facing port - Expected: 6006 Actual: 4800",
            ],
        },
    },
    (VerifyStunServer, "success"): {"eos_data": [{"enabled": True, "pid": 1895}], "inputs": {}, "expected": {"result": "success"}},
    (VerifyStunServer, "failure-disabled"): {
        "eos_data": [{"enabled": False, "pid": 1895}],
        "inputs": {},
        "expected": {"result": "failure", "messages": ["STUN server status is disabled"]},
    },
    (VerifyStunServer, "failure-not-running"): {
        "eos_data": [{"enabled": True, "pid": 0}],
        "inputs": {},
        "expected": {"result": "failure", "messages": ["STUN server is not running"]},
    },
    (VerifyStunServer, "failure-not-running-disabled"): {
        "eos_data": [{"enabled": False, "pid": 0}],
        "inputs": {},
        "expected": {"result": "failure", "messages": ["STUN server status is disabled and not running"]},
    },
}
