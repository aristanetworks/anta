# Copyright (c) 2023-2024 Arista Networks, Inc.
# Use of this source code is governed by the Apache License 2.0
# that can be found in the LICENSE file.
"""
Tests for anta.tests.security.py
"""
from __future__ import annotations

from typing import Any

from anta.tests.services import VerifyDNSLookup
from tests.lib.anta import test  # noqa: F401; pylint: disable=W0611

DATA: list[dict[str, Any]] = [
    {
        "name": "success",
        "test": VerifyDNSLookup,
        "eos_data": [
            {
                "messages": [
                    "Server:\t\t127.0.0.1\nAddress:\t127.0.0.1#53\n\nNon-authoritative answer:\nName:\tarista.com\nAddress: 151.101.130.132\nName:\tarista.com\n"
                    "Address: 151.101.2.132\nName:\tarista.com\nAddress: 151.101.194.132\nName:\tarista.com\nAddress: 151.101.66.132\n\n"
                ]
            },
            {"messages": ["Server:\t\t127.0.0.1\nAddress:\t127.0.0.1#53\n\nNon-authoritative answer:\nName:\twww.google.com\nAddress: 172.217.12.100\n\n"]},
        ],
        "inputs": {"domain_names": ["arista.com", "www.google.com"]},
        "expected": {"result": "success"},
    },
    {
        "name": "failure",
        "test": VerifyDNSLookup,
        "eos_data": [
            {
                "messages": [
                    "Server:\t\t127.0.0.1\nAddress:\t127.0.0.1#53\n\nNon-authoritative answer:\nName:\tarista.com\nAddress: 151.101.130.132\nName:\tarista.com\n"
                    "Address: 151.101.2.132\nName:\tarista.com\nAddress: 151.101.194.132\nName:\tarista.com\nAddress: 151.101.66.132\n\n"
                ]
            },
            {"messages": ["Server:\t\t127.0.0.1\nAddress:\t127.0.0.1#53\n\nNon-authoritative answer:\nName:\twww.google.com\nAddress: 172.217.12.100\n\n"]},
            {"messages": ["Server:\t\t127.0.0.1\nAddress:\t127.0.0.1#53\n\nNon-authoritative answer:\n*** Can't find khatri.com: No answer\n\n"]},
        ],
        "inputs": {"domain_names": ["arista.com", "www.google.com", "khatri.com"]},
        "expected": {"result": "failure", "messages": ["Domain khatri.com is not resolved to an IP address."]},
    },
]
