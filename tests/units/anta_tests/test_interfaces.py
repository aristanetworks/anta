# Copyright (c) 2023-2025 Arista Networks, Inc.
# Use of this source code is governed by the Apache License 2.0
# that can be found in the LICENSE file.
"""Test inputs for anta.tests.interfaces."""

# pylint: disable=C0302
from __future__ import annotations

import sys
from typing import TYPE_CHECKING, Any

from anta.models import AntaTest
from anta.result_manager.models import AntaTestStatus
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

if TYPE_CHECKING:
    from tests.units.anta_tests import AntaUnitTestDataDict

DATA: AntaUnitTestDataDict = {
    (VerifyInterfaceUtilization, "success"): {
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
        "expected": {"result": AntaTestStatus.SUCCESS},
    },
    (VerifyInterfaceUtilization, "success-ignored-interface"): {
        "eos_data": [
            {
                "interfaces": {
                    "Ethernet1": {
                        "description": "MLAG Peer-link - s1-leaf2",
                        "interval": 300,
                        "inBpsRate": 1801.8707256244886,
                        "inPktsRate": 0.00022136128440856573,
                        "inPpsRate": 2.573388240382304,
                        "outBpsRate": 1351.2921726055374,
                        "outPktsRate": 0.00017125571109710073,
                        "outPpsRate": 2.2579058647841856,
                        "lastUpdateTimestamp": 1743750428.6092474,
                    },
                    "Ethernet2": {
                        "description": "L3 Uplink - s1-spine1",
                        "interval": 300,
                        "inBpsRate": 93.35295126808322,
                        "inPktsRate": 1.0505400223350173e-05,
                        "inPpsRate": 0.07313156853386583,
                        "outBpsRate": 0.0,
                        "outPktsRate": 0.0,
                        "outPpsRate": 0.0,
                        "lastUpdateTimestamp": 1743750428.6092517,
                    },
                    "Ethernet3": {
                        "description": "L3 Uplink - s1-spine2",
                        "interval": 300,
                        "inBpsRate": 91.64440293982129,
                        "inPktsRate": 1.0286893435756781e-05,
                        "inPpsRate": 0.07015332136091573,
                        "outBpsRate": 0.0,
                        "outPktsRate": 0.0,
                        "outPpsRate": 0.0,
                        "lastUpdateTimestamp": 1743750428.6091988,
                    },
                    "Ethernet4": {
                        "description": "MLAG Downlink - s1-host1",
                        "interval": 300,
                        "inBpsRate": 98.73132596805515,
                        "inPktsRate": 1.0928950412403655e-05,
                        "inPpsRate": 0.06598861347488381,
                        "outBpsRate": 497.70036505586484,
                        "outPktsRate": 5.810165469175271e-05,
                        "outPpsRate": 0.52072613663539,
                        "lastUpdateTimestamp": 1743750428.6092432,
                    },
                    "Ethernet6": {
                        "description": "MLAG Peer-link - s1-leaf2",
                        "interval": 300,
                        "inBpsRate": 98.18960870790458,
                        "inPktsRate": 1.0859909720407048e-05,
                        "inPpsRate": 0.06505930310103682,
                        "outBpsRate": 256.359818648091,
                        "outPktsRate": 2.9610552696562436e-05,
                        "outPpsRate": 0.24841067698458383,
                        "lastUpdateTimestamp": 1743750428.6092384,
                    },
                    "Management0": {
                        "description": "",
                        "interval": 300,
                        "inBpsRate": 7626.480173033807,
                        "inPktsRate": 0.0009048203095460882,
                        "inPpsRate": 8.885768265169219,
                        "outBpsRate": 9127.592145035744,
                        "outPktsRate": 0.001049926825271909,
                        "outPpsRate": 8.572975673020922,
                        "lastUpdateTimestamp": 1743750428.6079214,
                    },
                    "Port-Channel1": {
                        "description": "MLAG Peer-link - s1-leaf2",
                        "interval": 300,
                        "inBpsRate": 1905.0055237111224,
                        "inPktsRate": 0.00011641274575015027,
                        "inPpsRate": 2.645308695574268,
                        "outBpsRate": 1611.693121818935,
                        "outPktsRate": 0.00010068646137044125,
                        "outPpsRate": 2.5127256599368124,
                        "lastUpdateTimestamp": 1743750428.0041468,
                    },
                    "Port-Channel5": {
                        "description": "MLAG Downlink - s1-host1",
                        "interval": 300,
                        "inBpsRate": 99.0032866811298,
                        "inPktsRate": 5.479571309111963e-06,
                        "inPpsRate": 0.06617587188193425,
                        "outBpsRate": 499.030957052671,
                        "outPktsRate": 2.912854497590912e-05,
                        "outPpsRate": 0.5221246404094458,
                        "lastUpdateTimestamp": 1743750428.004128,
                    },
                }
            },
            {
                "interfaces": {
                    "Ethernet2": {
                        "name": "Ethernet2",
                        "forwardingModel": "routed",
                        "lineProtocolStatus": "up",
                        "interfaceStatus": "connected",
                        "hardware": "ethernet",
                        "interfaceAddress": [
                            {
                                "primaryIp": {"address": "10.111.1.1", "maskLen": 31},
                                "secondaryIps": {},
                                "secondaryIpsOrderedList": [],
                                "virtualIp": {"address": "0.0.0.0", "maskLen": 0},
                                "virtualSecondaryIps": {},
                                "virtualSecondaryIpsOrderedList": [],
                                "broadcastAddress": "255.255.255.255",
                                "dhcp": False,
                            }
                        ],
                        "physicalAddress": "56:4a:04:73:1b:8f",
                        "burnedInAddress": "56:4a:04:73:1b:8f",
                        "description": "L3 Uplink - s1-spine1",
                        "bandwidth": 1000000000,
                        "mtu": 1500,
                        "l3MtuConfigured": False,
                        "l2Mru": 0,
                        "lastStatusChangeTimestamp": 1743738144.3375356,
                        "interfaceStatistics": {
                            "updateInterval": 300.0,
                            "inBitsRate": 92.4778371032985,
                            "inPktsRate": 0.0746926415480351,
                            "outBitsRate": 0.0,
                            "outPktsRate": 0.0,
                        },
                        "interfaceCounters": {
                            "inOctets": 143806,
                            "inUcastPkts": 497,
                            "inMulticastPkts": 415,
                            "inBroadcastPkts": 0,
                            "inDiscards": 0,
                            "inTotalPkts": 912,
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
                            "counterRefreshTime": 1743750532.606648,
                        },
                        "duplex": "duplexHalf",
                        "autoNegotiate": "unknown",
                        "loopbackMode": "loopbackNone",
                        "lanes": 0,
                    },
                    "Ethernet4": {
                        "name": "Ethernet4",
                        "forwardingModel": "dataLink",
                        "lineProtocolStatus": "up",
                        "interfaceStatus": "connected",
                        "hardware": "ethernet",
                        "interfaceAddress": [],
                        "physicalAddress": "76:65:c2:9b:b6:c6",
                        "burnedInAddress": "76:65:c2:9b:b6:c6",
                        "description": "MLAG Downlink - s1-host1",
                        "bandwidth": 1000000000,
                        "mtu": 9214,
                        "l3MtuConfigured": False,
                        "l2Mru": 0,
                        "lastStatusChangeTimestamp": 1743738144.3373442,
                        "interfaceMembership": "Member of Port-Channel5",
                        "interfaceStatistics": {
                            "updateInterval": 300.0,
                            "inBitsRate": 100.7957345751666,
                            "inPktsRate": 0.06629448229302994,
                            "outBitsRate": 497.7020017231056,
                            "outPktsRate": 0.5202975240121512,
                        },
                        "interfaceCounters": {
                            "inOctets": 157065,
                            "inUcastPkts": 0,
                            "inMulticastPkts": 833,
                            "inBroadcastPkts": 1,
                            "inDiscards": 0,
                            "inTotalPkts": 834,
                            "outOctets": 771821,
                            "outUcastPkts": 0,
                            "outMulticastPkts": 6071,
                            "outBroadcastPkts": 392,
                            "outDiscards": 0,
                            "outTotalPkts": 6463,
                            "linkStatusChanges": 2,
                            "totalInErrors": 0,
                            "inputErrorsDetail": {"runtFrames": 0, "giantFrames": 0, "fcsErrors": 0, "alignmentErrors": 0, "symbolErrors": 0, "rxPause": 0},
                            "totalOutErrors": 0,
                            "outputErrorsDetail": {"collisions": 0, "lateCollisions": 0, "deferredTransmissions": 0, "txPause": 0},
                            "counterRefreshTime": 1743750532.608292,
                        },
                        "duplex": "duplexHalf",
                        "autoNegotiate": "unknown",
                        "loopbackMode": "loopbackNone",
                        "lanes": 0,
                    },
                    "Ethernet1": {
                        "name": "Ethernet1",
                        "forwardingModel": "dataLink",
                        "lineProtocolStatus": "up",
                        "interfaceStatus": "connected",
                        "hardware": "ethernet",
                        "interfaceAddress": [],
                        "physicalAddress": "02:42:96:67:17:36",
                        "burnedInAddress": "02:42:96:67:17:36",
                        "description": "MLAG Peer-link - s1-leaf2",
                        "bandwidth": 1000000000,
                        "mtu": 9214,
                        "l3MtuConfigured": False,
                        "l2Mru": 0,
                        "lastStatusChangeTimestamp": 1743738132.4965024,
                        "interfaceMembership": "Member of Port-Channel1",
                        "interfaceStatistics": {
                            "updateInterval": 300.0,
                            "inBitsRate": 1812.7431567446233,
                            "inPktsRate": 2.585487950559777,
                            "outBitsRate": 1356.8652036248704,
                            "outPktsRate": 2.266164541741404,
                        },
                        "interfaceCounters": {
                            "inOctets": 2853088,
                            "inUcastPkts": 30923,
                            "inMulticastPkts": 838,
                            "inBroadcastPkts": 394,
                            "inDiscards": 0,
                            "inTotalPkts": 32155,
                            "outOctets": 2150114,
                            "outUcastPkts": 27821,
                            "outMulticastPkts": 4,
                            "outBroadcastPkts": 394,
                            "outDiscards": 0,
                            "outTotalPkts": 28219,
                            "linkStatusChanges": 2,
                            "totalInErrors": 0,
                            "inputErrorsDetail": {"runtFrames": 0, "giantFrames": 0, "fcsErrors": 0, "alignmentErrors": 0, "symbolErrors": 0, "rxPause": 0},
                            "totalOutErrors": 0,
                            "outputErrorsDetail": {"collisions": 0, "lateCollisions": 0, "deferredTransmissions": 0, "txPause": 0},
                            "counterRefreshTime": 1743750532.609684,
                        },
                        "duplex": "duplexFull",
                        "autoNegotiate": "unknown",
                        "loopbackMode": "loopbackNone",
                        "lanes": 0,
                    },
                    "Ethernet3": {
                        "name": "Ethernet3",
                        "forwardingModel": "routed",
                        "lineProtocolStatus": "up",
                        "interfaceStatus": "connected",
                        "hardware": "ethernet",
                        "interfaceAddress": [
                            {
                                "primaryIp": {"address": "10.111.2.1", "maskLen": 31},
                                "secondaryIps": {},
                                "secondaryIpsOrderedList": [],
                                "virtualIp": {"address": "0.0.0.0", "maskLen": 0},
                                "virtualSecondaryIps": {},
                                "virtualSecondaryIpsOrderedList": [],
                                "broadcastAddress": "255.255.255.255",
                                "dhcp": False,
                            }
                        ],
                        "physicalAddress": "06:9a:0a:bd:c4:0a",
                        "burnedInAddress": "06:9a:0a:bd:c4:0a",
                        "description": "L3 Uplink - s1-spine2",
                        "bandwidth": 1000000000,
                        "mtu": 1500,
                        "l3MtuConfigured": False,
                        "l2Mru": 0,
                        "lastStatusChangeTimestamp": 1743738144.3376553,
                        "interfaceStatistics": {
                            "updateInterval": 300.0,
                            "inBitsRate": 88.71171669451815,
                            "inPktsRate": 0.06881326151587384,
                            "outBitsRate": 0.0,
                            "outPktsRate": 0.0,
                        },
                        "interfaceCounters": {
                            "inOctets": 143610,
                            "inUcastPkts": 494,
                            "inMulticastPkts": 415,
                            "inBroadcastPkts": 0,
                            "inDiscards": 0,
                            "inTotalPkts": 909,
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
                            "counterRefreshTime": 1743750532.611445,
                        },
                        "duplex": "duplexHalf",
                        "autoNegotiate": "unknown",
                        "loopbackMode": "loopbackNone",
                        "lanes": 0,
                    },
                    "Ethernet6": {
                        "name": "Ethernet6",
                        "forwardingModel": "dataLink",
                        "lineProtocolStatus": "up",
                        "interfaceStatus": "connected",
                        "hardware": "ethernet",
                        "interfaceAddress": [],
                        "physicalAddress": "0e:f1:16:69:c2:24",
                        "burnedInAddress": "0e:f1:16:69:c2:24",
                        "description": "MLAG Peer-link - s1-leaf2",
                        "bandwidth": 1000000000,
                        "mtu": 9214,
                        "l3MtuConfigured": False,
                        "l2Mru": 0,
                        "lastStatusChangeTimestamp": 1743738132.4881961,
                        "interfaceMembership": "Member of Port-Channel1",
                        "interfaceStatistics": {
                            "updateInterval": 300.0,
                            "inBitsRate": 100.27689321743554,
                            "inPktsRate": 0.06536784140527623,
                            "outBitsRate": 256.71341417227643,
                            "outPktsRate": 0.2487533083064691,
                        },
                        "interfaceCounters": {
                            "inOctets": 158632,
                            "inUcastPkts": 0,
                            "inMulticastPkts": 835,
                            "inBroadcastPkts": 0,
                            "inDiscards": 0,
                            "inTotalPkts": 835,
                            "outOctets": 399513,
                            "outUcastPkts": 3097,
                            "outMulticastPkts": 0,
                            "outBroadcastPkts": 0,
                            "outDiscards": 0,
                            "outTotalPkts": 3097,
                            "linkStatusChanges": 2,
                            "totalInErrors": 0,
                            "inputErrorsDetail": {"runtFrames": 0, "giantFrames": 0, "fcsErrors": 0, "alignmentErrors": 0, "symbolErrors": 0, "rxPause": 0},
                            "totalOutErrors": 0,
                            "outputErrorsDetail": {"collisions": 0, "lateCollisions": 0, "deferredTransmissions": 0, "txPause": 0},
                            "counterRefreshTime": 1743750532.61287,
                        },
                        "duplex": "duplexFull",
                        "autoNegotiate": "unknown",
                        "loopbackMode": "loopbackNone",
                        "lanes": 0,
                    },
                    "Management0": {
                        "name": "Management0",
                        "forwardingModel": "routed",
                        "lineProtocolStatus": "up",
                        "interfaceStatus": "connected",
                        "hardware": "ethernet",
                        "interfaceAddress": [
                            {
                                "primaryIp": {"address": "192.168.0.12", "maskLen": 24},
                                "secondaryIps": {},
                                "secondaryIpsOrderedList": [],
                                "virtualIp": {"address": "0.0.0.0", "maskLen": 0},
                                "virtualSecondaryIps": {},
                                "virtualSecondaryIpsOrderedList": [],
                                "broadcastAddress": "255.255.255.255",
                                "dhcp": False,
                            }
                        ],
                        "physicalAddress": "12:0f:d9:6d:47:f7",
                        "burnedInAddress": "12:0f:d9:6d:47:f7",
                        "description": "",
                        "bandwidth": 1000000000,
                        "mtu": 1500,
                        "l3MtuConfigured": False,
                        "l2Mru": 0,
                        "lastStatusChangeTimestamp": 1743738085.9221241,
                        "interfaceStatistics": {
                            "updateInterval": 300.0,
                            "inBitsRate": 7012.071138622059,
                            "inPktsRate": 8.017886333233701,
                            "outBitsRate": 8498.044232124328,
                            "outPktsRate": 8.009337516051946,
                        },
                        "interfaceCounters": {
                            "inOctets": 6411618,
                            "inUcastPkts": 47869,
                            "inMulticastPkts": 0,
                            "inBroadcastPkts": 0,
                            "inDiscards": 0,
                            "inTotalPkts": 47869,
                            "outOctets": 8628471,
                            "outUcastPkts": 62799,
                            "outMulticastPkts": 0,
                            "outBroadcastPkts": 0,
                            "outDiscards": 0,
                            "outTotalPkts": 62799,
                            "linkStatusChanges": 3,
                            "totalInErrors": 0,
                            "inputErrorsDetail": {"runtFrames": 0, "giantFrames": 0, "fcsErrors": 0, "alignmentErrors": 0, "symbolErrors": 0, "rxPause": 0},
                            "totalOutErrors": 0,
                            "outputErrorsDetail": {"collisions": 0, "lateCollisions": 0, "deferredTransmissions": 0, "txPause": 0},
                            "counterRefreshTime": 1743750532.614511,
                        },
                        "duplex": "duplexHalf",
                        "autoNegotiate": "success",
                        "loopbackMode": "loopbackNone",
                        "lanes": 0,
                    },
                    "Port-Channel1": {
                        "name": "Port-Channel1",
                        "forwardingModel": "bridged",
                        "lineProtocolStatus": "up",
                        "interfaceStatus": "connected",
                        "hardware": "portChannel",
                        "interfaceAddress": [],
                        "physicalAddress": "02:42:96:67:17:36",
                        "description": "MLAG Peer-link - s1-leaf2",
                        "bandwidth": 2000000000,
                        "mtu": 9214,
                        "l3MtuConfigured": False,
                        "l2Mru": 0,
                        "lastStatusChangeTimestamp": 1743738138.0347695,
                        "interfaceStatistics": {
                            "updateInterval": 300.0,
                            "inBitsRate": 1913.0830400575996,
                            "inPktsRate": 2.650885401124123,
                            "outBitsRate": 1613.4392876435538,
                            "outPktsRate": 2.5147804494049457,
                        },
                        "interfaceCounters": {
                            "inOctets": 3010846,
                            "inUcastPkts": 30923,
                            "inMulticastPkts": 1667,
                            "inBroadcastPkts": 394,
                            "inDiscards": 0,
                            "inTotalPkts": 32984,
                            "outOctets": 2549627,
                            "outUcastPkts": 30918,
                            "outMulticastPkts": 4,
                            "outBroadcastPkts": 394,
                            "outDiscards": 0,
                            "outTotalPkts": 31316,
                            "linkStatusChanges": 2,
                            "totalInErrors": 0,
                            "totalOutErrors": 0,
                            "counterRefreshTime": 1743750532.618036,
                        },
                        "memberInterfaces": {
                            "Ethernet1": {"bandwidth": 1000000000, "duplex": "duplexHalf"},
                            "Ethernet6": {"bandwidth": 1000000000, "duplex": "duplexHalf"},
                        },
                        "fallbackEnabled": False,
                        "fallbackEnabledType": "fallbackNone",
                    },
                    "Port-Channel5": {
                        "name": "Port-Channel5",
                        "forwardingModel": "bridged",
                        "lineProtocolStatus": "up",
                        "interfaceStatus": "connected",
                        "hardware": "portChannel",
                        "interfaceAddress": [],
                        "physicalAddress": "76:65:c2:9b:b6:c6",
                        "description": "MLAG Downlink - s1-host1",
                        "bandwidth": 2000000000,
                        "mtu": 9214,
                        "l3MtuConfigured": False,
                        "l2Mru": 0,
                        "lastStatusChangeTimestamp": 1743738149.0576365,
                        "interfaceStatistics": {
                            "updateInterval": 300.0,
                            "inBitsRate": 100.7548468852208,
                            "inPktsRate": 0.06627334239526746,
                            "outBitsRate": 497.58423264927563,
                            "outPktsRate": 0.5201821117573231,
                        },
                        "interfaceCounters": {
                            "inOctets": 156706,
                            "inUcastPkts": 0,
                            "inMulticastPkts": 831,
                            "inBroadcastPkts": 1,
                            "inDiscards": 0,
                            "inTotalPkts": 832,
                            "outOctets": 771821,
                            "outUcastPkts": 0,
                            "outMulticastPkts": 6071,
                            "outBroadcastPkts": 392,
                            "outDiscards": 0,
                            "outTotalPkts": 6463,
                            "linkStatusChanges": 2,
                            "totalInErrors": 0,
                            "totalOutErrors": 0,
                            "counterRefreshTime": 1743750532.619669,
                        },
                        "memberInterfaces": {
                            "Ethernet4": {"bandwidth": 1000000000, "duplex": "duplexFull"},
                            "PeerEthernet4": {"bandwidth": 1000000000, "duplex": "duplexFull"},
                        },
                        "fallbackEnabled": False,
                        "fallbackEnabledType": "fallbackNone",
                    },
                }
            },
        ],
        "inputs": {"threshold": 70.0, "ignored_interfaces": ["Ethernet", "Port-Channel1", "Management0"]},
        "expected": {"result": AntaTestStatus.SUCCESS},
    },
    (VerifyInterfaceUtilization, "failure"): {
        "eos_data": [
            {
                "interfaces": {
                    "Ethernet1/1": {
                        "description": "P2P_LINK_TO_DC1-SPINE1_Ethernet1/1",
                        "interval": 300,
                        "inBpsRate": 100000000.0,
                        "inPktsRate": 0.00028663359326985426,
                        "inPpsRate": 3.9005388262031966,
                        "outBpsRate": 100000000.0,
                        "outPktsRate": 0.0,
                        "outPpsRate": 0.0,
                        "lastUpdateTimestamp": 1710253727.138605,
                    },
                    "Port-Channel31": {
                        "description": "MLAG_PEER_dc1-leaf1b_Po31",
                        "interval": 300,
                        "inBpsRate": 100000000.0,
                        "inPktsRate": 0.00011473185873493155,
                        "inPpsRate": 2.7009344704495084,
                        "outBpsRate": 1862.4876594267096,
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
            "result": AntaTestStatus.FAILURE,
            "messages": [
                "Interface: Ethernet1/1 BPS Rate: inBpsRate - Usage exceeds the threshold - Expected: < 3.0% Actual: 10.0%",
                "Interface: Ethernet1/1 BPS Rate: outBpsRate - Usage exceeds the threshold - Expected: < 3.0% Actual: 10.0%",
                "Interface: Port-Channel31 BPS Rate: inBpsRate - Usage exceeds the threshold - Expected: < 3.0% Actual: 5.0%",
            ],
        },
    },
    (VerifyInterfaceUtilization, "error-duplex-half"): {
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
            "result": AntaTestStatus.FAILURE,
            "messages": ["Interface: Ethernet1/1 - Test not implemented for non-full-duplex interfaces - Expected: duplexFull Actual: duplexHalf"],
        },
    },
    (VerifyInterfaceUtilization, "error-duplex-half-po"): {
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
            "result": AntaTestStatus.FAILURE,
            "messages": [
                "Interface: Port-Channel31 Member Interface: Ethernet3/1 - Test not implemented for non-full-duplex interfaces - "
                "Expected: duplexFull Actual: duplexHalf",
                "Interface: Port-Channel31 Member Interface: Ethernet4/1 - Test not implemented for non-full-duplex interfaces - "
                "Expected: duplexFull Actual: duplexHalf",
            ],
        },
    },
    (VerifyInterfaceErrors, "success"): {
        "eos_data": [
            {
                "interfaceErrorCounters": {
                    "Ethernet1": {"inErrors": 0, "frameTooLongs": 0, "outErrors": 0, "frameTooShorts": 0, "fcsErrors": 0, "alignmentErrors": 0, "symbolErrors": 0},
                    "Ethernet6": {"inErrors": 0, "frameTooLongs": 0, "outErrors": 0, "frameTooShorts": 0, "fcsErrors": 0, "alignmentErrors": 0, "symbolErrors": 0},
                }
            }
        ],
        "expected": {"result": AntaTestStatus.SUCCESS},
    },
    (VerifyInterfaceErrors, "success-ignore-interface"): {
        "eos_data": [
            {
                "interfaces": {
                    "Ethernet2": {
                        "name": "Ethernet2",
                        "interfaceAddress": [],
                        "interfaceStatistics": {},
                        "interfaceCounters": {
                            "linkStatusChanges": 2,
                            "totalInErrors": 0,
                            "inputErrorsDetail": {"runtFrames": 30, "giantFrames": 0, "fcsErrors": 0, "alignmentErrors": 0, "symbolErrors": 0, "rxPause": 0},
                            "totalOutErrors": 0,
                            "outputErrorsDetail": {"collisions": 0, "lateCollisions": 30, "deferredTransmissions": 0, "txPause": 0},
                        },
                    },
                }
            }
        ],
        "inputs": {"ignored_interfaces": ["Ethernet", "Management0"]},
        "expected": {"result": AntaTestStatus.SUCCESS},
    },
    (VerifyInterfaceErrors, "failure-ignore-interface"): {
        "eos_data": [
            {
                "interfaces": {
                    "Ethernet2": {
                        "name": "Ethernet2",
                        "interfaceAddress": [],
                        "interfaceStatistics": {},
                        "interfaceCounters": {
                            "linkStatusChanges": 12,
                            "totalInErrors": 0,
                            "inputErrorsDetail": {"runtFrames": 0, "giantFrames": 0, "fcsErrors": 0, "alignmentErrors": 0, "symbolErrors": 0, "rxPause": 0},
                            "totalOutErrors": 0,
                            "outputErrorsDetail": {"collisions": 0, "lateCollisions": 0, "deferredTransmissions": 0, "txPause": 0},
                        },
                    },
                    "Ethernet10": {"inErrors": 42, "frameTooLongs": 0, "outErrors": 0, "frameTooShorts": 0, "fcsErrors": 0, "alignmentErrors": 0, "symbolErrors": 0},
                }
            }
        ],
        "inputs": {"ignored_interfaces": ["Ethernet1", "Management0"]},
        "expected": {"result": AntaTestStatus.FAILURE, "messages": ["Interface: Ethernet10 - Non-zero error counter(s) - inErrors: 42"]},
    },
    (VerifyInterfaceErrors, "failure-multiple-intfs"): {
        "eos_data": [
            {
                "interfaceErrorCounters": {
                    "Ethernet1": {"inErrors": 42, "frameTooLongs": 0, "outErrors": 0, "frameTooShorts": 0, "fcsErrors": 0, "alignmentErrors": 0, "symbolErrors": 0},
                    "Ethernet6": {"inErrors": 0, "frameTooLongs": 0, "outErrors": 0, "frameTooShorts": 0, "fcsErrors": 0, "alignmentErrors": 666, "symbolErrors": 0},
                }
            }
        ],
        "expected": {
            "result": AntaTestStatus.FAILURE,
            "messages": [
                "Interface: Ethernet2 - Non-zero input error counter(s) - runtFrames: 10, giantFrames: 10, fcsErrors: 10, alignmentErrors: 10, symbolErrors: 10",
                "Interface: Ethernet2 - Total input error counter(s) mismatch - Expected: 0 Actual: 10",
                "Interface: Ethernet4 - Non-zero input error counter(s) - runtFrames: 20, giantFrames: 20, fcsErrors: 20, alignmentErrors: 20, symbolErrors: 20",
                "Interface: Ethernet4 - Total input error counter(s) mismatch - Expected: 0 Actual: 20",
            ],
        },
    },
    (VerifyInterfaceErrors, "failure-multiple-intfs-multiple-errors"): {
        "eos_data": [
            {
                "interfaceErrorCounters": {
                    "Ethernet1": {"inErrors": 42, "frameTooLongs": 0, "outErrors": 10, "frameTooShorts": 0, "fcsErrors": 0, "alignmentErrors": 0, "symbolErrors": 0},
                    "Ethernet6": {"inErrors": 0, "frameTooLongs": 0, "outErrors": 0, "frameTooShorts": 0, "fcsErrors": 0, "alignmentErrors": 6, "symbolErrors": 10},
                }
            }
        ],
        "expected": {
            "result": AntaTestStatus.FAILURE,
            "messages": [
                "Interface: Ethernet2 - Non-zero output error counter(s) - collisions: 20, lateCollisions: 20",
                "Interface: Ethernet2 - Total output error counter(s) mismatch - Expected: 0 Actual: 10",
            ],
        },
    },
    (VerifyInterfaceErrors, "failure-single-intf-multiple-errors"): {
        "eos_data": [
            {
                "interfaceErrorCounters": {
                    "Ethernet1": {"inErrors": 42, "frameTooLongs": 0, "outErrors": 2, "frameTooShorts": 0, "fcsErrors": 0, "alignmentErrors": 0, "symbolErrors": 0}
                }
            }
        ],
        "expected": {"result": AntaTestStatus.FAILURE, "messages": ["Interface: Ethernet1 - Non-zero error counter(s) - inErrors: 42, outErrors: 2"]},
    },
    (VerifyInterfaceDiscards, "success"): {
        "eos_data": [
            {
                "inDiscardsTotal": 0,
                "interfaces": {"Ethernet2": {"outDiscards": 0, "inDiscards": 0}, "Ethernet1": {"outDiscards": 0, "inDiscards": 0}},
                "outDiscardsTotal": 0,
            }
        ],
        "expected": {"result": AntaTestStatus.SUCCESS},
    },
    (VerifyInterfaceDiscards, "success-ignored-interface"): {
        "eos_data": [
            {
                "inDiscardsTotal": 0,
                "interfaces": {
                    "Ethernet2": {"outDiscards": 42, "inDiscards": 0},
                    "Ethernet1": {"outDiscards": 0, "inDiscards": 42},
                    "Ethernet3": {"outDiscards": 0, "inDiscards": 42},
                    "Port-Channel1": {"outDiscards": 0, "inDiscards": 42},
                    "Port-Channel2": {"outDiscards": 0, "inDiscards": 0},
                },
                "outDiscardsTotal": 0,
            }
        ],
        "inputs": {"ignored_interfaces": ["Port-Channel1", "Ethernet"]},
        "expected": {"result": AntaTestStatus.SUCCESS},
    },
    (VerifyInterfaceDiscards, "failure"): {
        "eos_data": [
            {
                "inDiscardsTotal": 0,
                "interfaces": {"Ethernet2": {"outDiscards": 42, "inDiscards": 0}, "Ethernet1": {"outDiscards": 0, "inDiscards": 42}},
                "outDiscardsTotal": 0,
            }
        ],
        "expected": {
            "result": AntaTestStatus.FAILURE,
            "messages": [
                "Interface: Ethernet2 - Non-zero discard counter(s): outDiscards: 42",
                "Interface: Ethernet1 - Non-zero discard counter(s): inDiscards: 42",
            ],
        },
    },
    (VerifyInterfaceErrDisabled, "success"): {"eos_data": [{"interfaceStatuses": {}}], "expected": {"result": AntaTestStatus.SUCCESS}},
    (VerifyInterfaceErrDisabled, "failure"): {
        "eos_data": [{"interfaceStatuses": {"Ethernet2": {"description": "", "status": "errdisabled", "causes": ["bpduguard"]}}}],
        "expected": {"result": AntaTestStatus.FAILURE, "messages": ["Interface: Ethernet2 - Error disabled - Causes: bpduguard"]},
    },
    (VerifyInterfaceErrDisabled, "failure-no-cause"): {
        "eos_data": [{"interfaceStatuses": {"Ethernet2": {"description": "", "status": "errdisabled"}}}],
        "expected": {"result": AntaTestStatus.FAILURE, "messages": ["Interface: Ethernet2 - Error disabled"]},
    },
    (VerifyInterfacesStatus, "success"): {
        "eos_data": [
            {
                "interfaceDescriptions": {
                    "Ethernet8": {"interfaceStatus": "up", "description": "", "lineProtocolStatus": "up"},
                    "Ethernet2": {"interfaceStatus": "adminDown", "description": "", "lineProtocolStatus": "down"},
                    "Ethernet3": {"interfaceStatus": "up", "description": "", "lineProtocolStatus": "up"},
                }
            }
        ],
        "inputs": {"interfaces": [{"name": "Ethernet2", "status": "adminDown"}, {"name": "Ethernet8", "status": "up"}, {"name": "Ethernet3", "status": "up"}]},
        "expected": {"result": AntaTestStatus.SUCCESS},
    },
    (VerifyInterfacesStatus, "success-up-with-line-protocol-status"): {
        "eos_data": [{"interfaceDescriptions": {"Ethernet8": {"interfaceStatus": "up", "description": "", "lineProtocolStatus": "down"}}}],
        "inputs": {"interfaces": [{"name": "Ethernet8", "status": "up", "line_protocol_status": "down"}]},
        "expected": {"result": AntaTestStatus.SUCCESS},
    },
    (VerifyInterfacesStatus, "success-with-line-protocol-status"): {
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
        "expected": {"result": AntaTestStatus.SUCCESS},
    },
    (VerifyInterfacesStatus, "success-lower"): {
        "eos_data": [
            {
                "interfaceDescriptions": {
                    "Ethernet8": {"interfaceStatus": "up", "description": "", "lineProtocolStatus": "up"},
                    "Ethernet2": {"interfaceStatus": "adminDown", "description": "", "lineProtocolStatus": "down"},
                    "Ethernet3": {"interfaceStatus": "up", "description": "", "lineProtocolStatus": "up"},
                }
            }
        ],
        "inputs": {"interfaces": [{"name": "ethernet2", "status": "adminDown"}, {"name": "ethernet8", "status": "up"}, {"name": "ethernet3", "status": "up"}]},
        "expected": {"result": AntaTestStatus.SUCCESS},
    },
    (VerifyInterfacesStatus, "success-eth-name"): {
        "eos_data": [
            {
                "interfaceDescriptions": {
                    "Ethernet8": {"interfaceStatus": "up", "description": "", "lineProtocolStatus": "up"},
                    "Ethernet2": {"interfaceStatus": "adminDown", "description": "", "lineProtocolStatus": "down"},
                    "Ethernet3": {"interfaceStatus": "up", "description": "", "lineProtocolStatus": "up"},
                }
            }
        ],
        "inputs": {"interfaces": [{"name": "eth2", "status": "adminDown"}, {"name": "et8", "status": "up"}, {"name": "et3", "status": "up"}]},
        "expected": {"result": AntaTestStatus.SUCCESS},
    },
    (VerifyInterfacesStatus, "success-po-name"): {
        "eos_data": [{"interfaceDescriptions": {"Port-Channel100": {"interfaceStatus": "up", "description": "", "lineProtocolStatus": "up"}}}],
        "inputs": {"interfaces": [{"name": "po100", "status": "up"}]},
        "expected": {"result": AntaTestStatus.SUCCESS},
    },
    (VerifyInterfacesStatus, "success-sub-interfaces"): {
        "eos_data": [{"interfaceDescriptions": {"Ethernet52/1.1963": {"interfaceStatus": "up", "description": "", "lineProtocolStatus": "up"}}}],
        "inputs": {"interfaces": [{"name": "Ethernet52/1.1963", "status": "up"}]},
        "expected": {"result": AntaTestStatus.SUCCESS},
    },
    (VerifyInterfacesStatus, "success-transceiver-down"): {
        "eos_data": [{"interfaceDescriptions": {"Ethernet49/1": {"interfaceStatus": "adminDown", "description": "", "lineProtocolStatus": "notPresent"}}}],
        "inputs": {"interfaces": [{"name": "Ethernet49/1", "status": "adminDown"}]},
        "expected": {"result": AntaTestStatus.SUCCESS},
    },
    (VerifyInterfacesStatus, "success-po-down"): {
        "eos_data": [{"interfaceDescriptions": {"Port-Channel100": {"interfaceStatus": "adminDown", "description": "", "lineProtocolStatus": "lowerLayerDown"}}}],
        "inputs": {"interfaces": [{"name": "PortChannel100", "status": "adminDown"}]},
        "expected": {"result": AntaTestStatus.SUCCESS},
    },
    (VerifyInterfacesStatus, "success-po-lowerlayerdown"): {
        "eos_data": [{"interfaceDescriptions": {"Port-Channel100": {"interfaceStatus": "adminDown", "description": "", "lineProtocolStatus": "lowerLayerDown"}}}],
        "inputs": {"interfaces": [{"name": "Port-Channel100", "status": "adminDown", "line_protocol_status": "lowerLayerDown"}]},
        "expected": {"result": AntaTestStatus.SUCCESS},
    },
    (VerifyInterfacesStatus, "failure-not-configured"): {
        "eos_data": [
            {
                "interfaceDescriptions": {
                    "Ethernet2": {"interfaceStatus": "up", "description": "", "lineProtocolStatus": "up"},
                    "Ethernet3": {"interfaceStatus": "up", "description": "", "lineProtocolStatus": "up"},
                }
            }
        ],
        "inputs": {"interfaces": [{"name": "Ethernet2", "status": "up"}, {"name": "Ethernet8", "status": "up"}, {"name": "Ethernet3", "status": "up"}]},
        "expected": {"result": AntaTestStatus.FAILURE, "messages": ["Ethernet8 - Not configured"]},
    },
    (VerifyInterfacesStatus, "failure-status-down"): {
        "eos_data": [
            {
                "interfaceDescriptions": {
                    "Ethernet8": {"interfaceStatus": "down", "description": "", "lineProtocolStatus": "down"},
                    "Ethernet2": {"interfaceStatus": "up", "description": "", "lineProtocolStatus": "up"},
                    "Ethernet3": {"interfaceStatus": "up", "description": "", "lineProtocolStatus": "up"},
                }
            }
        ],
        "inputs": {"interfaces": [{"name": "Ethernet2", "status": "up"}, {"name": "Ethernet8", "status": "up"}, {"name": "Ethernet3", "status": "up"}]},
        "expected": {"result": AntaTestStatus.FAILURE, "messages": ["Ethernet8 - Status mismatch - Expected: up/up, Actual: down/down"]},
    },
    (VerifyInterfacesStatus, "failure-proto-down"): {
        "eos_data": [
            {
                "interfaceDescriptions": {
                    "Ethernet8": {"interfaceStatus": "up", "description": "", "lineProtocolStatus": "down"},
                    "Ethernet2": {"interfaceStatus": "up", "description": "", "lineProtocolStatus": "up"},
                    "Ethernet3": {"interfaceStatus": "up", "description": "", "lineProtocolStatus": "up"},
                }
            }
        ],
        "inputs": {"interfaces": [{"name": "Ethernet2", "status": "up"}, {"name": "Ethernet8", "status": "up"}, {"name": "Ethernet3", "status": "up"}]},
        "expected": {"result": AntaTestStatus.FAILURE, "messages": ["Ethernet8 - Status mismatch - Expected: up/up, Actual: up/down"]},
    },
    (VerifyInterfacesStatus, "failure-po-status-down"): {
        "eos_data": [{"interfaceDescriptions": {"Port-Channel100": {"interfaceStatus": "down", "description": "", "lineProtocolStatus": "lowerLayerDown"}}}],
        "inputs": {"interfaces": [{"name": "PortChannel100", "status": "up"}]},
        "expected": {"result": AntaTestStatus.FAILURE, "messages": ["Port-Channel100 - Status mismatch - Expected: up/up, Actual: down/lowerLayerDown"]},
    },
    (VerifyInterfacesStatus, "failure-proto-unknown"): {
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
            "result": AntaTestStatus.FAILURE,
            "messages": ["Ethernet2 - Status mismatch - Expected: up/down, Actual: up/unknown", "Ethernet8 - Status mismatch - Expected: up/up, Actual: up/down"],
        },
    },
    (VerifyInterfacesStatus, "failure-interface-status-down"): {
        "eos_data": [
            {
                "interfaceDescriptions": {
                    "Ethernet8": {"interfaceStatus": "up", "description": "", "lineProtocolStatus": "down"},
                    "Ethernet2": {"interfaceStatus": "up", "description": "", "lineProtocolStatus": "unknown"},
                    "Ethernet3": {"interfaceStatus": "up", "description": "", "lineProtocolStatus": "up"},
                }
            }
        ],
        "inputs": {"interfaces": [{"name": "Ethernet2", "status": "down"}, {"name": "Ethernet8", "status": "down"}, {"name": "Ethernet3", "status": "down"}]},
        "expected": {
            "result": AntaTestStatus.FAILURE,
            "messages": [
                "Ethernet2 - Status mismatch - Expected: down, Actual: up",
                "Ethernet8 - Status mismatch - Expected: down, Actual: up",
                "Ethernet3 - Status mismatch - Expected: down, Actual: up",
            ],
        },
    },
    (VerifyStormControlDrops, "success"): {
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
        "expected": {"result": AntaTestStatus.SUCCESS},
    },
    (VerifyStormControlDrops, "failure"): {
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
        "expected": {"result": AntaTestStatus.FAILURE, "messages": ["Interface: Ethernet1 - Non-zero storm-control drop counter(s) - broadcast: 666"]},
    },
    (VerifyPortChannels, "success"): {
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
        "expected": {"result": AntaTestStatus.SUCCESS},
    },
    (VerifyPortChannels, "success-ignored-interface"): {
        "eos_data": [
            {
                "portChannels": {
                    "Port-Channel1": {
                        "activePorts": {"Ethernet1": {}, "Ethernet6": {}},
                        "rxPorts": {},
                        "inactivePorts": {},
                        "recircFeature": [],
                        "inactiveLag": False,
                        "minLinks": 0,
                        "minSpeed": "0 gbps",
                        "currWeight": 0,
                        "maxWeight": 16,
                    },
                    "Port-Channel5": {
                        "activePorts": {"Ethernet4": {}, "PeerEthernet4": {}},
                        "rxPorts": {},
                        "inactivePorts": {"Ethernet8": {"reasonUnconfigured": "waiting for LACP response"}},
                        "recircFeature": [],
                        "inactiveLag": False,
                        "minLinks": 0,
                        "minSpeed": "0 gbps",
                        "currWeight": 0,
                        "maxWeight": 16,
                    },
                }
            }
        ],
        "inputs": {"ignored_interfaces": ["Port-Channel5"]},
        "expected": {"result": AntaTestStatus.SUCCESS},
    },
    (VerifyPortChannels, "success-ignored-all-interface"): {
        "eos_data": [
            {
                "portChannels": {
                    "Port-Channel1": {
                        "activePorts": {"Ethernet1": {}, "Ethernet6": {}},
                        "rxPorts": {},
                        "inactivePorts": {},
                        "recircFeature": [],
                        "inactiveLag": False,
                        "minLinks": 0,
                        "minSpeed": "0 gbps",
                        "currWeight": 0,
                        "maxWeight": 16,
                    },
                    "Port-Channel5": {
                        "activePorts": {"Ethernet4": {}, "PeerEthernet4": {}},
                        "rxPorts": {},
                        "inactivePorts": {"Ethernet8": {"reasonUnconfigured": "waiting for LACP response"}},
                        "recircFeature": [],
                        "inactiveLag": False,
                        "minLinks": 0,
                        "minSpeed": "0 gbps",
                        "currWeight": 0,
                        "maxWeight": 16,
                    },
                }
            }
        ],
        "inputs": {"ignored_interfaces": ["Port-Channel5"]},
        "expected": {"result": AntaTestStatus.SUCCESS},
    },
    (VerifyPortChannels, "failure"): {
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
        "expected": {"result": AntaTestStatus.FAILURE, "messages": ["Port-Channel42 - Inactive port(s) - Ethernet8"]},
    },
    (VerifyIllegalLACP, "success"): {
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
        "expected": {"result": AntaTestStatus.SUCCESS},
    },
    (VerifyIllegalLACP, "success-ignored-interface"): {
        "eos_data": [
            {
                "portChannels": {
                    "Port-Channel1": {
                        "interfaces": {
                            "Ethernet1": {
                                "actorPortStatus": "bundled",
                                "lacpdusRxCount": 512,
                                "lacpdusTxCount": 514,
                                "markersRxCount": 0,
                                "markersTxCount": 0,
                                "markerResponseRxCount": 0,
                                "markerResponseTxCount": 0,
                                "illegalRxCount": 66,
                            },
                            "Ethernet6": {
                                "actorPortStatus": "bundled",
                                "lacpdusRxCount": 513,
                                "lacpdusTxCount": 516,
                                "markersRxCount": 0,
                                "markersTxCount": 0,
                                "markerResponseRxCount": 0,
                                "markerResponseTxCount": 0,
                                "illegalRxCount": 0,
                            },
                        }
                    },
                    "Port-Channel5": {
                        "markers": {"markers": ["*"]},
                        "interfaces": {
                            "Ethernet4": {
                                "actorPortStatus": "bundled",
                                "lacpdusRxCount": 521,
                                "lacpdusTxCount": 15119,
                                "markersRxCount": 0,
                                "markersTxCount": 0,
                                "markerResponseRxCount": 0,
                                "markerResponseTxCount": 0,
                                "illegalRxCount": 66,
                            }
                        },
                    },
                },
                "markerMessages": {"markerMessages": [{"marker": "*"}]},
                "orphanPorts": {},
            }
        ],
        "inputs": {"ignored_interfaces": ["Port-Channel1", "Port-Channel5"]},
        "expected": {"result": AntaTestStatus.SUCCESS},
    },
    (VerifyIllegalLACP, "failure"): {
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
        "expected": {"result": AntaTestStatus.FAILURE, "messages": ["Port-Channel42 Interface: Ethernet8 - Illegal LACP packets found"]},
    },
    (VerifyLoopbackCount, "success"): {
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
                    "Ethernet666": {
                        "name": "Ethernet666",
                        "interfaceStatus": "connected",
                        "interfaceAddress": {"ipAddr": {"maskLen": 32, "address": "6.6.6.6"}},
                        "ipv4Routable240": False,
                        "lineProtocolStatus": "up",
                    },
                }
            }
        ],
        "inputs": {"number": 2},
        "expected": {"result": AntaTestStatus.SUCCESS},
    },
    (VerifyLoopbackCount, "failure-loopback-down"): {
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
                }
            }
        ],
        "inputs": {"number": 2},
        "expected": {
            "result": AntaTestStatus.FAILURE,
            "messages": [
                "Interface: Loopback666 - Invalid line protocol status - Expected: up Actual: down",
                "Interface: Loopback666 - Invalid interface status - Expected: connected Actual: notconnect",
            ],
        },
    },
    (VerifyLoopbackCount, "failure-count-loopback"): {
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
                    }
                }
            }
        ],
        "inputs": {"number": 2},
        "expected": {"result": AntaTestStatus.FAILURE, "messages": ["Loopback interface(s) count mismatch: Expected 2 Actual: 1"]},
    },
    (VerifySVI, "success"): {
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
        "expected": {"result": AntaTestStatus.SUCCESS},
    },
    (VerifySVI, "failure"): {
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
        "expected": {
            "result": AntaTestStatus.FAILURE,
            "messages": [
                "SVI: Vlan42 - Invalid line protocol status - Expected: up Actual: lowerLayerDown",
                "SVI: Vlan42 - Invalid interface status - Expected: connected Actual: notconnect",
            ],
        },
    },
    (VerifyL3MTU, "success"): {
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
                }
            }
        ],
        "inputs": {"mtu": 1500},
        "expected": {"result": AntaTestStatus.SUCCESS},
    },
    (VerifyL3MTU, "success-ignored-interfaces"): {
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
                }
            }
        ],
        "inputs": {"mtu": 1500, "ignored_interfaces": ["Loopback", "Port-Channel", "Management", "Vxlan"], "specific_mtu": [{"Ethernet10": 1501}]},
        "expected": {"result": AntaTestStatus.SUCCESS},
    },
    (VerifyL3MTU, "failure"): {
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
                }
            }
        ],
        "inputs": {"mtu": 1500},
        "expected": {"result": AntaTestStatus.FAILURE, "messages": ["Interface: Ethernet2 - Incorrect MTU - Expected: 1500 Actual: 1600"]},
    },
    (VerifyL3MTU, "failure-specified-interface-mtu"): {
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
                }
            }
        ],
        "inputs": {"mtu": 1500, "ignored_interfaces": ["Loopback", "Port-Channel2", "Management", "Vxlan1"], "specific_mtu": [{"Ethernet10": 1501}]},
        "expected": {"result": AntaTestStatus.FAILURE, "messages": ["Interface: Ethernet10 - Incorrect MTU - Expected: 1501 Actual: 1502"]},
    },
    (VerifyL3MTU, "failure-ignored-specified-interface-mtu"): {
        "eos_data": [
            {
                "interfaces": {
                    "Ethernet2": {
                        "name": "Ethernet2",
                        "forwardingModel": "routed",
                        "lineProtocolStatus": "up",
                        "interfaceStatus": "connected",
                        "hardware": "ethernet",
                        "mtu": 1503,
                        "l3MtuConfigured": True,
                        "l2Mru": 0,
                    },
                    "Ethernet1/1": {
                        "name": "Ethernet1/1",
                        "forwardingModel": "routed",
                        "lineProtocolStatus": "up",
                        "interfaceStatus": "connected",
                        "hardware": "ethernet",
                        "mtu": 1502,
                        "l3MtuConfigured": False,
                        "l2Mru": 0,
                    },
                    "Ethernet1.100": {
                        "name": "Ethernet1.100",
                        "forwardingModel": "routed",
                        "lineProtocolStatus": "up",
                        "interfaceStatus": "connected",
                        "hardware": "ethernet",
                        "mtu": 1507,
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
                }
            }
        ],
        "inputs": {
            "mtu": 1500,
            "ignored_interfaces": ["Loopback", "Port-Channel2", "Management", "Vxlan1", "Ethernet1/1", "Ethernet1.100"],
            "specific_mtu": [{"Ethernet1/1": 1501}],
        },
        "expected": {"result": AntaTestStatus.FAILURE, "messages": ["Interface: Ethernet2 - Incorrect MTU - Expected: 1500 Actual: 1503"]},
    },
    (VerifyL3MTU, "failure-ignored-specified-ethernet"): {
        "eos_data": [
            {
                "interfaces": {
                    "Ethernet2": {
                        "name": "Ethernet2",
                        "forwardingModel": "routed",
                        "lineProtocolStatus": "up",
                        "interfaceStatus": "connected",
                        "hardware": "ethernet",
                        "mtu": 1503,
                        "l3MtuConfigured": True,
                        "l2Mru": 0,
                    },
                    "Ethernet1/1": {
                        "name": "Ethernet1/1",
                        "forwardingModel": "routed",
                        "lineProtocolStatus": "up",
                        "interfaceStatus": "connected",
                        "hardware": "ethernet",
                        "mtu": 1502,
                        "l3MtuConfigured": False,
                        "l2Mru": 0,
                    },
                    "Ethernet1.100": {
                        "name": "Ethernet1.100",
                        "forwardingModel": "routed",
                        "lineProtocolStatus": "up",
                        "interfaceStatus": "connected",
                        "hardware": "ethernet",
                        "mtu": 1507,
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
                }
            }
        ],
        "inputs": {"mtu": 1500, "ignored_interfaces": ["Loopback", "Ethernet1"], "specific_mtu": [{"Ethernet1/1": 1501}]},
        "expected": {
            "result": AntaTestStatus.FAILURE,
            "messages": [
                "Interface: Ethernet2 - Incorrect MTU - Expected: 1500 Actual: 1503",
                "Interface: Ethernet1/1 - Incorrect MTU - Expected: 1501 Actual: 1502",
                "Interface: Ethernet1.100 - Incorrect MTU - Expected: 1500 Actual: 1507",
            ],
        },
    },
    (VerifyL3MTU, "succuss-ethernet-all"): {
        "eos_data": [
            {
                "interfaces": {
                    "Ethernet2": {
                        "name": "Ethernet2",
                        "forwardingModel": "routed",
                        "lineProtocolStatus": "up",
                        "interfaceStatus": "connected",
                        "hardware": "ethernet",
                        "mtu": 1503,
                        "l3MtuConfigured": True,
                        "l2Mru": 0,
                    },
                    "Ethernet1/1": {
                        "name": "Ethernet1/1",
                        "forwardingModel": "routed",
                        "lineProtocolStatus": "up",
                        "interfaceStatus": "connected",
                        "hardware": "ethernet",
                        "mtu": 1502,
                        "l3MtuConfigured": False,
                        "l2Mru": 0,
                    },
                    "Ethernet1.100": {
                        "name": "Ethernet1.100",
                        "forwardingModel": "routed",
                        "lineProtocolStatus": "up",
                        "interfaceStatus": "connected",
                        "hardware": "ethernet",
                        "mtu": 1507,
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
                }
            }
        ],
        "inputs": {"mtu": 1500, "ignored_interfaces": ["Loopback", "Ethernet"], "specific_mtu": [{"Ethernet1/1": 1501}]},
        "expected": {"result": AntaTestStatus.SUCCESS},
    },
    (VerifyL2MTU, "success"): {
        "eos_data": [
            {
                "interfaces": {
                    "Ethernet2/1": {
                        "name": "Ethernet2/1",
                        "forwardingModel": "bridged",
                        "lineProtocolStatus": "up",
                        "interfaceStatus": "connected",
                        "hardware": "ethernet",
                        "mtu": 9218,
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
                }
            }
        ],
        "inputs": {"mtu": 9214, "ignored_interfaces": ["Loopback0", "Port-Channel", "Management0", "Vxlan", "Ethernet2/1"], "specific_mtu": [{"Ethernet10": 9214}]},
        "expected": {"result": AntaTestStatus.SUCCESS},
    },
    (VerifyL2MTU, "failure"): {
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
                }
            }
        ],
        "inputs": {"mtu": 1500},
        "expected": {
            "result": AntaTestStatus.FAILURE,
            "messages": [
                "Interface: Ethernet10 - Incorrect MTU - Expected: 1500 Actual: 9214",
                "Interface: Port-Channel2 - Incorrect MTU - Expected: 1500 Actual: 9214",
            ],
        },
    },
    (VerifyL2MTU, "failure-specific-interface"): {
        "eos_data": [
            {
                "interfaces": {
                    "Ethernet1.100": {
                        "name": "Ethernet2",
                        "forwardingModel": "bridged",
                        "lineProtocolStatus": "up",
                        "interfaceStatus": "connected",
                        "hardware": "ethernet",
                        "mtu": 9218,
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
                }
            }
        ],
        "inputs": {"specific_mtu": [{"Et10": 9214}, {"Port-Channel2": 10000}], "ignored_interfaces": ["Ethernet", "Vxlan1"]},
        "expected": {"result": AntaTestStatus.FAILURE, "messages": ["Interface: Port-Channel2 - Incorrect MTU - Expected: 10000 Actual: 9214"]},
    },
    (VerifyIPProxyARP, "success"): {
        "eos_data": [
            {
                "interfaces": {
                    "Ethernet1": {"name": "Ethernet1", "lineProtocolStatus": "up", "interfaceStatus": "connected", "proxyArp": True},
                    "Ethernet2": {"name": "Ethernet2", "lineProtocolStatus": "up", "interfaceStatus": "connected", "proxyArp": True},
                }
            }
        ],
        "inputs": {"interfaces": ["Ethernet1", "Ethernet2"]},
        "expected": {"result": AntaTestStatus.SUCCESS},
    },
    (VerifyIPProxyARP, "failure-interface-not-found"): {
        "eos_data": [{"interfaces": {"Ethernet1": {"name": "Ethernet1", "lineProtocolStatus": "up", "interfaceStatus": "connected", "proxyArp": True}}}],
        "inputs": {"interfaces": ["Ethernet1", "Ethernet2"]},
        "expected": {"result": AntaTestStatus.FAILURE, "messages": ["Interface: Ethernet2 - Not found"]},
    },
    (VerifyIPProxyARP, "failure"): {
        "eos_data": [
            {
                "interfaces": {
                    "Ethernet1": {"name": "Ethernet1", "lineProtocolStatus": "up", "interfaceStatus": "connected", "proxyArp": True},
                    "Ethernet2": {"name": "Ethernet2", "lineProtocolStatus": "up", "interfaceStatus": "connected", "proxyArp": False},
                }
            }
        ],
        "inputs": {"interfaces": ["Ethernet1", "Ethernet2"]},
        "expected": {"result": AntaTestStatus.FAILURE, "messages": ["Interface: Ethernet2 - Proxy-ARP disabled"]},
    },
    (VerifyInterfaceIPv4, "success"): {
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
            }
        ],
        "inputs": {
            "interfaces": [
                {"name": "Ethernet2", "primary_ip": "172.30.11.1/31", "secondary_ips": ["10.10.10.1/31", "10.10.10.10/31"]},
                {"name": "Ethernet12", "primary_ip": "172.30.11.10/31", "secondary_ips": ["10.10.10.10/31", "10.10.10.20/31"]},
            ]
        },
        "expected": {"result": AntaTestStatus.SUCCESS},
    },
    (VerifyInterfaceIPv4, "success-without-secondary-ip"): {
        "eos_data": [
            {
                "interfaces": {
                    "Ethernet2": {"interfaceAddress": {"primaryIp": {"address": "172.30.11.0", "maskLen": 31}, "secondaryIpsOrderedList": []}},
                    "Ethernet12": {"interfaceAddress": {"primaryIp": {"address": "172.30.11.10", "maskLen": 31}, "secondaryIpsOrderedList": []}},
                }
            }
        ],
        "inputs": {"interfaces": [{"name": "Ethernet2", "primary_ip": "172.30.11.0/31"}, {"name": "Ethernet12", "primary_ip": "172.30.11.10/31"}]},
        "expected": {"result": AntaTestStatus.SUCCESS},
    },
    (VerifyInterfaceIPv4, "failure-interface-not-found"): {
        "eos_data": [{"interfaces": {"Ethernet10": {"interfaceAddress": {"primaryIp": {"address": "172.30.11.0", "maskLen": 31}, "secondaryIpsOrderedList": []}}}}],
        "inputs": {
            "interfaces": [
                {"name": "Ethernet2", "primary_ip": "172.30.11.0/31", "secondary_ips": ["10.10.10.0/31", "10.10.10.10/31"]},
                {"name": "Ethernet12", "primary_ip": "172.30.11.20/31", "secondary_ips": ["10.10.11.0/31", "10.10.11.10/31"]},
            ]
        },
        "expected": {"result": AntaTestStatus.FAILURE, "messages": ["Interface: Ethernet2 - Not found", "Interface: Ethernet12 - Not found"]},
    },
    (VerifyInterfaceIPv4, "failure-not-l3-interface"): {
        "eos_data": [{"interfaces": {"Ethernet2": {"interfaceAddress": {}}, "Ethernet12": {"interfaceAddress": {}}}}],
        "inputs": {
            "interfaces": [
                {"name": "Ethernet2", "primary_ip": "172.30.11.0/31", "secondary_ips": ["10.10.10.0/31", "10.10.10.10/31"]},
                {"name": "Ethernet12", "primary_ip": "172.30.11.20/31", "secondary_ips": ["10.10.11.0/31", "10.10.11.10/31"]},
            ]
        },
        "expected": {
            "result": AntaTestStatus.FAILURE,
            "messages": ["Interface: Ethernet2 - IP address is not configured", "Interface: Ethernet12 - IP address is not configured"],
        },
    },
    (VerifyInterfaceIPv4, "failure-ip-address-not-configured"): {
        "eos_data": [
            {
                "interfaces": {
                    "Ethernet2": {"interfaceAddress": {"primaryIp": {"address": "0.0.0.0", "maskLen": 0}, "secondaryIpsOrderedList": []}},
                    "Ethernet12": {"interfaceAddress": {"primaryIp": {"address": "0.0.0.0", "maskLen": 0}, "secondaryIpsOrderedList": []}},
                }
            }
        ],
        "inputs": {
            "interfaces": [
                {"name": "Ethernet2", "primary_ip": "172.30.11.0/31", "secondary_ips": ["10.10.10.0/31", "10.10.10.10/31"]},
                {"name": "Ethernet12", "primary_ip": "172.30.11.10/31", "secondary_ips": ["10.10.11.0/31", "10.10.11.10/31"]},
            ]
        },
        "expected": {
            "result": AntaTestStatus.FAILURE,
            "messages": [
                "Interface: Ethernet2 - IP address mismatch - Expected: 172.30.11.0/31 Actual: 0.0.0.0/0",
                "Interface: Ethernet2 - Secondary IP address is not configured",
                "Interface: Ethernet12 - IP address mismatch - Expected: 172.30.11.10/31 Actual: 0.0.0.0/0",
                "Interface: Ethernet12 - Secondary IP address is not configured",
            ],
        },
    },
    (VerifyInterfaceIPv4, "failure-ip-address-missmatch"): {
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
            }
        ],
        "inputs": {
            "interfaces": [
                {"name": "Ethernet2", "primary_ip": "172.30.11.2/31", "secondary_ips": ["10.10.10.20/31", "10.10.10.30/31"]},
                {"name": "Ethernet3", "primary_ip": "172.30.10.2/31", "secondary_ips": ["10.10.11.0/31", "10.10.11.10/31"]},
            ]
        },
        "expected": {
            "result": AntaTestStatus.FAILURE,
            "messages": [
                "Interface: Ethernet2 - IP address mismatch - Expected: 172.30.11.2/31 Actual: 172.30.11.0/31",
                "Interface: Ethernet2 - Secondary IP address mismatch - Expected: 10.10.10.20/31, 10.10.10.30/31 Actual: 10.10.10.0/31, 10.10.10.10/31",
                "Interface: Ethernet3 - IP address mismatch - Expected: 172.30.10.2/31 Actual: 172.30.10.10/31",
                "Interface: Ethernet3 - Secondary IP address mismatch - Expected: 10.10.11.0/31, 10.10.11.10/31 Actual: 10.10.11.0/31, 10.11.11.10/31",
            ],
        },
    },
    (VerifyInterfaceIPv4, "failure-secondary-ip-address"): {
        "eos_data": [
            {
                "interfaces": {
                    "Ethernet2": {"interfaceAddress": {"primaryIp": {"address": "172.30.11.0", "maskLen": 31}, "secondaryIpsOrderedList": []}},
                    "Ethernet3": {
                        "interfaceAddress": {
                            "primaryIp": {"address": "172.30.10.10", "maskLen": 31},
                            "secondaryIpsOrderedList": [{"address": "10.10.11.0", "maskLen": 31}, {"address": "10.11.11.10", "maskLen": 31}],
                        }
                    },
                }
            }
        ],
        "inputs": {
            "interfaces": [
                {"name": "Ethernet2", "primary_ip": "172.30.11.2/31", "secondary_ips": ["10.10.10.20/31", "10.10.10.30/31"]},
                {"name": "Ethernet3", "primary_ip": "172.30.10.2/31", "secondary_ips": ["10.10.11.0/31", "10.10.11.10/31"]},
            ]
        },
        "expected": {
            "result": AntaTestStatus.FAILURE,
            "messages": [
                "Interface: Ethernet2 - IP address mismatch - Expected: 172.30.11.2/31 Actual: 172.30.11.0/31",
                "Interface: Ethernet2 - Secondary IP address is not configured",
                "Interface: Ethernet3 - IP address mismatch - Expected: 172.30.10.2/31 Actual: 172.30.10.10/31",
                "Interface: Ethernet3 - Secondary IP address mismatch - Expected: 10.10.11.0/31, 10.10.11.10/31 Actual: 10.10.11.0/31, 10.11.11.10/31",
            ],
        },
    },
    (VerifyIpVirtualRouterMac, "success"): {
        "eos_data": [{"virtualMacs": [{"macAddress": "00:1c:73:00:dc:01"}]}],
        "inputs": {"mac_address": "00:1c:73:00:dc:01"},
        "expected": {"result": AntaTestStatus.SUCCESS},
    },
    (VerifyIpVirtualRouterMac, "faliure-incorrect-mac-address"): {
        "eos_data": [{"virtualMacs": [{"macAddress": "00:00:00:00:00:00"}]}],
        "inputs": {"mac_address": "00:1c:73:00:dc:01"},
        "expected": {"result": AntaTestStatus.FAILURE, "messages": ["IP virtual router MAC address: 00:1c:73:00:dc:01 - Not configured"]},
    },
    (VerifyInterfacesSpeed, "success"): {
        "eos_data": [
            {
                "interfaces": {
                    "Ethernet1": {"bandwidth": 1000000000, "autoNegotiate": "unknown", "duplex": "duplexFull", "lanes": 2},
                    "Ethernet1/1/2": {"bandwidth": 1000000000, "autoNegotiate": "unknown", "duplex": "duplexFull", "lanes": 2},
                    "Ethernet3": {"bandwidth": 100000000000, "autoNegotiate": "success", "duplex": "duplexFull", "lanes": 8},
                    "Ethernet4": {"bandwidth": 2500000000, "autoNegotiate": "unknown", "duplex": "duplexFull", "lanes": 8},
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
        "expected": {"result": AntaTestStatus.SUCCESS},
    },
    (VerifyInterfacesSpeed, "failure-incorrect-speed"): {
        "eos_data": [
            {
                "interfaces": {
                    "Ethernet1": {"bandwidth": 100000000000, "autoNegotiate": "unknown", "duplex": "duplexFull", "lanes": 2},
                    "Ethernet1/1/1": {"bandwidth": 100000000000, "autoNegotiate": "unknown", "duplex": "duplexFull", "lanes": 2},
                    "Ethernet3": {"bandwidth": 10000000000, "autoNegotiate": "success", "duplex": "duplexFull", "lanes": 8},
                    "Ethernet4": {"bandwidth": 25000000000, "autoNegotiate": "unknown", "duplex": "duplexFull", "lanes": 8},
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
            "result": AntaTestStatus.FAILURE,
            "messages": [
                "Interface: Ethernet1 - Bandwidth mismatch - Expected: 1.0Gbps Actual: 100Gbps",
                "Interface: Ethernet1/1/1 - Bandwidth mismatch - Expected: 1.0Gbps Actual: 100Gbps",
                "Interface: Ethernet3 - Bandwidth mismatch - Expected: 100.0Gbps Actual: 10Gbps",
                "Interface: Ethernet4 - Bandwidth mismatch - Expected: 2.5Gbps Actual: 25Gbps",
            ],
        },
    },
    (VerifyInterfacesSpeed, "failure-incorrect-mode"): {
        "eos_data": [
            {
                "interfaces": {
                    "Ethernet1": {"bandwidth": 1000000000, "autoNegotiate": "unknown", "duplex": "duplexHalf", "lanes": 2},
                    "Ethernet1/2/2": {"bandwidth": 1000000000, "autoNegotiate": "unknown", "duplex": "duplexHalf", "lanes": 2},
                    "Ethernet3": {"bandwidth": 100000000000, "autoNegotiate": "success", "duplex": "duplexHalf", "lanes": 8},
                    "Ethernet4": {"bandwidth": 2500000000, "autoNegotiate": "unknown", "duplex": "duplexHalf", "lanes": 8},
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
            "result": AntaTestStatus.FAILURE,
            "messages": [
                "Interface: Ethernet1 - Duplex mode mismatch - Expected: duplexFull Actual: duplexHalf",
                "Interface: Ethernet1/2/2 - Duplex mode mismatch - Expected: duplexFull Actual: duplexHalf",
                "Interface: Ethernet3 - Duplex mode mismatch - Expected: duplexFull Actual: duplexHalf",
                "Interface: Ethernet3 - Duplex mode mismatch - Expected: duplexFull Actual: duplexHalf",
                "Interface: Ethernet4 - Duplex mode mismatch - Expected: duplexFull Actual: duplexHalf",
            ],
        },
    },
    (VerifyInterfacesSpeed, "failure-incorrect-lane"): {
        "eos_data": [
            {
                "interfaces": {
                    "Ethernet1": {"bandwidth": 1000000000, "autoNegotiate": "unknown", "duplex": "duplexFull", "lanes": 4},
                    "Ethernet2": {"bandwidth": 10000000000, "autoNegotiate": "unknown", "duplex": "duplexFull", "lanes": 4},
                    "Ethernet3": {"bandwidth": 100000000000, "autoNegotiate": "success", "duplex": "duplexFull", "lanes": 4},
                    "Ethernet4": {"bandwidth": 2500000000, "autoNegotiate": "unknown", "duplex": "duplexFull", "lanes": 6},
                    "Ethernet4/1/1": {"bandwidth": 2500000000, "autoNegotiate": "unknown", "duplex": "duplexFull", "lanes": 6},
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
            "result": AntaTestStatus.FAILURE,
            "messages": [
                "Interface: Ethernet1 - Data lanes count mismatch - Expected: 2 Actual: 4",
                "Interface: Ethernet3 - Data lanes count mismatch - Expected: 8 Actual: 4",
                "Interface: Ethernet4 - Data lanes count mismatch - Expected: 4 Actual: 6",
                "Interface: Ethernet4/1/1 - Data lanes count mismatch - Expected: 4 Actual: 6",
            ],
        },
    },
    (VerifyInterfacesSpeed, "failure-all-type"): {
        "eos_data": [
            {
                "interfaces": {
                    "Ethernet1": {"bandwidth": 10000000000, "autoNegotiate": "unknown", "duplex": "duplexHalf", "lanes": 4},
                    "Ethernet2/1/2": {"bandwidth": 1000000000, "autoNegotiate": "unknown", "duplex": "duplexHalf", "lanes": 2},
                    "Ethernet3": {"bandwidth": 10000000000, "autoNegotiate": "unknown", "duplex": "duplexHalf", "lanes": 6},
                    "Ethernet4": {"bandwidth": 25000000000, "autoNegotiate": "unknown", "duplex": "duplexHalf", "lanes": 4},
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
            "result": AntaTestStatus.FAILURE,
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
    (VerifyLACPInterfacesStatus, "success"): {
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
        "expected": {"result": AntaTestStatus.SUCCESS},
    },
    (VerifyLACPInterfacesStatus, "success-short-timeout"): {
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
        "expected": {"result": AntaTestStatus.SUCCESS},
    },
    (VerifyLACPInterfacesStatus, "failure-not-bundled"): {
        "eos_data": [
            {"portChannels": {"Port-Channel5": {"interfaces": {"Ethernet5": {"actorPortStatus": "No Aggregate"}}}}, "interface": "Ethernet5", "orphanPorts": {}}
        ],
        "inputs": {"interfaces": [{"name": "Ethernet5", "portchannel": "Po5"}]},
        "expected": {"result": AntaTestStatus.FAILURE, "messages": ["Interface: Ethernet5 Port-Channel: Port-Channel5 - Not bundled - Port Status: No Aggregate"]},
    },
    (VerifyLACPInterfacesStatus, "failure-no-details-found"): {
        "eos_data": [{"portChannels": {"Port-Channel5": {"interfaces": {}}}}],
        "inputs": {"interfaces": [{"name": "Ethernet5", "portchannel": "Po 5"}]},
        "expected": {"result": AntaTestStatus.FAILURE, "messages": ["Interface: Ethernet5 Port-Channel: Port-Channel5 - Not configured"]},
    },
    (VerifyLACPInterfacesStatus, "failure-lacp-params"): {
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
            "result": AntaTestStatus.FAILURE,
            "messages": [
                "Interface: Ethernet5 Port-Channel: Port-Channel5 - Actor port details mismatch - "
                "Activity: False, Aggregation: False, Synchronization: False, Collecting: True, Distributing: True, Timeout: False",
                "Interface: Ethernet5 Port-Channel: Port-Channel5 - Partner port details mismatch - "
                "Activity: False, Aggregation: False, Synchronization: False, Collecting: True, Distributing: True, Timeout: False",
            ],
        },
    },
    (VerifyLACPInterfacesStatus, "failure-short-timeout"): {
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
            "result": AntaTestStatus.FAILURE,
            "messages": [
                "Interface: Ethernet5 Port-Channel: Port-Channel5 - Actor port details mismatch - "
                "Activity: True, Aggregation: True, Synchronization: True, Collecting: True, Distributing: True, Timeout: False",
                "Interface: Ethernet5 Port-Channel: Port-Channel5 - Partner port details mismatch - "
                "Activity: True, Aggregation: True, Synchronization: True, Collecting: True, Distributing: True, Timeout: False",
            ],
        },
    },
}
