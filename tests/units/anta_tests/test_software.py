# Copyright (c) 2023-2025 Arista Networks, Inc.
# Use of this source code is governed by the Apache License 2.0
# that can be found in the LICENSE file.
"""Test inputs for anta.tests.hardware."""

from __future__ import annotations

from typing import Any

from anta.tests.software import VerifyEOSExtensions, VerifyEOSVersion, VerifyTerminAttrVersion
from tests.units.anta_tests import test

DATA: list[dict[str, Any]] = [
    {
        "name": "success",
        "test": VerifyEOSVersion,
        "eos_data": [
            {
                "modelName": "vEOS-lab",
                "internalVersion": "4.27.0F-24305004.4270F",
                "version": "4.27.0F",
            },
        ],
        "inputs": {"versions": ["4.27.0F", "4.28.0F"]},
        "expected": {"result": "success"},
    },
    {
        "name": "failure",
        "test": VerifyEOSVersion,
        "eos_data": [
            {
                "modelName": "vEOS-lab",
                "internalVersion": "4.27.0F-24305004.4270F",
                "version": "4.27.0F",
            },
        ],
        "inputs": {"versions": ["4.27.1F"]},
        "expected": {"result": "failure", "messages": ["device is running version \"4.27.0F\" not in expected versions: ['4.27.1F']"]},
    },
    {
        "name": "success",
        "test": VerifyTerminAttrVersion,
        "eos_data": [
            {
                "imageFormatVersion": "1.0",
                "uptime": 1107543.52,
                "modelName": "vEOS-lab",
                "details": {
                    "deviations": [],
                    "components": [{"name": "Aboot", "version": "Aboot-veos-8.0.0-3255441"}],
                    "switchType": "fixedSystem",
                    "packages": {
                        "TerminAttr-core": {"release": "1", "version": "v1.17.0"},
                    },
                },
            },
        ],
        "inputs": {"versions": ["v1.17.0", "v1.18.1"]},
        "expected": {"result": "success"},
    },
    {
        "name": "failure",
        "test": VerifyTerminAttrVersion,
        "eos_data": [
            {
                "imageFormatVersion": "1.0",
                "uptime": 1107543.52,
                "modelName": "vEOS-lab",
                "details": {
                    "deviations": [],
                    "components": [{"name": "Aboot", "version": "Aboot-veos-8.0.0-3255441"}],
                    "switchType": "fixedSystem",
                    "packages": {
                        "TerminAttr-core": {"release": "1", "version": "v1.17.0"},
                    },
                },
            },
        ],
        "inputs": {"versions": ["v1.17.1", "v1.18.1"]},
        "expected": {"result": "failure", "messages": ["device is running TerminAttr version v1.17.0 and is not in the allowed list: ['v1.17.1', 'v1.18.1']"]},
    },
    # TODO: add a test with a real extension?
    {
        "name": "success-no-extensions",
        "test": VerifyEOSExtensions,
        "eos_data": [
            {"extensions": {}, "extensionStoredDir": "flash:", "warnings": ["No extensions are available"]},
            {"extensions": []},
        ],
        "inputs": None,
        "expected": {"result": "success"},
    },
    {
        "name": "success-empty-extension",
        "test": VerifyEOSExtensions,
        "eos_data": [
            {"extensions": {}, "extensionStoredDir": "flash:", "warnings": ["No extensions are available"]},
            {"extensions": [""]},
        ],
        "inputs": None,
        "expected": {"result": "success"},
    },
    {
        "name": "failure",
        "test": VerifyEOSExtensions,
        "eos_data": [
            {"extensions": {}, "extensionStoredDir": "flash:", "warnings": ["No extensions are available"]},
            {"extensions": ["dummy"]},
        ],
        "inputs": None,
        "expected": {"result": "failure", "messages": ["Missing EOS extensions: installed [] / configured: ['dummy']"]},
    },
]
