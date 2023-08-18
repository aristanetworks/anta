# Copyright (c) 2023 Arista Networks, Inc.
# Use of this source code is governed by the Apache License 2.0
# that can be found in the LICENSE file.
"""Test inputs for anta.tests.system"""

from typing import Any, Dict, List

INPUT_UPTIME: List[Dict[str, Any]] = [
    {
        "name": "success",
        "eos_data": [{"upTime": 1186689.15, "loadAvg": [0.13, 0.12, 0.09], "users": 1, "currentTime": 1683186659.139859}],
        "side_effect": 666,
        "expected_result": "success",
        "expected_messages": [],
    },
    {
        "name": "failure",
        "eos_data": [{"upTime": 665.15, "loadAvg": [0.13, 0.12, 0.09], "users": 1, "currentTime": 1683186659.139859}],
        "side_effect": 666,
        "expected_result": "failure",
        "expected_messages": ["Device uptime is 665.15 seconds"],
    },
    {
        "name": "skipped-no-minimum",
        "eos_data": [{"upTime": 665.15, "loadAvg": [0.13, 0.12, 0.09], "users": 1, "currentTime": 1683186659.139859}],
        "side_effect": None,
        "expected_result": "skipped",
        "expected_messages": ["VerifyUptime was not run since the provided uptime value is invalid or negative"],
    },
]

INPUT_RELOAD_CAUSE: List[Dict[str, Any]] = [
    {
        "name": "success-no-reload",
        "eos_data": [{"kernelCrashData": [], "resetCauses": [], "full": False}],
        "side_effect": [],
        "expected_result": "success",
        "expected_messages": [],
    },
    {
        "name": "success-valid-cause",
        "eos_data": [
            {
                "resetCauses": [
                    {"recommendedAction": "No action necessary.", "description": "Reload requested by the user.", "timestamp": 1683186892.0, "debugInfoIsDir": False}
                ],
                "full": False,
            }
        ],
        "side_effect": [],
        "expected_result": "success",
        "expected_messages": [],
    },
    {
        "name": "failure",
        # The failure cause is made up
        "eos_data": [
            {
                "resetCauses": [
                    {"recommendedAction": "No action necessary.", "description": "Reload after crash.", "timestamp": 1683186892.0, "debugInfoIsDir": False}
                ],
                "full": False,
            }
        ],
        "side_effect": [],
        "expected_result": "failure",
        "expected_messages": ["Reload cause is: 'Reload after crash.'"],
    },
    {
        "name": "error",
        "eos_data": [
            {}
        ],
        "side_effect": [],
        "expected_result": "error",
        "expected_messages": ["No reload causes available"],
    },
]

INPUT_COREDUMP: List[Dict[str, Any]] = [
    {
        "name": "success-without-minidump",
        "eos_data": [
            {
                'mode': 'compressedDeferred',
                'coreFiles': []
            }
        ],
        "side_effect": [],
        "expected_result": "success",
        "expected_messages": [],
    },
    {
        "name": "success-with-minidump",
        "eos_data": [
            {
                'mode': 'compressedDeferred',
                'coreFiles': ['minidump']
            }
        ],
        "side_effect": [],
        "expected_result": "success",
        "expected_messages": [],
    },
    {
        "name": "failure-without-minidump",
        "eos_data": [
            {
                'mode': 'compressedDeferred',
                'coreFiles': ["core.2344.1584483862.Mlag.gz", "core.23101.1584483867.Mlag.gz"]
            }
        ],
        "side_effect": [],
        "expected_result": "failure",
        "expected_messages": ["Core dump(s) have been found: ['core.2344.1584483862.Mlag.gz', 'core.23101.1584483867.Mlag.gz']"]
    },
    {
        "name": "failure-with-minidump",
        "eos_data": [
            {
                'mode': 'compressedDeferred',
                'coreFiles': ["minidump", "core.2344.1584483862.Mlag.gz", "core.23101.1584483867.Mlag.gz"]
            }
        ],
        "side_effect": [],
        "expected_result": "failure",
        "expected_messages": ["Core dump(s) have been found: ['core.2344.1584483862.Mlag.gz', 'core.23101.1584483867.Mlag.gz']"]
    },
]

INPUT_AGENT_LOGS: List[Dict[str, Any]] = [
    {
        "name": "success",
        "eos_data": [""],
        "side_effect": [],
        "expected_result": "success",
        "expected_messages": [],
    },
    {
        "name": "failure",
        "eos_data": [
            """===> /var/log/agents/Test-666 Thu May  4 09:57:02 2023 <===
CLI Exception: Exception
CLI Exception: Backtrace
===> /var/log/agents/Aaa-855 Fri Jul  7 15:07:00 2023 <===
===== Output from /usr/bin/Aaa [] (PID=855) started Jul  7 15:06:11.606414 ===
EntityManager::doBackoff waiting for remote sysdb version ....ok

===> /var/log/agents/Acl-830 Fri Jul  7 15:07:00 2023 <===
===== Output from /usr/bin/Acl [] (PID=830) started Jul  7 15:06:10.871700 ===
EntityManager::doBackoff waiting for remote sysdb version ...................ok
"""
        ],
        "side_effect": [],
        "expected_result": "failure",
        "expected_messages": [
            'Device has reported agent crashes:\n'
            ' * /var/log/agents/Test-666 Thu May  4 09:57:02 2023\n'
            ' * /var/log/agents/Aaa-855 Fri Jul  7 15:07:00 2023\n'
            ' * /var/log/agents/Acl-830 Fri Jul  7 15:07:00 2023',
        ],
    },
]


INPUT_CPU_UTILIZATION: List[Dict[str, Any]] = [
    {
        "name": "success",
        "eos_data": [
            {
                "cpuInfo": {"%Cpu(s)": {"idle": 88.2, "stolen": 0.0, "user": 5.9, "swIrq": 0.0, "ioWait": 0.0, "system": 0.0, "hwIrq": 5.9, "nice": 0.0}},
                "processes": {
                    "1": {
                        "userName": "root",
                        "status": "S",
                        "memPct": 0.3,
                        "niceValue": 0,
                        "cpuPct": 0.0,
                        "cpuPctType": "{:.1f}",
                        "cmd": "systemd",
                        "residentMem": "5096",
                        "priority": "20",
                        "activeTime": 360,
                        "virtMem": "6644",
                        "sharedMem": "3996",
                    }
                },
            }
        ],
        "side_effect": [],
        "expected_result": "success",
        "expected_messages": [],
    },
    {
        "name": "failure",
        "eos_data": [
            {
                "cpuInfo": {"%Cpu(s)": {"idle": 24.8, "stolen": 0.0, "user": 5.9, "swIrq": 0.0, "ioWait": 0.0, "system": 0.0, "hwIrq": 5.9, "nice": 0.0}},
                "processes": {
                    "1": {
                        "userName": "root",
                        "status": "S",
                        "memPct": 0.3,
                        "niceValue": 0,
                        "cpuPct": 0.0,
                        "cpuPctType": "{:.1f}",
                        "cmd": "systemd",
                        "residentMem": "5096",
                        "priority": "20",
                        "activeTime": 360,
                        "virtMem": "6644",
                        "sharedMem": "3996",
                    }
                },
            }
        ],
        "side_effect": [],
        "expected_result": "failure",
        "expected_messages": ["Device has reported a high CPU utilization: 75.2%"],
    },
]

INPUT_MEMORY_UTILIZATION: List[Dict[str, Any]] = [
    {
        "name": "success",
        "eos_data": [
            {
                "uptime": 1994.67,
                "modelName": "vEOS-lab",
                "internalVersion": "4.27.3F-26379303.4273F",
                "memTotal": 2004568,
                "memFree": 879004,
                "version": "4.27.3F",
            }
        ],
        "side_effect": [],
        "expected_result": "success",
        "expected_messages": [],
    },
    {
        "name": "failure",
        "eos_data": [
            {
                "uptime": 1994.67,
                "modelName": "vEOS-lab",
                "internalVersion": "4.27.3F-26379303.4273F",
                "memTotal": 2004568,
                "memFree": 89004,
                "version": "4.27.3F",
            }
        ],
        "side_effect": [],
        "expected_result": "failure",
        "expected_messages": ["Device has reported a high memory usage: 95.56%"],
    },
]

INPUT_FILE_SYSTEM_UTILIZATION: List[Dict[str, Any]] = [
    {
        "name": "success",
        "eos_data": [
            """Filesystem      Size  Used Avail Use% Mounted on
/dev/sda2       3.9G  988M  2.9G  26% /mnt/flash
none            294M   78M  217M  27% /
none            294M   78M  217M  27% /.overlay
/dev/loop0      461M  461M     0 100% /rootfs-i386
"""
        ],
        "side_effect": [],
        "expected_result": "success",
        "expected_messages": [],
    },
    {
        "name": "failure",
        "eos_data": [
            """Filesystem      Size  Used Avail Use% Mounted on
/dev/sda2       3.9G  988M  2.9G  84% /mnt/flash
none            294M   78M  217M  27% /
none            294M   78M  217M  84% /.overlay
/dev/loop0      461M  461M     0 100% /rootfs-i386
"""
        ],
        "side_effect": [],
        "expected_result": "failure",
        "expected_messages": [
            "Mount point /dev/sda2       3.9G  988M  2.9G  84% /mnt/flash is higher than 75%: reported 84%",
            "Mount point none            294M   78M  217M  84% /.overlay is higher than 75%: reported 84%",
        ],
    },
]


INPUT_NTP: List[Dict[str, Any]] = [
    {
        "name": "success",
        "eos_data": [
            """synchronised
poll interval unknown
"""
        ],
        "side_effect": [],
        "expected_result": "success",
        "expected_messages": [],
    },
    {
        "name": "failure",
        "eos_data": [
            """unsynchronised
poll interval unknown
"""
        ],
        "side_effect": [],
        "expected_result": "failure",
        "expected_messages": ["NTP server is not synchronized: 'unsynchronised'"],
    },
]
