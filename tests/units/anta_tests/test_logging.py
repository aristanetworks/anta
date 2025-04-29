# Copyright (c) 2023-2025 Arista Networks, Inc.
# Use of this source code is governed by the Apache License 2.0
# that can be found in the LICENSE file.
"""Data for testing anta.tests.logging."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, TypeAlias

from anta.models import AntaTest
from anta.tests.logging import (
    VerifyLoggingAccounting,
    VerifyLoggingEntries,
    VerifyLoggingErrors,
    VerifyLoggingHostname,
    VerifyLoggingHosts,
    VerifyLoggingLogsGeneration,
    VerifyLoggingPersistent,
    VerifyLoggingSourceIntf,
    VerifyLoggingTimestamp,
    VerifySyslogLogging,
)
from tests.units.anta_tests import AntaUnitTest, test

AntaUnitTestDataDict: TypeAlias = dict[tuple[type[AntaTest], str], AntaUnitTest]

DATA: AntaUnitTestDataDict = {
    (VerifyLoggingPersistent, "success"): {
        "eos_data": [
            "Persistent logging: level debugging\n",
            "Directory of flash:/persist/messages\n\n                   -rw-        9948           May 10 13:54  messages\n\n"
            "            33214693376 bytes total (10081136640 bytes free)\n\n            ",
        ],
        "inputs": None,
        "expected": {"result": "success"},
    },
    (VerifyLoggingPersistent, "failure-disabled"): {
        "eos_data": [
            "Persistent logging: disabled\n",
            "Directory of flash:/persist/messages\n\n                   -rw-           0           Apr 13 16:29  messages\n\n"
            "            33214693376 bytes total (10082168832 bytes free)\n\n            ",
        ],
        "inputs": None,
        "expected": {"result": "failure", "messages": ["Persistent logging is disabled"]},
    },
    (VerifyLoggingPersistent, "failure-not-saved"): {
        "eos_data": [
            "Persistent logging: level debugging\n",
            "Directory of flash:/persist/messages\n\n                   -rw-           0           Apr 13 16:29  messages\n\n"
            "            33214693376 bytes total (10082168832 bytes free)\n\n            ",
        ],
        "inputs": None,
        "expected": {"result": "failure", "messages": ["No persistent logs are saved in flash"]},
    },
    (VerifyLoggingSourceIntf, "success"): {
        "eos_data": [
            "Trap logging: level informational\n                Logging source-interface 'Management0', IP Address 172.20.20.12 in VRF MGMT\n"
            "                Logging to '10.22.10.92' port 514 in VRF MGMT via udp\n                Logging to '10.22.10.93' port 514 in VRF MGMT via tcp\n"
            "                Logging to '10.22.10.94' port 911 in VRF MGMT via udp\n\n                "
        ],
        "inputs": {"interface": "Management0", "vrf": "MGMT"},
        "expected": {"result": "success"},
    },
    (VerifyLoggingSourceIntf, "failure-intf"): {
        "eos_data": [
            "Trap logging: level informational\n                Logging source-interface 'Management1', IP Address 172.20.20.12 in VRF MGMT\n"
            "                Logging to '10.22.10.92' port 514 in VRF MGMT via udp\n                Logging to '10.22.10.93' port 514 in VRF MGMT via tcp\n"
            "                Logging to '10.22.10.94' port 911 in VRF MGMT via udp\n\n                "
        ],
        "inputs": {"interface": "Management0", "vrf": "MGMT"},
        "expected": {"result": "failure", "messages": ["Source-interface: Management0 VRF: MGMT - Not configured"]},
    },
    (VerifyLoggingSourceIntf, "failure-vrf"): {
        "eos_data": [
            "Trap logging: level informational\n                Logging source-interface 'Management0', IP Address 172.20.20.12 in VRF default\n"
            "                Logging to '10.22.10.92' port 514 in VRF MGMT via udp\n                Logging to '10.22.10.93' port 514 in VRF MGMT via tcp\n"
            "                Logging to '10.22.10.94' port 911 in VRF MGMT via udp\n\n                "
        ],
        "inputs": {"interface": "Management0", "vrf": "MGMT"},
        "expected": {"result": "failure", "messages": ["Source-interface: Management0 VRF: MGMT - Not configured"]},
    },
    (VerifyLoggingHosts, "success"): {
        "eos_data": [
            "Trap logging: level informational\n                Logging source-interface 'Management0', IP Address 172.20.20.12 in VRF MGMT\n"
            "                Logging to '10.22.10.92' port 514 in VRF MGMT via udp\n                Logging to '10.22.10.93' port 514 in VRF MGMT via tcp\n"
            "                Logging to '10.22.10.94' port 911 in VRF MGMT via udp\n\n                "
        ],
        "inputs": {"hosts": ["10.22.10.92", "10.22.10.93", "10.22.10.94"], "vrf": "MGMT"},
        "expected": {"result": "success"},
    },
    (VerifyLoggingHosts, "failure-hosts"): {
        "eos_data": [
            "Trap logging: level informational\n                Logging source-interface 'Management1', IP Address 172.20.20.12 in VRF MGMT\n"
            "                Logging to '10.22.10.92' port 514 in VRF MGMT via udp\n                Logging to '10.22.10.103' port 514 in VRF MGMT via tcp\n"
            "                Logging to '10.22.10.104' port 911 in VRF MGMT via udp\n\n                "
        ],
        "inputs": {"hosts": ["10.22.10.92", "10.22.10.93", "10.22.10.94"], "vrf": "MGMT"},
        "expected": {"result": "failure", "messages": ["Syslog servers 10.22.10.93, 10.22.10.94 are not configured in VRF MGMT"]},
    },
    (VerifyLoggingHosts, "failure-vrf"): {
        "eos_data": [
            "Trap logging: level informational\n                Logging source-interface 'Management0', IP Address 172.20.20.12 in VRF MGMT\n"
            "                Logging to '10.22.10.92' port 514 in VRF MGMT via udp\n                Logging to '10.22.10.93' port 514 in VRF default via tcp\n"
            "                Logging to '10.22.10.94' port 911 in VRF default via udp\n\n                "
        ],
        "inputs": {"hosts": ["10.22.10.92", "10.22.10.93", "10.22.10.94"], "vrf": "MGMT"},
        "expected": {"result": "failure", "messages": ["Syslog servers 10.22.10.93, 10.22.10.94 are not configured in VRF MGMT"]},
    },
    (VerifyLoggingLogsGeneration, "success"): {
        "eos_data": [
            "",
            "2023-05-10T13:54:21.463497-05:00 NW-CORE.example.org ConfigAgent: %SYS-6-LOGMSG_INFO: Message from arista on command-api (10.22.1.107):"
            " ANTA VerifyLoggingLogsGeneration validation\n",
        ],
        "inputs": {"severity_level": "informational"},
        "expected": {"result": "success"},
    },
    (VerifyLoggingLogsGeneration, "failure"): {
        "eos_data": ["", "Log Buffer:\n"],
        "inputs": {"severity_level": "notifications"},
        "expected": {"result": "failure", "messages": ["Logs are not generated"]},
    },
    (VerifyLoggingHostname, "success"): {
        "eos_data": [
            {"hostname": "NW-CORE", "fqdn": "NW-CORE.example.org"},
            "",
            "2023-05-10T15:41:44.701810-05:00 NW-CORE.example.org ConfigAgent: %SYS-6-LOGMSG_INFO: Message from arista on command-api (10.22.1.107):"
            " ANTA VerifyLoggingHostname validation\n",
        ],
        "inputs": {"severity_level": "informational"},
        "expected": {"result": "success"},
    },
    (VerifyLoggingHostname, "failure"): {
        "eos_data": [
            {"hostname": "NW-CORE", "fqdn": "NW-CORE.example.org"},
            "",
            "2023-05-10T13:54:21.463497-05:00 NW-CORE ConfigAgent: %SYS-6-LOGMSG_NOTICE: Message from arista on command-api (10.22.1.107):"
            " ANTA VerifyLoggingLogsHostname validation\n",
        ],
        "inputs": {"severity_level": "notifications"},
        "expected": {"result": "failure", "messages": ["Logs are not generated with the device FQDN"]},
    },
    (VerifyLoggingTimestamp, "success-negative-offset"): {
        "eos_data": [
            "",
            "2023-05-10T15:41:44.680813-05:00 NW-CORE.example.org ConfigAgent: %SYS-6-LOGMSG_INFO: Message from arista on command-api (10.22.1.107):"
            " ANTA VerifyLoggingTimestamp validation\n2023-05-10T15:42:44.680813-05:00 NW-CORE.example.org ConfigAgent: %SYS-6-LOGMSG_INFO: Other log\n",
        ],
        "inputs": {"severity_level": "informational"},
        "expected": {"result": "success"},
    },
    (VerifyLoggingTimestamp, "success-positive-offset"): {
        "eos_data": [
            "",
            "2023-05-10T15:41:44.680813+05:00 NW-CORE.example.org ConfigAgent: %SYS-6-LOGMSG_INFO: Message from arista on command-api (10.22.1.107):"
            " ANTA VerifyLoggingTimestamp validation\n2023-05-10T15:42:44.680813+05:00 NW-CORE.example.org ConfigAgent: %SYS-6-LOGMSG_INFO: Other log\n",
        ],
        "inputs": {"severity_level": "informational"},
        "expected": {"result": "success"},
    },
    (VerifyLoggingTimestamp, "failure"): {
        "eos_data": [
            "",
            "May 10 13:54:22 NE-CORE.example.org ConfigAgent: %SYS-6-LOGMSG_ALERT: Message from arista on command-api (10.22.1.107):"
            " ANTA VerifyLoggingTimestamp validation\n",
        ],
        "inputs": {"severity_level": "alerts"},
        "expected": {"result": "failure", "messages": ["Logs are not generated with the appropriate timestamp format"]},
    },
    (VerifyLoggingTimestamp, "failure-no-matching-log"): {
        "eos_data": ["", "May 10 13:54:22 NE-CORE.example.org ConfigAgent: %SYS-6-LOGMSG_NOTICE: Message from arista on command-api (10.22.1.107): BLAH\n"],
        "inputs": {"severity_level": "notifications"},
        "expected": {"result": "failure", "messages": ["Logs are not generated with the appropriate timestamp format"]},
    },
    (VerifyLoggingAccounting, "success"): {
        "eos_data": ["2023 May 10 15:50:31 arista   command-api 10.22.1.107     stop   service=shell priv-lvl=15 cmd=show aaa accounting logs | tail\n"],
        "inputs": None,
        "expected": {"result": "success"},
    },
    (VerifyLoggingAccounting, "failure"): {
        "eos_data": ["2023 May 10 15:52:26 arista   vty14       10.22.1.107     stop   service=shell priv-lvl=15 cmd=show bgp summary\n"],
        "inputs": None,
        "expected": {"result": "failure", "messages": ["AAA accounting logs are not generated"]},
    },
    (VerifyLoggingErrors, "success"): {"eos_data": [""], "inputs": None, "expected": {"result": "success"}},
    (VerifyLoggingErrors, "failure"): {
        "eos_data": [
            "Aug  2 19:57:42 DC1-LEAF1A Mlag: %FWK-3-SOCKET_CLOSE_REMOTE: Connection to Mlag (pid:27200) at tbt://192.168.0.1:4432/+n closed by peer (EOF)"
        ],
        "inputs": None,
        "expected": {
            "result": "failure",
            "messages": [
                "Device has reported syslog messages with a severity of ERRORS or higher:\nAug  2 19:57:42 DC1-LEAF1A Mlag:"
                " %FWK-3-SOCKET_CLOSE_REMOTE: Connection to Mlag (pid:27200) at tbt://192.168.0.1:4432/+n closed by peer (EOF)"
            ],
        },
    },
    (VerifySyslogLogging, "success"): {
        "eos_data": [
            "Syslog logging: enabled\n            Buffer logging: level debugging\n\n            External configuration:\n                active:\n"
            "                inactive:\n\n            Facility                   Severity            Effective Severity\n"
            "            --------------------       -------------       ------------------\n            aaa                        debugging"
            "           debugging\n            accounting                 debugging           debugging"
        ],
        "inputs": None,
        "expected": {"result": "success"},
    },
    (VerifySyslogLogging, "failure"): {
        "eos_data": [
            "Syslog logging: disabled\n            Buffer logging: level debugging\n            Console logging: level errors\n"
            "            Persistent logging: disabled\n            Monitor logging: level errors\n\n            External configuration:\n"
            "                active:\n                inactive:\n\n            Facility                   Severity            Effective Severity\n"
            "            --------------------       -------------       ------------------\n            aaa                        debugging"
            "           debugging\n            accounting                 debugging           debugging"
        ],
        "inputs": None,
        "expected": {"result": "failure", "messages": ["Syslog logging is disabled"]},
    },
    (VerifyLoggingEntries, "success"): {
        "eos_data": [
            "Mar 13 04:10:45 s1-leaf1 ProcMgr: %PROCMGR-6-TERMINATE_RUNNING_PROCESS: Terminating deconfigured/reconfigured process 'SystemInitMonitor'"
            " (PID=859)\n Mar 13 04:10:45 s1-leaf1 ProcMgr: %PROCMGR-6-PROCESS_TERMINATED: 'SystemInitMonitor' (PID=859, status=9) has terminated.",
            "Mar 13 04:10:45 s1-leaf1 ProcMgr: %PROCMGR-7-WORKER_WARMSTART_DONE: ProcMgr worker warm start done. (PID=547)",
        ],
        "inputs": {
            "logging_entries": [
                {"regex_match": ".*PROCMGR-6-PROCESS_TERMINATED:.*", "last_number_messages": 3},
                {"regex_match": ".*ProcMgr worker warm start.*", "last_number_messages": 2, "severity_level": "debugging"},
            ]
        },
        "expected": {"result": "success"},
    },
    (VerifyLoggingEntries, "failure-log-str-not-found"): {
        "eos_data": [
            "Mar 12 04:34:01 s1-leaf1 ProcMgr: %PROCMGR-7-WORKER_WARMSTART_DONE: ProcMgr worker warm start done. (PID=559)\nMar 12 04:34:01 "
            "s1-leaf1 ProcMgr: %PROCMGR-6-PROCESS_TERMINATED: 'SystemInitMonitor' (PID=867, status=9) has terminated.",
            "Mar 13 03:58:12 s1-leaf1 ConfigAgent: %SYS-5-CONFIG_SESSION_ABORTED: User cvpsystem aborted\n             "
            "configuration session capiVerify-612-612b34a2ffbf11ef96ba3a348d538ba0 on TerminAttr (localhost)\n "
            "Mar 13 04:10:45 s1-leaf1 SystemInitMonitor: %SYS-5-SYSTEM_INITIALIZED: System is initialized",
        ],
        "inputs": {
            "logging_entries": [
                {"regex_match": ".ACCOUNTING-5-EXEC: cvpadmin ssh.", "last_number_messages": 3},
                {"regex_match": ".*ProcMgr worker warm start.*", "last_number_messages": 10, "severity_level": "debugging"},
            ]
        },
        "expected": {
            "result": "failure",
            "messages": [
                "Pattern: .ACCOUNTING-5-EXEC: cvpadmin ssh. - Not found in last 3 informational log entries",
                "Pattern: .*ProcMgr worker warm start.* - Not found in last 10 debugging log entries",
            ],
        },
    },
}
