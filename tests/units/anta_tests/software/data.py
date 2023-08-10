# Copyright (c) 2023 Arista Networks, Inc.
# Use of this source code is governed by the Apache License 2.0
# that can be found in the LICENSE file.
"""Test inputs for anta.tests.hardware"""

from typing import Any, Dict, List

INPUT_VERIFY_EOS_VERSION: List[Dict[str, Any]] = [
    {
        "name": "success",
        "eos_data": [
            {
                "modelName": "vEOS-lab",
                "internalVersion": "4.27.0F-24305004.4270F",
                "version": "4.27.0F",
            }
        ],
        "inputs": ["4.27.0F", "4.28.0F"],
        "expected": {"result": "success"},
            },
    {
        "name": "failure",
        "eos_data": [
            {
                "modelName": "vEOS-lab",
                "internalVersion": "4.27.0F-24305004.4270F",
                "version": "4.27.0F",
            }
        ],
        "inputs": ["4.27.1F"],
        "expected": {"result": "failure", "messages": ["device is running version 4.27.0F not in expected versions: ['4.27.1F']"]},
    },
]

INPUT_VERIFY_TERMINATTR_VERSION: List[Dict[str, Any]] = [
    {
        "name": "success",
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
            }
        ],
        "inputs": ["v1.17.0", "v1.18.1"],
        "expected": {"result": "success"},
            },
    {
        "name": "failure",
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
            }
        ],
        "inputs": ["v1.17.1", "v1.18.1"],
        "expected": {"result": "failure", "messages": ["device is running TerminAttr version v1.17.0 and is not in the allowed list: ['v1.17.1', 'v1.18.1']"]},
    },
]

INPUT_VERIFY_EOS_EXTENSIONS: List[Dict[str, Any]] = [
    {
        "name": "success-no-extensions",
        "eos_data": [
            {"extensions": {}, "extensionStoredDir": "flash:", "warnings": ["No extensions are available"]},
            {"extensions": []},
        ],
        "inputs": None,
        "expected": {"result": "success"},
            },
    {
        "name": "failure",
        "eos_data": [
            {"extensions": {}, "extensionStoredDir": "flash:", "warnings": ["No extensions are available"]},
            {"extensions": ["dummy"]},
        ],
        "inputs": None,
        "expected": {"result": "failure", "messages": ["Missing EOS extensions: installed [] / configured: ['dummy']"]},
    },
]
