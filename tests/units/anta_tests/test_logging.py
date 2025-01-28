# Copyright (c) 2023-2025 Arista Networks, Inc.
# Use of this source code is governed by the Apache License 2.0
# that can be found in the LICENSE file.
"""Data for testing anta.tests.logging."""

from __future__ import annotations

from typing import Any

from anta.tests.logging import (
    VerifyLoggingAccounting,
    VerifyLoggingErrors,
    VerifyLoggingHostname,
    VerifyLoggingHosts,
    VerifyLoggingLogsGeneration,
    VerifyLoggingPersistent,
    VerifyLoggingSourceIntf,
    VerifyLoggingTimestamp,
    VerifySyslogLogging,
)
from tests.units.anta_tests import test

DATA: list[dict[str, Any]] = [
    {
        "name": "success",
        "test": VerifyLoggingPersistent,
        "eos_data": [
            "Persistent logging: level debugging\n",
            """Directory of flash:/persist/messages

                   -rw-        9948           May 10 13:54  messages

            33214693376 bytes total (10081136640 bytes free)

            """,
        ],
        "inputs": None,
        "expected": {"result": "success"},
    },
    {
        "name": "failure-disabled",
        "test": VerifyLoggingPersistent,
        "eos_data": [
            "Persistent logging: disabled\n",
            """Directory of flash:/persist/messages

                   -rw-           0           Apr 13 16:29  messages

            33214693376 bytes total (10082168832 bytes free)

            """,
        ],
        "inputs": None,
        "expected": {"result": "failure", "messages": ["Persistent logging is disabled"]},
    },
    {
        "name": "failure-not-saved",
        "test": VerifyLoggingPersistent,
        "eos_data": [
            "Persistent logging: level debugging\n",
            """Directory of flash:/persist/messages

                   -rw-           0           Apr 13 16:29  messages

            33214693376 bytes total (10082168832 bytes free)

            """,
        ],
        "inputs": None,
        "expected": {"result": "failure", "messages": ["No persistent logs are saved in flash"]},
    },
    {
        "name": "success",
        "test": VerifyLoggingSourceIntf,
        "eos_data": [
            """Trap logging: level informational
                Logging source-interface 'Management0', IP Address 172.20.20.12 in VRF MGMT
                Logging to '10.22.10.92' port 514 in VRF MGMT via udp
                Logging to '10.22.10.93' port 514 in VRF MGMT via tcp
                Logging to '10.22.10.94' port 911 in VRF MGMT via udp

                """,
        ],
        "inputs": {"interface": "Management0", "vrf": "MGMT"},
        "expected": {"result": "success"},
    },
    {
        "name": "failure-intf",
        "test": VerifyLoggingSourceIntf,
        "eos_data": [
            """Trap logging: level informational
                Logging source-interface 'Management1', IP Address 172.20.20.12 in VRF MGMT
                Logging to '10.22.10.92' port 514 in VRF MGMT via udp
                Logging to '10.22.10.93' port 514 in VRF MGMT via tcp
                Logging to '10.22.10.94' port 911 in VRF MGMT via udp

                """,
        ],
        "inputs": {"interface": "Management0", "vrf": "MGMT"},
        "expected": {"result": "failure", "messages": ["Source-interface 'Management0' is not configured in VRF MGMT"]},
    },
    {
        "name": "failure-vrf",
        "test": VerifyLoggingSourceIntf,
        "eos_data": [
            """Trap logging: level informational
                Logging source-interface 'Management0', IP Address 172.20.20.12 in VRF default
                Logging to '10.22.10.92' port 514 in VRF MGMT via udp
                Logging to '10.22.10.93' port 514 in VRF MGMT via tcp
                Logging to '10.22.10.94' port 911 in VRF MGMT via udp

                """,
        ],
        "inputs": {"interface": "Management0", "vrf": "MGMT"},
        "expected": {"result": "failure", "messages": ["Source-interface 'Management0' is not configured in VRF MGMT"]},
    },
    {
        "name": "success",
        "test": VerifyLoggingHosts,
        "eos_data": [
            """Trap logging: level informational
                Logging source-interface 'Management0', IP Address 172.20.20.12 in VRF MGMT
                Logging to '10.22.10.92' port 514 in VRF MGMT via udp
                Logging to '10.22.10.93' port 514 in VRF MGMT via tcp
                Logging to '10.22.10.94' port 911 in VRF MGMT via udp

                """,
        ],
        "inputs": {"hosts": ["10.22.10.92", "10.22.10.93", "10.22.10.94"], "vrf": "MGMT"},
        "expected": {"result": "success"},
    },
    {
        "name": "failure-hosts",
        "test": VerifyLoggingHosts,
        "eos_data": [
            """Trap logging: level informational
                Logging source-interface 'Management1', IP Address 172.20.20.12 in VRF MGMT
                Logging to '10.22.10.92' port 514 in VRF MGMT via udp
                Logging to '10.22.10.103' port 514 in VRF MGMT via tcp
                Logging to '10.22.10.104' port 911 in VRF MGMT via udp

                """,
        ],
        "inputs": {"hosts": ["10.22.10.92", "10.22.10.93", "10.22.10.94"], "vrf": "MGMT"},
        "expected": {"result": "failure", "messages": ["Syslog servers ['10.22.10.93', '10.22.10.94'] are not configured in VRF MGMT"]},
    },
    {
        "name": "failure-vrf",
        "test": VerifyLoggingHosts,
        "eos_data": [
            """Trap logging: level informational
                Logging source-interface 'Management0', IP Address 172.20.20.12 in VRF MGMT
                Logging to '10.22.10.92' port 514 in VRF MGMT via udp
                Logging to '10.22.10.93' port 514 in VRF default via tcp
                Logging to '10.22.10.94' port 911 in VRF default via udp

                """,
        ],
        "inputs": {"hosts": ["10.22.10.92", "10.22.10.93", "10.22.10.94"], "vrf": "MGMT"},
        "expected": {"result": "failure", "messages": ["Syslog servers ['10.22.10.93', '10.22.10.94'] are not configured in VRF MGMT"]},
    },
    {
        "name": "success",
        "test": VerifyLoggingLogsGeneration,
        "eos_data": [
            "",
            "2023-05-10T13:54:21.463497-05:00 NW-CORE.example.org ConfigAgent: %SYS-6-LOGMSG_INFO: "
            "Message from arista on command-api (10.22.1.107): ANTA VerifyLoggingLogsGeneration validation\n",
        ],
        "inputs": {"severity_level": "informational"},
        "expected": {"result": "success"},
    },
    {
        "name": "failure",
        "test": VerifyLoggingLogsGeneration,
        "eos_data": ["", "Log Buffer:\n"],
        "inputs": {"severity_level": "notifications"},
        "expected": {"result": "failure", "messages": ["Logs are not generated"]},
    },
    {
        "name": "success",
        "test": VerifyLoggingHostname,
        "eos_data": [
            {"hostname": "NW-CORE", "fqdn": "NW-CORE.example.org"},
            "",
            "2023-05-10T15:41:44.701810-05:00 NW-CORE.example.org ConfigAgent: %SYS-6-LOGMSG_INFO: "
            "Message from arista on command-api (10.22.1.107): ANTA VerifyLoggingHostname validation\n",
        ],
        "inputs": {"severity_level": "informational"},
        "expected": {"result": "success"},
    },
    {
        "name": "failure",
        "test": VerifyLoggingHostname,
        "eos_data": [
            {"hostname": "NW-CORE", "fqdn": "NW-CORE.example.org"},
            "",
            "2023-05-10T13:54:21.463497-05:00 NW-CORE ConfigAgent: %SYS-6-LOGMSG_NOTICE: "
            "Message from arista on command-api (10.22.1.107): ANTA VerifyLoggingLogsHostname validation\n",
        ],
        "inputs": {"severity_level": "notifications"},
        "expected": {"result": "failure", "messages": ["Logs are not generated with the device FQDN"]},
    },
    {
        "name": "success-negative-offset",
        "test": VerifyLoggingTimestamp,
        "eos_data": [
            "",
            "2023-05-10T15:41:44.680813-05:00 NW-CORE.example.org ConfigAgent: %SYS-6-LOGMSG_INFO: "
            "Message from arista on command-api (10.22.1.107): ANTA VerifyLoggingTimestamp validation\n"
            "2023-05-10T15:42:44.680813-05:00 NW-CORE.example.org ConfigAgent: %SYS-6-LOGMSG_INFO: "
            "Other log\n",
        ],
        "inputs": {"severity_level": "informational"},
        "expected": {"result": "success"},
    },
    {
        "name": "success-positive-offset",
        "test": VerifyLoggingTimestamp,
        "eos_data": [
            "",
            "2023-05-10T15:41:44.680813+05:00 NW-CORE.example.org ConfigAgent: %SYS-6-LOGMSG_INFO: "
            "Message from arista on command-api (10.22.1.107): ANTA VerifyLoggingTimestamp validation\n"
            "2023-05-10T15:42:44.680813+05:00 NW-CORE.example.org ConfigAgent: %SYS-6-LOGMSG_INFO: "
            "Other log\n",
        ],
        "inputs": {"severity_level": "informational"},
        "expected": {"result": "success"},
    },
    {
        "name": "failure",
        "test": VerifyLoggingTimestamp,
        "eos_data": [
            "",
            "May 10 13:54:22 NE-CORE.example.org ConfigAgent: %SYS-6-LOGMSG_ALERT: "
            "Message from arista on command-api (10.22.1.107): ANTA VerifyLoggingTimestamp validation\n",
        ],
        "inputs": {"severity_level": "alerts"},
        "expected": {"result": "failure", "messages": ["Logs are not generated with the appropriate timestamp format"]},
    },
    {
        "name": "failure-no-matching-log",
        "test": VerifyLoggingTimestamp,
        "eos_data": [
            "",
            "May 10 13:54:22 NE-CORE.example.org ConfigAgent: %SYS-6-LOGMSG_NOTICE: Message from arista on command-api (10.22.1.107): BLAH\n",
        ],
        "inputs": {"severity_level": "notifications"},
        "expected": {"result": "failure", "messages": ["Logs are not generated with the appropriate timestamp format"]},
    },
    {
        "name": "success",
        "test": VerifyLoggingAccounting,
        "eos_data": ["2023 May 10 15:50:31 arista   command-api 10.22.1.107     stop   service=shell priv-lvl=15 cmd=show aaa accounting logs | tail\n"],
        "inputs": None,
        "expected": {"result": "success"},
    },
    {
        "name": "failure",
        "test": VerifyLoggingAccounting,
        "eos_data": ["2023 May 10 15:52:26 arista   vty14       10.22.1.107     stop   service=shell priv-lvl=15 cmd=show bgp summary\n"],
        "inputs": None,
        "expected": {"result": "failure", "messages": ["AAA accounting logs are not generated"]},
    },
    {
        "name": "success",
        "test": VerifyLoggingErrors,
        "eos_data": [""],
        "inputs": None,
        "expected": {"result": "success"},
    },
    {
        "name": "failure",
        "test": VerifyLoggingErrors,
        "eos_data": [
            "Aug  2 19:57:42 DC1-LEAF1A Mlag: %FWK-3-SOCKET_CLOSE_REMOTE: Connection to Mlag (pid:27200) at tbt://192.168.0.1:4432/+n closed by peer (EOF)",
        ],
        "inputs": None,
        "expected": {"result": "failure", "messages": ["Device has reported syslog messages with a severity of ERRORS or higher"]},
    },
    {
        "name": "success",
        "test": VerifySyslogLogging,
        "eos_data": [
            """Syslog logging: enabled
            Buffer logging: level debugging

            External configuration:
                active:
                inactive:

            Facility                   Severity            Effective Severity
            --------------------       -------------       ------------------
            aaa                        debugging           debugging
            accounting                 debugging           debugging""",
        ],
        "inputs": None,
        "expected": {"result": "success"},
    },
    {
        "name": "failure",
        "test": VerifySyslogLogging,
        "eos_data": [
            """Syslog logging: disabled
            Buffer logging: level debugging
            Console logging: level errors
            Persistent logging: disabled
            Monitor logging: level errors

            External configuration:
                active:
                inactive:

            Facility                   Severity            Effective Severity
            --------------------       -------------       ------------------
            aaa                        debugging           debugging
            accounting                 debugging           debugging""",
        ],
        "inputs": None,
        "expected": {"result": "failure", "messages": ["Syslog logging is disabled."]},
    },
]
