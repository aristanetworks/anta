# Copyright (c) 2023-2025 Arista Networks, Inc.
# Use of this source code is governed by the Apache License 2.0
# that can be found in the LICENSE file.
"""Test inputs for anta.tests.interfaces."""

# pylint: disable=C0302
from __future__ import annotations

from typing import Any

from anta.tests.interfaces import (
    VerifyIllegalLACP,
    VerifyInterfaceDiscards,
    VerifyInterfaceErrDisabled,
    VerifyInterfaceErrors,
    VerifyInterfaceIPv4,
    VerifyInterfacesSpeed,
    VerifyInterfacesStatus,
    VerifyInterfaceUtilization,
    VerifyIPProxyARP,
    VerifyIpVirtualRouterMac,
    VerifyL2MTU,
    VerifyL3MTU,
    VerifyLACPInterfacesStatus,
    VerifyLoopbackCount,
    VerifyPortChannels,
    VerifyStormControlDrops,
    VerifySVI,
)
from tests.units.anta_tests import test

DATA: list[dict[str, Any]] = [
    {
        "name": "success",
        "test": VerifyInterfaceUtilization,
        "eos_data": [
            {
                "interfaces": {
                    "Ethernet1/1": {
                        "description": "P2P_LINK_TO_DC1-SPINE1_Ethernet1/1",
                        "interval": 300,
                        "inBpsRate": 2242.2497205060313,
                        "inPktsRate": 0.00028663359326985426,
                        "inPpsRate": 3.9005388262031966,
                        "outBpsRate": 0.0,
                        "outPktsRate": 0.0,
                        "outPpsRate": 0.0,
                        "lastUpdateTimestamp": 1710253727.138605,
                    },
                    "Port-Channel31": {
                        "description": "MLAG_PEER_dc1-leaf1b_Po31",
                        "interval": 300,
                        "inBpsRate": 1862.4876594267096,
                        "inPktsRate": 0.00011473185873493155,
                        "inPpsRate": 2.7009344704495084,
                        "outBpsRate": 1758.0044570479704,
                        "outPktsRate": 0.00010844978034772172,
                        "outPpsRate": 2.5686946869154013,
                        "lastUpdateTimestamp": 1710253726.4029949,
                    },
                }
            },
            {
                "interfaces": {
                    "Ethernet1/1": {
                        "name": "Ethernet1/1",
                        "forwardingModel": "routed",
                        "lineProtocolStatus": "up",
                        "interfaceStatus": "connected",
                        "hardware": "ethernet",
                        "interfaceAddress": [
                            {
                                "primaryIp": {"address": "10.255.255.1", "maskLen": 31},
                                "secondaryIps": {},
                                "secondaryIpsOrderedList": [],
                                "virtualIp": {"address": "0.0.0.0", "maskLen": 0},
                                "virtualSecondaryIps": {},
                                "virtualSecondaryIpsOrderedList": [],
                                "broadcastAddress": "255.255.255.255",
                                "dhcp": False,
                            }
                        ],
                        "physicalAddress": "aa:c1:ab:7e:76:36",
                        "burnedInAddress": "aa:c1:ab:7e:76:36",
                        "description": "P2P_LINK_TO_DC1-SPINE1_Ethernet1/1",
                        "bandwidth": 1000000000,
                        "mtu": 1500,
                        "l3MtuConfigured": True,
                        "l2Mru": 0,
                        "lastStatusChangeTimestamp": 1710234511.3085763,
                        "interfaceStatistics": {
                            "updateInterval": 300.0,
                            "inBitsRate": 2240.0023281094,
                            "inPktsRate": 3.8978070399448654,
                            "outBitsRate": 0.0,
                            "outPktsRate": 0.0,
                        },
                        "interfaceCounters": {
                            "inOctets": 5413008,
                            "inUcastPkts": 74693,
                            "inMulticastPkts": 643,
                            "inBroadcastPkts": 1,
                            "inDiscards": 0,
                            "inTotalPkts": 75337,
                            "outOctets": 0,
                            "outUcastPkts": 0,
                            "outMulticastPkts": 0,
                            "outBroadcastPkts": 0,
                            "outDiscards": 0,
                            "outTotalPkts": 0,
                            "linkStatusChanges": 2,
                            "totalInErrors": 0,
                            "inputErrorsDetail": {"runtFrames": 0, "giantFrames": 0, "fcsErrors": 0, "alignmentErrors": 0, "symbolErrors": 0, "rxPause": 0},
                            "totalOutErrors": 0,
                            "outputErrorsDetail": {"collisions": 0, "lateCollisions": 0, "deferredTransmissions": 0, "txPause": 0},
                            "counterRefreshTime": 1710253760.6489396,
                        },
                        "duplex": "duplexFull",
                        "autoNegotiate": "unknown",
                        "loopbackMode": "loopbackNone",
                        "lanes": 0,
                    },
                    "Port-Channel31": {
                        "name": "Port-Channel31",
                        "forwardingModel": "bridged",
                        "lineProtocolStatus": "up",
                        "interfaceStatus": "connected",
                        "hardware": "portChannel",
                        "interfaceAddress": [],
                        "physicalAddress": "aa:c1:ab:72:58:40",
                        "description": "MLAG_PEER_dc1-leaf1b_Po31",
                        "bandwidth": 2000000000,
                        "mtu": 9214,
                        "l3MtuConfigured": False,
                        "l2Mru": 0,
                        "lastStatusChangeTimestamp": 1710234510.1133935,
                        "interfaceStatistics": {
                            "updateInterval": 300.0,
                            "inBitsRate": 1854.287898883752,
                            "inPktsRate": 2.6902775246495665,
                            "outBitsRate": 1749.1141130864632,
                            "outPktsRate": 2.5565618978302362,
                        },
                        "interfaceCounters": {
                            "inOctets": 4475556,
                            "inUcastPkts": 48949,
                            "inMulticastPkts": 2579,
                            "inBroadcastPkts": 2,
                            "inDiscards": 0,
                            "inTotalPkts": 51530,
                            "outOctets": 4230011,
                            "outUcastPkts": 48982,
                            "outMulticastPkts": 6,
                            "outBroadcastPkts": 2,
                            "outDiscards": 0,
                            "outTotalPkts": 48990,
                            "linkStatusChanges": 2,
                            "totalInErrors": 0,
                            "totalOutErrors": 0,
                            "counterRefreshTime": 1710253760.6500373,
                        },
                        "memberInterfaces": {
                            "Ethernet3/1": {"bandwidth": 1000000000, "duplex": "duplexFull"},
                            "Ethernet4/1": {"bandwidth": 1000000000, "duplex": "duplexFull"},
                        },
                        "fallbackEnabled": False,
                        "fallbackEnabledType": "fallbackNone",
                    },
                }
            },
        ],
        "inputs": {"threshold": 70.0},
        "expected": {"result": "success"},
    },
    {
        "name": "success-ignored-interface",
        "test": VerifyInterfaceUtilization,
        "eos_data": [
            {
                "interfaces": {
                    "Ethernet1/1": {
                        "description": "P2P_LINK_TO_DC1-SPINE1_Ethernet1/1",
                        "interval": 300,
                        "inBpsRate": 2242.2497205060313,
                        "inPktsRate": 0.00028663359326985426,
                        "inPpsRate": 3.9005388262031966,
                        "outBpsRate": 0.0,
                        "outPktsRate": 0.0,
                        "outPpsRate": 0.0,
                        "lastUpdateTimestamp": 1710253727.138605,
                    },
                    "Port-Channel31": {
                        "description": "MLAG_PEER_dc1-leaf1b_Po31",
                        "interval": 300,
                        "inBpsRate": 1862.4876594267096,
                        "inPktsRate": 0.00011473185873493155,
                        "inPpsRate": 2.7009344704495084,
                        "outBpsRate": 1758.0044570479704,
                        "outPktsRate": 0.00010844978034772172,
                        "outPpsRate": 2.5686946869154013,
                        "lastUpdateTimestamp": 1710253726.4029949,
                    },
                    "Port-Channel51": {
                        "description": "dc1-leaf1-server1",
                        "interval": 300,
                        "inBpsRate": 0.0023680437493116147,
                        "inPpsRate": 2.3125427239371238e-06,
                        "outBpsRate": 0.0,
                        "outPpsRate": 0.0,
                        "lastUpdateTimestamp": 1712928643.7805147,
                    },
                },
            },
            {
                "interfaces": {
                    "Ethernet1/1": {
                        "name": "Ethernet1/1",
                        "forwardingModel": "routed",
                        "lineProtocolStatus": "up",
                        "interfaceStatus": "connected",
                        "hardware": "ethernet",
                        "interfaceAddress": [
                            {
                                "primaryIp": {"address": "10.255.255.1", "maskLen": 31},
                                "secondaryIps": {},
                                "secondaryIpsOrderedList": [],
                                "virtualIp": {"address": "0.0.0.0", "maskLen": 0},
                                "virtualSecondaryIps": {},
                                "virtualSecondaryIpsOrderedList": [],
                                "broadcastAddress": "255.255.255.255",
                                "dhcp": False,
                            }
                        ],
                        "physicalAddress": "aa:c1:ab:7e:76:36",
                        "burnedInAddress": "aa:c1:ab:7e:76:36",
                        "description": "P2P_LINK_TO_DC1-SPINE1_Ethernet1/1",
                        "bandwidth": 1000000000,
                        "mtu": 1500,
                        "l3MtuConfigured": True,
                        "l2Mru": 0,
                        "lastStatusChangeTimestamp": 1710234511.3085763,
                        "interfaceStatistics": {
                            "updateInterval": 300.0,
                            "inBitsRate": 2240.0023281094,
                            "inPktsRate": 3.8978070399448654,
                            "outBitsRate": 0.0,
                            "outPktsRate": 0.0,
                        },
                        "interfaceCounters": {
                            "inOctets": 5413008,
                            "inUcastPkts": 74693,
                            "inMulticastPkts": 643,
                            "inBroadcastPkts": 1,
                            "inDiscards": 0,
                            "inTotalPkts": 75337,
                            "outOctets": 0,
                            "outUcastPkts": 0,
                            "outMulticastPkts": 0,
                            "outBroadcastPkts": 0,
                            "outDiscards": 0,
                            "outTotalPkts": 0,
                            "linkStatusChanges": 2,
                            "totalInErrors": 0,
                            "inputErrorsDetail": {"runtFrames": 0, "giantFrames": 0, "fcsErrors": 0, "alignmentErrors": 0, "symbolErrors": 0, "rxPause": 0},
                            "totalOutErrors": 0,
                            "outputErrorsDetail": {"collisions": 0, "lateCollisions": 0, "deferredTransmissions": 0, "txPause": 0},
                            "counterRefreshTime": 1710253760.6489396,
                        },
                        "duplex": "duplexFull",
                        "autoNegotiate": "unknown",
                        "loopbackMode": "loopbackNone",
                        "lanes": 0,
                    },
                    "Port-Channel31": {
                        "name": "Port-Channel31",
                        "forwardingModel": "bridged",
                        "lineProtocolStatus": "up",
                        "interfaceStatus": "connected",
                        "hardware": "portChannel",
                        "interfaceAddress": [],
                        "physicalAddress": "aa:c1:ab:72:58:40",
                        "description": "MLAG_PEER_dc1-leaf1b_Po31",
                        "bandwidth": 2000000000,
                        "mtu": 9214,
                        "l3MtuConfigured": False,
                        "l2Mru": 0,
                        "lastStatusChangeTimestamp": 1710234510.1133935,
                        "interfaceStatistics": {
                            "updateInterval": 300.0,
                            "inBitsRate": 1854.287898883752,
                            "inPktsRate": 2.6902775246495665,
                            "outBitsRate": 1749.1141130864632,
                            "outPktsRate": 2.5565618978302362,
                        },
                        "interfaceCounters": {
                            "inOctets": 4475556,
                            "inUcastPkts": 48949,
                            "inMulticastPkts": 2579,
                            "inBroadcastPkts": 2,
                            "inDiscards": 0,
                            "inTotalPkts": 51530,
                            "outOctets": 4230011,
                            "outUcastPkts": 48982,
                            "outMulticastPkts": 6,
                            "outBroadcastPkts": 2,
                            "outDiscards": 0,
                            "outTotalPkts": 48990,
                            "linkStatusChanges": 2,
                            "totalInErrors": 0,
                            "totalOutErrors": 0,
                            "counterRefreshTime": 1710253760.6500373,
                        },
                        "memberInterfaces": {
                            "Ethernet3/1": {"bandwidth": 1000000000, "duplex": "duplexFull"},
                            "Ethernet4/1": {"bandwidth": 1000000000, "duplex": "duplexFull"},
                        },
                        "fallbackEnabled": False,
                        "fallbackEnabledType": "fallbackNone",
                    },
                    "Port-Channel51": {
                        "name": "Port-Channel51",
                        "forwardingModel": "bridged",
                        "lineProtocolStatus": "lowerLayerDown",
                        "interfaceStatus": "notconnect",
                        "hardware": "portChannel",
                        "interfaceAddress": [],
                        "physicalAddress": "00:00:00:00:00:00",
                        "description": "dc1-leaf1-server1",
                        "bandwidth": 0,
                        "mtu": 9214,
                        "l3MtuConfigured": False,
                        "l2Mru": 0,
                        "lastStatusChangeTimestamp": 1712925798.5035574,
                        "interfaceStatistics": {
                            "updateInterval": 300.0,
                            "inBitsRate": 0.00839301770723288,
                            "inPktsRate": 8.19630635471961e-06,
                            "outBitsRate": 0.0,
                            "outPktsRate": 0.0,
                        },
                        "interfaceCounters": {
                            "inOctets": 329344,
                            "inUcastPkts": 0,
                            "inMulticastPkts": 2573,
                            "inBroadcastPkts": 0,
                            "inDiscards": 0,
                            "inTotalPkts": 2573,
                            "outOctets": 0,
                            "outUcastPkts": 0,
                            "outMulticastPkts": 0,
                            "outBroadcastPkts": 0,
                            "outDiscards": 0,
                            "outTotalPkts": 0,
                            "linkStatusChanges": 3,
                            "totalInErrors": 0,
                            "totalOutErrors": 0,
                            "counterRefreshTime": 1712928265.9816775,
                        },
                        "memberInterfaces": {},
                        "fallbackEnabled": False,
                        "fallbackEnabledType": "fallbackNone",
                    },
                }
            },
        ],
        "inputs": {"threshold": 70.0},
        "expected": {"result": "success"},
    },
    {
        "name": "failure",
        "test": VerifyInterfaceUtilization,
        "eos_data": [
            {
                "interfaces": {
                    "Ethernet1/1": {
                        "description": "P2P_LINK_TO_DC1-SPINE1_Ethernet1/1",
                        "interval": 300,
                        "inBpsRate": 100000000.0,
                        "inPktsRate": 0.00028663359326985426,
                        "inPpsRate": 3.9005388262031966,
                        "outBpsRate": 0.0,
                        "outPktsRate": 0.0,
                        "outPpsRate": 0.0,
                        "lastUpdateTimestamp": 1710253727.138605,
                    },
                    "Port-Channel31": {
                        "description": "MLAG_PEER_dc1-leaf1b_Po31",
                        "interval": 300,
                        "inBpsRate": 1862.4876594267096,
                        "inPktsRate": 0.00011473185873493155,
                        "inPpsRate": 2.7009344704495084,
                        "outBpsRate": 100000000.0,
                        "outPktsRate": 0.00010844978034772172,
                        "outPpsRate": 2.5686946869154013,
                        "lastUpdateTimestamp": 1710253726.4029949,
                    },
                }
            },
            {
                "interfaces": {
                    "Ethernet1/1": {
                        "name": "Ethernet1/1",
                        "forwardingModel": "routed",
                        "lineProtocolStatus": "up",
                        "interfaceStatus": "connected",
                        "hardware": "ethernet",
                        "interfaceAddress": [
                            {
                                "primaryIp": {"address": "10.255.255.1", "maskLen": 31},
                                "secondaryIps": {},
                                "secondaryIpsOrderedList": [],
                                "virtualIp": {"address": "0.0.0.0", "maskLen": 0},
                                "virtualSecondaryIps": {},
                                "virtualSecondaryIpsOrderedList": [],
                                "broadcastAddress": "255.255.255.255",
                                "dhcp": False,
                            }
                        ],
                        "physicalAddress": "aa:c1:ab:7e:76:36",
                        "burnedInAddress": "aa:c1:ab:7e:76:36",
                        "description": "P2P_LINK_TO_DC1-SPINE1_Ethernet1/1",
                        "bandwidth": 1000000000,
                        "mtu": 1500,
                        "l3MtuConfigured": True,
                        "l2Mru": 0,
                        "lastStatusChangeTimestamp": 1710234511.3085763,
                        "interfaceStatistics": {
                            "updateInterval": 300.0,
                            "inBitsRate": 2240.0023281094,
                            "inPktsRate": 3.8978070399448654,
                            "outBitsRate": 0.0,
                            "outPktsRate": 0.0,
                        },
                        "interfaceCounters": {
                            "inOctets": 5413008,
                            "inUcastPkts": 74693,
                            "inMulticastPkts": 643,
                            "inBroadcastPkts": 1,
                            "inDiscards": 0,
                            "inTotalPkts": 75337,
                            "outOctets": 0,
                            "outUcastPkts": 0,
                            "outMulticastPkts": 0,
                            "outBroadcastPkts": 0,
                            "outDiscards": 0,
                            "outTotalPkts": 0,
                            "linkStatusChanges": 2,
                            "totalInErrors": 0,
                            "inputErrorsDetail": {"runtFrames": 0, "giantFrames": 0, "fcsErrors": 0, "alignmentErrors": 0, "symbolErrors": 0, "rxPause": 0},
                            "totalOutErrors": 0,
                            "outputErrorsDetail": {"collisions": 0, "lateCollisions": 0, "deferredTransmissions": 0, "txPause": 0},
                            "counterRefreshTime": 1710253760.6489396,
                        },
                        "duplex": "duplexFull",
                        "autoNegotiate": "unknown",
                        "loopbackMode": "loopbackNone",
                        "lanes": 0,
                    },
                    "Port-Channel31": {
                        "name": "Port-Channel31",
                        "forwardingModel": "bridged",
                        "lineProtocolStatus": "up",
                        "interfaceStatus": "connected",
                        "hardware": "portChannel",
                        "interfaceAddress": [],
                        "physicalAddress": "aa:c1:ab:72:58:40",
                        "description": "MLAG_PEER_dc1-leaf1b_Po31",
                        "bandwidth": 2000000000,
                        "mtu": 9214,
                        "l3MtuConfigured": False,
                        "l2Mru": 0,
                        "lastStatusChangeTimestamp": 1710234510.1133935,
                        "interfaceStatistics": {
                            "updateInterval": 300.0,
                            "inBitsRate": 1854.287898883752,
                            "inPktsRate": 2.6902775246495665,
                            "outBitsRate": 1749.1141130864632,
                            "outPktsRate": 2.5565618978302362,
                        },
                        "interfaceCounters": {
                            "inOctets": 4475556,
                            "inUcastPkts": 48949,
                            "inMulticastPkts": 2579,
                            "inBroadcastPkts": 2,
                            "inDiscards": 0,
                            "inTotalPkts": 51530,
                            "outOctets": 4230011,
                            "outUcastPkts": 48982,
                            "outMulticastPkts": 6,
                            "outBroadcastPkts": 2,
                            "outDiscards": 0,
                            "outTotalPkts": 48990,
                            "linkStatusChanges": 2,
                            "totalInErrors": 0,
                            "totalOutErrors": 0,
                            "counterRefreshTime": 1710253760.6500373,
                        },
                        "memberInterfaces": {
                            "Ethernet3/1": {"bandwidth": 1000000000, "duplex": "duplexFull"},
                            "Ethernet4/1": {"bandwidth": 1000000000, "duplex": "duplexFull"},
                        },
                        "fallbackEnabled": False,
                        "fallbackEnabledType": "fallbackNone",
                    },
                }
            },
        ],
        "inputs": {"threshold": 3.0},
        "expected": {
            "result": "failure",
            "messages": [
                "Interface: Ethernet1/1 BPS Rate: inBpsRate - Usage exceeds the threshold - Expected: < 3.0% Actual: 10.0%",
                "Interface: Port-Channel31 BPS Rate: outBpsRate - Usage exceeds the threshold - Expected: < 3.0% Actual: 5.0%",
            ],
        },
    },
    {
        "name": "error-duplex-half",
        "test": VerifyInterfaceUtilization,
        "eos_data": [
            {
                "interfaces": {
                    "Ethernet1/1": {
                        "description": "P2P_LINK_TO_DC1-SPINE1_Ethernet1/1",
                        "interval": 300,
                        "inBpsRate": 2242.2497205060313,
                        "inPktsRate": 0.00028663359326985426,
                        "inPpsRate": 3.9005388262031966,
                        "outBpsRate": 0.0,
                        "outPktsRate": 0.0,
                        "outPpsRate": 0.0,
                        "lastUpdateTimestamp": 1710253727.138605,
                    },
                    "Port-Channel31": {
                        "description": "MLAG_PEER_dc1-leaf1b_Po31",
                        "interval": 300,
                        "inBpsRate": 1862.4876594267096,
                        "inPktsRate": 0.00011473185873493155,
                        "inPpsRate": 2.7009344704495084,
                        "outBpsRate": 1758.0044570479704,
                        "outPktsRate": 0.00010844978034772172,
                        "outPpsRate": 2.5686946869154013,
                        "lastUpdateTimestamp": 1710253726.4029949,
                    },
                }
            },
            {
                "interfaces": {
                    "Ethernet1/1": {
                        "name": "Ethernet1/1",
                        "forwardingModel": "routed",
                        "lineProtocolStatus": "up",
                        "interfaceStatus": "connected",
                        "hardware": "ethernet",
                        "interfaceAddress": [
                            {
                                "primaryIp": {"address": "10.255.255.1", "maskLen": 31},
                                "secondaryIps": {},
                                "secondaryIpsOrderedList": [],
                                "virtualIp": {"address": "0.0.0.0", "maskLen": 0},
                                "virtualSecondaryIps": {},
                                "virtualSecondaryIpsOrderedList": [],
                                "broadcastAddress": "255.255.255.255",
                                "dhcp": False,
                            }
                        ],
                        "physicalAddress": "aa:c1:ab:7e:76:36",
                        "burnedInAddress": "aa:c1:ab:7e:76:36",
                        "description": "P2P_LINK_TO_DC1-SPINE1_Ethernet1/1",
                        "bandwidth": 1000000000,
                        "mtu": 1500,
                        "l3MtuConfigured": True,
                        "l2Mru": 0,
                        "lastStatusChangeTimestamp": 1710234511.3085763,
                        "interfaceStatistics": {
                            "updateInterval": 300.0,
                            "inBitsRate": 2240.0023281094,
                            "inPktsRate": 3.8978070399448654,
                            "outBitsRate": 0.0,
                            "outPktsRate": 0.0,
                        },
                        "interfaceCounters": {
                            "inOctets": 5413008,
                            "inUcastPkts": 74693,
                            "inMulticastPkts": 643,
                            "inBroadcastPkts": 1,
                            "inDiscards": 0,
                            "inTotalPkts": 75337,
                            "outOctets": 0,
                            "outUcastPkts": 0,
                            "outMulticastPkts": 0,
                            "outBroadcastPkts": 0,
                            "outDiscards": 0,
                            "outTotalPkts": 0,
                            "linkStatusChanges": 2,
                            "totalInErrors": 0,
                            "inputErrorsDetail": {"runtFrames": 0, "giantFrames": 0, "fcsErrors": 0, "alignmentErrors": 0, "symbolErrors": 0, "rxPause": 0},
                            "totalOutErrors": 0,
                            "outputErrorsDetail": {"collisions": 0, "lateCollisions": 0, "deferredTransmissions": 0, "txPause": 0},
                            "counterRefreshTime": 1710253760.6489396,
                        },
                        "duplex": "duplexHalf",
                        "autoNegotiate": "unknown",
                        "loopbackMode": "loopbackNone",
                        "lanes": 0,
                    },
                    "Port-Channel31": {
                        "name": "Port-Channel31",
                        "forwardingModel": "bridged",
                        "lineProtocolStatus": "up",
                        "interfaceStatus": "connected",
                        "hardware": "portChannel",
                        "interfaceAddress": [],
                        "physicalAddress": "aa:c1:ab:72:58:40",
                        "description": "MLAG_PEER_dc1-leaf1b_Po31",
                        "bandwidth": 2000000000,
                        "mtu": 9214,
                        "l3MtuConfigured": False,
                        "l2Mru": 0,
                        "lastStatusChangeTimestamp": 1710234510.1133935,
                        "interfaceStatistics": {
                            "updateInterval": 300.0,
                            "inBitsRate": 1854.287898883752,
                            "inPktsRate": 2.6902775246495665,
                            "outBitsRate": 1749.1141130864632,
                            "outPktsRate": 2.5565618978302362,
                        },
                        "interfaceCounters": {
                            "inOctets": 4475556,
                            "inUcastPkts": 48949,
                            "inMulticastPkts": 2579,
                            "inBroadcastPkts": 2,
                            "inDiscards": 0,
                            "inTotalPkts": 51530,
                            "outOctets": 4230011,
                            "outUcastPkts": 48982,
                            "outMulticastPkts": 6,
                            "outBroadcastPkts": 2,
                            "outDiscards": 0,
                            "outTotalPkts": 48990,
                            "linkStatusChanges": 2,
                            "totalInErrors": 0,
                            "totalOutErrors": 0,
                            "counterRefreshTime": 1710253760.6500373,
                        },
                        "memberInterfaces": {
                            "Ethernet3/1": {"bandwidth": 1000000000, "duplex": "duplexFull"},
                            "Ethernet4/1": {"bandwidth": 1000000000, "duplex": "duplexFull"},
                        },
                        "fallbackEnabled": False,
                        "fallbackEnabledType": "fallbackNone",
                    },
                }
            },
        ],
        "inputs": {"threshold": 70.0},
        "expected": {
            "result": "failure",
            "messages": ["Interface: Ethernet1/1 - Test not implemented for non-full-duplex interfaces - Expected: duplexFull Actual: duplexHalf"],
        },
    },
    {
        "name": "error-duplex-half-po",
        "test": VerifyInterfaceUtilization,
        "eos_data": [
            {
                "interfaces": {
                    "Ethernet1/1": {
                        "description": "P2P_LINK_TO_DC1-SPINE1_Ethernet1/1",
                        "interval": 300,
                        "inBpsRate": 2242.2497205060313,
                        "inPktsRate": 0.00028663359326985426,
                        "inPpsRate": 3.9005388262031966,
                        "outBpsRate": 0.0,
                        "outPktsRate": 0.0,
                        "outPpsRate": 0.0,
                        "lastUpdateTimestamp": 1710253727.138605,
                    },
                    "Port-Channel31": {
                        "description": "MLAG_PEER_dc1-leaf1b_Po31",
                        "interval": 300,
                        "inBpsRate": 1862.4876594267096,
                        "inPktsRate": 0.00011473185873493155,
                        "inPpsRate": 2.7009344704495084,
                        "outBpsRate": 1758.0044570479704,
                        "outPktsRate": 0.00010844978034772172,
                        "outPpsRate": 2.5686946869154013,
                        "lastUpdateTimestamp": 1710253726.4029949,
                    },
                }
            },
            {
                "interfaces": {
                    "Ethernet1/1": {
                        "name": "Ethernet1/1",
                        "forwardingModel": "routed",
                        "lineProtocolStatus": "up",
                        "interfaceStatus": "connected",
                        "hardware": "ethernet",
                        "interfaceAddress": [
                            {
                                "primaryIp": {"address": "10.255.255.1", "maskLen": 31},
                                "secondaryIps": {},
                                "secondaryIpsOrderedList": [],
                                "virtualIp": {"address": "0.0.0.0", "maskLen": 0},
                                "virtualSecondaryIps": {},
                                "virtualSecondaryIpsOrderedList": [],
                                "broadcastAddress": "255.255.255.255",
                                "dhcp": False,
                            }
                        ],
                        "physicalAddress": "aa:c1:ab:7e:76:36",
                        "burnedInAddress": "aa:c1:ab:7e:76:36",
                        "description": "P2P_LINK_TO_DC1-SPINE1_Ethernet1/1",
                        "bandwidth": 1000000000,
                        "mtu": 1500,
                        "l3MtuConfigured": True,
                        "l2Mru": 0,
                        "lastStatusChangeTimestamp": 1710234511.3085763,
                        "interfaceStatistics": {
                            "updateInterval": 300.0,
                            "inBitsRate": 2240.0023281094,
                            "inPktsRate": 3.8978070399448654,
                            "outBitsRate": 0.0,
                            "outPktsRate": 0.0,
                        },
                        "interfaceCounters": {
                            "inOctets": 5413008,
                            "inUcastPkts": 74693,
                            "inMulticastPkts": 643,
                            "inBroadcastPkts": 1,
                            "inDiscards": 0,
                            "inTotalPkts": 75337,
                            "outOctets": 0,
                            "outUcastPkts": 0,
                            "outMulticastPkts": 0,
                            "outBroadcastPkts": 0,
                            "outDiscards": 0,
                            "outTotalPkts": 0,
                            "linkStatusChanges": 2,
                            "totalInErrors": 0,
                            "inputErrorsDetail": {"runtFrames": 0, "giantFrames": 0, "fcsErrors": 0, "alignmentErrors": 0, "symbolErrors": 0, "rxPause": 0},
                            "totalOutErrors": 0,
                            "outputErrorsDetail": {"collisions": 0, "lateCollisions": 0, "deferredTransmissions": 0, "txPause": 0},
                            "counterRefreshTime": 1710253760.6489396,
                        },
                        "duplex": "duplexFull",
                        "autoNegotiate": "unknown",
                        "loopbackMode": "loopbackNone",
                        "lanes": 0,
                    },
                    "Port-Channel31": {
                        "name": "Port-Channel31",
                        "forwardingModel": "bridged",
                        "lineProtocolStatus": "up",
                        "interfaceStatus": "connected",
                        "hardware": "portChannel",
                        "interfaceAddress": [],
                        "physicalAddress": "aa:c1:ab:72:58:40",
                        "description": "MLAG_PEER_dc1-leaf1b_Po31",
                        "bandwidth": 2000000000,
                        "mtu": 9214,
                        "l3MtuConfigured": False,
                        "l2Mru": 0,
                        "lastStatusChangeTimestamp": 1710234510.1133935,
                        "interfaceStatistics": {
                            "updateInterval": 300.0,
                            "inBitsRate": 1854.287898883752,
                            "inPktsRate": 2.6902775246495665,
                            "outBitsRate": 1749.1141130864632,
                            "outPktsRate": 2.5565618978302362,
                        },
                        "interfaceCounters": {
                            "inOctets": 4475556,
                            "inUcastPkts": 48949,
                            "inMulticastPkts": 2579,
                            "inBroadcastPkts": 2,
                            "inDiscards": 0,
                            "inTotalPkts": 51530,
                            "outOctets": 4230011,
                            "outUcastPkts": 48982,
                            "outMulticastPkts": 6,
                            "outBroadcastPkts": 2,
                            "outDiscards": 0,
                            "outTotalPkts": 48990,
                            "linkStatusChanges": 2,
                            "totalInErrors": 0,
                            "totalOutErrors": 0,
                            "counterRefreshTime": 1710253760.6500373,
                        },
                        "memberInterfaces": {
                            "Ethernet3/1": {"bandwidth": 1000000000, "duplex": "duplexHalf"},
                            "Ethernet4/1": {"bandwidth": 1000000000, "duplex": "duplexHalf"},
                        },
                        "fallbackEnabled": False,
                        "fallbackEnabledType": "fallbackNone",
                    },
                }
            },
        ],
        "inputs": {"threshold": 70.0},
        "expected": {
            "result": "failure",
            "messages": [
                "Interface: Port-Channel31 Member Interface: Ethernet3/1 - Test not implemented for non-full-duplex interfaces - Expected: duplexFull "
                "Actual: duplexHalf",
                "Interface: Port-Channel31 Member Interface: Ethernet4/1 - Test not implemented for non-full-duplex interfaces - Expected: duplexFull "
                "Actual: duplexHalf",
            ],
        },
    },
    {
        "name": "success",
        "test": VerifyInterfaceErrors,
        "eos_data": [
            {
                "interfaceErrorCounters": {
                    "Ethernet1": {"inErrors": 0, "frameTooLongs": 0, "outErrors": 0, "frameTooShorts": 0, "fcsErrors": 0, "alignmentErrors": 0, "symbolErrors": 0},
                    "Ethernet6": {"inErrors": 0, "frameTooLongs": 0, "outErrors": 0, "frameTooShorts": 0, "fcsErrors": 0, "alignmentErrors": 0, "symbolErrors": 0},
                },
            },
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
                },
            },
        ],
        "inputs": None,
        "expected": {
            "result": "failure",
            "messages": [
                "Interface: Ethernet1 - Non-zero error counter(s) - inErrors: 42",
                "Interface: Ethernet6 - Non-zero error counter(s) - alignmentErrors: 666",
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
                },
            },
        ],
        "inputs": None,
        "expected": {
            "result": "failure",
            "messages": [
                "Interface: Ethernet1 - Non-zero error counter(s) - inErrors: 42, outErrors: 10",
                "Interface: Ethernet6 - Non-zero error counter(s) - alignmentErrors: 6, symbolErrors: 10",
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
                },
            },
        ],
        "inputs": None,
        "expected": {
            "result": "failure",
            "messages": ["Interface: Ethernet1 - Non-zero error counter(s) - inErrors: 42, outErrors: 2"],
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
            },
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
            },
        ],
        "inputs": None,
        "expected": {
            "result": "failure",
            "messages": [
                "Interface: Ethernet2 - Non-zero discard counter(s): outDiscards: 42",
                "Interface: Ethernet1 - Non-zero discard counter(s): inDiscards: 42",
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
                },
            },
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
                },
            },
        ],
        "inputs": None,
        "expected": {"result": "failure", "messages": ["Interface: Management1 - Link status Error disabled", "Interface: Ethernet8 - Link status Error disabled"]},
    },
    {
        "name": "success",
        "test": VerifyInterfacesStatus,
        "eos_data": [
            {
                "interfaceDescriptions": {
                    "Ethernet8": {"interfaceStatus": "up", "description": "", "lineProtocolStatus": "up"},
                    "Ethernet2": {"interfaceStatus": "adminDown", "description": "", "lineProtocolStatus": "down"},
                    "Ethernet3": {"interfaceStatus": "up", "description": "", "lineProtocolStatus": "up"},
                },
            },
        ],
        "inputs": {"interfaces": [{"name": "Ethernet2", "status": "adminDown"}, {"name": "Ethernet8", "status": "up"}, {"name": "Ethernet3", "status": "up"}]},
        "expected": {"result": "success"},
    },
    {
        "name": "success-up-with-line-protocol-status",
        "test": VerifyInterfacesStatus,
        "eos_data": [
            {
                "interfaceDescriptions": {
                    "Ethernet8": {"interfaceStatus": "up", "description": "", "lineProtocolStatus": "down"},
                }
            }
        ],
        "inputs": {"interfaces": [{"name": "Ethernet8", "status": "up", "line_protocol_status": "down"}]},
        "expected": {"result": "success"},
    },
    {
        "name": "success-with-line-protocol-status",
        "test": VerifyInterfacesStatus,
        "eos_data": [
            {
                "interfaceDescriptions": {
                    "Ethernet8": {"interfaceStatus": "adminDown", "description": "", "lineProtocolStatus": "testing"},
                    "Ethernet2": {"interfaceStatus": "adminDown", "description": "", "lineProtocolStatus": "down"},
                    "Ethernet3.10": {"interfaceStatus": "down", "description": "", "lineProtocolStatus": "dormant"},
                }
            }
        ],
        "inputs": {
            "interfaces": [
                {"name": "Ethernet2", "status": "adminDown", "line_protocol_status": "down"},
                {"name": "Ethernet8", "status": "adminDown", "line_protocol_status": "testing"},
                {"name": "Ethernet3.10", "status": "down", "line_protocol_status": "dormant"},
            ]
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
                    "Ethernet2": {"interfaceStatus": "adminDown", "description": "", "lineProtocolStatus": "down"},
                    "Ethernet3": {"interfaceStatus": "up", "description": "", "lineProtocolStatus": "up"},
                },
            },
        ],
        "inputs": {"interfaces": [{"name": "ethernet2", "status": "adminDown"}, {"name": "ethernet8", "status": "up"}, {"name": "ethernet3", "status": "up"}]},
        "expected": {"result": "success"},
    },
    {
        "name": "success-eth-name",
        "test": VerifyInterfacesStatus,
        "eos_data": [
            {
                "interfaceDescriptions": {
                    "Ethernet8": {"interfaceStatus": "up", "description": "", "lineProtocolStatus": "up"},
                    "Ethernet2": {"interfaceStatus": "adminDown", "description": "", "lineProtocolStatus": "down"},
                    "Ethernet3": {"interfaceStatus": "up", "description": "", "lineProtocolStatus": "up"},
                },
            },
        ],
        "inputs": {"interfaces": [{"name": "eth2", "status": "adminDown"}, {"name": "et8", "status": "up"}, {"name": "et3", "status": "up"}]},
        "expected": {"result": "success"},
    },
    {
        "name": "success-po-name",
        "test": VerifyInterfacesStatus,
        "eos_data": [
            {
                "interfaceDescriptions": {
                    "Port-Channel100": {"interfaceStatus": "up", "description": "", "lineProtocolStatus": "up"},
                },
            },
        ],
        "inputs": {"interfaces": [{"name": "po100", "status": "up"}]},
        "expected": {"result": "success"},
    },
    {
        "name": "success-sub-interfaces",
        "test": VerifyInterfacesStatus,
        "eos_data": [
            {
                "interfaceDescriptions": {
                    "Ethernet52/1.1963": {"interfaceStatus": "up", "description": "", "lineProtocolStatus": "up"},
                },
            },
        ],
        "inputs": {"interfaces": [{"name": "Ethernet52/1.1963", "status": "up"}]},
        "expected": {"result": "success"},
    },
    {
        "name": "success-transceiver-down",
        "test": VerifyInterfacesStatus,
        "eos_data": [
            {
                "interfaceDescriptions": {
                    "Ethernet49/1": {"interfaceStatus": "adminDown", "description": "", "lineProtocolStatus": "notPresent"},
                }
            }
        ],
        "inputs": {"interfaces": [{"name": "Ethernet49/1", "status": "adminDown"}]},
        "expected": {"result": "success"},
    },
    {
        "name": "success-po-down",
        "test": VerifyInterfacesStatus,
        "eos_data": [
            {
                "interfaceDescriptions": {
                    "Port-Channel100": {"interfaceStatus": "adminDown", "description": "", "lineProtocolStatus": "lowerLayerDown"},
                }
            }
        ],
        "inputs": {"interfaces": [{"name": "PortChannel100", "status": "adminDown"}]},
        "expected": {"result": "success"},
    },
    {
        "name": "success-po-lowerlayerdown",
        "test": VerifyInterfacesStatus,
        "eos_data": [
            {
                "interfaceDescriptions": {
                    "Port-Channel100": {"interfaceStatus": "adminDown", "description": "", "lineProtocolStatus": "lowerLayerDown"},
                }
            }
        ],
        "inputs": {"interfaces": [{"name": "Port-Channel100", "status": "adminDown", "line_protocol_status": "lowerLayerDown"}]},
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
                },
            },
        ],
        "inputs": {"interfaces": [{"name": "Ethernet2", "status": "up"}, {"name": "Ethernet8", "status": "up"}, {"name": "Ethernet3", "status": "up"}]},
        "expected": {
            "result": "failure",
            "messages": ["Ethernet8 - Not configured"],
        },
    },
    {
        "name": "failure-status-down",
        "test": VerifyInterfacesStatus,
        "eos_data": [
            {
                "interfaceDescriptions": {
                    "Ethernet8": {"interfaceStatus": "down", "description": "", "lineProtocolStatus": "down"},
                    "Ethernet2": {"interfaceStatus": "up", "description": "", "lineProtocolStatus": "up"},
                    "Ethernet3": {"interfaceStatus": "up", "description": "", "lineProtocolStatus": "up"},
                },
            },
        ],
        "inputs": {"interfaces": [{"name": "Ethernet2", "status": "up"}, {"name": "Ethernet8", "status": "up"}, {"name": "Ethernet3", "status": "up"}]},
        "expected": {
            "result": "failure",
            "messages": ["Ethernet8 - Status mismatch - Expected: up/up, Actual: down/down"],
        },
    },
    {
        "name": "failure-proto-down",
        "test": VerifyInterfacesStatus,
        "eos_data": [
            {
                "interfaceDescriptions": {
                    "Ethernet8": {"interfaceStatus": "up", "description": "", "lineProtocolStatus": "down"},
                    "Ethernet2": {"interfaceStatus": "up", "description": "", "lineProtocolStatus": "up"},
                    "Ethernet3": {"interfaceStatus": "up", "description": "", "lineProtocolStatus": "up"},
                },
            },
        ],
        "inputs": {
            "interfaces": [
                {"name": "Ethernet2", "status": "up"},
                {"name": "Ethernet8", "status": "up"},
                {"name": "Ethernet3", "status": "up"},
            ]
        },
        "expected": {
            "result": "failure",
            "messages": ["Ethernet8 - Status mismatch - Expected: up/up, Actual: up/down"],
        },
    },
    {
        "name": "failure-po-status-down",
        "test": VerifyInterfacesStatus,
        "eos_data": [
            {
                "interfaceDescriptions": {
                    "Port-Channel100": {"interfaceStatus": "down", "description": "", "lineProtocolStatus": "lowerLayerDown"},
                }
            }
        ],
        "inputs": {"interfaces": [{"name": "PortChannel100", "status": "up"}]},
        "expected": {
            "result": "failure",
            "messages": ["Port-Channel100 - Status mismatch - Expected: up/up, Actual: down/lowerLayerDown"],
        },
    },
    {
        "name": "failure-proto-unknown",
        "test": VerifyInterfacesStatus,
        "eos_data": [
            {
                "interfaceDescriptions": {
                    "Ethernet8": {"interfaceStatus": "up", "description": "", "lineProtocolStatus": "down"},
                    "Ethernet2": {"interfaceStatus": "up", "description": "", "lineProtocolStatus": "unknown"},
                    "Ethernet3": {"interfaceStatus": "up", "description": "", "lineProtocolStatus": "up"},
                }
            }
        ],
        "inputs": {
            "interfaces": [
                {"name": "Ethernet2", "status": "up", "line_protocol_status": "down"},
                {"name": "Ethernet8", "status": "up"},
                {"name": "Ethernet3", "status": "up"},
            ]
        },
        "expected": {
            "result": "failure",
            "messages": [
                "Ethernet2 - Status mismatch - Expected: up/down, Actual: up/unknown",
                "Ethernet8 - Status mismatch - Expected: up/up, Actual: up/down",
            ],
        },
    },
    {
        "name": "failure-interface-status-down",
        "test": VerifyInterfacesStatus,
        "eos_data": [
            {
                "interfaceDescriptions": {
                    "Ethernet8": {"interfaceStatus": "up", "description": "", "lineProtocolStatus": "down"},
                    "Ethernet2": {"interfaceStatus": "up", "description": "", "lineProtocolStatus": "unknown"},
                    "Ethernet3": {"interfaceStatus": "up", "description": "", "lineProtocolStatus": "up"},
                }
            }
        ],
        "inputs": {
            "interfaces": [
                {"name": "Ethernet2", "status": "down"},
                {"name": "Ethernet8", "status": "down"},
                {"name": "Ethernet3", "status": "down"},
            ]
        },
        "expected": {
            "result": "failure",
            "messages": [
                "Ethernet2 - Status mismatch - Expected: down, Actual: up",
                "Ethernet8 - Status mismatch - Expected: down, Actual: up",
                "Ethernet3 - Status mismatch - Expected: down, Actual: up",
            ],
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
                    },
                },
            },
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
                    },
                },
            },
        ],
        "inputs": None,
        "expected": {"result": "failure", "messages": ["Interface: Ethernet1 - Non-zero storm-control drop counter(s) - broadcast: 666"]},
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
                    },
                },
            },
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
                    },
                },
            },
        ],
        "inputs": None,
        "expected": {"result": "failure", "messages": ["Port-Channel42 - Inactive port(s) - Ethernet8"]},
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
                            },
                        },
                    },
                },
                "orphanPorts": {},
            },
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
                            },
                        },
                    },
                },
                "orphanPorts": {},
            },
        ],
        "inputs": None,
        "expected": {
            "result": "failure",
            "messages": ["Port-Channel42 Interface: Ethernet8 - Illegal LACP packets found"],
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
                    # Checking not loopbacks are skipped
                    "Ethernet666": {
                        "name": "Ethernet666",
                        "interfaceStatus": "connected",
                        "interfaceAddress": {"ipAddr": {"maskLen": 32, "address": "6.6.6.6"}},
                        "ipv4Routable240": False,
                        "lineProtocolStatus": "up",
                    },
                },
            },
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
                        "interfaceStatus": "notconnect",
                        "interfaceAddress": {"ipAddr": {"maskLen": 32, "address": "6.6.6.6"}},
                        "ipv4Routable240": False,
                        "lineProtocolStatus": "down",
                        "mtu": 65535,
                    },
                },
            },
        ],
        "inputs": {"number": 2},
        "expected": {
            "result": "failure",
            "messages": [
                "Interface: Loopback666 - Invalid line protocol status - Expected: up Actual: down",
                "Interface: Loopback666 - Invalid interface status - Expected: connected Actual: notconnect",
            ],
        },
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
                },
            },
        ],
        "inputs": {"number": 2},
        "expected": {"result": "failure", "messages": ["Loopback interface(s) count mismatch: Expected 2 Actual: 1"]},
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
                    },
                },
            },
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
                    },
                },
            },
        ],
        "inputs": None,
        "expected": {
            "result": "failure",
            "messages": [
                "SVI: Vlan42 - Invalid line protocol status - Expected: up Actual: lowerLayerDown",
                "SVI: Vlan42 - Invalid interface status - Expected: connected Actual: notconnect",
            ],
        },
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
            },
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
            },
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
            },
        ],
        "inputs": {"mtu": 1500},
        "expected": {"result": "failure", "messages": ["Interface: Ethernet2 - Incorrect MTU - Expected: 1500 Actual: 1600"]},
    },
    {
        "name": "failure-specified-interface-mtu",
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
                        "mtu": 1502,
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
            },
        ],
        "inputs": {"mtu": 1500, "ignored_interfaces": ["Loopback", "Port-Channel", "Management", "Vxlan"], "specific_mtu": [{"Ethernet10": 1501}]},
        "expected": {"result": "failure", "messages": ["Interface: Ethernet10 - Incorrect MTU - Expected: 1501 Actual: 1502"]},
    },
    {
        "name": "success",
        "test": VerifyL2MTU,
        "eos_data": [
            {
                "interfaces": {
                    "Ethernet2/1": {
                        "name": "Ethernet2/1",
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
            },
        ],
        "inputs": {"mtu": 9214, "ignored_interfaces": ["Loopback", "Port-Channel", "Management", "Vxlan"], "specific_mtu": [{"Ethernet10": 9214}]},
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
            },
        ],
        "inputs": {"mtu": 1500},
        "expected": {
            "result": "failure",
            "messages": [
                "Interface: Ethernet10 - Incorrect MTU configured - Expected: 1500 Actual: 9214",
                "Interface: Port-Channel2 - Incorrect MTU configured - Expected: 1500 Actual: 9214",
            ],
        },
    },
    {
        "name": "failure-specific-interface",
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
            },
        ],
        "inputs": {"specific_mtu": [{"Et10": 9214}, {"Port-Channel2": 10000}]},
        "expected": {"result": "failure", "messages": ["Interface: Port-Channel2 - Incorrect MTU configured - Expected: 10000 Actual: 9214"]},
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
                        "proxyArp": True,
                    },
                    "Ethernet2": {
                        "name": "Ethernet2",
                        "lineProtocolStatus": "up",
                        "interfaceStatus": "connected",
                        "proxyArp": True,
                    },
                },
            },
        ],
        "inputs": {"interfaces": ["Ethernet1", "Ethernet2"]},
        "expected": {"result": "success"},
    },
    {
        "name": "failure-interface-not-found",
        "test": VerifyIPProxyARP,
        "eos_data": [
            {
                "interfaces": {
                    "Ethernet1": {
                        "name": "Ethernet1",
                        "lineProtocolStatus": "up",
                        "interfaceStatus": "connected",
                        "proxyArp": True,
                    },
                },
            },
        ],
        "inputs": {"interfaces": ["Ethernet1", "Ethernet2"]},
        "expected": {"result": "failure", "messages": ["Interface: Ethernet2 - Not found"]},
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
                        "proxyArp": True,
                    },
                    "Ethernet2": {
                        "name": "Ethernet2",
                        "lineProtocolStatus": "up",
                        "interfaceStatus": "connected",
                        "proxyArp": False,
                    },
                },
            },
        ],
        "inputs": {"interfaces": ["Ethernet1", "Ethernet2"]},
        "expected": {"result": "failure", "messages": ["Interface: Ethernet2 - Proxy-ARP disabled"]},
    },
    {
        "name": "success",
        "test": VerifyInterfaceIPv4,
        "eos_data": [
            {
                "interfaces": {
                    "Ethernet2": {
                        "interfaceAddress": {
                            "primaryIp": {"address": "172.30.11.1", "maskLen": 31},
                            "secondaryIpsOrderedList": [{"address": "10.10.10.1", "maskLen": 31}, {"address": "10.10.10.10", "maskLen": 31}],
                        }
                    },
                    "Ethernet12": {
                        "interfaceAddress": {
                            "primaryIp": {"address": "172.30.11.10", "maskLen": 31},
                            "secondaryIpsOrderedList": [{"address": "10.10.10.10", "maskLen": 31}, {"address": "10.10.10.20", "maskLen": 31}],
                        }
                    },
                }
            },
        ],
        "inputs": {
            "interfaces": [
                {"name": "Ethernet2", "primary_ip": "172.30.11.1/31", "secondary_ips": ["10.10.10.1/31", "10.10.10.10/31"]},
                {"name": "Ethernet12", "primary_ip": "172.30.11.10/31", "secondary_ips": ["10.10.10.10/31", "10.10.10.20/31"]},
            ]
        },
        "expected": {"result": "success"},
    },
    {
        "name": "success-without-secondary-ip",
        "test": VerifyInterfaceIPv4,
        "eos_data": [
            {
                "interfaces": {
                    "Ethernet2": {
                        "interfaceAddress": {
                            "primaryIp": {"address": "172.30.11.0", "maskLen": 31},
                            "secondaryIpsOrderedList": [],
                        }
                    },
                    "Ethernet12": {
                        "interfaceAddress": {
                            "primaryIp": {"address": "172.30.11.10", "maskLen": 31},
                            "secondaryIpsOrderedList": [],
                        }
                    },
                }
            },
        ],
        "inputs": {
            "interfaces": [
                {"name": "Ethernet2", "primary_ip": "172.30.11.0/31"},
                {"name": "Ethernet12", "primary_ip": "172.30.11.10/31"},
            ]
        },
        "expected": {"result": "success"},
    },
    {
        "name": "failure-interface-not-found",
        "test": VerifyInterfaceIPv4,
        "eos_data": [
            {
                "interfaces": {
                    "Ethernet10": {
                        "interfaceAddress": {
                            "primaryIp": {"address": "172.30.11.0", "maskLen": 31},
                            "secondaryIpsOrderedList": [],
                        }
                    }
                }
            }
        ],
        "inputs": {
            "interfaces": [
                {"name": "Ethernet2", "primary_ip": "172.30.11.0/31", "secondary_ips": ["10.10.10.0/31", "10.10.10.10/31"]},
                {"name": "Ethernet12", "primary_ip": "172.30.11.20/31", "secondary_ips": ["10.10.11.0/31", "10.10.11.10/31"]},
            ]
        },
        "expected": {
            "result": "failure",
            "messages": ["Interface: Ethernet2 - Not found", "Interface: Ethernet12 - Not found"],
        },
    },
    {
        "name": "failure-not-l3-interface",
        "test": VerifyInterfaceIPv4,
        "eos_data": [{"interfaces": {"Ethernet2": {"interfaceAddress": {}}, "Ethernet12": {"interfaceAddress": {}}}}],
        "inputs": {
            "interfaces": [
                {"name": "Ethernet2", "primary_ip": "172.30.11.0/31", "secondary_ips": ["10.10.10.0/31", "10.10.10.10/31"]},
                {"name": "Ethernet12", "primary_ip": "172.30.11.20/31", "secondary_ips": ["10.10.11.0/31", "10.10.11.10/31"]},
            ]
        },
        "expected": {
            "result": "failure",
            "messages": ["Interface: Ethernet2 - IP address is not configured", "Interface: Ethernet12 - IP address is not configured"],
        },
    },
    {
        "name": "failure-ip-address-not-configured",
        "test": VerifyInterfaceIPv4,
        "eos_data": [
            {
                "interfaces": {
                    "Ethernet2": {
                        "interfaceAddress": {
                            "primaryIp": {"address": "0.0.0.0", "maskLen": 0},
                            "secondaryIpsOrderedList": [],
                        }
                    },
                    "Ethernet12": {
                        "interfaceAddress": {
                            "primaryIp": {"address": "0.0.0.0", "maskLen": 0},
                            "secondaryIpsOrderedList": [],
                        }
                    },
                }
            },
        ],
        "inputs": {
            "interfaces": [
                {"name": "Ethernet2", "primary_ip": "172.30.11.0/31", "secondary_ips": ["10.10.10.0/31", "10.10.10.10/31"]},
                {"name": "Ethernet12", "primary_ip": "172.30.11.10/31", "secondary_ips": ["10.10.11.0/31", "10.10.11.10/31"]},
            ]
        },
        "expected": {
            "result": "failure",
            "messages": [
                "Interface: Ethernet2 - IP address mismatch - Expected: 172.30.11.0/31 Actual: 0.0.0.0/0",
                "Interface: Ethernet2 - Secondary IP address is not configured",
                "Interface: Ethernet12 - IP address mismatch - Expected: 172.30.11.10/31 Actual: 0.0.0.0/0",
                "Interface: Ethernet12 - Secondary IP address is not configured",
            ],
        },
    },
    {
        "name": "failure-ip-address-missmatch",
        "test": VerifyInterfaceIPv4,
        "eos_data": [
            {
                "interfaces": {
                    "Ethernet2": {
                        "interfaceAddress": {
                            "primaryIp": {"address": "172.30.11.0", "maskLen": 31},
                            "secondaryIpsOrderedList": [{"address": "10.10.10.0", "maskLen": 31}, {"address": "10.10.10.10", "maskLen": 31}],
                        }
                    },
                    "Ethernet3": {
                        "interfaceAddress": {
                            "primaryIp": {"address": "172.30.10.10", "maskLen": 31},
                            "secondaryIpsOrderedList": [{"address": "10.10.11.0", "maskLen": 31}, {"address": "10.11.11.10", "maskLen": 31}],
                        }
                    },
                }
            },
        ],
        "inputs": {
            "interfaces": [
                {"name": "Ethernet2", "primary_ip": "172.30.11.2/31", "secondary_ips": ["10.10.10.20/31", "10.10.10.30/31"]},
                {"name": "Ethernet3", "primary_ip": "172.30.10.2/31", "secondary_ips": ["10.10.11.0/31", "10.10.11.10/31"]},
            ]
        },
        "expected": {
            "result": "failure",
            "messages": [
                "Interface: Ethernet2 - IP address mismatch - Expected: 172.30.11.2/31 Actual: 172.30.11.0/31",
                "Interface: Ethernet2 - Secondary IP address mismatch - Expected: 10.10.10.20/31, 10.10.10.30/31 Actual: 10.10.10.0/31, 10.10.10.10/31",
                "Interface: Ethernet3 - IP address mismatch - Expected: 172.30.10.2/31 Actual: 172.30.10.10/31",
                "Interface: Ethernet3 - Secondary IP address mismatch - Expected: 10.10.11.0/31, 10.10.11.10/31 Actual: 10.10.11.0/31, 10.11.11.10/31",
            ],
        },
    },
    {
        "name": "failure-secondary-ip-address",
        "test": VerifyInterfaceIPv4,
        "eos_data": [
            {
                "interfaces": {
                    "Ethernet2": {
                        "interfaceAddress": {
                            "primaryIp": {"address": "172.30.11.0", "maskLen": 31},
                            "secondaryIpsOrderedList": [],
                        }
                    },
                    "Ethernet3": {
                        "interfaceAddress": {
                            "primaryIp": {"address": "172.30.10.10", "maskLen": 31},
                            "secondaryIpsOrderedList": [{"address": "10.10.11.0", "maskLen": 31}, {"address": "10.11.11.10", "maskLen": 31}],
                        }
                    },
                }
            },
        ],
        "inputs": {
            "interfaces": [
                {"name": "Ethernet2", "primary_ip": "172.30.11.2/31", "secondary_ips": ["10.10.10.20/31", "10.10.10.30/31"]},
                {"name": "Ethernet3", "primary_ip": "172.30.10.2/31", "secondary_ips": ["10.10.11.0/31", "10.10.11.10/31"]},
            ]
        },
        "expected": {
            "result": "failure",
            "messages": [
                "Interface: Ethernet2 - IP address mismatch - Expected: 172.30.11.2/31 Actual: 172.30.11.0/31",
                "Interface: Ethernet2 - Secondary IP address is not configured",
                "Interface: Ethernet3 - IP address mismatch - Expected: 172.30.10.2/31 Actual: 172.30.10.10/31",
                "Interface: Ethernet3 - Secondary IP address mismatch - Expected: 10.10.11.0/31, 10.10.11.10/31 Actual: 10.10.11.0/31, 10.11.11.10/31",
            ],
        },
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
        "expected": {"result": "failure", "messages": ["IP virtual router MAC address: 00:1c:73:00:dc:01 - Not configured"]},
    },
    {
        "name": "success",
        "test": VerifyInterfacesSpeed,
        "eos_data": [
            {
                "interfaces": {
                    "Ethernet1": {
                        "bandwidth": 1000000000,
                        "autoNegotiate": "unknown",
                        "duplex": "duplexFull",
                        "lanes": 2,
                    },
                    "Ethernet1/1/2": {
                        "bandwidth": 1000000000,
                        "autoNegotiate": "unknown",
                        "duplex": "duplexFull",
                        "lanes": 2,
                    },
                    "Ethernet3": {
                        "bandwidth": 100000000000,
                        "autoNegotiate": "success",
                        "duplex": "duplexFull",
                        "lanes": 8,
                    },
                    "Ethernet4": {
                        "bandwidth": 2500000000,
                        "autoNegotiate": "unknown",
                        "duplex": "duplexFull",
                        "lanes": 8,
                    },
                }
            }
        ],
        "inputs": {
            "interfaces": [
                {"name": "Ethernet1", "auto": False, "speed": 1},
                {"name": "Ethernet1", "auto": False, "speed": 1, "lanes": 2},
                {"name": "Ethernet1/1/2", "auto": False, "speed": 1},
                {"name": "Ethernet3", "auto": True, "speed": 100},
                {"name": "Ethernet3", "auto": True, "speed": 100, "lanes": 8},
                {"name": "Ethernet3", "auto": True, "speed": 100},
                {"name": "Ethernet4", "auto": False, "speed": 2.5},
            ]
        },
        "expected": {"result": "success"},
    },
    {
        "name": "failure-incorrect-speed",
        "test": VerifyInterfacesSpeed,
        "eos_data": [
            {
                "interfaces": {
                    "Ethernet1": {
                        "bandwidth": 100000000000,
                        "autoNegotiate": "unknown",
                        "duplex": "duplexFull",
                        "lanes": 2,
                    },
                    "Ethernet1/1/1": {
                        "bandwidth": 100000000000,
                        "autoNegotiate": "unknown",
                        "duplex": "duplexFull",
                        "lanes": 2,
                    },
                    "Ethernet3": {
                        "bandwidth": 10000000000,
                        "autoNegotiate": "success",
                        "duplex": "duplexFull",
                        "lanes": 8,
                    },
                    "Ethernet4": {
                        "bandwidth": 25000000000,
                        "autoNegotiate": "unknown",
                        "duplex": "duplexFull",
                        "lanes": 8,
                    },
                }
            }
        ],
        "inputs": {
            "interfaces": [
                {"name": "Ethernet1", "auto": False, "speed": 1},
                {"name": "Ethernet1/1/1", "auto": False, "speed": 1},
                {"name": "Ethernet3", "auto": True, "speed": 100},
                {"name": "Ethernet4", "auto": False, "speed": 2.5},
            ]
        },
        "expected": {
            "result": "failure",
            "messages": [
                "Interface: Ethernet1 - Bandwidth mismatch - Expected: 1.0Gbps Actual: 100Gbps",
                "Interface: Ethernet1/1/1 - Bandwidth mismatch - Expected: 1.0Gbps Actual: 100Gbps",
                "Interface: Ethernet3 - Bandwidth mismatch - Expected: 100.0Gbps Actual: 10Gbps",
                "Interface: Ethernet4 - Bandwidth mismatch - Expected: 2.5Gbps Actual: 25Gbps",
            ],
        },
    },
    {
        "name": "failure-incorrect-mode",
        "test": VerifyInterfacesSpeed,
        "eos_data": [
            {
                "interfaces": {
                    "Ethernet1": {
                        "bandwidth": 1000000000,
                        "autoNegotiate": "unknown",
                        "duplex": "duplexHalf",
                        "lanes": 2,
                    },
                    "Ethernet1/2/2": {
                        "bandwidth": 1000000000,
                        "autoNegotiate": "unknown",
                        "duplex": "duplexHalf",
                        "lanes": 2,
                    },
                    "Ethernet3": {
                        "bandwidth": 100000000000,
                        "autoNegotiate": "success",
                        "duplex": "duplexHalf",
                        "lanes": 8,
                    },
                    "Ethernet4": {
                        "bandwidth": 2500000000,
                        "autoNegotiate": "unknown",
                        "duplex": "duplexHalf",
                        "lanes": 8,
                    },
                }
            }
        ],
        "inputs": {
            "interfaces": [
                {"name": "Ethernet1", "auto": False, "speed": 1},
                {"name": "Ethernet1/2/2", "auto": False, "speed": 1},
                {"name": "Ethernet3", "auto": True, "speed": 100},
                {"name": "Ethernet3", "auto": True, "speed": 100, "lanes": 8},
                {"name": "Ethernet4", "auto": False, "speed": 2.5},
            ]
        },
        "expected": {
            "result": "failure",
            "messages": [
                "Interface: Ethernet1 - Duplex mode mismatch - Expected: duplexFull Actual: duplexHalf",
                "Interface: Ethernet1/2/2 - Duplex mode mismatch - Expected: duplexFull Actual: duplexHalf",
                "Interface: Ethernet3 - Duplex mode mismatch - Expected: duplexFull Actual: duplexHalf",
                "Interface: Ethernet3 - Duplex mode mismatch - Expected: duplexFull Actual: duplexHalf",
                "Interface: Ethernet4 - Duplex mode mismatch - Expected: duplexFull Actual: duplexHalf",
            ],
        },
    },
    {
        "name": "failure-incorrect-lane",
        "test": VerifyInterfacesSpeed,
        "eos_data": [
            {
                "interfaces": {
                    "Ethernet1": {
                        "bandwidth": 1000000000,
                        "autoNegotiate": "unknown",
                        "duplex": "duplexFull",
                        "lanes": 4,
                    },
                    "Ethernet2": {
                        "bandwidth": 10000000000,
                        "autoNegotiate": "unknown",
                        "duplex": "duplexFull",
                        "lanes": 4,
                    },
                    "Ethernet3": {
                        "bandwidth": 100000000000,
                        "autoNegotiate": "success",
                        "duplex": "duplexFull",
                        "lanes": 4,
                    },
                    "Ethernet4": {
                        "bandwidth": 2500000000,
                        "autoNegotiate": "unknown",
                        "duplex": "duplexFull",
                        "lanes": 6,
                    },
                    "Ethernet4/1/1": {
                        "bandwidth": 2500000000,
                        "autoNegotiate": "unknown",
                        "duplex": "duplexFull",
                        "lanes": 6,
                    },
                }
            }
        ],
        "inputs": {
            "interfaces": [
                {"name": "Ethernet1", "auto": False, "speed": 1, "lanes": 2},
                {"name": "Ethernet3", "auto": True, "speed": 100, "lanes": 8},
                {"name": "Ethernet4", "auto": False, "speed": 2.5, "lanes": 4},
                {"name": "Ethernet4/1/1", "auto": False, "speed": 2.5, "lanes": 4},
            ]
        },
        "expected": {
            "result": "failure",
            "messages": [
                "Interface: Ethernet1 - Data lanes count mismatch - Expected: 2 Actual: 4",
                "Interface: Ethernet3 - Data lanes count mismatch - Expected: 8 Actual: 4",
                "Interface: Ethernet4 - Data lanes count mismatch - Expected: 4 Actual: 6",
                "Interface: Ethernet4/1/1 - Data lanes count mismatch - Expected: 4 Actual: 6",
            ],
        },
    },
    {
        "name": "failure-all-type",
        "test": VerifyInterfacesSpeed,
        "eos_data": [
            {
                "interfaces": {
                    "Ethernet1": {
                        "bandwidth": 10000000000,
                        "autoNegotiate": "unknown",
                        "duplex": "duplexHalf",
                        "lanes": 4,
                    },
                    "Ethernet2/1/2": {
                        "bandwidth": 1000000000,
                        "autoNegotiate": "unknown",
                        "duplex": "duplexHalf",
                        "lanes": 2,
                    },
                    "Ethernet3": {
                        "bandwidth": 10000000000,
                        "autoNegotiate": "unknown",
                        "duplex": "duplexHalf",
                        "lanes": 6,
                    },
                    "Ethernet4": {
                        "bandwidth": 25000000000,
                        "autoNegotiate": "unknown",
                        "duplex": "duplexHalf",
                        "lanes": 4,
                    },
                }
            }
        ],
        "inputs": {
            "interfaces": [
                {"name": "Ethernet1", "auto": False, "speed": 1, "lanes": 2},
                {"name": "Ethernet2/1/2", "auto": False, "speed": 10},
                {"name": "Ethernet3", "auto": True, "speed": 100, "lanes": 8},
                {"name": "Ethernet4", "auto": False, "speed": 2.5},
            ]
        },
        "expected": {
            "result": "failure",
            "messages": [
                "Interface: Ethernet1 - Bandwidth mismatch - Expected: 1.0Gbps Actual: 10Gbps",
                "Interface: Ethernet1 - Duplex mode mismatch - Expected: duplexFull Actual: duplexHalf",
                "Interface: Ethernet1 - Data lanes count mismatch - Expected: 2 Actual: 4",
                "Interface: Ethernet2/1/2 - Bandwidth mismatch - Expected: 10.0Gbps Actual: 1Gbps",
                "Interface: Ethernet2/1/2 - Duplex mode mismatch - Expected: duplexFull Actual: duplexHalf",
                "Interface: Ethernet3 - Bandwidth mismatch - Expected: 100.0Gbps Actual: 10Gbps",
                "Interface: Ethernet3 - Duplex mode mismatch - Expected: duplexFull Actual: duplexHalf",
                "Interface: Ethernet3 - Auto-negotiation mismatch - Expected: success Actual: unknown",
                "Interface: Ethernet3 - Data lanes count mismatch - Expected: 8 Actual: 6",
                "Interface: Ethernet4 - Bandwidth mismatch - Expected: 2.5Gbps Actual: 25Gbps",
                "Interface: Ethernet4 - Duplex mode mismatch - Expected: duplexFull Actual: duplexHalf",
            ],
        },
    },
    {
        "name": "success",
        "test": VerifyLACPInterfacesStatus,
        "eos_data": [
            {
                "portChannels": {
                    "Port-Channel5": {
                        "interfaces": {
                            "Ethernet5": {
                                "actorPortStatus": "bundled",
                                "partnerPortState": {
                                    "activity": True,
                                    "timeout": False,
                                    "aggregation": True,
                                    "synchronization": True,
                                    "collecting": True,
                                    "distributing": True,
                                },
                                "actorPortState": {
                                    "activity": True,
                                    "timeout": False,
                                    "aggregation": True,
                                    "synchronization": True,
                                    "collecting": True,
                                    "distributing": True,
                                },
                            }
                        }
                    }
                },
                "interface": "Ethernet5",
                "orphanPorts": {},
            }
        ],
        "inputs": {"interfaces": [{"name": "Ethernet5", "portchannel": "Port-Channel5"}]},
        "expected": {"result": "success"},
    },
    {
        "name": "success-short-timeout",
        "test": VerifyLACPInterfacesStatus,
        "eos_data": [
            {
                "portChannels": {
                    "Port-Channel5": {
                        "interfaces": {
                            "Ethernet5": {
                                "actorPortStatus": "bundled",
                                "partnerPortState": {
                                    "activity": True,
                                    "timeout": True,
                                    "aggregation": True,
                                    "synchronization": True,
                                    "collecting": True,
                                    "distributing": True,
                                },
                                "actorPortState": {
                                    "activity": True,
                                    "timeout": True,
                                    "aggregation": True,
                                    "synchronization": True,
                                    "collecting": True,
                                    "distributing": True,
                                },
                            }
                        }
                    }
                },
                "interface": "Ethernet5",
                "orphanPorts": {},
            }
        ],
        "inputs": {"interfaces": [{"name": "Ethernet5", "portchannel": "Port-Channel5", "lacp_rate_fast": True}]},
        "expected": {"result": "success"},
    },
    {
        "name": "failure-not-bundled",
        "test": VerifyLACPInterfacesStatus,
        "eos_data": [
            {
                "portChannels": {
                    "Port-Channel5": {
                        "interfaces": {
                            "Ethernet5": {
                                "actorPortStatus": "No Aggregate",
                            }
                        }
                    }
                },
                "interface": "Ethernet5",
                "orphanPorts": {},
            }
        ],
        "inputs": {"interfaces": [{"name": "Ethernet5", "portchannel": "Po5"}]},
        "expected": {
            "result": "failure",
            "messages": ["Interface: Ethernet5 Port-Channel: Port-Channel5 - Not bundled - Port Status: No Aggregate"],
        },
    },
    {
        "name": "failure-no-details-found",
        "test": VerifyLACPInterfacesStatus,
        "eos_data": [
            {
                "portChannels": {"Port-Channel5": {"interfaces": {}}},
            }
        ],
        "inputs": {"interfaces": [{"name": "Ethernet5", "portchannel": "Po 5"}]},
        "expected": {
            "result": "failure",
            "messages": ["Interface: Ethernet5 Port-Channel: Port-Channel5 - Not configured"],
        },
    },
    {
        "name": "failure-lacp-params",
        "test": VerifyLACPInterfacesStatus,
        "eos_data": [
            {
                "portChannels": {
                    "Port-Channel5": {
                        "interfaces": {
                            "Ethernet5": {
                                "actorPortStatus": "bundled",
                                "partnerPortState": {
                                    "activity": False,
                                    "timeout": False,
                                    "aggregation": False,
                                    "synchronization": False,
                                    "collecting": True,
                                    "distributing": True,
                                },
                                "actorPortState": {
                                    "activity": False,
                                    "timeout": False,
                                    "aggregation": False,
                                    "synchronization": False,
                                    "collecting": True,
                                    "distributing": True,
                                },
                            }
                        }
                    }
                },
                "interface": "Ethernet5",
                "orphanPorts": {},
            }
        ],
        "inputs": {"interfaces": [{"name": "Ethernet5", "portchannel": "port-channel 5"}]},
        "expected": {
            "result": "failure",
            "messages": [
                "Interface: Ethernet5 Port-Channel: Port-Channel5 - Actor port details mismatch - Activity: False, Aggregation: False, "
                "Synchronization: False, Collecting: True, Distributing: True, Timeout: False",
                "Interface: Ethernet5 Port-Channel: Port-Channel5 - Partner port details mismatch - Activity: False, Aggregation: False, "
                "Synchronization: False, Collecting: True, Distributing: True, Timeout: False",
            ],
        },
    },
    {
        "name": "failure-short-timeout",
        "test": VerifyLACPInterfacesStatus,
        "eos_data": [
            {
                "portChannels": {
                    "Port-Channel5": {
                        "interfaces": {
                            "Ethernet5": {
                                "actorPortStatus": "bundled",
                                "partnerPortState": {
                                    "activity": True,
                                    "timeout": False,
                                    "aggregation": True,
                                    "synchronization": True,
                                    "collecting": True,
                                    "distributing": True,
                                },
                                "actorPortState": {
                                    "activity": True,
                                    "timeout": False,
                                    "aggregation": True,
                                    "synchronization": True,
                                    "collecting": True,
                                    "distributing": True,
                                },
                            }
                        }
                    }
                },
                "interface": "Ethernet5",
                "orphanPorts": {},
            }
        ],
        "inputs": {"interfaces": [{"name": "Ethernet5", "portchannel": "port-channel 5", "lacp_rate_fast": True}]},
        "expected": {
            "result": "failure",
            "messages": [
                "Interface: Ethernet5 Port-Channel: Port-Channel5 - Actor port details mismatch - Activity: True, Aggregation: True, "
                "Synchronization: True, Collecting: True, Distributing: True, Timeout: False",
                "Interface: Ethernet5 Port-Channel: Port-Channel5 - Partner port details mismatch - Activity: True, Aggregation: True, "
                "Synchronization: True, Collecting: True, Distributing: True, Timeout: False",
            ],
        },
    },
]
