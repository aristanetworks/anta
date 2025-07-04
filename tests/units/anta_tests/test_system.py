# Copyright (c) 2023-2025 Arista Networks, Inc.
# Use of this source code is governed by the Apache License 2.0
# that can be found in the LICENSE file.
"""Test inputs for anta.tests.system."""

from __future__ import annotations

import sys
from typing import TYPE_CHECKING, Any

from anta.models import AntaTest
from anta.result_manager.models import AntaTestStatus
from anta.tests.system import (
    VerifyAgentLogs,
    VerifyCoredump,
    VerifyCPUUtilization,
    VerifyFAPLowLatency,
    VerifyFileSystemUtilization,
    VerifyMaintenance,
    VerifyMemoryUtilization,
    VerifyNTP,
    VerifyNTPAssociations,
    VerifyReloadCause,
    VerifyUptime,
)
from tests.units.anta_tests import test

if TYPE_CHECKING:
    from tests.units.anta_tests import AntaUnitTestDataDict

DATA: AntaUnitTestDataDict = {
    (VerifyUptime, "success"): {
        "eos_data": [{"upTime": 1186689.15, "loadAvg": [0.13, 0.12, 0.09], "users": 1, "currentTime": 1683186659.139859}],
        "inputs": {"minimum": 666},
        "expected": {"result": AntaTestStatus.SUCCESS},
    },
    (VerifyUptime, "failure"): {
        "eos_data": [{"upTime": 665.15, "loadAvg": [0.13, 0.12, 0.09], "users": 1, "currentTime": 1683186659.139859}],
        "inputs": {"minimum": 666},
        "expected": {"result": AntaTestStatus.FAILURE, "messages": ["Device uptime is incorrect - Expected: 666s Actual: 665.15s"]},
    },
    (VerifyReloadCause, "success-no-reload"): {
        "eos_data": [{"kernelCrashData": [], "resetCauses": [], "full": False}],
        "expected": {"result": AntaTestStatus.SUCCESS},
    },
    (VerifyReloadCause, "success-valid-cause-user"): {
        "eos_data": [
            {
                "resetCauses": [
                    {"recommendedAction": "No action necessary.", "description": "Reload requested by the user.", "timestamp": 1683186892.0, "debugInfoIsDir": False}
                ],
                "full": False,
            }
        ],
        "expected": {"result": AntaTestStatus.SUCCESS},
    },
    (VerifyReloadCause, "success-valid-reload-cause-ztp"): {
        "eos_data": [
            {
                "resetCauses": [
                    {
                        "description": "System reloaded due to Zero Touch Provisioning",
                        "timestamp": 1729856740.0,
                        "recommendedAction": "No action necessary.",
                        "debugInfoIsDir": False,
                    }
                ],
                "full": False,
            }
        ],
        "inputs": {"allowed_causes": ["ZTP"]},
        "expected": {"result": AntaTestStatus.SUCCESS},
    },
    (VerifyReloadCause, "success-valid-reload-cause-fpga"): {
        "eos_data": [
            {
                "resetCauses": [
                    {
                        "description": "Reload requested after FPGA upgrade",
                        "timestamp": 1729856740.0,
                        "recommendedAction": "No action necessary.",
                        "debugInfoIsDir": False,
                    }
                ],
                "full": False,
            }
        ],
        "inputs": {"allowed_causes": ["fpga"]},
        "expected": {"result": AntaTestStatus.SUCCESS},
    },
    (VerifyReloadCause, "failure-invalid-reload-cause"): {
        "eos_data": [
            {
                "resetCauses": [
                    {
                        "description": "Reload requested after FPGA upgrade",
                        "timestamp": 1729856740.0,
                        "recommendedAction": "No action necessary.",
                        "debugInfoIsDir": False,
                    }
                ],
                "full": False,
            }
        ],
        "inputs": {"allowed_causes": ["ZTP"]},
        "expected": {
            "result": AntaTestStatus.FAILURE,
            "messages": ["Invalid reload cause -  Expected: 'System reloaded due to Zero Touch Provisioning' Actual: 'Reload requested after FPGA upgrade'"],
        },
    },
    (VerifyReloadCause, "failure"): {
        "eos_data": [
            {
                "resetCauses": [
                    {"recommendedAction": "No action necessary.", "description": "Reload after crash.", "timestamp": 1683186892.0, "debugInfoIsDir": False}
                ],
                "full": False,
            }
        ],
        "expected": {
            "result": AntaTestStatus.FAILURE,
            "messages": ["Invalid reload cause -  Expected: 'Reload requested by the user.', 'Reload requested after FPGA upgrade' Actual: 'Reload after crash.'"],
        },
    },
    (VerifyCoredump, "success-without-minidump"): {
        "eos_data": [{"mode": "compressedDeferred", "coreFiles": []}],
        "expected": {"result": AntaTestStatus.SUCCESS},
    },
    (VerifyCoredump, "success-with-minidump"): {
        "eos_data": [{"mode": "compressedDeferred", "coreFiles": ["minidump"]}],
        "expected": {"result": AntaTestStatus.SUCCESS},
    },
    (VerifyCoredump, "failure-without-minidump"): {
        "eos_data": [{"mode": "compressedDeferred", "coreFiles": ["core.2344.1584483862.Mlag.gz", "core.23101.1584483867.Mlag.gz"]}],
        "expected": {"result": AntaTestStatus.FAILURE, "messages": ["Core dump(s) have been found: core.2344.1584483862.Mlag.gz, core.23101.1584483867.Mlag.gz"]},
    },
    (VerifyCoredump, "failure-with-minidump"): {
        "eos_data": [{"mode": "compressedDeferred", "coreFiles": ["minidump", "core.2344.1584483862.Mlag.gz", "core.23101.1584483867.Mlag.gz"]}],
        "expected": {"result": AntaTestStatus.FAILURE, "messages": ["Core dump(s) have been found: core.2344.1584483862.Mlag.gz, core.23101.1584483867.Mlag.gz"]},
    },
    (VerifyAgentLogs, "success"): {"eos_data": [""], "expected": {"result": AntaTestStatus.SUCCESS}},
    (VerifyAgentLogs, "failure"): {
        "eos_data": [
            "===> /var/log/agents/Test-666 Thu May  4 09:57:02 2023 <===\nCLI Exception: Exception\nCLI Exception: Backtrace\n===> /var/log/agents/Aaa-855"
            " Fri Jul  7 15:07:00 2023 <===\n===== Output from /usr/bin/Aaa [] (PID=855) started Jul  7 15:06:11.606414 ===\n"
            "EntityManager::doBackoff waiting for remote sysdb version ....ok\n\n===> /var/log/agents/Acl-830"
            " Fri Jul  7 15:07:00 2023 <===\n===== Output from /usr/bin/Acl [] (PID=830) started Jul  7 15:06:10.871700 ===\n"
            "EntityManager::doBackoff waiting for remote sysdb version ...................ok\n"
        ],
        "expected": {
            "result": AntaTestStatus.FAILURE,
            "messages": [
                "Device has reported agent crashes:\n * /var/log/agents/Test-666 Thu May  4 09:57:02 2023\n"
                " * /var/log/agents/Aaa-855 Fri Jul  7 15:07:00 2023\n * /var/log/agents/Acl-830 Fri Jul  7 15:07:00 2023"
            ],
        },
    },
    (VerifyCPUUtilization, "success"): {
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
        "expected": {"result": AntaTestStatus.SUCCESS},
    },
    (VerifyCPUUtilization, "failure"): {
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
        "expected": {"result": AntaTestStatus.FAILURE, "messages": ["Device has reported a high CPU utilization -  Expected: < 75% Actual: 75.2%"]},
    },
    (VerifyMemoryUtilization, "success"): {
        "eos_data": [
            {"uptime": 1994.67, "modelName": "vEOS-lab", "internalVersion": "4.27.3F-26379303.4273F", "memTotal": 2004568, "memFree": 879004, "version": "4.27.3F"}
        ],
        "expected": {"result": AntaTestStatus.SUCCESS},
    },
    (VerifyMemoryUtilization, "failure"): {
        "eos_data": [
            {"uptime": 1994.67, "modelName": "vEOS-lab", "internalVersion": "4.27.3F-26379303.4273F", "memTotal": 2004568, "memFree": 89004, "version": "4.27.3F"}
        ],
        "expected": {"result": AntaTestStatus.FAILURE, "messages": ["Device has reported a high memory usage - Expected: < 75% Actual: 95.56%"]},
    },
    (VerifyFileSystemUtilization, "success"): {
        "eos_data": [
            "Filesystem      Size  Used Avail Use% Mounted on\n/dev/sda2       3.9G  988M  2.9G  26% /mnt/flash\nnone            294M   78M  217M  27% /\n"
            "none            294M   78M  217M  27% /.overlay\n/dev/loop0      461M  461M     0 100% /rootfs-i386\n"
        ],
        "expected": {"result": AntaTestStatus.SUCCESS},
    },
    (VerifyFileSystemUtilization, "failure"): {
        "eos_data": [
            "Filesystem      Size  Used Avail Use% Mounted on\n/dev/sda2       3.9G  988M  2.9G  84% /mnt/flash\nnone            294M   78M  217M  27% /\n"
            "none            294M   78M  217M  84% /.overlay\n/dev/loop0      461M  461M     0 100% /rootfs-i386\n"
        ],
        "expected": {
            "result": AntaTestStatus.FAILURE,
            "messages": [
                "Mount point: /dev/sda2       3.9G  988M  2.9G  84% /mnt/flash - Higher disk space utilization - Expected: 75% Actual: 84%",
                "Mount point: none            294M   78M  217M  84% /.overlay - Higher disk space utilization - Expected: 75% Actual: 84%",
            ],
        },
    },
    (VerifyNTP, "success"): {"eos_data": ["synchronised\npoll interval unknown\n"], "expected": {"result": AntaTestStatus.SUCCESS}},
    (VerifyNTP, "failure"): {
        "eos_data": ["unsynchronised\npoll interval unknown\n"],
        "expected": {"result": AntaTestStatus.FAILURE, "messages": ["NTP status mismatch - Expected: synchronised Actual: unsynchronised"]},
    },
    (VerifyNTPAssociations, "success"): {
        "eos_data": [
            {
                "peers": {
                    "1.1.1.1": {"condition": "sys.peer", "peerIpAddr": "1.1.1.1", "stratumLevel": 1},
                    "2.2.2.2": {"condition": "candidate", "peerIpAddr": "2.2.2.2", "stratumLevel": 2},
                    "3.3.3.3": {"condition": "candidate", "peerIpAddr": "3.3.3.3", "stratumLevel": 2},
                }
            }
        ],
        "inputs": {
            "ntp_servers": [
                {"server_address": "1.1.1.1", "preferred": True, "stratum": 1},
                {"server_address": "2.2.2.2", "stratum": 2},
                {"server_address": "3.3.3.3", "stratum": 2},
            ]
        },
        "expected": {"result": AntaTestStatus.SUCCESS},
    },
    (VerifyNTPAssociations, "success-pool-name"): {
        "eos_data": [
            {
                "peers": {
                    "1.ntp.networks.com": {"condition": "sys.peer", "peerIpAddr": "1.1.1.1", "stratumLevel": 1},
                    "2.ntp.networks.com": {"condition": "candidate", "peerIpAddr": "2.2.2.2", "stratumLevel": 2},
                    "3.ntp.networks.com": {"condition": "candidate", "peerIpAddr": "3.3.3.3", "stratumLevel": 2},
                }
            }
        ],
        "inputs": {
            "ntp_servers": [
                {"server_address": "1.ntp.networks.com", "preferred": True, "stratum": 1},
                {"server_address": "2.ntp.networks.com", "stratum": 2},
                {"server_address": "3.ntp.networks.com", "stratum": 2},
            ]
        },
        "expected": {"result": AntaTestStatus.SUCCESS},
    },
    (VerifyNTPAssociations, "success-ntp-pool-as-input"): {
        "eos_data": [
            {
                "peers": {
                    "1.1.1.1": {"condition": "sys.peer", "peerIpAddr": "1.1.1.1", "stratumLevel": 1},
                    "2.2.2.2": {"condition": "candidate", "peerIpAddr": "2.2.2.2", "stratumLevel": 2},
                    "3.3.3.3": {"condition": "candidate", "peerIpAddr": "3.3.3.3", "stratumLevel": 2},
                }
            }
        ],
        "inputs": {"ntp_pool": {"server_addresses": ["1.1.1.1", "2.2.2.2", "3.3.3.3"], "preferred_stratum_range": [1, 2]}},
        "expected": {"result": AntaTestStatus.SUCCESS},
    },
    (VerifyNTPAssociations, "success-ntp-pool-hostname"): {
        "eos_data": [
            {
                "peers": {
                    "itsys-ntp010p.aristanetworks.com": {"condition": "sys.peer", "peerIpAddr": "1.1.1.1", "stratumLevel": 1},
                    "itsys-ntp011p.aristanetworks.com": {"condition": "candidate", "peerIpAddr": "2.2.2.2", "stratumLevel": 2},
                    "itsys-ntp012p.aristanetworks.com": {"condition": "candidate", "peerIpAddr": "3.3.3.3", "stratumLevel": 2},
                }
            }
        ],
        "inputs": {
            "ntp_pool": {
                "server_addresses": ["itsys-ntp010p.aristanetworks.com", "itsys-ntp011p.aristanetworks.com", "itsys-ntp012p.aristanetworks.com"],
                "preferred_stratum_range": [1, 2],
            }
        },
        "expected": {"result": AntaTestStatus.SUCCESS},
    },
    (VerifyNTPAssociations, "success-ip-dns"): {
        "eos_data": [
            {
                "peers": {
                    "1.1.1.1 (1.ntp.networks.com)": {"condition": "sys.peer", "peerIpAddr": "1.1.1.1", "stratumLevel": 1},
                    "2.2.2.2 (2.ntp.networks.com)": {"condition": "candidate", "peerIpAddr": "2.2.2.2", "stratumLevel": 2},
                    "3.3.3.3 (3.ntp.networks.com)": {"condition": "candidate", "peerIpAddr": "3.3.3.3", "stratumLevel": 2},
                }
            }
        ],
        "inputs": {
            "ntp_servers": [
                {"server_address": "1.1.1.1", "preferred": True, "stratum": 1},
                {"server_address": "2.2.2.2", "stratum": 2},
                {"server_address": "3.3.3.3", "stratum": 2},
            ]
        },
        "expected": {"result": AntaTestStatus.SUCCESS},
    },
    (VerifyNTPAssociations, "failure-ntp-server"): {
        "eos_data": [
            {
                "peers": {
                    "1.1.1.1": {"condition": "candidate", "peerIpAddr": "1.1.1.1", "stratumLevel": 2},
                    "2.2.2.2": {"condition": "sys.peer", "peerIpAddr": "2.2.2.2", "stratumLevel": 2},
                    "3.3.3.3": {"condition": "sys.peer", "peerIpAddr": "3.3.3.3", "stratumLevel": 3},
                }
            }
        ],
        "inputs": {
            "ntp_servers": [
                {"server_address": "1.1.1.1", "preferred": True, "stratum": 1},
                {"server_address": "2.2.2.2", "stratum": 2},
                {"server_address": "3.3.3.3", "stratum": 2},
            ]
        },
        "expected": {
            "result": AntaTestStatus.FAILURE,
            "messages": [
                "NTP Server: 1.1.1.1 Preferred: True Stratum: 1 - Incorrect condition - Expected: sys.peer Actual: candidate",
                "NTP Server: 1.1.1.1 Preferred: True Stratum: 1 - Incorrect stratum level - Expected: 1 Actual: 2",
                "NTP Server: 2.2.2.2 Preferred: False Stratum: 2 - Incorrect condition - Expected: candidate Actual: sys.peer",
                "NTP Server: 3.3.3.3 Preferred: False Stratum: 2 - Incorrect condition - Expected: candidate Actual: sys.peer",
                "NTP Server: 3.3.3.3 Preferred: False Stratum: 2 - Incorrect stratum level - Expected: 2 Actual: 3",
            ],
        },
    },
    (VerifyNTPAssociations, "failure-no-peers"): {
        "eos_data": [{"peers": {}}],
        "inputs": {
            "ntp_servers": [
                {"server_address": "1.1.1.1", "preferred": True, "stratum": 1},
                {"server_address": "2.2.2.2", "stratum": 1},
                {"server_address": "3.3.3.3", "stratum": 1},
            ]
        },
        "expected": {"result": AntaTestStatus.FAILURE, "messages": ["No NTP peers configured"]},
    },
    (VerifyNTPAssociations, "failure-one-peer-not-found"): {
        "eos_data": [
            {
                "peers": {
                    "1.1.1.1": {"condition": "sys.peer", "peerIpAddr": "1.1.1.1", "stratumLevel": 1},
                    "2.2.2.2": {"condition": "candidate", "peerIpAddr": "2.2.2.2", "stratumLevel": 1},
                }
            }
        ],
        "inputs": {
            "ntp_servers": [
                {"server_address": "1.1.1.1", "preferred": True, "stratum": 1},
                {"server_address": "2.2.2.2", "stratum": 1},
                {"server_address": "3.3.3.3", "stratum": 1},
            ]
        },
        "expected": {"result": AntaTestStatus.FAILURE, "messages": ["NTP Server: 3.3.3.3 Preferred: False Stratum: 1 - Not configured"]},
    },
    (VerifyNTPAssociations, "failure-with-two-peers-not-found"): {
        "eos_data": [{"peers": {"1.1.1.1": {"condition": "candidate", "peerIpAddr": "1.1.1.1", "stratumLevel": 1}}}],
        "inputs": {
            "ntp_servers": [
                {"server_address": "1.1.1.1", "preferred": True, "stratum": 1},
                {"server_address": "2.2.2.2", "stratum": 1},
                {"server_address": "3.3.3.3", "stratum": 1},
            ]
        },
        "expected": {
            "result": AntaTestStatus.FAILURE,
            "messages": [
                "NTP Server: 1.1.1.1 Preferred: True Stratum: 1 - Incorrect condition - Expected: sys.peer Actual: candidate",
                "NTP Server: 2.2.2.2 Preferred: False Stratum: 1 - Not configured",
                "NTP Server: 3.3.3.3 Preferred: False Stratum: 1 - Not configured",
            ],
        },
    },
    (VerifyNTPAssociations, "failure-ntp-pool-as-input"): {
        "eos_data": [
            {
                "peers": {
                    "ntp1.pool": {"condition": "sys.peer", "peerIpAddr": "1.1.1.1", "stratumLevel": 1},
                    "ntp2.pool": {"condition": "candidate", "peerIpAddr": "2.2.2.2", "stratumLevel": 2},
                    "ntp3.pool": {"condition": "candidate", "peerIpAddr": "3.3.3.3", "stratumLevel": 2},
                }
            }
        ],
        "inputs": {"ntp_pool": {"server_addresses": ["1.1.1.1", "2.2.2.2"], "preferred_stratum_range": [1, 2]}},
        "expected": {"result": AntaTestStatus.FAILURE, "messages": ["NTP Server: 3.3.3.3 Hostname: ntp3.pool - Associated but not part of the provided NTP pool"]},
    },
    (VerifyNTPAssociations, "failure-ntp-pool-as-input-bad-association"): {
        "eos_data": [
            {
                "peers": {
                    "ntp1.pool": {"condition": "sys.peer", "peerIpAddr": "1.1.1.1", "stratumLevel": 1},
                    "ntp2.pool": {"condition": "candidate", "peerIpAddr": "2.2.2.2", "stratumLevel": 2},
                    "ntp3.pool": {"condition": "reject", "peerIpAddr": "3.3.3.3", "stratumLevel": 3},
                }
            }
        ],
        "inputs": {"ntp_pool": {"server_addresses": ["1.1.1.1", "2.2.2.2", "3.3.3.3"], "preferred_stratum_range": [1, 2]}},
        "expected": {
            "result": AntaTestStatus.FAILURE,
            "messages": [
                "NTP Server: 3.3.3.3 Hostname: ntp3.pool - Incorrect condition  - Expected: sys.peer, candidate Actual: reject",
                "NTP Server: 3.3.3.3 Hostname: ntp3.pool - Incorrect stratum level - Expected Stratum Range: 1 to 2 Actual: 3",
            ],
        },
    },
    (VerifyNTPAssociations, "failure-ntp-pool-hostname"): {
        "eos_data": [
            {
                "peers": {
                    "itsys-ntp010p.aristanetworks.com": {"condition": "sys.peer", "peerIpAddr": "1.1.1.1", "stratumLevel": 5},
                    "itsys-ntp011p.aristanetworks.com": {"condition": "reject", "peerIpAddr": "2.2.2.2", "stratumLevel": 4},
                    "itsys-ntp012p.aristanetworks.com": {"condition": "candidate", "peerIpAddr": "3.3.3.3", "stratumLevel": 2},
                }
            }
        ],
        "inputs": {"ntp_pool": {"server_addresses": ["itsys-ntp010p.aristanetworks.com", "itsys-ntp011p.aristanetworks.com"], "preferred_stratum_range": [1, 2]}},
        "expected": {
            "result": AntaTestStatus.FAILURE,
            "messages": [
                "NTP Server: 1.1.1.1 Hostname: itsys-ntp010p.aristanetworks.com - Incorrect stratum level - Expected Stratum Range: 1 to 2 Actual: 5",
                "NTP Server: 2.2.2.2 Hostname: itsys-ntp011p.aristanetworks.com - Incorrect condition  - Expected: sys.peer, candidate Actual: reject",
                "NTP Server: 2.2.2.2 Hostname: itsys-ntp011p.aristanetworks.com - Incorrect stratum level - Expected Stratum Range: 1 to 2 Actual: 4",
                "NTP Server: 3.3.3.3 Hostname: itsys-ntp012p.aristanetworks.com - Associated but not part of the provided NTP pool",
            ],
        },
    },
    (VerifyMaintenance, "success-no-maintenance-configured"): {
        "eos_data": [{"units": {}, "interfaces": {}, "vrfs": {}, "warnings": ["Maintenance Mode is disabled."]}],
        "expected": {"result": AntaTestStatus.SUCCESS},
    },
    (VerifyMaintenance, "success-maintenance-configured-but-not-enabled"): {
        "eos_data": [
            {
                "units": {
                    "System": {
                        "state": "active",
                        "adminState": "active",
                        "stateChangeTime": 0.0,
                        "onBootMaintenance": False,
                        "intfsViolatingTrafficThreshold": False,
                        "aggInBpsRate": 0,
                        "aggOutBpsRate": 0,
                    }
                },
                "interfaces": {},
                "vrfs": {},
            }
        ],
        "expected": {"result": AntaTestStatus.SUCCESS},
    },
    (VerifyMaintenance, "success-multiple-units-but-not-enabled"): {
        "eos_data": [
            {
                "units": {
                    "mlag": {
                        "state": "active",
                        "adminState": "active",
                        "stateChangeTime": 0.0,
                        "onBootMaintenance": False,
                        "intfsViolatingTrafficThreshold": False,
                        "aggInBpsRate": 0,
                        "aggOutBpsRate": 0,
                    },
                    "System": {
                        "state": "active",
                        "adminState": "active",
                        "stateChangeTime": 0.0,
                        "onBootMaintenance": False,
                        "intfsViolatingTrafficThreshold": False,
                        "aggInBpsRate": 0,
                        "aggOutBpsRate": 0,
                    },
                },
                "interfaces": {},
                "vrfs": {},
            }
        ],
        "expected": {"result": AntaTestStatus.SUCCESS},
    },
    (VerifyMaintenance, "failure-maintenance-enabled"): {
        "eos_data": [
            {
                "units": {
                    "mlag": {
                        "state": "underMaintenance",
                        "adminState": "underMaintenance",
                        "stateChangeTime": 1741257120.9532886,
                        "onBootMaintenance": False,
                        "intfsViolatingTrafficThreshold": False,
                        "aggInBpsRate": 0,
                        "aggOutBpsRate": 0,
                    },
                    "System": {
                        "state": "active",
                        "adminState": "active",
                        "stateChangeTime": 0.0,
                        "onBootMaintenance": False,
                        "intfsViolatingTrafficThreshold": False,
                        "aggInBpsRate": 0,
                        "aggOutBpsRate": 0,
                    },
                },
                "interfaces": {},
                "vrfs": {},
            }
        ],
        "expected": {"result": AntaTestStatus.FAILURE, "messages": ["Units under maintenance: 'mlag'", "Possible causes: 'Quiesce is configured'"]},
    },
    (VerifyMaintenance, "failure-multiple-reasons"): {
        "eos_data": [
            {
                "units": {
                    "mlag": {
                        "state": "underMaintenance",
                        "adminState": "underMaintenance",
                        "stateChangeTime": 1741257120.9532895,
                        "onBootMaintenance": False,
                        "intfsViolatingTrafficThreshold": False,
                        "aggInBpsRate": 0,
                        "aggOutBpsRate": 0,
                    },
                    "System": {
                        "state": "maintenanceModeEnter",
                        "adminState": "underMaintenance",
                        "stateChangeTime": 1741257669.7231765,
                        "onBootMaintenance": False,
                        "intfsViolatingTrafficThreshold": False,
                        "aggInBpsRate": 0,
                        "aggOutBpsRate": 0,
                    },
                },
                "interfaces": {},
                "vrfs": {},
            }
        ],
        "expected": {
            "result": AntaTestStatus.FAILURE,
            "messages": ["Units under maintenance: 'mlag'", "Units entering maintenance: 'System'", "Possible causes: 'Quiesce is configured'"],
        },
    },
    (VerifyMaintenance, "failure-onboot-maintenance"): {
        "eos_data": [
            {
                "units": {
                    "System": {
                        "state": "underMaintenance",
                        "adminState": "underMaintenance",
                        "stateChangeTime": 1741258774.3756502,
                        "onBootMaintenance": True,
                        "intfsViolatingTrafficThreshold": False,
                        "aggInBpsRate": 0,
                        "aggOutBpsRate": 0,
                    }
                },
                "interfaces": {},
                "vrfs": {},
            }
        ],
        "expected": {
            "result": AntaTestStatus.FAILURE,
            "messages": ["Units under maintenance: 'System'", "Possible causes: 'On-boot maintenance is configured, Quiesce is configured'"],
        },
    },
    (VerifyMaintenance, "failure-entering-maintenance-interface-violation"): {
        "eos_data": [
            {
                "units": {
                    "System": {
                        "state": "maintenanceModeEnter",
                        "adminState": "underMaintenance",
                        "stateChangeTime": 1741257669.7231765,
                        "onBootMaintenance": False,
                        "intfsViolatingTrafficThreshold": True,
                        "aggInBpsRate": 0,
                        "aggOutBpsRate": 0,
                    }
                },
                "interfaces": {},
                "vrfs": {},
            }
        ],
        "expected": {
            "result": AntaTestStatus.FAILURE,
            "messages": ["Units entering maintenance: 'System'", "Possible causes: 'Interface traffic threshold violation, Quiesce is configured'"],
        },
    },
    (VerifyFAPLowLatency, "success"): {
        "eos_data": ["Fap0 diag d SCH_SLOW_SCALE_B_SSB 0 1:\nSCH_SLOW_SCALE_B_SSB.SCH0[0]: <SLOW_RATE=0x78e,MAX_BUCKET=1>\n\n"],
        "expected": {"result": AntaTestStatus.SUCCESS},
    },
    (VerifyFAPLowLatency, "failure"): {
        "eos_data": ["Fap0 diag d SCH_SLOW_SCALE_B_SSB 0 1:\nSCH_SLOW_SCALE_B_SSB.SCH0[0]: <SLOW_RATE=0x987,MAX_BUCKET=1>\n\n"],
        "expected": {"result": AntaTestStatus.FAILURE, "messages": ["Fap: Fap0 Core: 0 - Register mismatch - Expected: 0x78e Actual: 0x987"]},
    },
    (VerifyFAPLowLatency, "failure-multiple-fap"): {
        "eos_data": [
            "Fap10/0 diag d SCH_SLOW_SCALE_B_SSB 0 1:\nSCH_SLOW_SCALE_B_SSB.SCH0[0]: <SLOW_RATE=0x987,MAX_BUCKET=1>\n\nSCH_SLOW_SCALE_B_SSB.SCH1[0]: "
            "<SLOW_RATE=0x987,MAX_BUCKET=1>\n\nFap10/1 diag d SCH_SLOW_SCALE_B_SSB 0 1:\nSCH_SLOW_SCALE_B_SSB.SCH0[0]: <SLOW_RATE=0x987,MAX_BUCKET=1>"
            "\n\nSCH_SLOW_SCALE_B_SSB.SCH1[0]: <SLOW_RATE=0x987,MAX_BUCKET=1>\n\nFap11/0 diag d SCH_SLOW_SCALE_B_SSB 0 1:\nSCH_SLOW_SCALE_B_SSB.SCH0[0]:"
            " <SLOW_RATE=0x987,MAX_BUCKET=1>\n\nSCH_SLOW_SCALE_B_SSB.SCH1[0]: <SLOW_RATE=0x987,MAX_BUCKET=1>\n\nFap11/1 diag d SCH_SLOW_SCALE_B_SSB 0 1:"
            "\nSCH_SLOW_SCALE_B_SSB.SCH0[0]: <SLOW_RATE=0x987,MAX_BUCKET=1>\n\nSCH_SLOW_SCALE_B_SSB.SCH1[0]: <SLOW_RATE=0x987,MAX_BUCKET=1>\n\n"
        ],
        "expected": {
            "result": AntaTestStatus.FAILURE,
            "messages": [
                "Fap: Fap10/0 Core: 0 - Register mismatch - Expected: 0x78e Actual: 0x987",
                "Fap: Fap10/0 Core: 1 - Register mismatch - Expected: 0x78e Actual: 0x987",
                "Fap: Fap10/1 Core: 0 - Register mismatch - Expected: 0x78e Actual: 0x987",
                "Fap: Fap10/1 Core: 1 - Register mismatch - Expected: 0x78e Actual: 0x987",
                "Fap: Fap11/0 Core: 0 - Register mismatch - Expected: 0x78e Actual: 0x987",
                "Fap: Fap11/0 Core: 1 - Register mismatch - Expected: 0x78e Actual: 0x987",
                "Fap: Fap11/1 Core: 0 - Register mismatch - Expected: 0x78e Actual: 0x987",
                "Fap: Fap11/1 Core: 1 - Register mismatch - Expected: 0x78e Actual: 0x987",
            ],
        },
    },
}
