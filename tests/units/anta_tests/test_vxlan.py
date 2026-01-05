# Copyright (c) 2023-2026 Arista Networks, Inc.
# Use of this source code is governed by the Apache License 2.0
# that can be found in the LICENSE file.
"""Tests for anta.tests.vxlan.py."""

from __future__ import annotations

from typing import TypeAlias

from anta.models import AntaTest
from anta.result_manager.models import AntaTestStatus
from anta.tests.vxlan import VerifyVxlan1ConnSettings, VerifyVxlan1Interface, VerifyVxlanConfigSanity, VerifyVxlanVniBinding, VerifyVxlanVtep
from tests.units.anta_tests import AntaUnitTest, test

AntaUnitTestData: TypeAlias = dict[tuple[type[AntaTest], str], AntaUnitTest]

DATA: AntaUnitTestData = {
    (VerifyVxlan1Interface, "success"): {
        "eos_data": [{"interfaceDescriptions": {"Vxlan1": {"lineProtocolStatus": "up", "interfaceStatus": "up"}}}],
        "expected": {"result": AntaTestStatus.SUCCESS},
    },
    (VerifyVxlan1Interface, "skipped"): {
        "eos_data": [{"interfaceDescriptions": {"Loopback0": {"lineProtocolStatus": "up", "interfaceStatus": "up"}}}],
        "expected": {"result": AntaTestStatus.SKIPPED, "messages": ["Interface: Vxlan1 - Not configured"]},
    },
    (VerifyVxlan1Interface, "failure-down-up"): {
        "eos_data": [{"interfaceDescriptions": {"Vxlan1": {"lineProtocolStatus": "down", "interfaceStatus": "up"}}}],
        "expected": {"result": AntaTestStatus.FAILURE, "messages": ["Interface: Vxlan1 - Incorrect Line protocol status/Status - Expected: up/up Actual: down/up"]},
    },
    (VerifyVxlan1Interface, "failure-up-down"): {
        "eos_data": [{"interfaceDescriptions": {"Vxlan1": {"lineProtocolStatus": "up", "interfaceStatus": "down"}}}],
        "expected": {"result": AntaTestStatus.FAILURE, "messages": ["Interface: Vxlan1 - Incorrect Line protocol status/Status - Expected: up/up Actual: up/down"]},
    },
    (VerifyVxlan1Interface, "failure-down-down"): {
        "eos_data": [{"interfaceDescriptions": {"Vxlan1": {"lineProtocolStatus": "down", "interfaceStatus": "down"}}}],
        "expected": {
            "result": AntaTestStatus.FAILURE,
            "messages": ["Interface: Vxlan1 - Incorrect Line protocol status/Status - Expected: up/up Actual: down/down"],
        },
    },
    (VerifyVxlanConfigSanity, "success"): {
        "eos_data": [
            {
                "categories": {
                    "localVtep": {
                        "description": "Local VTEP Configuration Check",
                        "allCheckPass": True,
                        "detail": "",
                        "hasWarning": False,
                        "items": [
                            {"name": "Loopback IP Address", "checkPass": True, "hasWarning": False, "detail": ""},
                            {"name": "VLAN-VNI Map", "checkPass": True, "hasWarning": False, "detail": ""},
                            {"name": "Flood List", "checkPass": True, "hasWarning": False, "detail": ""},
                            {"name": "Routing", "checkPass": True, "hasWarning": False, "detail": ""},
                            {"name": "VNI VRF ACL", "checkPass": True, "hasWarning": False, "detail": ""},
                            {"name": "VRF-VNI Dynamic VLAN", "checkPass": True, "hasWarning": False, "detail": ""},
                            {"name": "Decap VRF-VNI Map", "checkPass": True, "hasWarning": False, "detail": ""},
                        ],
                    },
                    "remoteVtep": {
                        "description": "Remote VTEP Configuration Check",
                        "allCheckPass": True,
                        "detail": "",
                        "hasWarning": False,
                        "items": [{"name": "Remote VTEP", "checkPass": True, "hasWarning": False, "detail": ""}],
                    },
                    "pd": {
                        "description": "Platform Dependent Check",
                        "allCheckPass": True,
                        "detail": "",
                        "hasWarning": False,
                        "items": [
                            {"name": "VXLAN Bridging", "checkPass": True, "hasWarning": False, "detail": ""},
                            {"name": "VXLAN Routing", "checkPass": True, "hasWarning": False, "detail": "VXLAN Routing not enabled"},
                        ],
                    },
                    "cvx": {
                        "description": "CVX Configuration Check",
                        "allCheckPass": True,
                        "detail": "",
                        "hasWarning": False,
                        "items": [{"name": "CVX Server", "checkPass": True, "hasWarning": False, "detail": "Not in controller client mode"}],
                    },
                    "mlag": {
                        "description": "MLAG Configuration Check",
                        "allCheckPass": True,
                        "detail": "Run 'show mlag config-sanity' to verify MLAG config",
                        "hasWarning": False,
                        "items": [
                            {"name": "Peer VTEP IP", "checkPass": True, "hasWarning": False, "detail": ""},
                            {"name": "MLAG VTEP IP", "checkPass": True, "hasWarning": False, "detail": ""},
                            {"name": "Virtual VTEP IP", "checkPass": True, "hasWarning": False, "detail": ""},
                            {"name": "Peer VLAN-VNI", "checkPass": True, "hasWarning": False, "detail": ""},
                            {"name": "MLAG Inactive State", "checkPass": True, "hasWarning": False, "detail": ""},
                        ],
                    },
                },
                "warnings": [],
            }
        ],
        "expected": {"result": AntaTestStatus.SUCCESS},
    },
    (VerifyVxlanConfigSanity, "failure"): {
        "eos_data": [
            {
                "categories": {
                    "localVtep": {
                        "description": "Local VTEP Configuration Check",
                        "allCheckPass": False,
                        "detail": "",
                        "hasWarning": True,
                        "items": [
                            {"name": "Loopback IP Address", "checkPass": True, "hasWarning": False, "detail": ""},
                            {"name": "VLAN-VNI Map", "checkPass": False, "hasWarning": False, "detail": "No VLAN-VNI mapping in Vxlan1"},
                            {"name": "Flood List", "checkPass": False, "hasWarning": True, "detail": "No VXLAN VLANs in Vxlan1"},
                            {"name": "Routing", "checkPass": True, "hasWarning": False, "detail": ""},
                            {"name": "VNI VRF ACL", "checkPass": True, "hasWarning": False, "detail": ""},
                            {"name": "VRF-VNI Dynamic VLAN", "checkPass": True, "hasWarning": False, "detail": ""},
                            {"name": "Decap VRF-VNI Map", "checkPass": True, "hasWarning": False, "detail": ""},
                        ],
                    },
                    "remoteVtep": {
                        "description": "Remote VTEP Configuration Check",
                        "allCheckPass": True,
                        "detail": "",
                        "hasWarning": False,
                        "items": [{"name": "Remote VTEP", "checkPass": True, "hasWarning": False, "detail": ""}],
                    },
                    "pd": {
                        "description": "Platform Dependent Check",
                        "allCheckPass": True,
                        "detail": "",
                        "hasWarning": False,
                        "items": [
                            {"name": "VXLAN Bridging", "checkPass": True, "hasWarning": False, "detail": ""},
                            {"name": "VXLAN Routing", "checkPass": True, "hasWarning": False, "detail": "VXLAN Routing not enabled"},
                        ],
                    },
                    "cvx": {
                        "description": "CVX Configuration Check",
                        "allCheckPass": True,
                        "detail": "",
                        "hasWarning": False,
                        "items": [{"name": "CVX Server", "checkPass": True, "hasWarning": False, "detail": "Not in controller client mode"}],
                    },
                    "mlag": {
                        "description": "MLAG Configuration Check",
                        "allCheckPass": True,
                        "detail": "Run 'show mlag config-sanity' to verify MLAG config",
                        "hasWarning": False,
                        "items": [
                            {"name": "Peer VTEP IP", "checkPass": True, "hasWarning": False, "detail": ""},
                            {"name": "MLAG VTEP IP", "checkPass": True, "hasWarning": False, "detail": ""},
                            {"name": "Virtual VTEP IP", "checkPass": True, "hasWarning": False, "detail": ""},
                            {"name": "Peer VLAN-VNI", "checkPass": True, "hasWarning": False, "detail": ""},
                            {"name": "MLAG Inactive State", "checkPass": True, "hasWarning": False, "detail": ""},
                        ],
                    },
                },
                "warnings": ["Your configuration contains warnings. This does not mean misconfigurations. But you may wish to re-check your configurations."],
            }
        ],
        "expected": {"result": AntaTestStatus.FAILURE, "messages": ["Vxlan Category: localVtep - Config sanity check is not passing"]},
    },
    (VerifyVxlanConfigSanity, "skipped"): {
        "eos_data": [{"categories": {}}],
        "expected": {"result": AntaTestStatus.SKIPPED, "messages": ["VXLAN is not configured"]},
    },
    (VerifyVxlanVniBinding, "success"): {
        "eos_data": [
            {
                "vxlanIntfs": {
                    "Vxlan1": {
                        "vniBindings": {
                            "10020": {"vlan": 20, "dynamicVlan": False, "source": "static", "interfaces": {"Ethernet31": {"dot1q": 0}, "Vxlan1": {"dot1q": 20}}}
                        },
                        "vniBindingsToVrf": {"500": {"vrfName": "TEST", "vlan": 1199, "source": "evpn"}, "600": {"vrfName": "PROD", "vlan": 1198, "source": "evpn"}},
                    }
                }
            }
        ],
        "inputs": {"bindings": {10020: 20, 500: 1199, 600: "PROD"}},
        "expected": {"result": AntaTestStatus.SUCCESS},
    },
    (VerifyVxlanVniBinding, "failure-no-binding"): {
        "eos_data": [
            {
                "vxlanIntfs": {
                    "Vxlan1": {
                        "vniBindings": {
                            "10020": {"vlan": 20, "dynamicVlan": False, "source": "static", "interfaces": {"Ethernet31": {"dot1q": 0}, "Vxlan1": {"dot1q": 20}}}
                        },
                        "vniBindingsToVrf": {"500": {"vrfName": "PROD", "vlan": 1199, "source": "evpn"}},
                    }
                }
            }
        ],
        "inputs": {"bindings": {10010: 10, 10020: 20, 500: 1199}},
        "expected": {"result": AntaTestStatus.FAILURE, "messages": ["Interface: Vxlan1 VNI: 10010 - Binding not found"]},
    },
    (VerifyVxlanVniBinding, "failure-vrf-wrong-binding"): {
        "eos_data": [
            {
                "vxlanIntfs": {
                    "Vxlan1": {
                        "vniBindings": {
                            "10020": {"vlan": 20, "dynamicVlan": False, "source": "static", "interfaces": {"Ethernet31": {"dot1q": 0}, "Vxlan1": {"dot1q": 20}}}
                        },
                        "vniBindingsToVrf": {"500": {"vrfName": "PROD", "vlan": 1199, "source": "evpn"}, "600": {"vrfName": "TEST", "vlan": 1199, "source": "evpn"}},
                    }
                }
            }
        ],
        "inputs": {"bindings": {10020: 20, 500: 1199, 600: "PROD"}},
        "expected": {"result": AntaTestStatus.FAILURE, "messages": ["Interface: Vxlan1 VNI: 600 - Wrong VRF binding - Expected: PROD Actual: TEST"]},
    },
    (VerifyVxlanVniBinding, "failure-wrong-binding"): {
        "eos_data": [
            {
                "vxlanIntfs": {
                    "Vxlan1": {
                        "vniBindings": {
                            "10020": {"vlan": 30, "dynamicVlan": False, "source": "static", "interfaces": {"Ethernet31": {"dot1q": 0}, "Vxlan1": {"dot1q": 20}}}
                        },
                        "vniBindingsToVrf": {"500": {"vrfName": "PROD", "vlan": 1199, "source": "evpn"}},
                    }
                }
            }
        ],
        "inputs": {"bindings": {10020: 20, 500: 1199}},
        "expected": {"result": AntaTestStatus.FAILURE, "messages": ["Interface: Vxlan1 VNI: 10020 - Wrong VLAN binding - Expected: 20 Actual: 30"]},
    },
    (VerifyVxlanVniBinding, "failure-no-and-wrong-binding"): {
        "eos_data": [
            {
                "vxlanIntfs": {
                    "Vxlan1": {
                        "vniBindings": {
                            "10020": {"vlan": 30, "dynamicVlan": False, "source": "static", "interfaces": {"Ethernet31": {"dot1q": 0}, "Vxlan1": {"dot1q": 20}}}
                        },
                        "vniBindingsToVrf": {"500": {"vrfName": "PROD", "vlan": 1199, "source": "evpn"}},
                    }
                }
            }
        ],
        "inputs": {"bindings": {10010: 10, 10020: 20, 500: 1199}},
        "expected": {
            "result": AntaTestStatus.FAILURE,
            "messages": ["Interface: Vxlan1 VNI: 10010 - Binding not found", "Interface: Vxlan1 VNI: 10020 - Wrong VLAN binding - Expected: 20 Actual: 30"],
        },
    },
    (VerifyVxlanVniBinding, "failure-wrong-vni-vrf-binding"): {
        "eos_data": [
            {
                "vxlanIntfs": {
                    "Vxlan1": {
                        "vniBindings": {
                            "10020": {"vlan": 30, "dynamicVlan": False, "source": "static", "interfaces": {"Ethernet31": {"dot1q": 0}, "Vxlan1": {"dot1q": 20}}}
                        },
                        "vniBindingsToVrf": {"500": {"vrfName": "PROD", "vlan": 1199, "source": "evpn"}},
                    }
                }
            }
        ],
        "inputs": {"bindings": {10020: "PROD", 500: 30}},
        "expected": {
            "result": AntaTestStatus.FAILURE,
            "messages": ["Interface: Vxlan1 VNI: 10020 - Binding not found", "Interface: Vxlan1 VNI: 500 - Wrong VLAN binding - Expected: 30 Actual: 1199"],
        },
    },
    (VerifyVxlanVniBinding, "skipped"): {
        "eos_data": [{"vxlanIntfs": {}}],
        "inputs": {"bindings": {10020: 20, 500: 1199}},
        "expected": {"result": AntaTestStatus.SKIPPED, "messages": ["Interface: Vxlan1 - Not configured"]},
    },
    (VerifyVxlanVtep, "success"): {
        "eos_data": [{"vteps": {}, "interfaces": {"Vxlan1": {"vteps": ["10.1.1.5", "10.1.1.6"]}}}],
        "inputs": {"vteps": ["10.1.1.5", "10.1.1.6"]},
        "expected": {"result": AntaTestStatus.SUCCESS},
    },
    (VerifyVxlanVtep, "failure-missing-vtep"): {
        "eos_data": [{"vteps": {}, "interfaces": {"Vxlan1": {"vteps": ["10.1.1.5", "10.1.1.6"]}}}],
        "inputs": {"vteps": ["10.1.1.5", "10.1.1.6", "10.1.1.7"]},
        "expected": {"result": AntaTestStatus.FAILURE, "messages": ["The following VTEP peer(s) are missing from the Vxlan1 interface: 10.1.1.7"]},
    },
    (VerifyVxlanVtep, "failure-no-vtep"): {
        "eos_data": [{"vteps": {}, "interfaces": {"Vxlan1": {"vteps": []}}}],
        "inputs": {"vteps": ["10.1.1.5", "10.1.1.6"]},
        "expected": {"result": AntaTestStatus.FAILURE, "messages": ["The following VTEP peer(s) are missing from the Vxlan1 interface: 10.1.1.5, 10.1.1.6"]},
    },
    (VerifyVxlanVtep, "failure-no-input-vtep"): {
        "eos_data": [{"vteps": {}, "interfaces": {"Vxlan1": {"vteps": ["10.1.1.5"]}}}],
        "inputs": {"vteps": []},
        "expected": {"result": AntaTestStatus.FAILURE, "messages": ["Unexpected VTEP peer(s) on Vxlan1 interface: 10.1.1.5"]},
    },
    (VerifyVxlanVtep, "failure-missmatch"): {
        "eos_data": [{"vteps": {}, "interfaces": {"Vxlan1": {"vteps": ["10.1.1.6", "10.1.1.7", "10.1.1.8"]}}}],
        "inputs": {"vteps": ["10.1.1.5", "10.1.1.6"]},
        "expected": {
            "result": AntaTestStatus.FAILURE,
            "messages": [
                "The following VTEP peer(s) are missing from the Vxlan1 interface: 10.1.1.5",
                "Unexpected VTEP peer(s) on Vxlan1 interface: 10.1.1.7, 10.1.1.8",
            ],
        },
    },
    (VerifyVxlanVtep, "skipped"): {
        "eos_data": [{"vteps": {}, "interfaces": {}}],
        "inputs": {"vteps": ["10.1.1.5", "10.1.1.6", "10.1.1.7"]},
        "expected": {"result": AntaTestStatus.SKIPPED, "messages": ["Interface: Vxlan1 - Not configured"]},
    },
    (VerifyVxlan1ConnSettings, "success"): {
        "eos_data": [{"interfaces": {"Vxlan1": {"srcIpIntf": "Loopback1", "udpPort": 4789}}}],
        "inputs": {"source_interface": "Loopback1", "udp_port": 4789},
        "expected": {"result": AntaTestStatus.SUCCESS},
    },
    (VerifyVxlan1ConnSettings, "success-dps-src-intf"): {
        "eos_data": [{"interfaces": {"Vxlan1": {"srcIpIntf": "Dps1", "udpPort": 4789}}}],
        "inputs": {"source_interface": "Dps1", "udp_port": 4789},
        "expected": {"result": AntaTestStatus.SUCCESS},
    },
    (VerifyVxlan1ConnSettings, "skipped"): {
        "eos_data": [{"interfaces": {}}],
        "inputs": {"source_interface": "Loopback1", "udp_port": 4789},
        "expected": {"result": AntaTestStatus.SKIPPED, "messages": ["Interface: Vxlan1 - Not configured"]},
    },
    (VerifyVxlan1ConnSettings, "failure-wrong-interface"): {
        "eos_data": [{"interfaces": {"Vxlan1": {"srcIpIntf": "Loopback10", "udpPort": 4789}}}],
        "inputs": {"source_interface": "lo1", "udp_port": 4789},
        "expected": {"result": AntaTestStatus.FAILURE, "messages": ["Interface: Vxlan1 - Incorrect Source interface - Expected: Loopback1 Actual: Loopback10"]},
    },
    (VerifyVxlan1ConnSettings, "failure-wrong-port"): {
        "eos_data": [{"interfaces": {"Vxlan1": {"srcIpIntf": "Loopback10", "udpPort": 4789}}}],
        "inputs": {"source_interface": "Lo1", "udp_port": 4780},
        "expected": {
            "result": AntaTestStatus.FAILURE,
            "messages": [
                "Interface: Vxlan1 - Incorrect Source interface - Expected: Loopback1 Actual: Loopback10",
                "Interface: Vxlan1 - Incorrect UDP port - Expected: 4780 Actual: 4789",
            ],
        },
    },
    (VerifyVxlan1ConnSettings, "failure-dps-src-intf"): {
        "eos_data": [{"interfaces": {"Vxlan1": {"srcIpIntf": "Loopback10", "udpPort": 4789}}}],
        "inputs": {"source_interface": "dps1", "udp_port": 4789},
        "expected": {"result": AntaTestStatus.FAILURE, "messages": ["Interface: Vxlan1 - Incorrect Source interface - Expected: Dps1 Actual: Loopback10"]},
    },
}
