# Copyright (c) 2023-2026 Arista Networks, Inc.
# Use of this source code is governed by the Apache License 2.0
# that can be found in the LICENSE file.
"""Tests for anta.tests.routing.generic.py."""

from __future__ import annotations

import sys
from typing import TYPE_CHECKING, Any

import pytest
from pydantic import ValidationError

from anta.input_models.routing.generic import RoutingTableSizeRouteSource, RoutingTableSizeVRF
from anta.models import AntaTest
from anta.result_manager.models import AntaTestStatus
from anta.tests.routing.generic import (
    VerifyIPv4RouteNextHops,
    VerifyIPv4RoutePresencePerPrefix,
    VerifyIPv4RoutePresencePerVRF,
    VerifyIPv4RouteType,
    VerifyRoutingProtocolModel,
    VerifyRoutingStatus,
    VerifyRoutingTableEntry,
    VerifyRoutingTableSize,
)
from tests.units.anta_tests import test

if TYPE_CHECKING:
    from tests.units.anta_tests import AntaUnitTestData

DATA: AntaUnitTestData = {
    (VerifyRoutingProtocolModel, "success"): {
        "eos_data": [{"vrfs": {"default": {}}, "protoModelStatus": {"configuredProtoModel": "multi-agent", "operatingProtoModel": "multi-agent"}}],
        "inputs": {"model": "multi-agent"},
        "expected": {"result": AntaTestStatus.SUCCESS},
    },
    (VerifyRoutingProtocolModel, "failure-wrong-configured-model"): {
        "eos_data": [{"vrfs": {"default": {}}, "protoModelStatus": {"configuredProtoModel": "ribd", "operatingProtoModel": "ribd"}}],
        "inputs": {"model": "multi-agent"},
        "expected": {"result": AntaTestStatus.FAILURE, "messages": ["Routing model is misconfigured - Expected: multi-agent Actual: ribd"]},
    },
    (VerifyRoutingProtocolModel, "failure-mismatch-operating-model"): {
        "eos_data": [{"vrfs": {"default": {}}, "protoModelStatus": {"configuredProtoModel": "multi-agent", "operatingProtoModel": "ribd"}}],
        "inputs": {"model": "multi-agent"},
        "expected": {"result": AntaTestStatus.FAILURE, "messages": ["Routing model is misconfigured - Expected: multi-agent Actual: ribd"]},
    },
    # Scenario 1 — basic: no vrfs provided, defaults to default VRF with total_routes
    (VerifyRoutingTableSize, "success"): {
        "eos_data": [{"vrfs": {"default": {"maskLen": {"8": 2}, "totalRoutes": 123}}}],
        "inputs": {"minimum": 42, "maximum": 666},
        "expected": {
            "result": AntaTestStatus.SUCCESS,
            "atomic_results": [
                {"description": "VRF: default Route Source: total_routes", "result": AntaTestStatus.SUCCESS},
            ],
        },
    },
    (VerifyRoutingTableSize, "failure-above-maximum"): {
        "eos_data": [{"vrfs": {"default": {"maskLen": {"8": 2}, "totalRoutes": 1000}}}],
        "inputs": {"minimum": 42, "maximum": 666},
        "expected": {
            "result": AntaTestStatus.FAILURE,
            "messages": ["VRF: default Route Source: total_routes - Routes above maximum - Expected: <= 666 Actual: 1000"],
            "atomic_results": [
                {
                    "description": "VRF: default Route Source: total_routes",
                    "result": AntaTestStatus.FAILURE,
                    "messages": ["Routes above maximum - Expected: <= 666 Actual: 1000"],
                },
            ],
        },
    },
    (VerifyRoutingTableSize, "failure-below-minimum"): {
        "eos_data": [{"vrfs": {"default": {"maskLen": {"8": 2}, "totalRoutes": 2}}}],
        "inputs": {"minimum": 42, "maximum": 666},
        "expected": {
            "result": AntaTestStatus.FAILURE,
            "messages": ["VRF: default Route Source: total_routes - Routes below minimum - Expected: >= 42 Actual: 2"],
            "atomic_results": [
                {
                    "description": "VRF: default Route Source: total_routes",
                    "result": AntaTestStatus.FAILURE,
                    "messages": ["Routes below minimum - Expected: >= 42 Actual: 2"],
                },
            ],
        },
    },
    (VerifyRoutingTableEntry, "success"): {
        "eos_data": [
            {
                "vrfs": {
                    "default": {
                        "routingDisabled": False,
                        "allRoutesProgrammedHardware": True,
                        "allRoutesProgrammedKernel": True,
                        "defaultRouteState": "notSet",
                        "routes": {
                            "10.1.0.1/32": {
                                "hardwareProgrammed": True,
                                "routeType": "eBGP",
                                "routeLeaked": False,
                                "kernelProgrammed": True,
                                "routeAction": "forward",
                                "directlyConnected": False,
                                "preference": 20,
                                "metric": 0,
                                "vias": [{"nexthopAddr": "10.1.255.4", "interface": "Ethernet1"}],
                            }
                        },
                    }
                }
            },
            {
                "vrfs": {
                    "default": {
                        "routingDisabled": False,
                        "allRoutesProgrammedHardware": True,
                        "allRoutesProgrammedKernel": True,
                        "defaultRouteState": "notSet",
                        "routes": {
                            "10.1.0.2/32": {
                                "hardwareProgrammed": True,
                                "routeType": "eBGP",
                                "routeLeaked": False,
                                "kernelProgrammed": True,
                                "routeAction": "forward",
                                "directlyConnected": False,
                                "preference": 20,
                                "metric": 0,
                                "vias": [{"nexthopAddr": "10.1.255.6", "interface": "Ethernet2"}],
                            }
                        },
                    }
                }
            },
        ],
        "inputs": {"vrf": "default", "routes": ["10.1.0.1", "10.1.0.2"]},
        "expected": {"result": AntaTestStatus.SUCCESS},
    },
    (VerifyRoutingTableEntry, "success-collect-all"): {
        "eos_data": [
            {
                "vrfs": {
                    "default": {
                        "routingDisabled": False,
                        "allRoutesProgrammedHardware": True,
                        "allRoutesProgrammedKernel": True,
                        "defaultRouteState": "notSet",
                        "routes": {
                            "10.1.0.1/32": {
                                "hardwareProgrammed": True,
                                "routeType": "eBGP",
                                "routeLeaked": False,
                                "kernelProgrammed": True,
                                "routeAction": "forward",
                                "directlyConnected": False,
                                "preference": 20,
                                "metric": 0,
                                "vias": [{"nexthopAddr": "10.1.255.4", "interface": "Ethernet1"}],
                            },
                            "10.1.0.2/32": {
                                "hardwareProgrammed": True,
                                "routeType": "eBGP",
                                "routeLeaked": False,
                                "kernelProgrammed": True,
                                "routeAction": "forward",
                                "directlyConnected": False,
                                "preference": 20,
                                "metric": 0,
                                "vias": [{"nexthopAddr": "10.1.255.6", "interface": "Ethernet2"}],
                            },
                        },
                    }
                }
            }
        ],
        "inputs": {"vrf": "default", "routes": ["10.1.0.1", "10.1.0.2"], "collect": "all"},
        "expected": {"result": AntaTestStatus.SUCCESS},
    },
    (VerifyRoutingTableEntry, "failure-missing-route"): {
        "eos_data": [
            {
                "vrfs": {
                    "default": {
                        "routingDisabled": False,
                        "allRoutesProgrammedHardware": True,
                        "allRoutesProgrammedKernel": True,
                        "defaultRouteState": "notSet",
                        "routes": {},
                    }
                }
            },
            {
                "vrfs": {
                    "default": {
                        "routingDisabled": False,
                        "allRoutesProgrammedHardware": True,
                        "allRoutesProgrammedKernel": True,
                        "defaultRouteState": "notSet",
                        "routes": {
                            "10.1.0.2/32": {
                                "hardwareProgrammed": True,
                                "routeType": "eBGP",
                                "routeLeaked": False,
                                "kernelProgrammed": True,
                                "routeAction": "forward",
                                "directlyConnected": False,
                                "preference": 20,
                                "metric": 0,
                                "vias": [{"nexthopAddr": "10.1.255.6", "interface": "Ethernet2"}],
                            }
                        },
                    }
                }
            },
            {
                "vrfs": {
                    "default": {
                        "routingDisabled": False,
                        "allRoutesProgrammedHardware": True,
                        "allRoutesProgrammedKernel": True,
                        "defaultRouteState": "notSet",
                        "routes": {},
                    }
                }
            },
        ],
        "inputs": {"vrf": "default", "routes": ["10.1.0.1", "10.1.0.2", "10.1.0.3"]},
        "expected": {"result": AntaTestStatus.FAILURE, "messages": ["The following route(s) are missing from the routing table of VRF default: 10.1.0.1, 10.1.0.3"]},
    },
    (VerifyRoutingTableEntry, "failure-wrong-route"): {
        "eos_data": [
            {
                "vrfs": {
                    "default": {
                        "routingDisabled": False,
                        "allRoutesProgrammedHardware": True,
                        "allRoutesProgrammedKernel": True,
                        "defaultRouteState": "notSet",
                        "routes": {
                            "10.1.0.1/32": {
                                "hardwareProgrammed": True,
                                "routeType": "eBGP",
                                "routeLeaked": False,
                                "kernelProgrammed": True,
                                "routeAction": "forward",
                                "directlyConnected": False,
                                "preference": 20,
                                "metric": 0,
                                "vias": [{"nexthopAddr": "10.1.255.4", "interface": "Ethernet1"}],
                            }
                        },
                    }
                }
            },
            {
                "vrfs": {
                    "default": {
                        "routingDisabled": False,
                        "allRoutesProgrammedHardware": True,
                        "allRoutesProgrammedKernel": True,
                        "defaultRouteState": "notSet",
                        "routes": {
                            "10.1.0.55/32": {
                                "hardwareProgrammed": True,
                                "routeType": "eBGP",
                                "routeLeaked": False,
                                "kernelProgrammed": True,
                                "routeAction": "forward",
                                "directlyConnected": False,
                                "preference": 20,
                                "metric": 0,
                                "vias": [{"nexthopAddr": "10.1.255.6", "interface": "Ethernet2"}],
                            }
                        },
                    }
                }
            },
        ],
        "inputs": {"vrf": "default", "routes": ["10.1.0.1", "10.1.0.2"]},
        "expected": {"result": AntaTestStatus.FAILURE, "messages": ["The following route(s) are missing from the routing table of VRF default: 10.1.0.2"]},
    },
    (VerifyRoutingTableEntry, "failure-wrong-route-collect-all"): {
        "eos_data": [
            {
                "vrfs": {
                    "default": {
                        "routingDisabled": False,
                        "allRoutesProgrammedHardware": True,
                        "allRoutesProgrammedKernel": True,
                        "defaultRouteState": "notSet",
                        "routes": {
                            "10.1.0.1/32": {
                                "hardwareProgrammed": True,
                                "routeType": "eBGP",
                                "routeLeaked": False,
                                "kernelProgrammed": True,
                                "routeAction": "forward",
                                "directlyConnected": False,
                                "preference": 20,
                                "metric": 0,
                                "vias": [{"nexthopAddr": "10.1.255.4", "interface": "Ethernet1"}],
                            },
                            "10.1.0.55/32": {
                                "hardwareProgrammed": True,
                                "routeType": "eBGP",
                                "routeLeaked": False,
                                "kernelProgrammed": True,
                                "routeAction": "forward",
                                "directlyConnected": False,
                                "preference": 20,
                                "metric": 0,
                                "vias": [{"nexthopAddr": "10.1.255.6", "interface": "Ethernet2"}],
                            },
                        },
                    }
                }
            }
        ],
        "inputs": {"vrf": "default", "routes": ["10.1.0.1", "10.1.0.2"], "collect": "all"},
        "expected": {"result": AntaTestStatus.FAILURE, "messages": ["The following route(s) are missing from the routing table of VRF default: 10.1.0.2"]},
    },
    (VerifyIPv4RouteType, "success-valid-route-type"): {
        "eos_data": [
            {
                "vrfs": {
                    "default": {"routes": {"10.10.0.1/32": {"routeType": "eBGP"}, "10.100.0.12/31": {"routeType": "connected"}}},
                    "MGMT": {"routes": {"10.100.1.5/32": {"routeType": "iBGP"}}},
                }
            }
        ],
        "inputs": {
            "routes_entries": [
                {"vrf": "default", "prefix": "10.10.0.1/32", "route_type": "eBGP"},
                {"vrf": "default", "prefix": "10.100.0.12/31", "route_type": "connected"},
                {"vrf": "MGMT", "prefix": "10.100.1.5/32", "route_type": "iBGP"},
            ]
        },
        "expected": {"result": AntaTestStatus.SUCCESS},
    },
    (VerifyIPv4RouteType, "success-bgpAggregate"): {
        "eos_data": [{"vrfs": {"default": {"routes": {"10.10.0.1/32": {"routeType": "bgpAggregate"}}}}}],
        "inputs": {
            "routes_entries": [
                {"vrf": "default", "prefix": "10.10.0.1/32", "route_type": "BGP Aggregate"},
            ]
        },
        "expected": {"result": AntaTestStatus.SUCCESS},
    },
    (VerifyIPv4RouteType, "failure-route-not-found"): {
        "eos_data": [{"vrfs": {"default": {"routes": {}}}}],
        "inputs": {"routes_entries": [{"vrf": "default", "prefix": "10.10.0.1/32", "route_type": "eBGP"}]},
        "expected": {"result": AntaTestStatus.FAILURE, "messages": ["Prefix: 10.10.0.1/32 VRF: default - Route not found"]},
    },
    (VerifyIPv4RouteType, "failure-invalid-route-type"): {
        "eos_data": [{"vrfs": {"default": {"routes": {"10.10.0.1/32": {"routeType": "eBGP"}}}}}],
        "inputs": {"routes_entries": [{"vrf": "default", "prefix": "10.10.0.1/32", "route_type": "iBGP"}]},
        "expected": {"result": AntaTestStatus.FAILURE, "messages": ["Prefix: 10.10.0.1/32 VRF: default - Incorrect route type - Expected: iBGP Actual: eBGP"]},
    },
    (VerifyIPv4RouteType, "failure-vrf-not-configured"): {
        "eos_data": [{"vrfs": {}}],
        "inputs": {"routes_entries": [{"vrf": "default", "prefix": "10.10.0.1/32", "route_type": "eBGP"}]},
        "expected": {"result": AntaTestStatus.FAILURE, "messages": ["Prefix: 10.10.0.1/32 VRF: default - VRF not configured"]},
    },
    (VerifyIPv4RouteNextHops, "success"): {
        "eos_data": [
            {
                "vrfs": {
                    "default": {
                        "routes": {
                            "10.10.0.1/32": {
                                "vias": [{"nexthopAddr": "10.100.0.8", "interface": "Ethernet1"}, {"nexthopAddr": "10.100.0.10", "interface": "Ethernet2"}]
                            }
                        }
                    },
                    "MGMT": {
                        "routes": {
                            "10.100.0.128/31": {
                                "vias": [
                                    {"nexthopAddr": "10.100.0.8", "interface": "Ethernet1"},
                                    {"nexthopAddr": "10.100.0.10", "interface": "Ethernet2"},
                                    {"nexthopAddr": "10.100.0.101", "interface": "Ethernet4"},
                                ]
                            }
                        }
                    },
                }
            }
        ],
        "inputs": {
            "route_entries": [
                {"prefix": "10.10.0.1/32", "vrf": "default", "nexthops": ["10.100.0.10", "10.100.0.8"]},
                {"prefix": "10.100.0.128/31", "vrf": "MGMT", "nexthops": ["10.100.0.8", "10.100.0.10"]},
            ]
        },
        "expected": {"result": AntaTestStatus.SUCCESS},
    },
    (VerifyIPv4RouteNextHops, "success-strict-true"): {
        "eos_data": [
            {
                "vrfs": {
                    "default": {
                        "routes": {
                            "10.10.0.1/32": {
                                "vias": [{"nexthopAddr": "10.100.0.8", "interface": "Ethernet1"}, {"nexthopAddr": "10.100.0.10", "interface": "Ethernet2"}]
                            }
                        }
                    },
                    "MGMT": {
                        "routes": {
                            "10.100.0.128/31": {
                                "vias": [{"nexthopAddr": "10.100.0.8", "interface": "Ethernet1"}, {"nexthopAddr": "10.100.0.10", "interface": "Ethernet2"}]
                            }
                        }
                    },
                }
            }
        ],
        "inputs": {
            "route_entries": [
                {"prefix": "10.10.0.1/32", "vrf": "default", "strict": True, "nexthops": ["10.100.0.8", "10.100.0.10"]},
                {"prefix": "10.100.0.128/31", "vrf": "MGMT", "strict": True, "nexthops": ["10.100.0.8", "10.100.0.10"]},
            ]
        },
        "expected": {"result": AntaTestStatus.SUCCESS},
    },
    (VerifyIPv4RouteNextHops, "failure-not-configured"): {
        "eos_data": [{"vrfs": {"default": {"routes": {}}, "MGMT": {"routes": {}}}}],
        "inputs": {
            "route_entries": [
                {"prefix": "10.10.0.1/32", "vrf": "default", "strict": True, "nexthops": ["10.100.0.8", "10.100.0.10"]},
                {"prefix": "10.100.0.128/31", "vrf": "MGMT", "strict": True, "nexthops": ["10.100.0.8", "10.100.0.10"]},
            ]
        },
        "expected": {
            "result": AntaTestStatus.FAILURE,
            "messages": ["Prefix: 10.10.0.1/32 VRF: default - prefix not found", "Prefix: 10.100.0.128/31 VRF: MGMT - prefix not found"],
        },
    },
    (VerifyIPv4RouteNextHops, "failure-strict-failed"): {
        "eos_data": [
            {
                "vrfs": {
                    "default": {
                        "routes": {
                            "10.10.0.1/32": {
                                "vias": [{"nexthopAddr": "10.100.0.8", "interface": "Ethernet1"}, {"nexthopAddr": "10.100.0.10", "interface": "Ethernet2"}]
                            }
                        }
                    },
                    "MGMT": {
                        "routes": {
                            "10.100.0.128/31": {
                                "vias": [{"nexthopAddr": "10.100.0.8", "interface": "Ethernet1"}, {"nexthopAddr": "10.100.0.11", "interface": "Ethernet2"}]
                            }
                        }
                    },
                }
            }
        ],
        "inputs": {
            "route_entries": [
                {"prefix": "10.10.0.1/32", "vrf": "default", "strict": True, "nexthops": ["10.100.0.8", "10.100.0.10", "10.100.0.11"]},
                {"prefix": "10.100.0.128/31", "vrf": "MGMT", "strict": True, "nexthops": ["10.100.0.8", "10.100.0.10"]},
            ]
        },
        "expected": {
            "result": AntaTestStatus.FAILURE,
            "messages": [
                "Prefix: 10.10.0.1/32 VRF: default - List of next-hops not matching - "
                "Expected: 10.100.0.10, 10.100.0.11, 10.100.0.8 Actual: 10.100.0.10, 10.100.0.8",
                "Prefix: 10.100.0.128/31 VRF: MGMT - List of next-hops not matching - Expected: 10.100.0.10, 10.100.0.8 Actual: 10.100.0.11, 10.100.0.8",
            ],
        },
    },
    (VerifyIPv4RouteNextHops, "failure"): {
        "eos_data": [
            {
                "vrfs": {
                    "default": {
                        "routes": {
                            "10.10.0.1/32": {
                                "vias": [{"nexthopAddr": "10.100.0.8", "interface": "Ethernet1"}, {"nexthopAddr": "10.100.0.10", "interface": "Ethernet2"}]
                            }
                        }
                    },
                    "MGMT": {
                        "routes": {
                            "10.100.0.128/31": {
                                "vias": [{"nexthopAddr": "10.100.0.8", "interface": "Ethernet1"}, {"nexthopAddr": "10.100.0.10", "interface": "Ethernet2"}]
                            }
                        }
                    },
                }
            }
        ],
        "inputs": {
            "route_entries": [
                {"prefix": "10.10.0.1/32", "vrf": "default", "nexthops": ["10.100.0.8", "10.100.0.10", "10.100.0.11"]},
                {"prefix": "10.100.0.128/31", "vrf": "MGMT", "nexthops": ["10.100.0.8", "10.100.0.10", "10.100.0.11"]},
            ]
        },
        "expected": {
            "result": AntaTestStatus.FAILURE,
            "messages": [
                "Prefix: 10.10.0.1/32 VRF: default Nexthop: 10.100.0.11 - Route not found",
                "Prefix: 10.100.0.128/31 VRF: MGMT Nexthop: 10.100.0.11 - Route not found",
            ],
        },
    },
    (VerifyRoutingStatus, "success-routing-enablement"): {
        "eos_data": [
            {
                "v4RoutingEnabled": True,
                "v6RoutingEnabled": True,
                "vrrpIntfs": 0,
                "v6IntfForwarding": True,
                "multicastRouting": {"ipMulticastEnabled": False, "ip6MulticastEnabled": False},
                "v6EcmpInfo": {"v6EcmpRouteSupport": True},
            }
        ],
        "inputs": {"ipv4_unicast": True, "ipv6_unicast": True, "ipv6_interfaces": True},
        "expected": {"result": AntaTestStatus.SUCCESS},
    },
    (VerifyRoutingStatus, "success-routing-disable-all"): {
        "eos_data": [
            {
                "v4RoutingEnabled": False,
                "v6RoutingEnabled": False,
                "vrrpIntfs": 0,
                "multicastRouting": {"ipMulticastEnabled": False, "ip6MulticastEnabled": False},
                "v6EcmpInfo": {"v6EcmpRouteSupport": False},
            }
        ],
        "expected": {"result": AntaTestStatus.SUCCESS},
    },
    (VerifyRoutingStatus, "failure-ip6multicast-not-found"): {
        "eos_data": [
            {
                "v4RoutingEnabled": False,
                "v6RoutingEnabled": False,
                "vrrpIntfs": 0,
                "v4uRpfState": "disabled",
                "v6uRpfState": "disabled",
                "multicastRouting": {"ipMulticastEnabled": True},
                "v6EcmpInfo": {"v6EcmpRouteSupport": True},
            }
        ],
        "inputs": {"ipv4_multicast": True, "ipv6_multicast": True},
        "expected": {
            "result": AntaTestStatus.FAILURE,
            "messages": [
                "IPv6 multicast routing enabled status mismatch - Expected: True Actual: False",
            ],
        },
    },
    (VerifyRoutingStatus, "failure-ipv4multicast-not-found"): {
        "eos_data": [
            {
                "v4RoutingEnabled": True,
                "v6RoutingEnabled": True,
                "vrrpIntfs": 0,
                "v4uRpfState": "disabled",
                "v6uRpfState": "disabled",
                "multicastRouting": {"ip6MulticastEnabled": True},
                "v6EcmpInfo": {"v6EcmpRouteSupport": True},
            }
        ],
        "inputs": {"ipv4_unicast": True, "ipv6_unicast": True, "ipv4_multicast": True, "ipv6_multicast": True},
        "expected": {
            "result": AntaTestStatus.FAILURE,
            "messages": ["IPv4 multicast routing enabled status mismatch - Expected: True Actual: False"],
        },
    },
    (VerifyRoutingStatus, "failure-ipmulticastrouting-enablement"): {
        "eos_data": [
            {
                "v4RoutingEnabled": False,
                "v6RoutingEnabled": False,
                "vrrpIntfs": 0,
                "multicastRouting": {"ipMulticastEnabled": False, "ip6MulticastEnabled": False},
                "v6EcmpInfo": {"v6EcmpRouteSupport": True},
            }
        ],
        "inputs": {"ipv4_multicast": True, "ipv6_multicast": True},
        "expected": {
            "result": AntaTestStatus.FAILURE,
            "messages": [
                "IPv4 multicast routing enabled status mismatch - Expected: True Actual: False",
                "IPv6 multicast routing enabled status mismatch - Expected: True Actual: False",
            ],
        },
    },
    (VerifyRoutingStatus, "failure-ip-routing-enablement"): {
        "eos_data": [
            {
                "v4RoutingEnabled": False,
                "v6RoutingEnabled": False,
                "vrrpIntfs": 0,
                "multicastRouting": {"ipMulticastEnabled": True, "ip6MulticastEnabled": True},
                "v6EcmpInfo": {"v6EcmpRouteSupport": True},
            }
        ],
        "inputs": {"ipv4_unicast": True, "ipv6_unicast": True},
        "expected": {
            "result": AntaTestStatus.FAILURE,
            "messages": [
                "IPv4 unicast routing enabled status mismatch - Expected: True Actual: False",
                "IPv6 unicast routing enabled status mismatch - Expected: True Actual: False",
                "IPv4 multicast routing enabled status mismatch - Expected: False Actual: True",
                "IPv6 multicast routing enabled status mismatch - Expected: False Actual: True",
            ],
        },
    },
    (VerifyRoutingStatus, "failure-ipv6-interface-routing-enablement"): {
        "eos_data": [
            {
                "v4RoutingEnabled": True,
                "v6RoutingEnabled": True,
                "vrrpIntfs": 0,
                "multicastRouting": {"ipMulticastEnabled": False, "ip6MulticastEnabled": False},
                "v6EcmpInfo": {"v6EcmpRouteSupport": True},
            }
        ],
        "inputs": {"ipv4_unicast": True, "ipv6_unicast": True, "ipv6_interfaces": True},
        "expected": {"result": AntaTestStatus.FAILURE, "messages": ["IPv6 interfaces routing enabled status mismatch - Expected: True Actual: False"]},
    },
    (VerifyIPv4RoutePresencePerPrefix, "success"): {
        "eos_data": [
            {
                "vrfs": {
                    "default": {
                        "routes": {
                            "10.100.0.128/31": {
                                "routeType": "eBGP",
                                "vias": [
                                    {"nexthopAddr": "10.100.0.8", "interface": "Ethernet1"},
                                ],
                            }
                        }
                    }
                }
            },
            {
                "vrfs": {
                    "data": {
                        "routes": {
                            "10.100.0.130/31": {
                                "routeType": "eBGP",
                                "vias": [
                                    {
                                        "nexthopAddr": "",
                                        "vtepAddr": "10.100.2.3",
                                        "vni": 20,
                                    }
                                ],
                            }
                        }
                    }
                }
            },
        ],
        "inputs": {"route_entries": [{"prefix": "10.100.0.128/31"}, {"prefix": "10.100.0.130/31", "vrf": "data"}]},
        "expected": {
            "result": AntaTestStatus.SUCCESS,
            "atomic_results": [
                {
                    "description": "Prefix: 10.100.0.128/31 VRF: default",
                    "result": AntaTestStatus.SUCCESS,
                },
                {
                    "description": "Prefix: 10.100.0.130/31 VRF: data",
                    "result": AntaTestStatus.SUCCESS,
                },
            ],
        },
    },
    (VerifyIPv4RoutePresencePerPrefix, "success-with-custom-description"): {
        "eos_data": [
            {
                "vrfs": {
                    "default": {
                        "routes": {
                            "10.100.0.128/31": {
                                "routeType": "eBGP",
                                "vias": [
                                    {"nexthopAddr": "10.100.0.8", "interface": "Ethernet1"},
                                ],
                            }
                        }
                    }
                }
            },
        ],
        "inputs": {"route_entries": [{"prefix": "10.100.0.128/31", "description": "route to leaf"}]},
        "expected": {
            "result": AntaTestStatus.SUCCESS,
            "atomic_results": [
                {
                    "description": "Prefix: 10.100.0.128/31 (route to leaf) VRF: default",
                    "result": AntaTestStatus.SUCCESS,
                },
            ],
        },
    },
    (VerifyIPv4RoutePresencePerPrefix, "failure"): {
        "eos_data": [{"vrfs": {"default": {"routes": {}}}}, {"vrfs": {"data": {"routes": {}}}}],
        "inputs": {"route_entries": [{"prefix": "10.100.0.128/31"}, {"prefix": "10.100.0.130/31", "vrf": "data"}]},
        "expected": {
            "result": AntaTestStatus.FAILURE,
            "messages": ["Prefix: 10.100.0.128/31 VRF: default - Route not found", "Prefix: 10.100.0.130/31 VRF: data - Route not found"],
            "atomic_results": [
                {"description": "Prefix: 10.100.0.128/31 VRF: default", "result": AntaTestStatus.FAILURE, "messages": ["Route not found"]},
                {"description": "Prefix: 10.100.0.130/31 VRF: data", "result": AntaTestStatus.FAILURE, "messages": ["Route not found"]},
            ],
        },
    },
    (VerifyIPv4RoutePresencePerVRF, "success"): {
        "eos_data": [
            {
                "vrfs": {
                    "default": {
                        "routes": {
                            "10.100.0.128/31": {
                                "routeType": "eBGP",
                                "vias": [
                                    {"nexthopAddr": "10.100.0.8", "interface": "Ethernet1"},
                                ],
                            },
                            "10.100.10.100/31": {
                                "routeType": "eBGP",
                                "vias": [
                                    {"nexthopAddr": "10.100.0.89", "interface": "Ethernet1"},
                                ],
                            },
                        }
                    }
                }
            },
            {
                "vrfs": {
                    "data": {
                        "routes": {
                            "10.100.0.130/31": {
                                "routeType": "eBGP",
                                "vias": [
                                    {
                                        "nexthopAddr": "",
                                        "vtepAddr": "10.100.2.3",
                                        "vni": 20,
                                    }
                                ],
                            },
                            "10.100.10.100/31": {
                                "routeType": "eBGP",
                                "vias": [
                                    {
                                        "nexthopAddr": "",
                                        "vtepAddr": "10.100.12.3",
                                        "vni": 10,
                                    }
                                ],
                            },
                        }
                    }
                }
            },
        ],
        "inputs": {"route_entries": [{"prefix": "10.100.0.128/31"}, {"prefix": "10.100.0.130/31", "vrf": "data"}]},
        "expected": {
            "result": AntaTestStatus.SUCCESS,
            "atomic_results": [
                {
                    "description": "Prefix: 10.100.0.128/31 VRF: default",
                    "result": AntaTestStatus.SUCCESS,
                },
                {
                    "description": "Prefix: 10.100.0.130/31 VRF: data",
                    "result": AntaTestStatus.SUCCESS,
                },
            ],
        },
    },
    (VerifyIPv4RoutePresencePerVRF, "success-with-custom-description"): {
        "eos_data": [
            {
                "vrfs": {
                    "default": {
                        "routes": {
                            "10.100.0.128/31": {
                                "routeType": "eBGP",
                                "vias": [
                                    {"nexthopAddr": "10.100.0.8", "interface": "Ethernet1"},
                                ],
                            },
                            "10.100.10.100/31": {
                                "routeType": "eBGP",
                                "vias": [
                                    {"nexthopAddr": "10.100.0.89", "interface": "Ethernet1"},
                                ],
                            },
                        }
                    }
                }
            },
        ],
        "inputs": {"route_entries": [{"prefix": "10.100.0.128/31", "description": "route to leaf"}]},
        "expected": {
            "result": AntaTestStatus.SUCCESS,
            "atomic_results": [
                {
                    "description": "Prefix: 10.100.0.128/31 (route to leaf) VRF: default",
                    "result": AntaTestStatus.SUCCESS,
                },
            ],
        },
    },
    (VerifyIPv4RoutePresencePerVRF, "failure"): {
        "eos_data": [
            {"vrfs": {"default": {"routes": {}}}},
            {
                "vrfs": {
                    "data": {
                        "routes": {
                            "10.100.10.130/31": {
                                "routeType": "eBGP",
                                "vias": [
                                    {
                                        "nexthopAddr": "",
                                        "vtepAddr": "10.100.2.3",
                                        "vni": 20,
                                    }
                                ],
                            },
                            "10.100.100.130/31": {
                                "routeType": "eBGP",
                                "vias": [
                                    {
                                        "nexthopAddr": "",
                                        "vtepAddr": "10.100.2.3",
                                        "vni": 20,
                                    }
                                ],
                            },
                        }
                    }
                }
            },
        ],
        "inputs": {"route_entries": [{"prefix": "10.100.0.128/31"}, {"prefix": "10.100.0.130/31", "vrf": "data"}]},
        "expected": {
            "result": AntaTestStatus.FAILURE,
            "messages": ["Prefix: 10.100.0.128/31 VRF: default - Route not found", "Prefix: 10.100.0.130/31 VRF: data - Route not found"],
            "atomic_results": [
                {"description": "Prefix: 10.100.0.128/31 VRF: default", "result": AntaTestStatus.FAILURE, "messages": ["Route not found"]},
                {"description": "Prefix: 10.100.0.130/31 VRF: data", "result": AntaTestStatus.FAILURE, "messages": ["Route not found"]},
            ],
        },
    },
    # Scenario 2 — vrfs with default route_sources: implicit `total` check inheriting global bounds
    (VerifyRoutingTableSize, "success-vrfs-inherit"): {
        "eos_data": [
            {
                "vrfs": {
                    "default": {"totalRoutes": 5},
                    "PROD": {"totalRoutes": 50},
                    "DEV": {"totalRoutes": 80},
                }
            }
        ],
        "inputs": {
            "minimum": 10,
            "maximum": 100,
            "vrfs": [
                {"vrf": "PROD"},
                {"vrf": "DEV"},
            ],
        },
        "expected": {
            "result": AntaTestStatus.SUCCESS,
            "atomic_results": [
                {"description": "VRF: PROD Route Source: total_routes", "result": AntaTestStatus.SUCCESS},
                {"description": "VRF: DEV Route Source: total_routes", "result": AntaTestStatus.SUCCESS},
            ],
        },
    },
    (VerifyRoutingTableSize, "failure-vrfs-inherit-out-of-range"): {
        "eos_data": [
            {
                "vrfs": {
                    "PROD": {"totalRoutes": 5},
                    "DEV": {"totalRoutes": 200},
                }
            }
        ],
        "inputs": {
            "minimum": 10,
            "maximum": 100,
            "vrfs": [
                {"vrf": "PROD"},
                {"vrf": "DEV"},
            ],
        },
        "expected": {
            "result": AntaTestStatus.FAILURE,
            "messages": [
                "VRF: PROD Route Source: total_routes - Routes below minimum - Expected: >= 10 Actual: 5",
                "VRF: DEV Route Source: total_routes - Routes above maximum - Expected: <= 100 Actual: 200",
            ],
            "atomic_results": [
                {
                    "description": "VRF: PROD Route Source: total_routes",
                    "result": AntaTestStatus.FAILURE,
                    "messages": ["Routes below minimum - Expected: >= 10 Actual: 5"],
                },
                {
                    "description": "VRF: DEV Route Source: total_routes",
                    "result": AntaTestStatus.FAILURE,
                    "messages": ["Routes above maximum - Expected: <= 100 Actual: 200"],
                },
            ],
        },
    },
    # Scenario 3 — per-VRF override on minimum, maximum inherits global
    (VerifyRoutingTableSize, "success-per-vrf-override-min-only"): {
        "eos_data": [
            {
                "vrfs": {
                    "PROD": {"totalRoutes": 200},
                    "TRANSIT": {"totalRoutes": 1500},
                }
            }
        ],
        "inputs": {
            "minimum": 1,
            "maximum": 5000,
            "vrfs": [
                {"vrf": "PROD"},
                {"vrf": "TRANSIT", "route_sources": [{"source": "total_routes", "minimum": 1000}]},
            ],
        },
        "expected": {
            "result": AntaTestStatus.SUCCESS,
            "atomic_results": [
                {"description": "VRF: PROD Route Source: total_routes", "result": AntaTestStatus.SUCCESS},
                {"description": "VRF: TRANSIT Route Source: total_routes", "result": AntaTestStatus.SUCCESS},
            ],
        },
    },
    (VerifyRoutingTableSize, "failure-per-vrf-override-below-overridden-min"): {
        "eos_data": [
            {
                "vrfs": {
                    "PROD": {"totalRoutes": 200},
                    "TRANSIT": {"totalRoutes": 500},
                }
            }
        ],
        "inputs": {
            "minimum": 1,
            "maximum": 5000,
            "vrfs": [
                {"vrf": "PROD"},
                {"vrf": "TRANSIT", "route_sources": [{"source": "total_routes", "minimum": 1000}]},
            ],
        },
        "expected": {
            "result": AntaTestStatus.FAILURE,
            "messages": ["VRF: TRANSIT Route Source: total_routes - Routes below minimum - Expected: >= 1000 Actual: 500"],
            "atomic_results": [
                {"description": "VRF: PROD Route Source: total_routes", "result": AntaTestStatus.SUCCESS},
                {
                    "description": "VRF: TRANSIT Route Source: total_routes",
                    "result": AntaTestStatus.FAILURE,
                    "messages": ["Routes below minimum - Expected: >= 1000 Actual: 500"],
                },
            ],
        },
    },
    # Scenario 4 — per-protocol source checks within a single VRF
    (VerifyRoutingTableSize, "success-per-protocol-source-checks"): {
        "eos_data": [
            {
                "vrfs": {
                    "BORDER": {
                        "connected": 3,
                        "static": 50,
                        "bgpCounts": {"bgpTotal": 100},
                        "totalRoutes": 153,
                    },
                }
            }
        ],
        "inputs": {
            "minimum": 1,
            "maximum": 100,
            "vrfs": [
                {
                    "vrf": "BORDER",
                    "route_sources": [
                        {"source": "bgp", "minimum": 50, "maximum": 500},
                        {"source": "static"},
                        {"source": "connected", "maximum": 5},
                    ],
                },
            ],
        },
        "expected": {
            "result": AntaTestStatus.SUCCESS,
            "atomic_results": [
                {"description": "VRF: BORDER Route Source: bgp", "result": AntaTestStatus.SUCCESS},
                {"description": "VRF: BORDER Route Source: static", "result": AntaTestStatus.SUCCESS},
                {"description": "VRF: BORDER Route Source: connected", "result": AntaTestStatus.SUCCESS},
            ],
        },
    },
    (VerifyRoutingTableSize, "failure-per-protocol-multiple-failures"): {
        "eos_data": [
            {
                "vrfs": {
                    "BORDER": {
                        "connected": 10,
                        "static": 200,
                        "bgpCounts": {"bgpTotal": 30},
                        "totalRoutes": 240,
                    },
                }
            }
        ],
        "inputs": {
            "minimum": 1,
            "maximum": 100,
            "vrfs": [
                {
                    "vrf": "BORDER",
                    "route_sources": [
                        {"source": "bgp", "minimum": 50, "maximum": 500},
                        {"source": "static"},
                        {"source": "connected", "maximum": 5},
                    ],
                },
            ],
        },
        "expected": {
            "result": AntaTestStatus.FAILURE,
            "messages": [
                "VRF: BORDER Route Source: bgp - Routes below minimum - Expected: >= 50 Actual: 30",
                "VRF: BORDER Route Source: static - Routes above maximum - Expected: <= 100 Actual: 200",
                "VRF: BORDER Route Source: connected - Routes above maximum - Expected: <= 5 Actual: 10",
            ],
            "atomic_results": [
                {
                    "description": "VRF: BORDER Route Source: bgp",
                    "result": AntaTestStatus.FAILURE,
                    "messages": ["Routes below minimum - Expected: >= 50 Actual: 30"],
                },
                {
                    "description": "VRF: BORDER Route Source: static",
                    "result": AntaTestStatus.FAILURE,
                    "messages": ["Routes above maximum - Expected: <= 100 Actual: 200"],
                },
                {
                    "description": "VRF: BORDER Route Source: connected",
                    "result": AntaTestStatus.FAILURE,
                    "messages": ["Routes above maximum - Expected: <= 5 Actual: 10"],
                },
            ],
        },
    },
    # Scenario 5 — comprehensive audit
    (VerifyRoutingTableSize, "success-comprehensive-audit"): {
        "eos_data": [
            {
                "vrfs": {
                    "default": {"totalRoutes": 50},
                    "MGMT": {"static": 5, "totalRoutes": 5},
                    "EVPN_TENANT_A": {"bgpCounts": {"bgpTotal": 500}, "totalRoutes": 500},
                }
            }
        ],
        "inputs": {
            "minimum": 1,
            "maximum": 100,
            "vrfs": [
                {"vrf": "default"},
                {"vrf": "MGMT", "route_sources": [{"source": "static", "maximum": 10}]},
                {"vrf": "EVPN_TENANT_A", "route_sources": [{"source": "bgp", "minimum": 200, "maximum": 1000}]},
            ],
        },
        "expected": {
            "result": AntaTestStatus.SUCCESS,
            "atomic_results": [
                {"description": "VRF: default Route Source: total_routes", "result": AntaTestStatus.SUCCESS},
                {"description": "VRF: MGMT Route Source: static", "result": AntaTestStatus.SUCCESS},
                {"description": "VRF: EVPN_TENANT_A Route Source: bgp", "result": AntaTestStatus.SUCCESS},
            ],
        },
    },
    (VerifyRoutingTableSize, "failure-vrf-not-configured"): {
        "eos_data": [
            {
                "vrfs": {
                    "default": {"totalRoutes": 50},
                }
            }
        ],
        "inputs": {
            "minimum": 1,
            "maximum": 100,
            "vrfs": [
                {"vrf": "default"},
                {"vrf": "MISSING", "route_sources": [{"source": "bgp"}]},
            ],
        },
        "expected": {
            "result": AntaTestStatus.FAILURE,
            "messages": ["VRF: MISSING Route Source: bgp - VRF not configured"],
            "atomic_results": [
                {"description": "VRF: default Route Source: total_routes", "result": AntaTestStatus.SUCCESS},
                {
                    "description": "VRF: MISSING Route Source: bgp",
                    "result": AntaTestStatus.FAILURE,
                    "messages": ["VRF not configured"],
                },
            ],
        },
    },
}


class TestVerifyRoutingTableSizeInputs:
    """Test anta.tests.routing.generic.VerifyRoutingTableSize.Input."""

    @pytest.mark.parametrize(
        ("minimum", "maximum"),
        [
            pytest.param(0, 0, id="zero"),
            pytest.param(1, 2, id="1<2"),
            pytest.param(0, sys.maxsize, id="max"),
        ],
    )
    def test_valid(self, minimum: int, maximum: int) -> None:
        """Test VerifyRoutingTableSize valid inputs."""
        VerifyRoutingTableSize.Input(minimum=minimum, maximum=maximum)  # pyright: ignore[reportCallIssue]

    @pytest.mark.parametrize(
        ("minimum", "maximum"),
        [
            pytest.param(-2, -1, id="negative"),
            pytest.param(2, 1, id="2<1"),
            pytest.param(sys.maxsize, 0, id="max"),
        ],
    )
    def test_invalid(self, minimum: int, maximum: int) -> None:
        """Test VerifyRoutingTableSize invalid inputs."""
        with pytest.raises(ValidationError):
            VerifyRoutingTableSize.Input(minimum=minimum, maximum=maximum)  # pyright: ignore[reportCallIssue]

    def test_valid_default_vrfs(self) -> None:
        """Default `vrfs` with global bounds is valid and defaults to default VRF with total source."""
        inp = VerifyRoutingTableSize.Input(minimum=1, maximum=100)  # pyright: ignore[reportCallIssue]
        assert len(inp.vrfs) == 1
        assert inp.vrfs[0].vrf == "default"
        assert len(inp.vrfs[0].route_sources) == 1
        assert inp.vrfs[0].route_sources[0].source == "total_routes"
        assert inp.vrfs[0].route_sources[0].minimum == 1
        assert inp.vrfs[0].route_sources[0].maximum == 100

    def test_valid_vrfs_inherits(self) -> None:
        """Per-source checks inherit global bounds and default to total_routes when route_sources not provided."""
        inp = VerifyRoutingTableSize.Input(minimum=1, maximum=100, vrfs=[{"vrf": "PROD"}])  # pyright: ignore[reportArgumentType]
        assert inp.vrfs[0].route_sources[0].source == "total_routes"
        assert inp.vrfs[0].route_sources[0].minimum == 1
        assert inp.vrfs[0].route_sources[0].maximum == 100

    def test_valid_vrfs_override_minimum(self) -> None:
        """Per-source minimum override, maximum inherited from global."""
        inp = VerifyRoutingTableSize.Input(minimum=1, maximum=100, vrfs=[{"vrf": "PROD", "route_sources": [{"source": "bgp", "minimum": 50}]}])  # pyright: ignore[reportArgumentType]
        assert inp.vrfs[0].route_sources[0].minimum == 50
        assert inp.vrfs[0].route_sources[0].maximum == 100

    def test_valid_vrfs_override_maximum(self) -> None:
        """Per-source maximum override, minimum inherited from global."""
        inp = VerifyRoutingTableSize.Input(minimum=1, maximum=100, vrfs=[{"vrf": "PROD", "route_sources": [{"source": "bgp", "maximum": 500}]}])  # pyright: ignore[reportArgumentType]
        assert inp.vrfs[0].route_sources[0].minimum == 1
        assert inp.vrfs[0].route_sources[0].maximum == 500

    def test_invalid_route_source_min_gt_max(self) -> None:
        """Per-source bounds must satisfy min <= max."""
        with pytest.raises(ValidationError):
            RoutingTableSizeRouteSource(source="bgp", minimum=100, maximum=10)

    def test_invalid_unknown_source(self) -> None:
        """Per-source must be one of the supported literals."""
        with pytest.raises(ValidationError):
            RoutingTableSizeRouteSource(source="unknown", minimum=1, maximum=10)  # pyright: ignore[reportArgumentType]

    def test_invalid_duplicate_route_sources(self) -> None:
        """Duplicate route sources within the same VRF are rejected."""
        with pytest.raises(ValidationError):
            RoutingTableSizeVRF(
                vrf="PROD",
                route_sources=[
                    RoutingTableSizeRouteSource(source="bgp", minimum=1, maximum=10),
                    RoutingTableSizeRouteSource(source="bgp", minimum=1, maximum=10),
                ],
            )
