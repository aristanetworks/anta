"""Test inputs for anta.tests.hardware"""

from typing import Any, Dict, List

INPUT_INTERFACE_UTILIZATION: List[Dict[str, Any]] = [
    {
        "name": "success",
        "eos_data": [
            """Port      Name        Intvl   In Mbps      %  In Kpps  Out Mbps      % Out Kpps
Et1                    5:00       0.0   0.0%        0       0.0   0.0%        0
Et4                    5:00       0.0   0.0%        0       0.0   0.0%        0
"""
        ],
        "side_effect": [],
        "expected_result": "success",
        "expected_messages": [],
    },
    {
        "name": "failure",
        "eos_data": [
            """Port      Name        Intvl   In Mbps      %  In Kpps  Out Mbps      % Out Kpps
Et1                    5:00       0.0   0.0%        0       0.0  80.0%        0
Et4                    5:00       0.0  99.9%        0       0.0   0.0%        0
"""
        ],
        "side_effect": [],
        "expected_result": "failure",
        "expected_messages": ["The following interfaces have a usage > 75%: {'Et1': '80.0%', 'Et4': '99.9%'}"],
    },
]

INPUT_INTERFACE_ERRORS: List[Dict[str, Any]] = [
    {
        "name": "success",
        "eos_data": [
            {
                "interfaceErrorCounters": {
                    "Ethernet1": {"inErrors": 0, "frameTooLongs": 0, "outErrors": 0, "frameTooShorts": 0, "fcsErrors": 0, "alignmentErrors": 0, "symbolErrors": 0},
                    "Ethernet6": {"inErrors": 0, "frameTooLongs": 0, "outErrors": 0, "frameTooShorts": 0, "fcsErrors": 0, "alignmentErrors": 0, "symbolErrors": 0},
                }
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
                "interfaceErrorCounters": {
                    "Ethernet1": {"inErrors": 42, "frameTooLongs": 0, "outErrors": 0, "frameTooShorts": 0, "fcsErrors": 0, "alignmentErrors": 0, "symbolErrors": 0},
                    "Ethernet6": {"inErrors": 0, "frameTooLongs": 0, "outErrors": 0, "frameTooShorts": 0, "fcsErrors": 0, "alignmentErrors": 666, "symbolErrors": 0},
                }
            }
        ],
        "side_effect": [],
        "expected_result": "failure",
        "expected_messages": [
            "The following interfaces have non 0 error counter(s): [{'Ethernet1': {'inErrors': 42, 'frameTooLongs': 0, 'outErrors': 0, 'frameTooShorts': 0,"
            " 'fcsErrors': 0, 'alignmentErrors': 0, 'symbolErrors': 0}}, {'Ethernet6': {'inErrors': 0, 'frameTooLongs': 0, 'outErrors': 0, 'frameTooShorts':"
            " 0, 'fcsErrors': 0, 'alignmentErrors': 666, 'symbolErrors': 0}}]"
        ],
    },
]


INPUT_INTERFACE_DISCARDS: List[Dict[str, Any]] = [
    {
        "name": "success",
        "eos_data": [
            {
                "inDiscardsTotal": 0,
                "interfaces": {
                    "Ethernet2": {"outDiscards": 0, "inDiscards": 0},
                    "Ethernet1": {"outDiscards": 0, "inDiscards": 0},
                },
                "outDiscardsTotal": 0,
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
                "inDiscardsTotal": 0,
                "interfaces": {
                    "Ethernet2": {"outDiscards": 42, "inDiscards": 0},
                    "Ethernet1": {"outDiscards": 0, "inDiscards": 42},
                },
                "outDiscardsTotal": 0,
            }
        ],
        "side_effect": [],
        "expected_result": "failure",
        "expected_messages": [
            "The following interfaces have non 0 discard counter(s): [{'Ethernet2': {'outDiscards': 42, 'inDiscards': 0}},"
            " {'Ethernet1': {'outDiscards': 0, 'inDiscards': 42}}]"
        ],
    },
]

INPUT_INTERFACE_ERR_DISABLED: List[Dict[str, Any]] = [
    {
        "name": "success",
        "eos_data": [
            {
                "interfaceStatuses": {
                    "Management1": {
                        "linkStatus": "connected",
                    },
                    "Ethernet8": {
                        "linkStatus": "connected",
                    },
                }
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
                "interfaceStatuses": {
                    "Management1": {
                        "linkStatus": "errdisabled",
                    },
                    "Ethernet8": {
                        "linkStatus": "errdisabled",
                    },
                }
            }
        ],
        "side_effect": [],
        "expected_result": "failure",
        "expected_messages": ["The following interfaces are in error disabled state: ['Management1', 'Ethernet8']"],
    },
]

INPUT_INTERFACES_STATUS: List[Dict[str, Any]] = [
    {
        "name": "success",
        "eos_data": [
            {
                "interfaceDescriptions": {
                    "Ethernet8": {"interfaceStatus": "up", "description": "", "lineProtocolStatus": "up"},
                    "Ethernet2": {"interfaceStatus": "up", "description": "", "lineProtocolStatus": "up"},
                    "Ethernet3": {"interfaceStatus": "up", "description": "", "lineProtocolStatus": "up"},
                }
            }
        ],
        "side_effect": 3,
        "expected_result": "success",
        "expected_messages": [],
    },
    {
        "name": "failure",
        "eos_data": [
            {
                "interfaceDescriptions": {
                    "Ethernet8": {"interfaceStatus": "up", "description": "", "lineProtocolStatus": "down"},
                    "Ethernet2": {"interfaceStatus": "up", "description": "", "lineProtocolStatus": "up"},
                    "Ethernet3": {"interfaceStatus": "up", "description": "", "lineProtocolStatus": "up"},
                }
            }
        ],
        "side_effect": 3,
        "expected_result": "failure",
        "expected_messages": ["Only 2, less than 3 Ethernet interfaces are UP/UP", "The following Ethernet interfaces are not UP/UP: ['Ethernet8']"],
    },
    {
        "name": "skipped",
        "eos_data": [
            {
                "interfaceDescriptions": {
                    "Management1": {"interfaceStatus": "up", "description": "", "lineProtocolStatus": "up"},
                    "Ethernet8": {"interfaceStatus": "up", "description": "", "lineProtocolStatus": "up"},
                    "Ethernet2": {"interfaceStatus": "up", "description": "", "lineProtocolStatus": "up"},
                    "Ethernet3": {"interfaceStatus": "up", "description": "", "lineProtocolStatus": "up"},
                }
            }
        ],
        "side_effect": -1,
        "expected_result": "skipped",
        "expected_messages": ["VerifyInterfacesStatus was not run as an invalid minimum value was given -1."],
    },
]

# TODO
# INPUT_STORM_CONTROL_DROPS: List[Dict[str, Any]] = [
#    {
#        "name": "success",
#        "eos_data": [
# DATA
#        ],
#        "side_effect": [],
#        "expected_result": "success",
#        "expected_messages": [],
#    },
#    {
#        "name": "failure",
#        "eos_data": [
# DATA
#        ],
#        "side_effect": [],
#        "expected_result": "failure",
#        "expected_messages": ["TODO"],
#    },
# ]

INPUT_PORT_CHANNELS: List[Dict[str, Any]] = [
    {
        "name": "success",
        "eos_data": [
            {
                "portChannels": {
                    "Port-Channel42": {
                        "recircFeature": [],
                        "maxWeight": 16,
                        "minSpeed": "0 gbps",
                        "rxPorts": {},
                        "currWeight": 0,
                        "minLinks": 0,
                        "inactivePorts": {},
                        "activePorts": {},
                        "inactiveLag": False,
                    }
                }
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
                "portChannels": {
                    "Port-Channel42": {
                        "recircFeature": [],
                        "maxWeight": 16,
                        "minSpeed": "0 gbps",
                        "rxPorts": {},
                        "currWeight": 0,
                        "minLinks": 0,
                        "inactivePorts": {"Ethernet8": {"reasonUnconfigured": "waiting for LACP response"}},
                        "activePorts": {},
                        "inactiveLag": False,
                    }
                }
            }
        ],
        "side_effect": [],
        "expected_result": "failure",
        "expected_messages": ["The following port-channels have inactive port(s): ['Port-Channel42']"],
    },
]
