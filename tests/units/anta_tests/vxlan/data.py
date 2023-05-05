"""Test inputs for anta.tests.vxlan"""

from typing import Any, Dict, List

INPUT_VXLAN_STATUS: List[Dict[str, Any]] = [
    {
        "name": "success",
        "eos_data": [
            {
                "interfaceDescriptions": {
                    "Vxlan1": {
                        "lineProtocolStatus": "up",
                        "interfaceStatus": "up"
                    }
                }
            }
        ],
        "side_effect": [],
        "expected_result": "success",
        "expected_messages": []
    },
    {
        "name": "skipped",
        "eos_data": [
            {
                "interfaceDescriptions": {
                    "Loopback0": {
                        "lineProtocolStatus": "up",
                        "interfaceStatus": "up"
                    }
                }
            }
        ],
        "side_effect": [],
        "expected_result": "skipped",
        "expected_messages": ["Vxlan1 interface is not configured"]
    },
    {
        "name": "failure",
        "eos_data": [
            {
                "interfaceDescriptions": {
                    "Vxlan1": {
                        "lineProtocolStatus": "down",
                        "interfaceStatus": "up"
                    }
                }
            }
        ],
        "side_effect": [],
        "expected_result": "failure",
        "expected_messages": ["Vxlan1 interface is down/up"]
    },
    {
        "name": "failure",
        "eos_data": [
            {
                "interfaceDescriptions": {
                    "Vxlan1": {
                        "lineProtocolStatus": "up",
                        "interfaceStatus": "down"
                    }
                }
            }
        ],
        "side_effect": [],
        "expected_result": "failure",
        "expected_messages": ["Vxlan1 interface is up/down"]
    },
    {
        "name": "failure",
        "eos_data": [
            {
                "interfaceDescriptions": {
                    "Vxlan1": {
                        "lineProtocolStatus": "down",
                        "interfaceStatus": "down"
                    }
                }
            }
        ],
        "side_effect": [],
        "expected_result": "failure",
        "expected_messages": ["Vxlan1 interface is down/down"]
    },
]

INPUT_VXLAN_CONFIG_SANITY: List[Dict[str, Any]] = [
    {
        "name": "success",
        "eos_data": [
            {
                "categories": {
                    "localVtep": {
                        "description": "Local VTEP Configuration Check",
                        "allCheckPass": True,
                        "detail": "",
                        "hasWarning": False,
                        "items": [
                            {
                                "name": "Loopback IP Address",
                                "checkPass": True,
                                "hasWarning": False,
                                "detail": ""
                            },
                            {
                                "name": "VLAN-VNI Map",
                                "checkPass": True,
                                "hasWarning": False,
                                "detail": ""
                            },
                            {
                                "name": "Flood List",
                                "checkPass": True,
                                "hasWarning": False,
                                "detail": ""
                            },
                            {
                                "name": "Routing",
                                "checkPass": True,
                                "hasWarning": False,
                                "detail": ""
                            },
                            {
                                "name": "VNI VRF ACL",
                                "checkPass": True,
                                "hasWarning": False,
                                "detail": ""
                            },
                            {
                                "name": "VRF-VNI Dynamic VLAN",
                                "checkPass": True,
                                "hasWarning": False,
                                "detail": ""
                            },
                            {
                                "name": "Decap VRF-VNI Map",
                                "checkPass": True,
                                "hasWarning": False,
                                "detail": ""
                            }
                        ]
                    },
                    "remoteVtep": {
                        "description": "Remote VTEP Configuration Check",
                        "allCheckPass": True,
                        "detail": "",
                        "hasWarning": False,
                        "items": [
                            {
                                "name": "Remote VTEP",
                                "checkPass": True,
                                "hasWarning": False,
                                "detail": ""
                            }
                        ]
                    },
                    "pd": {
                        "description": "Platform Dependent Check",
                        "allCheckPass": True,
                        "detail": "",
                        "hasWarning": False,
                        "items": [
                            {
                                "name": "VXLAN Bridging",
                                "checkPass": True,
                                "hasWarning": False,
                                "detail": ""
                            },
                            {
                                "name": "VXLAN Routing",
                                "checkPass": True,
                                "hasWarning": False,
                                "detail": "VXLAN Routing not enabled"
                            }
                        ]
                    },
                    "cvx": {
                        "description": "CVX Configuration Check",
                        "allCheckPass": True,
                        "detail": "",
                        "hasWarning": False,
                        "items": [
                            {
                                "name": "CVX Server",
                                "checkPass": True,
                                "hasWarning": False,
                                "detail": "Not in controller client mode"
                            }
                        ]
                    },
                    "mlag": {
                        "description": "MLAG Configuration Check",
                        "allCheckPass": True,
                        "detail": "Run 'show mlag config-sanity' to verify MLAG config",
                        "hasWarning": False,
                        "items": [
                            {
                                "name": "Peer VTEP IP",
                                "checkPass": True,
                                "hasWarning": False,
                                "detail": ""
                            },
                            {
                                "name": "MLAG VTEP IP",
                                "checkPass": True,
                                "hasWarning": False,
                                "detail": ""
                            },
                            {
                                "name": "Virtual VTEP IP",
                                "checkPass": True,
                                "hasWarning": False,
                                "detail": ""
                            },
                            {
                                "name": "Peer VLAN-VNI",
                                "checkPass": True,
                                "hasWarning": False,
                                "detail": ""
                            },
                            {
                                "name": "MLAG Inactive State",
                                "checkPass": True,
                                "hasWarning": False,
                                "detail": ""
                            }
                        ]
                    }
                },
                "warnings": []

            }
        ],
        "side_effect": [],
        "expected_result": "success",
        "expected_messages": []
    },
    {
        "name": "failure",
        "eos_data": [
            {

                "categories": {
                    "localVtep": {
                        "description": "Local VTEP Configuration Check",
                        "allCheckPass": False,
                        "detail": "",
                        "hasWarning": True,
                        "items": [
                            {
                                "name": "Loopback IP Address",
                                "checkPass": True,
                                "hasWarning": False,
                                "detail": ""
                            },
                            {
                                "name": "VLAN-VNI Map",
                                "checkPass": False,
                                "hasWarning": False,
                                "detail": "No VLAN-VNI mapping in Vxlan1"
                            },
                            {
                                "name": "Flood List",
                                "checkPass": False,
                                "hasWarning": True,
                                "detail": "No VXLAN VLANs in Vxlan1"
                            },
                            {
                                "name": "Routing",
                                "checkPass": True,
                                "hasWarning": False,
                                "detail": ""
                            },
                            {
                                "name": "VNI VRF ACL",
                                "checkPass": True,
                                "hasWarning": False,
                                "detail": ""
                            },
                            {
                                "name": "VRF-VNI Dynamic VLAN",
                                "checkPass": True,
                                "hasWarning": False,
                                "detail": ""
                            },
                            {
                                "name": "Decap VRF-VNI Map",
                                "checkPass": True,
                                "hasWarning": False,
                                "detail": ""
                            }
                        ]
                    },
                    "remoteVtep": {
                        "description": "Remote VTEP Configuration Check",
                        "allCheckPass": True,
                        "detail": "",
                        "hasWarning": False,
                        "items": [
                            {
                                "name": "Remote VTEP",
                                "checkPass": True,
                                "hasWarning": False,
                                "detail": ""
                            }
                        ]
                    },
                    "pd": {
                        "description": "Platform Dependent Check",
                        "allCheckPass": True,
                        "detail": "",
                        "hasWarning": False,
                        "items": [
                            {
                                "name": "VXLAN Bridging",
                                "checkPass": True,
                                "hasWarning": False,
                                "detail": ""
                            },
                            {
                                "name": "VXLAN Routing",
                                "checkPass": True,
                                "hasWarning": False,
                                "detail": "VXLAN Routing not enabled"
                            }
                        ]
                    },
                    "cvx": {
                        "description": "CVX Configuration Check",
                        "allCheckPass": True,
                        "detail": "",
                        "hasWarning": False,
                        "items": [
                            {
                                "name": "CVX Server",
                                "checkPass": True,
                                "hasWarning": False,
                                "detail": "Not in controller client mode"
                            }
                        ]
                    },
                    "mlag": {
                        "description": "MLAG Configuration Check",
                        "allCheckPass": True,
                        "detail": "Run 'show mlag config-sanity' to verify MLAG config",
                        "hasWarning": False,
                        "items": [
                            {
                                "name": "Peer VTEP IP",
                                "checkPass": True,
                                "hasWarning": False,
                                "detail": ""
                            },
                            {
                                "name": "MLAG VTEP IP",
                                "checkPass": True,
                                "hasWarning": False,
                                "detail": ""
                            },
                            {
                                "name": "Virtual VTEP IP",
                                "checkPass": True,
                                "hasWarning": False,
                                "detail": ""
                            },
                            {
                                "name": "Peer VLAN-VNI",
                                "checkPass": True,
                                "hasWarning": False,
                                "detail": ""
                            },
                            {
                                "name": "MLAG Inactive State",
                                "checkPass": True,
                                "hasWarning": False,
                                "detail": ""
                            }
                        ]
                    }
                },
                "warnings": [
                    "Your configuration contains warnings. This does not mean misconfigurations. But you may wish to re-check your configurations."
                ]

            }
        ],
        "side_effect": [],
        "expected_result": "failure",
        "expected_messages": ["Vxlan config sanity check is not passing: {'localVtep': {'description': 'Local VTEP Configuration Check', "
                              "'allCheckPass': False, 'detail': '', 'hasWarning': True, 'items': [{'name': 'Loopback IP Address', 'checkPass': True, "
                              "'hasWarning': False, 'detail': ''}, {'name': 'VLAN-VNI Map', 'checkPass': False, 'hasWarning': False, 'detail': "
                              "'No VLAN-VNI mapping in Vxlan1'}, {'name': 'Flood List', 'checkPass': False, 'hasWarning': True, 'detail': "
                              "'No VXLAN VLANs in Vxlan1'}, {'name': 'Routing', 'checkPass': True, 'hasWarning': False, 'detail': ''}, {'name': "
                              "'VNI VRF ACL', 'checkPass': True, 'hasWarning': False, 'detail': ''}, {'name': 'VRF-VNI Dynamic VLAN', 'checkPass': True, "
                              "'hasWarning': False, 'detail': ''}, {'name': 'Decap VRF-VNI Map', 'checkPass': True, 'hasWarning': False, 'detail': ''}]}}"]
    },
    {
        "name": "skipped",
        "eos_data": [
            {
                "categories": {}

            }
        ],
        "side_effect": [],
        "expected_result": "skipped",
        "expected_messages": ["VXLAN is not configured on this device"]
    },
]
