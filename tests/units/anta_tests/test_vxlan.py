# Copyright (c) 2023-2025 Arista Networks, Inc.
# Use of this source code is governed by the Apache License 2.0
# that can be found in the LICENSE file.
"""Tests for anta.tests.vxlan.py."""

from __future__ import annotations

from typing import Any

from anta.tests.vxlan import VerifyVxlan1ConnSettings, VerifyVxlan1Interface, VerifyVxlanConfigSanity, VerifyVxlanVniBinding, VerifyVxlanVtep
from tests.units.anta_tests import test

DATA: list[dict[str, Any]] = [
    {
        "name": "success",
        "test": VerifyVxlan1Interface,
        "eos_data": [{"interfaceDescriptions": {"Vxlan1": {"lineProtocolStatus": "up", "interfaceStatus": "up"}}}],
        "inputs": None,
        "expected": {"result": "success"},
    },
    {
        "name": "skipped",
        "test": VerifyVxlan1Interface,
        "eos_data": [{"interfaceDescriptions": {"Loopback0": {"lineProtocolStatus": "up", "interfaceStatus": "up"}}}],
        "inputs": None,
        "expected": {"result": "skipped", "messages": ["Vxlan1 interface is not configured"]},
    },
    {
        "name": "failure-down-up",
        "test": VerifyVxlan1Interface,
        "eos_data": [{"interfaceDescriptions": {"Vxlan1": {"lineProtocolStatus": "down", "interfaceStatus": "up"}}}],
        "inputs": None,
        "expected": {"result": "failure", "messages": ["Vxlan1 interface is down/up"]},
    },
    {
        "name": "failure-up-down",
        "test": VerifyVxlan1Interface,
        "eos_data": [{"interfaceDescriptions": {"Vxlan1": {"lineProtocolStatus": "up", "interfaceStatus": "down"}}}],
        "inputs": None,
        "expected": {"result": "failure", "messages": ["Vxlan1 interface is up/down"]},
    },
    {
        "name": "failure-down-down",
        "test": VerifyVxlan1Interface,
        "eos_data": [{"interfaceDescriptions": {"Vxlan1": {"lineProtocolStatus": "down", "interfaceStatus": "down"}}}],
        "inputs": None,
        "expected": {"result": "failure", "messages": ["Vxlan1 interface is down/down"]},
    },
    {
        "name": "success",
        "test": VerifyVxlanConfigSanity,
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
            },
        ],
        "inputs": None,
        "expected": {"result": "success"},
    },
    {
        "name": "failure",
        "test": VerifyVxlanConfigSanity,
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
            },
        ],
        "inputs": None,
        "expected": {
            "result": "failure",
            "messages": [
                "VXLAN config sanity check is not passing: {'localVtep': {'description': 'Local VTEP Configuration Check', "
                "'allCheckPass': False, 'detail': '', 'hasWarning': True, 'items': [{'name': 'Loopback IP Address', 'checkPass': True, "
                "'hasWarning': False, 'detail': ''}, {'name': 'VLAN-VNI Map', 'checkPass': False, 'hasWarning': False, 'detail': "
                "'No VLAN-VNI mapping in Vxlan1'}, {'name': 'Flood List', 'checkPass': False, 'hasWarning': True, 'detail': "
                "'No VXLAN VLANs in Vxlan1'}, {'name': 'Routing', 'checkPass': True, 'hasWarning': False, 'detail': ''}, {'name': "
                "'VNI VRF ACL', 'checkPass': True, 'hasWarning': False, 'detail': ''}, {'name': 'VRF-VNI Dynamic VLAN', 'checkPass': True, "
                "'hasWarning': False, 'detail': ''}, {'name': 'Decap VRF-VNI Map', 'checkPass': True, 'hasWarning': False, 'detail': ''}]}}",
            ],
        },
    },
    {
        "name": "skipped",
        "test": VerifyVxlanConfigSanity,
        "eos_data": [{"categories": {}}],
        "inputs": None,
        "expected": {"result": "skipped", "messages": ["VXLAN is not configured"]},
    },
    {
        "name": "success",
        "test": VerifyVxlanVniBinding,
        "eos_data": [
            {
                "vxlanIntfs": {
                    "Vxlan1": {
                        "vniBindings": {
                            "10020": {"vlan": 20, "dynamicVlan": False, "source": "static", "interfaces": {"Ethernet31": {"dot1q": 0}, "Vxlan1": {"dot1q": 20}}},
                        },
                        "vniBindingsToVrf": {"500": {"vrfName": "PROD", "vlan": 1199, "source": "evpn"}},
                    },
                },
            },
        ],
        "inputs": {"bindings": {10020: 20, 500: 1199}},
        "expected": {"result": "success"},
    },
    {
        "name": "failure-no-binding",
        "test": VerifyVxlanVniBinding,
        "eos_data": [
            {
                "vxlanIntfs": {
                    "Vxlan1": {
                        "vniBindings": {
                            "10020": {"vlan": 20, "dynamicVlan": False, "source": "static", "interfaces": {"Ethernet31": {"dot1q": 0}, "Vxlan1": {"dot1q": 20}}},
                        },
                        "vniBindingsToVrf": {"500": {"vrfName": "PROD", "vlan": 1199, "source": "evpn"}},
                    },
                },
            },
        ],
        "inputs": {"bindings": {10010: 10, 10020: 20, 500: 1199}},
        "expected": {"result": "failure", "messages": ["The following VNI(s) have no binding: ['10010']"]},
    },
    {
        "name": "failure-wrong-binding",
        "test": VerifyVxlanVniBinding,
        "eos_data": [
            {
                "vxlanIntfs": {
                    "Vxlan1": {
                        "vniBindings": {
                            "10020": {"vlan": 30, "dynamicVlan": False, "source": "static", "interfaces": {"Ethernet31": {"dot1q": 0}, "Vxlan1": {"dot1q": 20}}},
                        },
                        "vniBindingsToVrf": {"500": {"vrfName": "PROD", "vlan": 1199, "source": "evpn"}},
                    },
                },
            },
        ],
        "inputs": {"bindings": {10020: 20, 500: 1199}},
        "expected": {"result": "failure", "messages": ["The following VNI(s) have the wrong VLAN binding: [{'10020': 30}]"]},
    },
    {
        "name": "failure-no-and-wrong-binding",
        "test": VerifyVxlanVniBinding,
        "eos_data": [
            {
                "vxlanIntfs": {
                    "Vxlan1": {
                        "vniBindings": {
                            "10020": {"vlan": 30, "dynamicVlan": False, "source": "static", "interfaces": {"Ethernet31": {"dot1q": 0}, "Vxlan1": {"dot1q": 20}}},
                        },
                        "vniBindingsToVrf": {"500": {"vrfName": "PROD", "vlan": 1199, "source": "evpn"}},
                    },
                },
            },
        ],
        "inputs": {"bindings": {10010: 10, 10020: 20, 500: 1199}},
        "expected": {
            "result": "failure",
            "messages": ["The following VNI(s) have no binding: ['10010']", "The following VNI(s) have the wrong VLAN binding: [{'10020': 30}]"],
        },
    },
    {
        "name": "skipped",
        "test": VerifyVxlanVniBinding,
        "eos_data": [{"vxlanIntfs": {}}],
        "inputs": {"bindings": {10020: 20, 500: 1199}},
        "expected": {"result": "skipped", "messages": ["Vxlan1 interface is not configured"]},
    },
    {
        "name": "success",
        "test": VerifyVxlanVtep,
        "eos_data": [{"vteps": {}, "interfaces": {"Vxlan1": {"vteps": ["10.1.1.5", "10.1.1.6"]}}}],
        "inputs": {"vteps": ["10.1.1.5", "10.1.1.6"]},
        "expected": {"result": "success"},
    },
    {
        "name": "failure-missing-vtep",
        "test": VerifyVxlanVtep,
        "eos_data": [{"vteps": {}, "interfaces": {"Vxlan1": {"vteps": ["10.1.1.5", "10.1.1.6"]}}}],
        "inputs": {"vteps": ["10.1.1.5", "10.1.1.6", "10.1.1.7"]},
        "expected": {"result": "failure", "messages": ["The following VTEP peer(s) are missing from the Vxlan1 interface: ['10.1.1.7']"]},
    },
    {
        "name": "failure-no-vtep",
        "test": VerifyVxlanVtep,
        "eos_data": [{"vteps": {}, "interfaces": {"Vxlan1": {"vteps": []}}}],
        "inputs": {"vteps": ["10.1.1.5", "10.1.1.6"]},
        "expected": {"result": "failure", "messages": ["The following VTEP peer(s) are missing from the Vxlan1 interface: ['10.1.1.5', '10.1.1.6']"]},
    },
    {
        "name": "failure-no-input-vtep",
        "test": VerifyVxlanVtep,
        "eos_data": [{"vteps": {}, "interfaces": {"Vxlan1": {"vteps": ["10.1.1.5"]}}}],
        "inputs": {"vteps": []},
        "expected": {"result": "failure", "messages": ["Unexpected VTEP peer(s) on Vxlan1 interface: ['10.1.1.5']"]},
    },
    {
        "name": "failure-missmatch",
        "test": VerifyVxlanVtep,
        "eos_data": [{"vteps": {}, "interfaces": {"Vxlan1": {"vteps": ["10.1.1.6", "10.1.1.7", "10.1.1.8"]}}}],
        "inputs": {"vteps": ["10.1.1.5", "10.1.1.6"]},
        "expected": {
            "result": "failure",
            "messages": [
                "The following VTEP peer(s) are missing from the Vxlan1 interface: ['10.1.1.5']",
                "Unexpected VTEP peer(s) on Vxlan1 interface: ['10.1.1.7', '10.1.1.8']",
            ],
        },
    },
    {
        "name": "skipped",
        "test": VerifyVxlanVtep,
        "eos_data": [{"vteps": {}, "interfaces": {}}],
        "inputs": {"vteps": ["10.1.1.5", "10.1.1.6", "10.1.1.7"]},
        "expected": {"result": "skipped", "messages": ["Vxlan1 interface is not configured"]},
    },
    {
        "name": "success",
        "test": VerifyVxlan1ConnSettings,
        "eos_data": [{"interfaces": {"Vxlan1": {"srcIpIntf": "Loopback1", "udpPort": 4789}}}],
        "inputs": {"source_interface": "Loopback1", "udp_port": 4789},
        "expected": {"result": "success"},
    },
    {
        "name": "skipped",
        "test": VerifyVxlan1ConnSettings,
        "eos_data": [{"interfaces": {}}],
        "inputs": {"source_interface": "Loopback1", "udp_port": 4789},
        "expected": {"result": "skipped", "messages": ["Vxlan1 interface is not configured."]},
    },
    {
        "name": "failure-wrong-interface",
        "test": VerifyVxlan1ConnSettings,
        "eos_data": [{"interfaces": {"Vxlan1": {"srcIpIntf": "Loopback10", "udpPort": 4789}}}],
        "inputs": {"source_interface": "lo1", "udp_port": 4789},
        "expected": {
            "result": "failure",
            "messages": ["Source interface is not correct. Expected `Loopback1` as source interface but found `Loopback10` instead."],
        },
    },
    {
        "name": "failure-wrong-port",
        "test": VerifyVxlan1ConnSettings,
        "eos_data": [{"interfaces": {"Vxlan1": {"srcIpIntf": "Loopback10", "udpPort": 4789}}}],
        "inputs": {"source_interface": "Lo1", "udp_port": 4780},
        "expected": {
            "result": "failure",
            "messages": [
                "Source interface is not correct. Expected `Loopback1` as source interface but found `Loopback10` instead.",
                "UDP port is not correct. Expected `4780` as UDP port but found `4789` instead.",
            ],
        },
    },
]
