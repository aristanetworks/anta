# Copyright (c) 2023-2025 Arista Networks, Inc.
# Use of this source code is governed by the Apache License 2.0
# that can be found in the LICENSE file.
"""Unit tests data for the asynceapi client package."""

from asynceapi._types import EapiJsonOutput, JsonRpc

SUCCESS_EAPI_RESPONSE: EapiJsonOutput = {
    "jsonrpc": "2.0",
    "id": "EapiExplorer-1",
    "result": [
        {
            "mfgName": "Arista",
            "modelName": "cEOSLab",
            "hardwareRevision": "",
            "serialNumber": "5E9D49D20F09DA471333DD835835FD1A",
            "systemMacAddress": "00:1c:73:2e:7b:a3",
            "hwMacAddress": "00:00:00:00:00:00",
            "configMacAddress": "00:00:00:00:00:00",
            "version": "4.31.1F-34554157.4311F (engineering build)",
            "architecture": "i686",
            "internalVersion": "4.31.1F-34554157.4311F",
            "internalBuildId": "47114ca4-ae9f-4f32-8c1f-2864db93b7e8",
            "imageFormatVersion": "1.0",
            "imageOptimization": "None",
            "cEosToolsVersion": "(unknown)",
            "kernelVersion": "6.5.0-44-generic",
            "bootupTimestamp": 1723429239.9352903,
            "uptime": 1300202.749528885,
            "memTotal": 65832112,
            "memFree": 41610316,
            "isIntlVersion": False,
        },
        {
            "utcTime": 1724729442.6863558,
            "timezone": "EST",
            "localTime": {
                "year": 2024,
                "month": 8,
                "dayOfMonth": 26,
                "hour": 22,
                "min": 30,
                "sec": 42,
                "dayOfWeek": 0,
                "dayOfYear": 239,
                "daylightSavingsAdjust": 0,
            },
            "clockSource": {"local": True},
        },
    ],
}
"""Successful eAPI JSON response."""

ERROR_EAPI_RESPONSE: EapiJsonOutput = {
    "jsonrpc": "2.0",
    "id": "EapiExplorer-1",
    "error": {
        "code": 1002,
        "message": "CLI command 2 of 3 'bad command' failed: invalid command",
        "data": [
            {
                "mfgName": "Arista",
                "modelName": "cEOSLab",
                "hardwareRevision": "",
                "serialNumber": "5E9D49D20F09DA471333DD835835FD1A",
                "systemMacAddress": "00:1c:73:2e:7b:a3",
                "hwMacAddress": "00:00:00:00:00:00",
                "configMacAddress": "00:00:00:00:00:00",
                "version": "4.31.1F-34554157.4311F (engineering build)",
                "architecture": "i686",
                "internalVersion": "4.31.1F-34554157.4311F",
                "internalBuildId": "47114ca4-ae9f-4f32-8c1f-2864db93b7e8",
                "imageFormatVersion": "1.0",
                "imageOptimization": "None",
                "cEosToolsVersion": "(unknown)",
                "kernelVersion": "6.5.0-44-generic",
                "bootupTimestamp": 1723429239.9352903,
                "uptime": 1300027.2297976017,
                "memTotal": 65832112,
                "memFree": 41595080,
                "isIntlVersion": False,
            },
            {"errors": ["Invalid input (at token 1: 'bad')"]},
        ],
    },
}
"""Error eAPI JSON response."""

JSONRPC_REQUEST_TEMPLATE: JsonRpc = {"jsonrpc": "2.0", "method": "runCmds", "params": {"version": 1, "cmds": [], "format": "json"}, "id": "EapiExplorer-1"}
"""Template for JSON-RPC eAPI request. `cmds` must be filled by the parametrize decorator."""
