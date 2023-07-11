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
        "expected_messages": ["Uptime is 665.15"],
    },
    {
        "name": "skipped-no-minimum",
        "eos_data": [{"upTime": 665.15, "loadAvg": [0.13, 0.12, 0.09], "users": 1, "currentTime": 1683186659.139859}],
        "side_effect": None,
        "expected_result": "skipped",
        "expected_messages": ["VerifyUptime was not run as incorrect minimum uptime was given"],
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
        "expected_messages": ["Reload cause is Reload after crash."],
    },
]

INPUT_COREDUMP: List[Dict[str, Any]] = [
    {
        "name": "success",
        "eos_data": [""],
        "side_effect": [],
        "expected_result": "success",
        "expected_messages": [],
    },
    {
        "name": "failure",
        "eos_data": ["kernelcrash.last.2023-04-20-16-13-33"],
        "side_effect": [],
        "expected_result": "failure",
        "expected_messages": ["Core-dump(s) have been found: kernelcrash.last.2023-04-20-16-13-33"],
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
            'device reported some agent logs:\n'
            ' * /var/log/agents/Test-666 Thu May  4 09:57:02 2023\n'
            ' * /var/log/agents/Aaa-855 Fri Jul  7 15:07:00 2023\n'
            ' * /var/log/agents/Acl-830 Fri Jul  7 15:07:00 2023',
        ],
    },
]

INPUT_SYSLOG: List[Dict[str, Any]] = [
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
            """May  4 10:23:59 Leaf1 Lldp: %LLDP-3-NEIGHBOR_NEW: LLDP neighbor with chassisId 5022.0057.d059 and portId "Ethernet1" added on interface
Ethernet1
"""
        ],
        "side_effect": [],
        "expected_result": "failure",
        "expected_messages": ["Device has some log messages with a severity WARNING or higher"],
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
        "expected_messages": ["device reported a high CPU utilization (75.2%)"],
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
        "expected_messages": ["device report a high memory usage: 95.56%"],
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
            "mount point /dev/sda2       3.9G  988M  2.9G  84% /mnt/flash is higher than 75% (reported 84)",
            "mount point none            294M   78M  217M  84% /.overlay is higher than 75% (reported 84)",
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
        "expected_messages": ["not sync with NTP server (unsynchronised)"],
    },
]
