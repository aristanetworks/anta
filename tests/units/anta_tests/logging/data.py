"""Data for testing anta.tests.logging"""

from typing import Any, Dict, List

INPUT_LOGGING_PERSISTENT: List[Dict[str, Any]] = [
    {
        "name": "success",
        "eos_data": [
            "Persistent logging: level debugging\n",
            """Directory of flash:/persist/messages

                   -rw-        9948           May 10 13:54  messages

            33214693376 bytes total (10081136640 bytes free)

            """
        ],
        "side_effect": None,
        "expected_result": "success",
        "expected_messages": []
    },
    {
        "name": "failure-disabled",
        "eos_data": [
            "Persistent logging: disabled\n",
            """Directory of flash:/persist/messages

                   -rw-           0           Apr 13 16:29  messages

            33214693376 bytes total (10082168832 bytes free)

            """
        ],
        "side_effect": None,
        "expected_result": "failure",
        "expected_messages": ["Persistent logging is disabled"]
    },
    {
        "name": "failure-not-saved",
        "eos_data": [
            "Persistent logging: level debugging\n",
            """Directory of flash:/persist/messages

                   -rw-           0           Apr 13 16:29  messages

            33214693376 bytes total (10082168832 bytes free)

            """
        ],
        "side_effect": None,
        "expected_result": "failure",
        "expected_messages": ["No persistent logs are saved in flash"]
    },
]

INPUT_LOGGING_SOURCE_INTF: List[Dict[str, Any]] = [
    {
        "name": "success",
        "eos_data": [
            """Trap logging: level informational
                Logging source-interface 'Management0', IP Address 172.20.20.12 in VRF MGMT
                Logging to '10.22.10.92' port 514 in VRF MGMT via udp
                Logging to '10.22.10.93' port 514 in VRF MGMT via tcp
                Logging to '10.22.10.94' port 911 in VRF MGMT via udp

                """
        ],
        "side_effect": ("Management0", "MGMT"),
        "expected_result": "success",
        "expected_messages": []
    },
    {
        "name": "failure-intf",
        "eos_data": [
            """Trap logging: level informational
                Logging source-interface 'Management1', IP Address 172.20.20.12 in VRF MGMT
                Logging to '10.22.10.92' port 514 in VRF MGMT via udp
                Logging to '10.22.10.93' port 514 in VRF MGMT via tcp
                Logging to '10.22.10.94' port 911 in VRF MGMT via udp

                """
        ],
        "side_effect": ("Management0", "MGMT"),
        "expected_result": "failure",
        "expected_messages": ["Source-interface 'Management0' is not configured in VRF MGMT"]
    },
    {
        "name": "failure-vrf",
        "eos_data": [
            """Trap logging: level informational
                Logging source-interface 'Management0', IP Address 172.20.20.12 in VRF default
                Logging to '10.22.10.92' port 514 in VRF MGMT via udp
                Logging to '10.22.10.93' port 514 in VRF MGMT via tcp
                Logging to '10.22.10.94' port 911 in VRF MGMT via udp

                """
        ],
        "side_effect": ("Management0", "MGMT"),
        "expected_result": "failure",
        "expected_messages": ["Source-interface 'Management0' is not configured in VRF MGMT"]
    },
    {
        "name": "skipped-no-vrf",
        "eos_data": [""],
        "side_effect": ("Management0", None),
        "expected_result": "skipped",
        "expected_messages": ["VerifyLoggingSourceInt did not run because intf or vrf was not supplied"]
    },
    {
        "name": "skipped-no-intf",
        "eos_data": [""],
        "side_effect": (None, "MGMT"),
        "expected_result": "skipped",
        "expected_messages": ["VerifyLoggingSourceInt did not run because intf or vrf was not supplied"]
    },
]

INPUT_LOGGING_HOSTS: List[Dict[str, Any]] = [
    {
        "name": "success",
        "eos_data": [
            """Trap logging: level informational
                Logging source-interface 'Management0', IP Address 172.20.20.12 in VRF MGMT
                Logging to '10.22.10.92' port 514 in VRF MGMT via udp
                Logging to '10.22.10.93' port 514 in VRF MGMT via tcp
                Logging to '10.22.10.94' port 911 in VRF MGMT via udp

                """
        ],
        "side_effect": (["10.22.10.92", "10.22.10.93", "10.22.10.94"], "MGMT"),
        "expected_result": "success",
        "expected_messages": []
    },
    {
        "name": "failure-hosts",
        "eos_data": [
            """Trap logging: level informational
                Logging source-interface 'Management1', IP Address 172.20.20.12 in VRF MGMT
                Logging to '10.22.10.92' port 514 in VRF MGMT via udp
                Logging to '10.22.10.103' port 514 in VRF MGMT via tcp
                Logging to '10.22.10.104' port 911 in VRF MGMT via udp

                """
        ],
        "side_effect": (["10.22.10.92", "10.22.10.93", "10.22.10.94"], "MGMT"),
        "expected_result": "failure",
        "expected_messages": ["Syslog servers ['10.22.10.93', '10.22.10.94'] are not configured in VRF MGMT"]
    },
    {
        "name": "failure-vrf",
        "eos_data": [
            """Trap logging: level informational
                Logging source-interface 'Management0', IP Address 172.20.20.12 in VRF MGMT
                Logging to '10.22.10.92' port 514 in VRF MGMT via udp
                Logging to '10.22.10.93' port 514 in VRF default via tcp
                Logging to '10.22.10.94' port 911 in VRF default via udp

                """
        ],
        "side_effect": (["10.22.10.92", "10.22.10.93", "10.22.10.94"], "MGMT"),
        "expected_result": "failure",
        "expected_messages": ["Syslog servers ['10.22.10.93', '10.22.10.94'] are not configured in VRF MGMT"]
    },
    {
        "name": "skipped-no-vrf",
        "eos_data": [""],
        "side_effect": (["10.22.10.92", "10.22.10.93", "10.22.10.94"], None),
        "expected_result": "skipped",
        "expected_messages": ["VerifyLoggingHosts did not run because hosts or vrf were not supplied"]
    },
    {
        "name": "skipped-no-hosts",
        "eos_data": [""],
        "side_effect": (None, "MGMT"),
        "expected_result": "skipped",
        "expected_messages": ["VerifyLoggingHosts did not run because hosts or vrf were not supplied"]
    },
]

INPUT_LOGGING_LOGS_GEN: List[Dict[str, Any]] = [
    {
        "name": "success",
        "eos_data": [
            "",
            "2023-05-10T13:54:21.463497-05:00 NW-CORE.example.org ConfigAgent: %SYS-6-LOGMSG_INFO: "
            "Message from arista on command-api (10.22.1.107): ANTA VerifyLoggingLogsGeneration validation\n"
        ],
        "side_effect": None,
        "expected_result": "success",
        "expected_messages": []
    },
    {
        "name": "failure",
        "eos_data": [
            "",
            "Log Buffer:\n"
        ],
        "side_effect": None,
        "expected_result": "failure",
        "expected_messages": ["Logs are not generated"]
    },
]

INPUT_LOGGING_HOSTNAME: List[Dict[str, Any]] = [
    {
        "name": "success",
        "eos_data": [
            {
               "hostname": "NW-CORE",
               "fqdn": "NW-CORE.example.org"
            },
            "",
            "2023-05-10T15:41:44.701810-05:00 NW-CORE.example.org ConfigAgent: %SYS-6-LOGMSG_INFO: "
            "Message from arista on command-api (10.22.1.107): ANTA VerifyLoggingHostname validation\n"
        ],
        "side_effect": None,
        "expected_result": "success",
        "expected_messages": []
    },
    {
        "name": "failure",
        "eos_data": [
            {
               "hostname": "NW-CORE",
               "fqdn": "NW-CORE.example.org"
            },
            "",
            "2023-05-10T13:54:21.463497-05:00 NW-CORE ConfigAgent: %SYS-6-LOGMSG_INFO: "
            "Message from arista on command-api (10.22.1.107): ANTA VerifyLoggingLogsHostname validation\n"
        ],
        "side_effect": None,
        "expected_result": "failure",
        "expected_messages": ["Logs are not generated with the device FQDN"]
    },
]

INPUT_LOGGING_TIMESTAMP: List[Dict[str, Any]] = [
    {
        "name": "success",
        "eos_data": [
            "",
            "2023-05-10T15:41:44.680813-05:00 NW-CORE.example.org ConfigAgent: %SYS-6-LOGMSG_INFO: "
            "Message from arista on command-api (10.22.1.107): ANTA VerifyLoggingTimestamp validation\n"
        ],
        "side_effect": None,
        "expected_result": "success",
        "expected_messages": []
    },
    {
        "name": "failure",
        "eos_data": [
            "",
            "May 10 13:54:22 NE-CORE.example.org ConfigAgent: %SYS-6-LOGMSG_INFO: "
            "Message from arista on command-api (10.22.1.107): ANTA VerifyLoggingTimestamp validation\n"
        ],
        "side_effect": None,
        "expected_result": "failure",
        "expected_messages": ["Logs are not generated with the appropriate timestamp format"]
    },
]


INPUT_LOGGING_ACCOUNTING: List[Dict[str, Any]] = [
    {
        "name": "success",
        "eos_data": [
            "2023 May 10 15:50:31 arista   command-api 10.22.1.107     stop   service=shell priv-lvl=15 cmd=show aaa accounting logs | tail\n"
        ],
        "side_effect": None,
        "expected_result": "success",
        "expected_messages": []
    },
    {
        "name": "failure",
        "eos_data": [
            "2023 May 10 15:52:26 arista   vty14       10.22.1.107     stop   service=shell priv-lvl=15 cmd=show bgp summary\n"
        ],
        "side_effect": None,
        "expected_result": "failure",
        "expected_messages": ["AAA accounting logs are not generated"]
    },
]
