# Copyright (c) 2023-2024 Arista Networks, Inc.
# Use of this source code is governed by the Apache License 2.0
# that can be found in the LICENSE file.
"""Test inputs for anta.tests.system"""
from __future__ import annotations

from typing import Any

from anta.tests.stun import VerifyStunClient
from tests.lib.anta import test  # noqa: F401; pylint: disable=W0611

DATA: list[dict[str, Any]] = [
    {
        "name": "success-with-public-ip",
        "test": VerifyStunClient,
        "eos_data": [
            {
                "bindings": {
                    "000000010a64ff0100000000": {
                        "sourceAddress": {"ip": "100.64.3.2", "port": 4500},
                        "publicAddress": {"ip": "192.64.3.2", "port": 4500},
                    }
                }
            },
            {
                "bindings": {
                    "000000040a64ff0100000000": {
                        "sourceAddress": {"ip": "172.18.3.2", "port": 4500},
                        "publicAddress": {"ip": "192.18.3.2", "port": 4500},
                    }
                }
            },
        ],
        "inputs": {
            "stun_clients": [
                {"source_address": "100.64.3.2", "public_address": "192.64.3.2", "port": 4500},
                {"source_address": "172.18.3.2", "public_address": "192.18.3.2", "port": 4500},
            ]
        },
        "expected": {"result": "success"},
    },
    {
        "name": "success-without-public-ip",
        "test": VerifyStunClient,
        "eos_data": [
            {
                "bindings": {
                    "000000010a64ff0100000000": {
                        "sourceAddress": {"ip": "100.64.3.2", "port": 4500},
                        "publicAddress": {"ip": "192.64.3.2", "port": 4500},
                    }
                }
            },
            {
                "bindings": {
                    "000000040a64ff0100000000": {
                        "sourceAddress": {"ip": "172.18.3.2", "port": 4500},
                        "publicAddress": {"ip": "192.18.3.2", "port": 4500},
                    }
                }
            },
        ],
        "inputs": {
            "stun_clients": [
                {"source_address": "100.64.3.2", "port": 4500},
                {"source_address": "172.18.3.2", "port": 4500},
            ]
        },
        "expected": {"result": "success"},
    },
    {
        "name": "failure-incorrect-public-ip",
        "test": VerifyStunClient,
        "eos_data": [
            {
                "bindings": {
                    "000000010a64ff0100000000": {
                        "sourceAddress": {"ip": "100.64.3.2", "port": 4500},
                        "publicAddress": {"ip": "192.64.3.2", "port": 4500},
                    }
                }
            },
            {
                "bindings": {
                    "000000040a64ff0100000000": {
                        "sourceAddress": {"ip": "172.18.3.2", "port": 4500},
                        "publicAddress": {"ip": "192.18.3.2", "port": 4500},
                    }
                }
            },
        ],
        "inputs": {
            "stun_clients": [
                {"source_address": "100.64.3.2", "public_address": "192.164.3.2", "port": 4500},
                {"source_address": "172.18.3.2", "public_address": "192.118.3.2", "port": 4500},
            ]
        },
        "expected": {
            "result": "failure",
            "messages": [
                "For STUN source address 100.64.3.2:\nExpected `192.164.3.2` as the public ip, but found `192.64.3.2` instead.",
                "For STUN source address 172.18.3.2:\nExpected `192.118.3.2` as the public ip, but found `192.18.3.2` instead.",
            ],
        },
    },
    {
        "name": "failure-no-client",
        "test": VerifyStunClient,
        "eos_data": [
            {"bindings": {}},
            {"bindings": {}},
        ],
        "inputs": {
            "stun_clients": [
                {"source_address": "100.64.3.2", "public_address": "192.164.3.2", "port": 4500},
                {"source_address": "172.18.3.2", "public_address": "192.118.3.2", "port": 4500},
            ]
        },
        "expected": {
            "result": "failure",
            "messages": ["STUN client transaction for source `100.64.3.2:4500` is not found.", "STUN client transaction for source `172.18.3.2:4500` is not found."],
        },
    },
    {
        "name": "failure-incorrect-public-port",
        "test": VerifyStunClient,
        "eos_data": [
            {"bindings": {}},
            {
                "bindings": {
                    "000000040a64ff0100000000": {
                        "sourceAddress": {"ip": "172.18.3.2", "port": 4500},
                        "publicAddress": {"ip": "192.18.3.2", "port": 4800},
                    }
                }
            },
        ],
        "inputs": {
            "stun_clients": [
                {"source_address": "100.64.3.2", "public_address": "192.164.3.2", "port": 4500},
                {"source_address": "172.18.3.2", "public_address": "192.118.3.2", "port": 4500},
            ]
        },
        "expected": {
            "result": "failure",
            "messages": [
                "STUN client transaction for source `100.64.3.2:4500` is not found.",
                "For STUN source address 172.18.3.2:\nExpected `192.118.3.2` as the public ip, but found `192.18.3.2` instead.\n"
                "Expected `4500` as the public port, but found `4800` instead.",
            ],
        },
    },
]
