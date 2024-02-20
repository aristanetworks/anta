# Copyright (c) 2023-2024 Arista Networks, Inc.
# Use of this source code is governed by the Apache License 2.0
# that can be found in the LICENSE file.
"""Test inputs for anta.tests.hardware"""
from __future__ import annotations

from typing import Any

from anta.tests.interfaces import (
    VerifyIllegalLACP,
    VerifyInterfaceDiscards,
    VerifyInterfaceErrDisabled,
    VerifyInterfaceErrors,
    VerifyInterfacesStatus,
    VerifyInterfaceUtilization,
    VerifyIPProxyARP,
    VerifyIpVirtualRouterMac,
    VerifyL2MTU,
    VerifyL3MTU,
    VerifyLoopbackCount,
    VerifyPortChannels,
    VerifyStormControlDrops,
    VerifySVI,
)
from tests.lib.anta import test  # noqa: F401; pylint: disable=W0611

DATA: list[dict[str, Any]] = [
    {
        "name": "success",
        "test": VerifyInterfaceUtilization,
        "eos_data": [
            """Port      Name        Intvl   In Mbps      %  In Kpps  Out Mbps      % Out Kpps
Et1                    5:00       0.0   0.0%        0       0.0   0.0%        0
Et4                    5:00       0.0   0.0%        0       0.0   0.0%        0
"""
        ],
        "inputs": None,
        "expected": {"result": "success"},
    },
    {
        "name": "failure",
        "test": VerifyInterfaceUtilization,
        "eos_data": [
            """Port      Name        Intvl   In Mbps      %  In Kpps  Out Mbps      % Out Kpps
Et1                    5:00       0.0   0.0%        0       0.0  80.0%        0
Et4                    5:00       0.0  99.9%        0       0.0   0.0%        0
"""
        ],
        "inputs": None,
        "expected": {"result": "failure", "messages": ["The following interfaces have a usage > 75%: {'Et1': '80.0%', 'Et4': '99.9%'}"]},
    },
    {
        "name": "success",
        "test": VerifyInterfaceErrors,
        "eos_data": [
            {
                "interfaceErrorCounters": {
                    "Ethernet1": {"inErrors": 0, "frameTooLongs": 0, "outErrors": 0, "frameTooShorts": 0, "fcsErrors": 0, "alignmentErrors": 0, "symbolErrors": 0},
                    "Ethernet6": {"inErrors": 0, "frameTooLongs": 0, "outErrors": 0, "frameTooShorts": 0, "fcsErrors": 0, "alignmentErrors": 0, "symbolErrors": 0},
                }
            }
        ],
        "inputs": None,
        "expected": {"result": "success"},
    },
    {
        "name": "failure-multiple-intfs",
        "test": VerifyInterfaceErrors,
        "eos_data": [
            {
                "interfaceErrorCounters": {
                    "Ethernet1": {"inErrors": 42, "frameTooLongs": 0, "outErrors": 0, "frameTooShorts": 0, "fcsErrors": 0, "alignmentErrors": 0, "symbolErrors": 0},
                    "Ethernet6": {"inErrors": 0, "frameTooLongs": 0, "outErrors": 0, "frameTooShorts": 0, "fcsErrors": 0, "alignmentErrors": 666, "symbolErrors": 0},
                }
            }
        ],
        "inputs": None,
        "expected": {
            "result": "failure",
            "messages": [
                "The following interface(s) have non-zero error counters: [{'Ethernet1': {'inErrors': 42, 'frameTooLongs': 0, 'outErrors': 0, 'frameTooShorts': 0,"
                " 'fcsErrors': 0, 'alignmentErrors': 0, 'symbolErrors': 0}}, {'Ethernet6': {'inErrors': 0, 'frameTooLongs': 0, 'outErrors': 0, 'frameTooShorts':"
                " 0, 'fcsErrors': 0, 'alignmentErrors': 666, 'symbolErrors': 0}}]"
            ],
        },
    },
    {
        "name": "failure-multiple-intfs-multiple-errors",
        "test": VerifyInterfaceErrors,
        "eos_data": [
            {
                "interfaceErrorCounters": {
                    "Ethernet1": {"inErrors": 42, "frameTooLongs": 0, "outErrors": 10, "frameTooShorts": 0, "fcsErrors": 0, "alignmentErrors": 0, "symbolErrors": 0},
                    "Ethernet6": {"inErrors": 0, "frameTooLongs": 0, "outErrors": 0, "frameTooShorts": 0, "fcsErrors": 0, "alignmentErrors": 6, "symbolErrors": 10},
                }
            }
        ],
        "inputs": None,
        "expected": {
            "result": "failure",
            "messages": [
                "The following interface(s) have non-zero error counters: [{'Ethernet1': {'inErrors': 42, 'frameTooLongs': 0, 'outErrors': 10, 'frameTooShorts': 0,"
                " 'fcsErrors': 0, 'alignmentErrors': 0, 'symbolErrors': 0}}, {'Ethernet6': {'inErrors': 0, 'frameTooLongs': 0, 'outErrors': 0, 'frameTooShorts':"
                " 0, 'fcsErrors': 0, 'alignmentErrors': 6, 'symbolErrors': 10}}]"
            ],
        },
    },
    {
        "name": "failure-single-intf-multiple-errors",
        "test": VerifyInterfaceErrors,
        "eos_data": [
            {
                "interfaceErrorCounters": {
                    "Ethernet1": {"inErrors": 42, "frameTooLongs": 0, "outErrors": 2, "frameTooShorts": 0, "fcsErrors": 0, "alignmentErrors": 0, "symbolErrors": 0},
                }
            }
        ],
        "inputs": None,
        "expected": {
            "result": "failure",
            "messages": [
                "The following interface(s) have non-zero error counters: [{'Ethernet1': {'inErrors': 42, 'frameTooLongs': 0, 'outErrors': 2, 'frameTooShorts': 0,"
                " 'fcsErrors': 0, 'alignmentErrors': 0, 'symbolErrors': 0}}]"
            ],
        },
    },
    {
        "name": "success",
        "test": VerifyInterfaceDiscards,
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
        "inputs": None,
        "expected": {"result": "success"},
    },
    {
        "name": "failure",
        "test": VerifyInterfaceDiscards,
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
        "inputs": None,
        "expected": {
            "result": "failure",
            "messages": [
                "The following interfaces have non 0 discard counter(s): [{'Ethernet2': {'outDiscards': 42, 'inDiscards': 0}},"
                " {'Ethernet1': {'outDiscards': 0, 'inDiscards': 42}}]"
            ],
        },
    },
    {
        "name": "success",
        "test": VerifyInterfaceErrDisabled,
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
        "inputs": None,
        "expected": {"result": "success"},
    },
    {
        "name": "failure",
        "test": VerifyInterfaceErrDisabled,
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
        "inputs": None,
        "expected": {"result": "failure", "messages": ["The following interfaces are in error disabled state: ['Management1', 'Ethernet8']"]},
    },
    {
        "name": "success",
        "test": VerifyInterfacesStatus,
        "eos_data": [
            {
                "interfaceDescriptions": {
                    "Ethernet8": {"interfaceStatus": "up", "description": "", "lineProtocolStatus": "up"},
                    "Ethernet2": {"interfaceStatus": "adminDown", "description": "", "lineProtocolStatus": "up"},
                    "Ethernet3": {"interfaceStatus": "up", "description": "", "lineProtocolStatus": "up"},
                }
            }
        ],
        "inputs": {
            "interfaces": [{"interface": "Ethernet2", "state": "adminDown"}, {"interface": "Ethernet8", "state": "up"}, {"interface": "Ethernet3", "state": "up"}]
        },
        "expected": {"result": "success"},
    },
    {
        "name": "success-lower",
        "test": VerifyInterfacesStatus,
        "eos_data": [
            {
                "interfaceDescriptions": {
                    "Ethernet8": {"interfaceStatus": "up", "description": "", "lineProtocolStatus": "up"},
                    "Ethernet2": {"interfaceStatus": "adminDown", "description": "", "lineProtocolStatus": "up"},
                    "Ethernet3": {"interfaceStatus": "up", "description": "", "lineProtocolStatus": "up"},
                }
            }
        ],
        "inputs": {
            "interfaces": [{"interface": "ethernet2", "state": "adminDown"}, {"interface": "ethernet8", "state": "up"}, {"interface": "ethernet3", "state": "up"}]
        },
        "expected": {"result": "success"},
    },
    {
        "name": "success-eth-name",
        "test": VerifyInterfacesStatus,
        "eos_data": [
            {
                "interfaceDescriptions": {
                    "Ethernet8": {"interfaceStatus": "up", "description": "", "lineProtocolStatus": "up"},
                    "Ethernet2": {"interfaceStatus": "adminDown", "description": "", "lineProtocolStatus": "up"},
                    "Ethernet3": {"interfaceStatus": "up", "description": "", "lineProtocolStatus": "up"},
                }
            }
        ],
        "inputs": {"interfaces": [{"interface": "eth2", "state": "adminDown"}, {"interface": "et8", "state": "up"}, {"interface": "et3", "state": "up"}]},
        "expected": {"result": "success"},
    },
    {
        "name": "success-po-name",
        "test": VerifyInterfacesStatus,
        "eos_data": [
            {
                "interfaceDescriptions": {
                    "Port-Channel100": {"interfaceStatus": "up", "description": "", "lineProtocolStatus": "up"},
                }
            }
        ],
        "inputs": {"interfaces": [{"interface": "po100", "state": "up"}]},
        "expected": {"result": "success"},
    },
    {
        "name": "success-sub-interfaces",
        "test": VerifyInterfacesStatus,
        "eos_data": [
            {
                "interfaceDescriptions": {
                    "Ethernet52/1.1963": {"interfaceStatus": "up", "description": "", "lineProtocolStatus": "up"},
                }
            }
        ],
        "inputs": {"interfaces": [{"interface": "Ethernet52/1.1963", "state": "up"}]},
        "expected": {"result": "success"},
    },
    {
        "name": "failure-not-configured",
        "test": VerifyInterfacesStatus,
        "eos_data": [
            {
                "interfaceDescriptions": {
                    "Ethernet2": {"interfaceStatus": "up", "description": "", "lineProtocolStatus": "up"},
                    "Ethernet3": {"interfaceStatus": "up", "description": "", "lineProtocolStatus": "up"},
                }
            }
        ],
        "inputs": {"interfaces": [{"interface": "Ethernet2", "state": "up"}, {"interface": "Ethernet8", "state": "up"}, {"interface": "Ethernet3", "state": "up"}]},
        "expected": {
            "result": "failure",
            "messages": ["The following interface(s) are not configured: ['Ethernet8']"],
        },
    },
    {
        "name": "failure-down",
        "test": VerifyInterfacesStatus,
        "eos_data": [
            {
                "interfaceDescriptions": {
                    "Ethernet8": {"interfaceStatus": "adminDown", "description": "", "lineProtocolStatus": "down"},
                    "Ethernet2": {"interfaceStatus": "up", "description": "", "lineProtocolStatus": "up"},
                    "Ethernet3": {"interfaceStatus": "up", "description": "", "lineProtocolStatus": "up"},
                }
            }
        ],
        "inputs": {"interfaces": [{"interface": "Ethernet2", "state": "up"}, {"interface": "Ethernet8", "state": "up"}, {"interface": "Ethernet3", "state": "up"}]},
        "expected": {
            "result": "failure",
            "messages": ["The following interface(s) are not in the expected state: ['Ethernet8 is down/adminDown expected up/up'"],
        },
    },
    {
        "name": "failure-up",
        "test": VerifyInterfacesStatus,
        "eos_data": [
            {
                "interfaceDescriptions": {
                    "Ethernet8": {"interfaceStatus": "adminDown", "description": "", "lineProtocolStatus": "down"},
                    "Ethernet2": {"interfaceStatus": "up", "description": "", "lineProtocolStatus": "up"},
                    "Ethernet3": {"interfaceStatus": "up", "description": "", "lineProtocolStatus": "up"},
                }
            }
        ],
        "inputs": {
            "interfaces": [
                {"interface": "Ethernet2", "state": "adminDown", "protocol_status": "down"},
                {"interface": "Ethernet8", "state": "adminDown"},
                {"interface": "Ethernet3", "state": "up"},
            ]
        },
        "expected": {
            "result": "failure",
            "messages": ["The following interface(s) are not in the expected state: ['Ethernet2 is up/up expected down/adminDown'"],
        },
    },
    {
        "name": "success",
        "test": VerifyStormControlDrops,
        "eos_data": [
            {
                "aggregateTrafficClasses": {},
                "interfaces": {
                    "Ethernet1": {
                        "trafficTypes": {"broadcast": {"level": 100, "thresholdType": "packetsPerSecond", "rate": 0, "drop": 0, "dormant": False}},
                        "active": True,
                        "reason": "",
                        "errdisabled": False,
                    }
                },
            }
        ],
        "inputs": None,
        "expected": {"result": "success"},
    },
    {
        "name": "failure",
        "test": VerifyStormControlDrops,
        "eos_data": [
            {
                "aggregateTrafficClasses": {},
                "interfaces": {
                    "Ethernet1": {
                        "trafficTypes": {"broadcast": {"level": 100, "thresholdType": "packetsPerSecond", "rate": 0, "drop": 666, "dormant": False}},
                        "active": True,
                        "reason": "",
                        "errdisabled": False,
                    }
                },
            }
        ],
        "inputs": None,
        "expected": {"result": "failure", "messages": ["The following interfaces have none 0 storm-control drop counters {'Ethernet1': {'broadcast': 666}}"]},
    },
    {
        "name": "success",
        "test": VerifyPortChannels,
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
        "inputs": None,
        "expected": {"result": "success"},
    },
    {
        "name": "failure",
        "test": VerifyPortChannels,
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
        "inputs": None,
        "expected": {"result": "failure", "messages": ["The following port-channels have inactive port(s): ['Port-Channel42']"]},
    },
    {
        "name": "success",
        "test": VerifyIllegalLACP,
        "eos_data": [
            {
                "portChannels": {
                    "Port-Channel42": {
                        "interfaces": {
                            "Ethernet8": {
                                "actorPortStatus": "noAgg",
                                "illegalRxCount": 0,
                                "markerResponseTxCount": 0,
                                "markerResponseRxCount": 0,
                                "lacpdusRxCount": 0,
                                "lacpdusTxCount": 454,
                                "markersTxCount": 0,
                                "markersRxCount": 0,
                            }
                        }
                    }
                },
                "orphanPorts": {},
            }
        ],
        "inputs": None,
        "expected": {"result": "success"},
    },
    {
        "name": "failure",
        "test": VerifyIllegalLACP,
        "eos_data": [
            {
                "portChannels": {
                    "Port-Channel42": {
                        "interfaces": {
                            "Ethernet8": {
                                "actorPortStatus": "noAgg",
                                "illegalRxCount": 666,
                                "markerResponseTxCount": 0,
                                "markerResponseRxCount": 0,
                                "lacpdusRxCount": 0,
                                "lacpdusTxCount": 454,
                                "markersTxCount": 0,
                                "markersRxCount": 0,
                            }
                        }
                    }
                },
                "orphanPorts": {},
            }
        ],
        "inputs": None,
        "expected": {
            "result": "failure",
            "messages": ["The following port-channels have recieved illegal lacp packets on the following ports: [{'Port-Channel42': 'Ethernet8'}]"],
        },
    },
    {
        "name": "success",
        "test": VerifyLoopbackCount,
        "eos_data": [
            {
                "interfaces": {
                    "Loopback42": {
                        "name": "Loopback42",
                        "interfaceStatus": "connected",
                        "interfaceAddress": {"ipAddr": {"maskLen": 0, "address": "0.0.0.0"}, "unnumberedIntf": "Vlan42"},
                        "ipv4Routable240": False,
                        "lineProtocolStatus": "up",
                        "mtu": 65535,
                    },
                    "Loopback666": {
                        "name": "Loopback666",
                        "interfaceStatus": "connected",
                        "interfaceAddress": {"ipAddr": {"maskLen": 32, "address": "6.6.6.6"}},
                        "ipv4Routable240": False,
                        "lineProtocolStatus": "up",
                        "mtu": 65535,
                    },
                }
            }
        ],
        "inputs": {"number": 2},
        "expected": {"result": "success"},
    },
    {
        "name": "failure-loopback-down",
        "test": VerifyLoopbackCount,
        "eos_data": [
            {
                "interfaces": {
                    "Loopback42": {
                        "name": "Loopback42",
                        "interfaceStatus": "connected",
                        "interfaceAddress": {"ipAddr": {"maskLen": 0, "address": "0.0.0.0"}, "unnumberedIntf": "Vlan42"},
                        "ipv4Routable240": False,
                        "lineProtocolStatus": "up",
                        "mtu": 65535,
                    },
                    "Loopback666": {
                        "name": "Loopback666",
                        "interfaceStatus": "connected",
                        "interfaceAddress": {"ipAddr": {"maskLen": 32, "address": "6.6.6.6"}},
                        "ipv4Routable240": False,
                        "lineProtocolStatus": "down",
                        "mtu": 65535,
                    },
                }
            }
        ],
        "inputs": {"number": 2},
        "expected": {"result": "failure", "messages": ["The following Loopbacks are not up: ['Loopback666']"]},
    },
    {
        "name": "failure-count-loopback",
        "test": VerifyLoopbackCount,
        "eos_data": [
            {
                "interfaces": {
                    "Loopback42": {
                        "name": "Loopback42",
                        "interfaceStatus": "connected",
                        "interfaceAddress": {"ipAddr": {"maskLen": 0, "address": "0.0.0.0"}, "unnumberedIntf": "Vlan42"},
                        "ipv4Routable240": False,
                        "lineProtocolStatus": "up",
                        "mtu": 65535,
                    },
                }
            }
        ],
        "inputs": {"number": 2},
        "expected": {"result": "failure", "messages": ["Found 1 Loopbacks when expecting 2"]},
    },
    {
        "name": "success",
        "test": VerifySVI,
        "eos_data": [
            {
                "interfaces": {
                    "Vlan42": {
                        "name": "Vlan42",
                        "interfaceStatus": "connected",
                        "interfaceAddress": {"ipAddr": {"maskLen": 24, "address": "11.11.11.11"}},
                        "ipv4Routable240": False,
                        "lineProtocolStatus": "up",
                        "mtu": 1500,
                    }
                }
            }
        ],
        "inputs": None,
        "expected": {"result": "success"},
    },
    {
        "name": "failure",
        "test": VerifySVI,
        "eos_data": [
            {
                "interfaces": {
                    "Vlan42": {
                        "name": "Vlan42",
                        "interfaceStatus": "notconnect",
                        "interfaceAddress": {"ipAddr": {"maskLen": 24, "address": "11.11.11.11"}},
                        "ipv4Routable240": False,
                        "lineProtocolStatus": "lowerLayerDown",
                        "mtu": 1500,
                    }
                }
            }
        ],
        "inputs": None,
        "expected": {"result": "failure", "messages": ["The following SVIs are not up: ['Vlan42']"]},
    },
    {
        "name": "success",
        "test": VerifyL3MTU,
        "eos_data": [
            {
                "interfaces": {
                    "Ethernet2": {
                        "name": "Ethernet2",
                        "forwardingModel": "routed",
                        "lineProtocolStatus": "up",
                        "interfaceStatus": "connected",
                        "hardware": "ethernet",
                        "mtu": 1500,
                        "l3MtuConfigured": True,
                        "l2Mru": 0,
                    },
                    "Ethernet10": {
                        "name": "Ethernet10",
                        "forwardingModel": "bridged",
                        "lineProtocolStatus": "up",
                        "interfaceStatus": "connected",
                        "hardware": "ethernet",
                        "mtu": 1500,
                        "l3MtuConfigured": False,
                        "l2Mru": 0,
                    },
                    "Management1/1": {
                        "name": "Management0",
                        "forwardingModel": "routed",
                        "lineProtocolStatus": "up",
                        "interfaceStatus": "connected",
                        "hardware": "ethernet",
                        "mtu": 1500,
                        "l3MtuConfigured": False,
                        "l2Mru": 0,
                    },
                    "Port-Channel2": {
                        "name": "Port-Channel2",
                        "forwardingModel": "bridged",
                        "lineProtocolStatus": "lowerLayerDown",
                        "interfaceStatus": "notconnect",
                        "hardware": "portChannel",
                        "mtu": 1500,
                        "l3MtuConfigured": False,
                        "l2Mru": 0,
                    },
                    "Loopback0": {
                        "name": "Loopback0",
                        "forwardingModel": "routed",
                        "lineProtocolStatus": "up",
                        "interfaceStatus": "connected",
                        "hardware": "loopback",
                        "mtu": 65535,
                        "l3MtuConfigured": False,
                        "l2Mru": 0,
                    },
                    "Vxlan1": {
                        "name": "Vxlan1",
                        "forwardingModel": "bridged",
                        "lineProtocolStatus": "down",
                        "interfaceStatus": "notconnect",
                        "hardware": "vxlan",
                        "mtu": 0,
                        "l3MtuConfigured": False,
                        "l2Mru": 0,
                    },
                },
            }
        ],
        "inputs": {"mtu": 1500},
        "expected": {"result": "success"},
    },
    {
        "name": "success",
        "test": VerifyL3MTU,
        "eos_data": [
            {
                "interfaces": {
                    "Ethernet2": {
                        "name": "Ethernet2",
                        "forwardingModel": "routed",
                        "lineProtocolStatus": "up",
                        "interfaceStatus": "connected",
                        "hardware": "ethernet",
                        "mtu": 1500,
                        "l3MtuConfigured": True,
                        "l2Mru": 0,
                    },
                    "Ethernet10": {
                        "name": "Ethernet10",
                        "forwardingModel": "routed",
                        "lineProtocolStatus": "up",
                        "interfaceStatus": "connected",
                        "hardware": "ethernet",
                        "mtu": 1501,
                        "l3MtuConfigured": False,
                        "l2Mru": 0,
                    },
                    "Management0": {
                        "name": "Management0",
                        "forwardingModel": "routed",
                        "lineProtocolStatus": "up",
                        "interfaceStatus": "connected",
                        "hardware": "ethernet",
                        "mtu": 1500,
                        "l3MtuConfigured": False,
                        "l2Mru": 0,
                    },
                    "Port-Channel2": {
                        "name": "Port-Channel2",
                        "forwardingModel": "bridged",
                        "lineProtocolStatus": "lowerLayerDown",
                        "interfaceStatus": "notconnect",
                        "hardware": "portChannel",
                        "mtu": 1500,
                        "l3MtuConfigured": False,
                        "l2Mru": 0,
                    },
                    "Loopback0": {
                        "name": "Loopback0",
                        "forwardingModel": "routed",
                        "lineProtocolStatus": "up",
                        "interfaceStatus": "connected",
                        "hardware": "loopback",
                        "mtu": 65535,
                        "l3MtuConfigured": False,
                        "l2Mru": 0,
                    },
                    "Vxlan1": {
                        "name": "Vxlan1",
                        "forwardingModel": "bridged",
                        "lineProtocolStatus": "down",
                        "interfaceStatus": "notconnect",
                        "hardware": "vxlan",
                        "mtu": 0,
                        "l3MtuConfigured": False,
                        "l2Mru": 0,
                    },
                },
            }
        ],
        "inputs": {"mtu": 1500, "ignored_interfaces": ["Loopback", "Port-Channel", "Management", "Vxlan"], "specific_mtu": [{"Ethernet10": 1501}]},
        "expected": {"result": "success"},
    },
    {
        "name": "failure",
        "test": VerifyL3MTU,
        "eos_data": [
            {
                "interfaces": {
                    "Ethernet2": {
                        "name": "Ethernet2",
                        "forwardingModel": "routed",
                        "lineProtocolStatus": "up",
                        "interfaceStatus": "connected",
                        "hardware": "ethernet",
                        "mtu": 1600,
                        "l3MtuConfigured": True,
                        "l2Mru": 0,
                    },
                    "Ethernet10": {
                        "name": "Ethernet10",
                        "forwardingModel": "routed",
                        "lineProtocolStatus": "up",
                        "interfaceStatus": "connected",
                        "hardware": "ethernet",
                        "mtu": 1500,
                        "l3MtuConfigured": False,
                        "l2Mru": 0,
                    },
                    "Management0": {
                        "name": "Management0",
                        "forwardingModel": "routed",
                        "lineProtocolStatus": "up",
                        "interfaceStatus": "connected",
                        "hardware": "ethernet",
                        "mtu": 1500,
                        "l3MtuConfigured": False,
                        "l2Mru": 0,
                    },
                    "Port-Channel2": {
                        "name": "Port-Channel2",
                        "forwardingModel": "bridged",
                        "lineProtocolStatus": "lowerLayerDown",
                        "interfaceStatus": "notconnect",
                        "hardware": "portChannel",
                        "mtu": 1500,
                        "l3MtuConfigured": False,
                        "l2Mru": 0,
                    },
                    "Loopback0": {
                        "name": "Loopback0",
                        "forwardingModel": "routed",
                        "lineProtocolStatus": "up",
                        "interfaceStatus": "connected",
                        "hardware": "loopback",
                        "mtu": 65535,
                        "l3MtuConfigured": False,
                        "l2Mru": 0,
                    },
                    "Vxlan1": {
                        "name": "Vxlan1",
                        "forwardingModel": "bridged",
                        "lineProtocolStatus": "down",
                        "interfaceStatus": "notconnect",
                        "hardware": "vxlan",
                        "mtu": 0,
                        "l3MtuConfigured": False,
                        "l2Mru": 0,
                    },
                },
            }
        ],
        "inputs": {"mtu": 1500},
        "expected": {"result": "failure", "messages": ["Some interfaces do not have correct MTU configured:\n[{'Ethernet2': 1600}]"]},
    },
    {
        "name": "success",
        "test": VerifyL2MTU,
        "eos_data": [
            {
                "interfaces": {
                    "Ethernet2": {
                        "name": "Ethernet2",
                        "forwardingModel": "routed",
                        "lineProtocolStatus": "up",
                        "interfaceStatus": "connected",
                        "hardware": "ethernet",
                        "mtu": 1500,
                        "l3MtuConfigured": True,
                        "l2Mru": 0,
                    },
                    "Ethernet10": {
                        "name": "Ethernet10",
                        "forwardingModel": "bridged",
                        "lineProtocolStatus": "up",
                        "interfaceStatus": "connected",
                        "hardware": "ethernet",
                        "mtu": 9214,
                        "l3MtuConfigured": False,
                        "l2Mru": 0,
                    },
                    "Management0": {
                        "name": "Management0",
                        "forwardingModel": "routed",
                        "lineProtocolStatus": "up",
                        "interfaceStatus": "connected",
                        "hardware": "ethernet",
                        "mtu": 1500,
                        "l3MtuConfigured": False,
                        "l2Mru": 0,
                    },
                    "Port-Channel2": {
                        "name": "Port-Channel2",
                        "forwardingModel": "bridged",
                        "lineProtocolStatus": "lowerLayerDown",
                        "interfaceStatus": "notconnect",
                        "hardware": "portChannel",
                        "mtu": 9214,
                        "l3MtuConfigured": False,
                        "l2Mru": 0,
                    },
                    "Loopback0": {
                        "name": "Loopback0",
                        "forwardingModel": "routed",
                        "lineProtocolStatus": "up",
                        "interfaceStatus": "connected",
                        "hardware": "loopback",
                        "mtu": 65535,
                        "l3MtuConfigured": False,
                        "l2Mru": 0,
                    },
                    "Vxlan1": {
                        "name": "Vxlan1",
                        "forwardingModel": "bridged",
                        "lineProtocolStatus": "down",
                        "interfaceStatus": "notconnect",
                        "hardware": "vxlan",
                        "mtu": 0,
                        "l3MtuConfigured": False,
                        "l2Mru": 0,
                    },
                },
            }
        ],
        "inputs": {"mtu": 9214},
        "expected": {"result": "success"},
    },
    {
        "name": "failure",
        "test": VerifyL2MTU,
        "eos_data": [
            {
                "interfaces": {
                    "Ethernet2": {
                        "name": "Ethernet2",
                        "forwardingModel": "routed",
                        "lineProtocolStatus": "up",
                        "interfaceStatus": "connected",
                        "hardware": "ethernet",
                        "mtu": 1600,
                        "l3MtuConfigured": True,
                        "l2Mru": 0,
                    },
                    "Ethernet10": {
                        "name": "Ethernet10",
                        "forwardingModel": "bridged",
                        "lineProtocolStatus": "up",
                        "interfaceStatus": "connected",
                        "hardware": "ethernet",
                        "mtu": 9214,
                        "l3MtuConfigured": False,
                        "l2Mru": 0,
                    },
                    "Management0": {
                        "name": "Management0",
                        "forwardingModel": "routed",
                        "lineProtocolStatus": "up",
                        "interfaceStatus": "connected",
                        "hardware": "ethernet",
                        "mtu": 1500,
                        "l3MtuConfigured": False,
                        "l2Mru": 0,
                    },
                    "Port-Channel2": {
                        "name": "Port-Channel2",
                        "forwardingModel": "bridged",
                        "lineProtocolStatus": "lowerLayerDown",
                        "interfaceStatus": "notconnect",
                        "hardware": "portChannel",
                        "mtu": 9214,
                        "l3MtuConfigured": False,
                        "l2Mru": 0,
                    },
                    "Loopback0": {
                        "name": "Loopback0",
                        "forwardingModel": "routed",
                        "lineProtocolStatus": "up",
                        "interfaceStatus": "connected",
                        "hardware": "loopback",
                        "mtu": 65535,
                        "l3MtuConfigured": False,
                        "l2Mru": 0,
                    },
                    "Vxlan1": {
                        "name": "Vxlan1",
                        "forwardingModel": "bridged",
                        "lineProtocolStatus": "down",
                        "interfaceStatus": "notconnect",
                        "hardware": "vxlan",
                        "mtu": 0,
                        "l3MtuConfigured": False,
                        "l2Mru": 0,
                    },
                },
            }
        ],
        "inputs": {"mtu": 1500},
        "expected": {"result": "failure", "messages": ["Some L2 interfaces do not have correct MTU configured:\n[{'Ethernet10': 9214}, {'Port-Channel2': 9214}]"]},
    },
    {
        "name": "success",
        "test": VerifyIPProxyARP,
        "eos_data": [
            {
                "interfaces": {
                    "Ethernet1": {
                        "name": "Ethernet1",
                        "lineProtocolStatus": "up",
                        "interfaceStatus": "connected",
                        "mtu": 1500,
                        "interfaceAddressBrief": {"ipAddr": {"address": "10.1.0.0", "maskLen": 31}},
                        "ipv4Routable240": False,
                        "ipv4Routable0": False,
                        "enabled": True,
                        "description": "P2P_LINK_TO_NW-CORE_Ethernet1",
                        "proxyArp": True,
                        "localProxyArp": False,
                        "gratuitousArp": False,
                        "vrf": "default",
                        "urpf": "disable",
                        "addresslessForwarding": "isInvalid",
                        "directedBroadcastEnabled": False,
                        "maxMssIngress": 0,
                        "maxMssEgress": 0,
                    }
                }
            },
            {
                "interfaces": {
                    "Ethernet2": {
                        "name": "Ethernet2",
                        "lineProtocolStatus": "up",
                        "interfaceStatus": "connected",
                        "mtu": 1500,
                        "interfaceAddressBrief": {"ipAddr": {"address": "10.1.0.2", "maskLen": 31}},
                        "ipv4Routable240": False,
                        "ipv4Routable0": False,
                        "enabled": True,
                        "description": "P2P_LINK_TO_SW-CORE_Ethernet1",
                        "proxyArp": True,
                        "localProxyArp": False,
                        "gratuitousArp": False,
                        "vrf": "default",
                        "urpf": "disable",
                        "addresslessForwarding": "isInvalid",
                        "directedBroadcastEnabled": False,
                        "maxMssIngress": 0,
                        "maxMssEgress": 0,
                    }
                }
            },
        ],
        "inputs": {"interfaces": ["Ethernet1", "Ethernet2"]},
        "expected": {"result": "success"},
    },
    {
        "name": "failure",
        "test": VerifyIPProxyARP,
        "eos_data": [
            {
                "interfaces": {
                    "Ethernet1": {
                        "name": "Ethernet1",
                        "lineProtocolStatus": "up",
                        "interfaceStatus": "connected",
                        "mtu": 1500,
                        "interfaceAddressBrief": {"ipAddr": {"address": "10.1.0.0", "maskLen": 31}},
                        "ipv4Routable240": False,
                        "ipv4Routable0": False,
                        "enabled": True,
                        "description": "P2P_LINK_TO_NW-CORE_Ethernet1",
                        "proxyArp": True,
                        "localProxyArp": False,
                        "gratuitousArp": False,
                        "vrf": "default",
                        "urpf": "disable",
                        "addresslessForwarding": "isInvalid",
                        "directedBroadcastEnabled": False,
                        "maxMssIngress": 0,
                        "maxMssEgress": 0,
                    }
                }
            },
            {
                "interfaces": {
                    "Ethernet2": {
                        "name": "Ethernet2",
                        "lineProtocolStatus": "up",
                        "interfaceStatus": "connected",
                        "mtu": 1500,
                        "interfaceAddressBrief": {"ipAddr": {"address": "10.1.0.2", "maskLen": 31}},
                        "ipv4Routable240": False,
                        "ipv4Routable0": False,
                        "enabled": True,
                        "description": "P2P_LINK_TO_SW-CORE_Ethernet1",
                        "proxyArp": False,
                        "localProxyArp": False,
                        "gratuitousArp": False,
                        "vrf": "default",
                        "urpf": "disable",
                        "addresslessForwarding": "isInvalid",
                        "directedBroadcastEnabled": False,
                        "maxMssIngress": 0,
                        "maxMssEgress": 0,
                    }
                }
            },
        ],
        "inputs": {"interfaces": ["Ethernet1", "Ethernet2"]},
        "expected": {"result": "failure", "messages": ["The following interface(s) have Proxy-ARP disabled: ['Ethernet2']"]},
    },
    {
        "name": "success",
        "test": VerifyIpVirtualRouterMac,
        "eos_data": [
            {
                "virtualMacs": [
                    {
                        "macAddress": "00:1c:73:00:dc:01",
                    }
                ],
            }
        ],
        "inputs": {"mac_address": "00:1c:73:00:dc:01"},
        "expected": {"result": "success"},
    },
    {
        "name": "faliure-incorrect-mac-address",
        "test": VerifyIpVirtualRouterMac,
        "eos_data": [
            {
                "virtualMacs": [
                    {
                        "macAddress": "00:00:00:00:00:00",
                    }
                ],
            }
        ],
        "inputs": {"mac_address": "00:1c:73:00:dc:01"},
        "expected": {"result": "failure", "messages": ["IP virtual router MAC address `00:1c:73:00:dc:01` is not configured."]},
    },
]
