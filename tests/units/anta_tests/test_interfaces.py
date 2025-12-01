# Copyright (c) 2023-2025 Arista Networks, Inc.
# Use of this source code is governed by the Apache License 2.0
# that can be found in the LICENSE file.
"""Test inputs for anta.tests.interfaces."""

# pylint: disable=C0302
from __future__ import annotations

import sys
from datetime import datetime, timedelta, timezone
from typing import TYPE_CHECKING, Any

from anta.models import AntaTest
from anta.result_manager.models import AntaTestStatus
from anta.tests.interfaces import (
    VerifyIllegalLACP,
    VerifyInterfaceDiscards,
    VerifyInterfaceErrDisabled,
    VerifyInterfaceErrors,
    VerifyInterfaceIPv4,
    VerifyInterfacesBER,
    VerifyInterfacesCounterDetails,
    VerifyInterfacesECNCounters,
    VerifyInterfacesEgressQueueDrops,
    VerifyInterfacesOpticsReceivePower,
    VerifyInterfacesOpticsTemperature,
    VerifyInterfacesPFCCounters,
    VerifyInterfacesSpeed,
    VerifyInterfacesStatus,
    VerifyInterfacesTridentCounters,
    VerifyInterfacesVoqAndEgressQueueDrops,
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
    from tests.units.anta_tests import AntaUnitTestData


# Helper to create minimal rate data in unit tests
def create_rate_data(*interfaces_with_rates: tuple[str, float, float]) -> dict[str, Any]:
    """Create the 'show interfaces counters rates' data.

    Each arg is a tuple: (name, in_bps_rate, out_bps_rate).
    """
    data: dict[str, Any] = {"interfaces": {}}
    for name, in_rate, out_rate in interfaces_with_rates:
        data["interfaces"][name] = {"inBpsRate": float(in_rate), "outBpsRate": float(out_rate)}
    return data


# Helper to create minimal status data in unit tests
def create_status_data(*interfaces_with_status: tuple[str, str, float]) -> dict[str, Any]:
    """Create the 'show interfaces status' data.

    Each arg is a tuple: (name, duplex, bandwidth_bps)
    """
    data: dict[str, Any] = {"interfaceStatuses": {}}
    for name, duplex, bw in interfaces_with_status:
        data["interfaceStatuses"][name] = {"duplex": duplex, "bandwidth": int(bw)}
    return data


# Mock current time to maintain test VerifyInterfacesCounterDetails stability
now = datetime.now(timezone.utc)
one_day_ago = now - timedelta(days=1)
timestamp_one_day_ago = one_day_ago.timestamp()


DATA: AntaUnitTestData = {
    (VerifyInterfaceUtilization, "success"): {
        "eos_data": [
            create_rate_data(
                ("Ethernet1", 100e6, 50e6),  # 10%, 5% utilization
                ("Ethernet2/1", 20e6, 10e6),  # 2%, 1% utilization
                ("Ethernet3/1/1", 5e6, 5e6),  # 0.5%, 0.5% utilization
                ("Port-Channel1", 150e6, 150e6),  # 7.5%, 7.5% utilization (on 2G BW)
                ("Management0", 1e6, 1e6),  # 0.1%, 0.1% utilization
                ("Ethernet1.100", 0.5e6, 1e6),  # 0.05%, 0.1% utilization (inherits Eth1 BW)
                ("Port-Channel1.200", 1e6, 2e6),  # 0.05%, 0.1% utilization (inherits Po1 BW)
            ),
            create_status_data(
                ("Ethernet1", "duplexFull", 1e9),
                ("Ethernet2/1", "duplexFull", 1e9),
                ("Ethernet3/1/1", "duplexFull", 1e9),
                ("Port-Channel1", "duplexFull", 2e9),  # Example 2x1G LACP
                ("Management0", "duplexFull", 1e9),
                ("Ethernet1.100", "duplexFull", 1e9),  # Sub-interface status
                ("Port-Channel1.200", "duplexFull", 2e9),  # Sub-interface status
            ),
        ],
        "inputs": {"threshold": 15.0},  # All utilizations are <= 15%
        "expected": {"result": AntaTestStatus.SUCCESS},
    },
    (VerifyInterfaceUtilization, "success-ignored-interfaces"): {
        "eos_data": [
            create_rate_data(
                ("Ethernet1", 800e6, 10e6),  # 80% utilization, but will be ignored
                ("Port-Channel1", 1800e6, 50e6),  # 90% utilization, but will be ignored
                ("Management0", 50e6, 750e6),  # 5%, 75% utilization, Management0 ignored by type
                ("Ethernet2", 10e6, 20e6),  # 1%, 2% utilization (this one is checked)
            ),
            create_status_data(
                ("Ethernet1", "duplexFull", 1e9), ("Port-Channel1", "duplexFull", 2e9), ("Management0", "duplexFull", 1e9), ("Ethernet2", "duplexFull", 1e9)
            ),
        ],
        "inputs": {"threshold": 10.0, "ignored_interfaces": ["Ethernet1", "Port-Channel1", "Management"]},
        "expected": {"result": AntaTestStatus.SUCCESS},
    },
    (VerifyInterfaceUtilization, "success-user-provided-interfaces"): {
        "eos_data": [
            create_rate_data(
                ("Ethernet1/1", 800e6, 10e6),  # 80% (Not in user list)
                ("Port-Channel10", 50e6, 70e6),  # 2.5%, 3.5%
                ("Ethernet2.100", 1e6, 0.5e6),  # 0.1%, 0.05%
            ),
            create_status_data(("Ethernet1/1", "duplexFull", 1e9), ("Port-Channel10", "duplexFull", 2e9), ("Ethernet2.100", "duplexFull", 1e9)),
        ],
        "inputs": {"threshold": 5.0, "interfaces": ["Port-Channel10", "Ethernet2.100"]},
        "expected": {"result": AntaTestStatus.SUCCESS},
    },
    (VerifyInterfaceUtilization, "success-not-connected-interfaces"): {
        "eos_data": [
            create_rate_data(
                ("Ethernet1/1", 0.0, 0.0),  # Not connected
                ("Port-Channel10", 50e6, 70e6),  # 2.5%, 3.5%
                ("Ethernet2.100", 1e6, 0.5e6),  # 0.1%, 0.05%
            ),
            create_status_data(("Ethernet1/1", "duplexUnknown", 0.0), ("Port-Channel10", "duplexFull", 2e9), ("Ethernet2.100", "duplexFull", 1e9)),
        ],
        "inputs": {"threshold": 5.0},
        "expected": {"result": AntaTestStatus.SUCCESS},
    },
    (VerifyInterfaceUtilization, "failure-utilization-exceeded"): {
        "eos_data": [
            create_rate_data(
                ("Ethernet1", 100e6, 50e6),  # OK
                ("Port-Channel5", 800e6, 150e6),  # Ingress 800Mbps/2Gbps = 40%. Egress 150Mbps/2Gbps = 7.5%
            ),  # Fails on Ingress
            create_status_data(
                ("Ethernet1", "duplexFull", 1e9),
                ("Port-Channel5", "duplexFull", 2e9),  # Example: 2x1G LACP
            ),
        ],
        "inputs": {"threshold": 30.0},
        "expected": {
            "result": AntaTestStatus.FAILURE,
            "messages": ["Interface: Port-Channel5 BPS Rate: inBpsRate - Usage above threshold - Expected: <= 30.0% Actual: 40.0%"],
        },
    },
    (VerifyInterfaceUtilization, "failure-ethernet-duplex-half"): {
        "eos_data": [
            create_rate_data(("Ethernet1/1", 10e6, 10e6)),
            create_status_data(("Ethernet1/1", "duplexHalf", 1e9)),  # Problematic interface
        ],
        "inputs": {"threshold": 70.0},
        "expected": {
            "result": AntaTestStatus.FAILURE,
            "messages": ["Interface: Ethernet1/1 - Test not implemented for non-full-duplex interfaces - Expected: duplexFull Actual: duplexHalf"],
        },
    },
    (VerifyInterfaceUtilization, "failure-port-channel-subinterface-duplex-half"): {
        "eos_data": [
            create_rate_data(
                ("Port-Channel10", 10e6, 10e6),
                ("Port-Channel10.50", 1e6, 1e6),  # Rates for sub-interface
            ),
            create_status_data(
                ("Port-Channel10", "duplexFull", 2e9),
                ("Port-Channel10.50", "duplexHalf", 2e9),  # Problematic sub-interface
            ),
        ],
        "inputs": {"threshold": 70.0},
        "expected": {
            "result": AntaTestStatus.FAILURE,
            "messages": ["Interface: Port-Channel10.50 - Test not implemented for non-full-duplex interfaces - Expected: duplexFull Actual: duplexHalf"],
        },
    },
    (VerifyInterfaceUtilization, "failure-management0-duplex-half"): {
        "eos_data": [
            create_rate_data(("Management0", 10e6, 10e6)),
            create_status_data(("Management0", "duplexHalf", 1e9)),
        ],
        "inputs": {"threshold": 70.0},
        "expected": {
            "result": AntaTestStatus.FAILURE,
            "messages": ["Interface: Management0 - Test not implemented for non-full-duplex interfaces - Expected: duplexFull Actual: duplexHalf"],
        },
    },
    (VerifyInterfaceUtilization, "failure-specific-interface-not-found"): {
        "eos_data": [
            create_rate_data(("Ethernet1", 10e6, 10e6)),  # Ethernet99 is missing
            create_status_data(("Ethernet1", "duplexFull", 1e9)),
        ],
        "inputs": {"threshold": 70.0, "interfaces": ["Ethernet1", "Ethernet99"]},
        "expected": {
            "result": AntaTestStatus.FAILURE,
            "messages": ["Interface: Ethernet99 - Not found"],
        },
    },
    (VerifyInterfaceUtilization, "failure-specific-interface-null-bandwidth"): {
        "eos_data": [
            create_rate_data(("Ethernet1/1/1", 10e6, 10e6), ("Port-Channel1", 1e6, 1e6)),
            create_status_data(
                ("Ethernet1/1/1", "duplexFull", 1e9),
                ("Port-Channel1", "duplexFull", 0),  # Explicitly tested, BW is 0
            ),
        ],
        "inputs": {"threshold": 70.0, "interfaces": ["Ethernet1/1/1", "Port-Channel1"]},
        "expected": {
            "result": AntaTestStatus.FAILURE,
            "messages": ["Interface: Port-Channel1 - Cannot get interface utilization due to null bandwidth value"],
        },
    },
    (VerifyInterfaceUtilization, "success-null-bandwidth-general-scan-skipped"): {
        # This test ensures that when scanning ALL interfaces, a null bandwidth is skipped, not failed.
        # And other interfaces are still checked.
        "eos_data": [
            create_rate_data(
                ("Ethernet1", 10e6, 10e6),  # OK
                ("Ethernet2/1", 1e6, 1e6),  # Null BW, will be skipped
                ("Port-Channel1", 800e6, 10e6),  # High util, should fail the test
            ),
            create_status_data(
                ("Ethernet1", "duplexFull", 1e9),
                ("Ethernet2/1", "duplexFull", 0),  # Null bandwidth
                ("Port-Channel1", "duplexFull", 1e9),
            ),
        ],
        "inputs": {"threshold": 70.0},  # Po1 inBpsRate (800Mbps/1Gbps = 80%) will cause failure
        "expected": {
            "result": AntaTestStatus.FAILURE,  # Failure due to Port-Channel1, not Ethernet2/1
            "messages": ["Interface: Port-Channel1 BPS Rate: inBpsRate - Usage above threshold - Expected: <= 70.0% Actual: 80.0%"],
        },
    },
    (VerifyInterfaceUtilization, "success-all-interfaces-one-null-bw-others-ok"): {
        # Similar to above, but this time the other interfaces are OK, so the overall result is success
        "eos_data": [
            create_rate_data(
                ("Ethernet1", 10e6, 10e6),  # OK
                ("Ethernet2/1", 1e6, 1e6),  # Null BW, will be skipped
                ("Port-Channel1", 50e6, 10e6),  # OK (5%)
            ),
            create_status_data(
                ("Ethernet1", "duplexFull", 1e9),
                ("Ethernet2/1", "duplexFull", 0),  # Null bandwidth
                ("Port-Channel1", "duplexFull", 1e9),
            ),
        ],
        "inputs": {"threshold": 70.0},
        "expected": {
            "result": AntaTestStatus.SUCCESS,
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
                "interfaceErrorCounters": {
                    "Ethernet1": {"inErrors": 42, "frameTooLongs": 0, "outErrors": 0, "frameTooShorts": 0, "fcsErrors": 0, "alignmentErrors": 0, "symbolErrors": 0},
                    "Management0": {
                        "inErrors": 0,
                        "frameTooLongs": 0,
                        "outErrors": 0,
                        "frameTooShorts": 0,
                        "fcsErrors": 0,
                        "alignmentErrors": 666,
                        "symbolErrors": 0,
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
                "interfaceErrorCounters": {
                    "Ethernet1": {"inErrors": 42, "frameTooLongs": 0, "outErrors": 0, "frameTooShorts": 0, "fcsErrors": 0, "alignmentErrors": 0, "symbolErrors": 0},
                    "Management0": {
                        "inErrors": 0,
                        "frameTooLongs": 0,
                        "outErrors": 0,
                        "frameTooShorts": 0,
                        "fcsErrors": 0,
                        "alignmentErrors": 666,
                        "symbolErrors": 0,
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
                "Interface: Ethernet1 - Non-zero error counter(s) - inErrors: 42",
                "Interface: Ethernet6 - Non-zero error counter(s) - alignmentErrors: 666",
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
                "Interface: Ethernet1 - Non-zero error counter(s) - inErrors: 42, outErrors: 10",
                "Interface: Ethernet6 - Non-zero error counter(s) - alignmentErrors: 6, symbolErrors: 10",
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
    (VerifyInterfaceErrors, "success-specific-interface"): {
        "eos_data": [
            {
                "interfaceErrorCounters": {
                    "Ethernet1": {"inErrors": 0, "frameTooLongs": 0, "outErrors": 0, "frameTooShorts": 0, "fcsErrors": 0, "alignmentErrors": 0, "symbolErrors": 0},
                    "Management0": {
                        "inErrors": 0,
                        "frameTooLongs": 0,
                        "outErrors": 0,
                        "frameTooShorts": 0,
                        "fcsErrors": 0,
                        "alignmentErrors": 666,
                        "symbolErrors": 0,
                    },
                }
            }
        ],
        "inputs": {"interfaces": ["Etherne1"]},
        "expected": {"result": AntaTestStatus.SUCCESS},
    },
    (VerifyInterfaceErrors, "failure-specific-interface-not-found"): {
        "eos_data": [
            {
                "interfaceErrorCounters": {
                    "Ethernet1": {"inErrors": 0, "frameTooLongs": 0, "outErrors": 0, "frameTooShorts": 0, "fcsErrors": 0, "alignmentErrors": 0, "symbolErrors": 0},
                    "Management0": {
                        "inErrors": 0,
                        "frameTooLongs": 0,
                        "outErrors": 0,
                        "frameTooShorts": 0,
                        "fcsErrors": 0,
                        "alignmentErrors": 666,
                        "symbolErrors": 0,
                    },
                }
            }
        ],
        "inputs": {"interfaces": ["Etherne10"]},
        "expected": {"result": AntaTestStatus.FAILURE, "messages": ["Interface: Ethernet10 - Not found"]},
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
    (VerifyInterfaceErrDisabled, "success"): {
        "eos_data": [{"interfaceStatuses": {}}],
        "expected": {
            "result": AntaTestStatus.SUCCESS,
            "atomic_results": [],
        },
    },
    (VerifyInterfaceErrDisabled, "success-ignored-interfaces"): {
        "eos_data": [
            {
                "interfaceStatuses": {
                    "Ethernet1/2": {"description": "", "status": "errdisabled", "causes": ["speed-misconfigured"]},
                    "Ethernet1/3": {"description": "", "status": "errdisabled", "causes": ["speed-misconfigured"]},
                }
            }
        ],
        "inputs": {"interfaces": ["Ethernet1/1"], "ignored_interfaces": ["Ethernet1/2", "Ethernet1/3"]},
        "expected": {
            "result": AntaTestStatus.SUCCESS,
            "atomic_results": [
                {
                    "result": AntaTestStatus.SUCCESS,
                    "description": "Interface: Ethernet1/1",
                }
            ],
        },
    },
    (VerifyInterfaceErrDisabled, "success-only-ignored-interfaces"): {
        "eos_data": [
            {
                "interfaceStatuses": {
                    "Ethernet1/2": {"description": "", "status": "errdisabled", "causes": ["speed-misconfigured"]},
                    "Ethernet1/3": {"description": "", "status": "errdisabled", "causes": ["speed-misconfigured"]},
                }
            }
        ],
        "inputs": {"ignored_interfaces": ["Ethernet1/2", "Ethernet1/3"]},
        "expected": {
            "result": AntaTestStatus.SUCCESS,
            "atomic_results": [],
        },
    },
    (VerifyInterfaceErrDisabled, "failure"): {
        "eos_data": [{"interfaceStatuses": {"Ethernet2": {"description": "", "status": "errdisabled", "causes": ["bpduguard"]}}}],
        "expected": {
            "result": AntaTestStatus.FAILURE,
            "messages": ["Interface: Ethernet2 - Error disabled - Causes: bpduguard"],
            "atomic_results": [{"result": AntaTestStatus.FAILURE, "description": "Interface: Ethernet2", "messages": ["Error disabled - Causes: bpduguard"]}],
        },
    },
    (VerifyInterfaceErrDisabled, "failure-no-cause"): {
        "eos_data": [{"interfaceStatuses": {"Ethernet2": {"description": "", "status": "errdisabled"}}}],
        "expected": {
            "result": AntaTestStatus.FAILURE,
            "messages": ["Interface: Ethernet2 - Error disabled"],
            "atomic_results": [{"result": AntaTestStatus.FAILURE, "description": "Interface: Ethernet2", "messages": ["Error disabled"]}],
        },
    },
    (VerifyInterfaceDiscards, "success-specific-interface"): {
        "eos_data": [
            {
                "inDiscardsTotal": 0,
                "interfaces": {
                    "Ethernet2": {"outDiscards": 0, "inDiscards": 0},
                    "Ethernet1": {"outDiscards": 0, "inDiscards": 42},
                    "Ethernet3": {"outDiscards": 0, "inDiscards": 0},
                    "Port-Channel1": {"outDiscards": 0, "inDiscards": 0},
                    "Port-Channel2": {"outDiscards": 30, "inDiscards": 0},
                },
                "outDiscardsTotal": 0,
            }
        ],
        "inputs": {"interfaces": ["Port-Channel1", "Ethernet3", "Ethernet2"]},
        "expected": {"result": AntaTestStatus.SUCCESS},
    },
    (VerifyInterfaceDiscards, "failure-specific-interface-not-found"): {
        "eos_data": [
            {
                "inDiscardsTotal": 0,
                "interfaces": {
                    "Ethernet2": {"outDiscards": 0, "inDiscards": 0},
                    "Ethernet1": {"outDiscards": 0, "inDiscards": 42},
                    "Ethernet3": {"outDiscards": 40, "inDiscards": 0},
                    "Port-Channel1": {"outDiscards": 30, "inDiscards": 0},
                    "Port-Channel2": {"outDiscards": 30, "inDiscards": 0},
                },
                "outDiscardsTotal": 0,
            }
        ],
        "inputs": {"interfaces": ["Port-Channel10", "Ethernet3", "Ethernet2"]},
        "expected": {
            "result": AntaTestStatus.FAILURE,
            "messages": ["Interface: Port-Channel10 - Not found", "Interface: Ethernet3 - Non-zero discard counter(s): outDiscards: 40"],
        },
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
    (VerifyStormControlDrops, "success-ignore-interfface"): {
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
                    "Ethernet10": {
                        "trafficTypes": {"broadcast": {"level": 100, "thresholdType": "packetsPerSecond", "rate": 440, "drop": 40, "dormant": False}},
                        "active": True,
                        "reason": "",
                        "errdisabled": False,
                    },
                },
            }
        ],
        "inputs": {"ignored_interfaces": ["Ethernet10"]},
        "expected": {"result": AntaTestStatus.SUCCESS},
    },
    (VerifyStormControlDrops, "success-specific-interfface"): {
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
                    "Ethernet10": {
                        "trafficTypes": {"broadcast": {"level": 100, "thresholdType": "packetsPerSecond", "rate": 440, "drop": 40, "dormant": False}},
                        "active": True,
                        "reason": "",
                        "errdisabled": False,
                    },
                },
            }
        ],
        "inputs": {"interfaces": ["Ethernet1"]},
        "expected": {"result": AntaTestStatus.SUCCESS},
    },
    (VerifyStormControlDrops, "failure-specific-interfface-not-found"): {
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
                    "Ethernet10": {
                        "trafficTypes": {"broadcast": {"level": 100, "thresholdType": "packetsPerSecond", "rate": 440, "drop": 40, "dormant": False}},
                        "active": True,
                        "reason": "",
                        "errdisabled": False,
                    },
                    "Ethernet20": {
                        "trafficTypes": {"broadcast": {"level": 100, "thresholdType": "packetsPerSecond", "rate": 440, "drop": 40, "dormant": False}},
                        "active": True,
                        "reason": "",
                        "errdisabled": False,
                    },
                },
            }
        ],
        "inputs": {"interfaces": ["Ethernet13", "Ethernet10", "Ethernet20"]},
        "expected": {
            "result": AntaTestStatus.FAILURE,
            "messages": [
                "Interface: Ethernet13 - Not found",
                "Interface: Ethernet10 - Non-zero storm-control drop counter(s) - broadcast: 40",
                "Interface: Ethernet20 - Non-zero storm-control drop counter(s) - broadcast: 40",
            ],
        },
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
    (VerifyPortChannels, "success-specified-interface"): {
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
        "inputs": {"interfaces": ["Port-Channel1"]},
        "expected": {"result": AntaTestStatus.SUCCESS},
    },
    (VerifyPortChannels, "failure-specified-interface-not-found"): {
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
        "inputs": {"interfaces": ["Port-Channel10", "Port-Channel5"]},
        "expected": {"result": AntaTestStatus.FAILURE, "messages": ["Interface: Port-Channel10 - Not found", "Port-Channel5 - Inactive port(s) - Ethernet8"]},
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
    (VerifyIllegalLACP, "success-specific-interface"): {
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
                    },
                },
                "markerMessages": {"markerMessages": [{"marker": "*"}]},
                "orphanPorts": {},
            }
        ],
        "inputs": {"interfaces": ["Port-Channel42"]},
        "expected": {"result": AntaTestStatus.SUCCESS},
    },
    (VerifyIllegalLACP, "success-specific-interface-not-found"): {
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
                    },
                },
                "markerMessages": {"markerMessages": [{"marker": "*"}]},
                "orphanPorts": {},
            }
        ],
        "inputs": {"interfaces": ["Port-Channel4", "Port-Channel5"]},
        "expected": {
            "result": AntaTestStatus.FAILURE,
            "messages": ["Interface: Port-Channel4 - Not found", "Port-Channel5 Interface: Ethernet4 - Illegal LACP packets found"],
        },
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
                                "details": {"partnerChurnState": "noChurn", "actorChurnState": "noChurn"},
                            }
                        }
                    }
                },
                "orphanPorts": {},
            }
        ],
        "inputs": {"interfaces": [{"name": "Ethernet5", "portchannel": "Port-Channel5"}]},
        "expected": {"result": AntaTestStatus.SUCCESS},
    },
    (VerifyLACPInterfacesStatus, "success-validate-churn-state"): {
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
                                "details": {"partnerChurnState": "noChurn", "actorChurnState": "noChurn"},
                            }
                        }
                    }
                },
                "orphanPorts": {},
            }
        ],
        "inputs": {"interfaces": [{"name": "Ethernet5", "portchannel": "Port-Channel5", "lacp_churn_state": True}]},
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
                                "details": {"partnerChurnState": "noChurn", "actorChurnState": "noChurn"},
                            }
                        }
                    }
                },
                "orphanPorts": {},
            }
        ],
        "inputs": {"interfaces": [{"name": "Ethernet5", "portchannel": "Port-Channel5", "lacp_rate_fast": True}]},
        "expected": {"result": AntaTestStatus.SUCCESS},
    },
    (VerifyLACPInterfacesStatus, "failure-not-bundled"): {
        "eos_data": [
            {
                "portChannels": {
                    "Port-Channel5": {
                        "interfaces": {
                            "Ethernet5": {
                                "actorPortStatus": "negotiation",
                                "partnerPortState": {
                                    "activity": True,
                                    "timeout": False,
                                    "aggregation": True,
                                    "synchronization": False,
                                    "collecting": True,
                                    "distributing": True,
                                    "defaulted": False,
                                    "expired": False,
                                },
                                "actorPortState": {
                                    "activity": True,
                                    "timeout": False,
                                    "aggregation": True,
                                    "synchronization": True,
                                    "collecting": False,
                                    "distributing": False,
                                    "defaulted": False,
                                    "expired": False,
                                },
                                "details": {"partnerChurnState": "churnMonitor", "actorChurnState": "noChurn"},
                            }
                        }
                    }
                },
                "orphanPorts": {},
            }
        ],
        "inputs": {"interfaces": [{"name": "Ethernet5", "portchannel": "Po5"}]},
        "expected": {"result": AntaTestStatus.FAILURE, "messages": ["Interface: Ethernet5 Port-Channel: Port-Channel5 - Not bundled - Port Status: negotiation"]},
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
                                "details": {"partnerChurnState": "noChurn", "actorChurnState": "noChurn"},
                            }
                        }
                    }
                },
                "orphanPorts": {},
            }
        ],
        "inputs": {"interfaces": [{"name": "Ethernet5", "portchannel": "port-channel 5"}]},
        "expected": {
            "result": AntaTestStatus.FAILURE,
            "messages": [
                "Interface: Ethernet5 Port-Channel: Port-Channel5 - Actor port activity state mismatch - Expected: True Actual: False",
                "Interface: Ethernet5 Port-Channel: Port-Channel5 - Actor port aggregation state mismatch - Expected: True Actual: False",
                "Interface: Ethernet5 Port-Channel: Port-Channel5 - Actor port synchronization state mismatch - Expected: True Actual: False",
                "Interface: Ethernet5 Port-Channel: Port-Channel5 - Partner port activity state mismatch - Expected: True Actual: False",
                "Interface: Ethernet5 Port-Channel: Port-Channel5 - Partner port aggregation state mismatch - Expected: True Actual: False",
                "Interface: Ethernet5 Port-Channel: Port-Channel5 - Partner port synchronization state mismatch - Expected: True Actual: False",
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
                                "details": {"partnerChurnState": "noChurn", "actorChurnState": "noChurn"},
                            }
                        }
                    }
                },
                "orphanPorts": {},
            }
        ],
        "inputs": {"interfaces": [{"name": "Ethernet5", "portchannel": "port-channel 5", "lacp_rate_fast": True}]},
        "expected": {
            "result": AntaTestStatus.FAILURE,
            "messages": [
                "Interface: Ethernet5 Port-Channel: Port-Channel5 - Actor port timeout state mismatch - Expected: True Actual: False",
                "Interface: Ethernet5 Port-Channel: Port-Channel5 - Partner port timeout state mismatch - Expected: True Actual: False",
            ],
        },
    },
    (VerifyLACPInterfacesStatus, "failure-validate-churn-state"): {
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
                                    "collecting": False,
                                    "distributing": False,
                                },
                                "details": {"partnerChurnState": "churnDetected", "actorChurnState": "churnDetected"},
                            }
                        }
                    }
                },
                "orphanPorts": {},
            }
        ],
        "inputs": {"interfaces": [{"name": "Ethernet5", "portchannel": "Port-Channel5", "lacp_churn_state": False}]},
        "expected": {
            "result": AntaTestStatus.FAILURE,
            "messages": [
                "Interface: Ethernet5 Port-Channel: Port-Channel5 - Actor port collecting state mismatch - Expected: True Actual: False",
                "Interface: Ethernet5 Port-Channel: Port-Channel5 - Actor port distributing state mismatch - Expected: True Actual: False",
                "Interface: Ethernet5 Port-Channel: Port-Channel5 - Actor port timeout state mismatch - Expected: False Actual: True",
                "Interface: Ethernet5 Port-Channel: Port-Channel5 - Partner port timeout state mismatch - Expected: False Actual: True",
            ],
        },
    },
    (VerifyLACPInterfacesStatus, "failure-validate-actor-churn-state"): {
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
                                    "collecting": False,
                                    "distributing": False,
                                },
                                "details": {"partnerChurnState": "noChurn", "actorChurnState": "churnDetected"},
                            }
                        }
                    }
                },
                "orphanPorts": {},
            }
        ],
        "inputs": {"interfaces": [{"name": "Ethernet5", "portchannel": "Port-Channel5", "lacp_churn_state": True}]},
        "expected": {
            "result": AntaTestStatus.FAILURE,
            "messages": [
                "Interface: Ethernet5 Port-Channel: Port-Channel5 - Actor port collecting state mismatch - Expected: True Actual: False",
                "Interface: Ethernet5 Port-Channel: Port-Channel5 - Actor port distributing state mismatch - Expected: True Actual: False",
                "Interface: Ethernet5 Port-Channel: Port-Channel5 - Churn detected (mismatch system ID)",
            ],
        },
    },
    (VerifyLACPInterfacesStatus, "failure-validate-partner-churn-state"): {
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
                                    "collecting": False,
                                    "distributing": False,
                                },
                                "details": {"partnerChurnState": "churnDetected", "actorChurnState": "noChurn"},
                            }
                        }
                    }
                },
                "orphanPorts": {},
            }
        ],
        "inputs": {"interfaces": [{"name": "Ethernet5", "portchannel": "Port-Channel5", "lacp_churn_state": True}]},
        "expected": {
            "result": AntaTestStatus.FAILURE,
            "messages": [
                "Interface: Ethernet5 Port-Channel: Port-Channel5 - Actor port collecting state mismatch - Expected: True Actual: False",
                "Interface: Ethernet5 Port-Channel: Port-Channel5 - Actor port distributing state mismatch - Expected: True Actual: False",
                "Interface: Ethernet5 Port-Channel: Port-Channel5 - Churn detected (mismatch system ID)",
            ],
        },
    },
    (VerifyInterfacesVoqAndEgressQueueDrops, "success"): {
        "eos_data": [
            {
                "interfaces": {
                    "Ethernet48": {
                        "trafficClasses": {
                            "TC0": {
                                "ingressVoqCounters": {
                                    "countersSum": {
                                        "droppedPackets": 0,
                                    },
                                },
                                "egressQueueCounters": {
                                    "countersSum": {
                                        "droppedPackets": 0,
                                    },
                                },
                            },
                            "TC1": {
                                "ingressVoqCounters": {
                                    "countersSum": {
                                        "droppedPackets": 0,
                                    },
                                },
                                "egressQueueCounters": {
                                    "countersSum": {
                                        "droppedPackets": 0,
                                    },
                                },
                            },
                        }
                    },
                    "Ethernet49": {
                        "trafficClasses": {
                            "TC0": {
                                "ingressVoqCounters": {
                                    "countersSum": {
                                        "droppedPackets": 0,
                                    },
                                },
                                "egressQueueCounters": {
                                    "countersSum": {
                                        "droppedPackets": 0,
                                    },
                                },
                            },
                            "TC1": {
                                "ingressVoqCounters": {
                                    "countersSum": {
                                        "droppedPackets": 0,
                                    },
                                },
                                "egressQueueCounters": {
                                    "countersSum": {
                                        "droppedPackets": 0,
                                    },
                                },
                            },
                        }
                    },
                }
            }
        ],
        "expected": {"result": AntaTestStatus.SUCCESS},
    },
    (VerifyInterfacesVoqAndEgressQueueDrops, "success-range-of-traffic-class"): {
        "eos_data": [
            {
                "interfaces": {
                    "Ethernet48": {
                        "trafficClasses": {
                            "TC0-5": {
                                "ingressVoqCounters": {
                                    "countersSum": {
                                        "droppedPackets": 0,
                                    },
                                },
                                "egressQueueCounters": {
                                    "countersSum": {
                                        "droppedPackets": 0,
                                    },
                                },
                            },
                        }
                    },
                    "Ethernet49": {
                        "trafficClasses": {
                            "TC0-5": {
                                "ingressVoqCounters": {
                                    "countersSum": {
                                        "droppedPackets": 0,
                                    },
                                },
                                "egressQueueCounters": {
                                    "countersSum": {
                                        "droppedPackets": 0,
                                    },
                                },
                            },
                        }
                    },
                }
            }
        ],
        "inputs": {"interfaces": ["Ethernet48", "Ethernet49"], "traffic_classes": ["TC0", "TC1", "TC2", "TC3", "TC4", "TC5"]},
        "expected": {"result": AntaTestStatus.SUCCESS},
    },
    (VerifyInterfacesVoqAndEgressQueueDrops, "success-specific-intf"): {
        "eos_data": [
            {
                "interfaces": {
                    "Ethernet48": {
                        "trafficClasses": {
                            "TC0": {
                                "ingressVoqCounters": {
                                    "countersSum": {
                                        "droppedPackets": 0,
                                    },
                                },
                                "egressQueueCounters": {
                                    "countersSum": {
                                        "droppedPackets": 0,
                                    },
                                },
                            },
                            "TC1": {
                                "ingressVoqCounters": {
                                    "countersSum": {
                                        "droppedPackets": 0,
                                    },
                                },
                                "egressQueueCounters": {
                                    "countersSum": {
                                        "droppedPackets": 0,
                                    },
                                },
                            },
                        }
                    },
                    "Ethernet49": {
                        "trafficClasses": {
                            "TC0": {
                                "ingressVoqCounters": {
                                    "countersSum": {
                                        "droppedPackets": 5,
                                    },
                                },
                                "egressQueueCounters": {
                                    "countersSum": {
                                        "droppedPackets": 5,
                                    },
                                },
                            },
                            "TC1": {
                                "ingressVoqCounters": {
                                    "countersSum": {
                                        "droppedPackets": 5,
                                    },
                                },
                                "egressQueueCounters": {
                                    "countersSum": {
                                        "droppedPackets": 5,
                                    },
                                },
                            },
                        }
                    },
                }
            }
        ],
        "inputs": {"interfaces": ["Ethernet48"]},
        "expected": {"result": AntaTestStatus.SUCCESS},
    },
    (VerifyInterfacesVoqAndEgressQueueDrops, "success-all-intf-specific-traffic-class"): {
        "eos_data": [
            {
                "interfaces": {
                    "Ethernet48": {
                        "trafficClasses": {
                            "TC0": {
                                "ingressVoqCounters": {
                                    "countersSum": {
                                        "droppedPackets": 0,
                                    },
                                },
                                "egressQueueCounters": {
                                    "countersSum": {
                                        "droppedPackets": 0,
                                    },
                                },
                            },
                            "TC1": {
                                "ingressVoqCounters": {
                                    "countersSum": {
                                        "droppedPackets": 4,
                                    },
                                },
                                "egressQueueCounters": {
                                    "countersSum": {
                                        "droppedPackets": 5,
                                    },
                                },
                            },
                        }
                    },
                    "Ethernet49": {
                        "trafficClasses": {
                            "TC0": {
                                "ingressVoqCounters": {
                                    "countersSum": {
                                        "droppedPackets": 0,
                                    },
                                },
                                "egressQueueCounters": {
                                    "countersSum": {
                                        "droppedPackets": 0,
                                    },
                                },
                            },
                            "TC1": {
                                "ingressVoqCounters": {
                                    "countersSum": {
                                        "droppedPackets": 5,
                                    },
                                },
                                "egressQueueCounters": {
                                    "countersSum": {
                                        "droppedPackets": 4,
                                    },
                                },
                            },
                        }
                    },
                }
            }
        ],
        "inputs": {"traffic_classes": ["TC0"]},
        "expected": {"result": AntaTestStatus.SUCCESS},
    },
    (VerifyInterfacesVoqAndEgressQueueDrops, "success-specific-intf-specific-traffic-class"): {
        "eos_data": [
            {
                "interfaces": {
                    "Ethernet48": {
                        "trafficClasses": {
                            "TC0": {
                                "ingressVoqCounters": {
                                    "countersSum": {
                                        "droppedPackets": 0,
                                    },
                                },
                                "egressQueueCounters": {
                                    "countersSum": {
                                        "droppedPackets": 0,
                                    },
                                },
                            },
                            "TC1": {
                                "ingressVoqCounters": {
                                    "countersSum": {
                                        "droppedPackets": 4,
                                    },
                                },
                                "egressQueueCounters": {
                                    "countersSum": {
                                        "droppedPackets": 5,
                                    },
                                },
                            },
                        }
                    },
                    "Ethernet49": {
                        "trafficClasses": {
                            "TC0": {
                                "ingressVoqCounters": {
                                    "countersSum": {
                                        "droppedPackets": 5,
                                    },
                                },
                                "egressQueueCounters": {
                                    "countersSum": {
                                        "droppedPackets": 6,
                                    },
                                },
                            },
                            "TC1": {
                                "ingressVoqCounters": {
                                    "countersSum": {
                                        "droppedPackets": 5,
                                    },
                                },
                                "egressQueueCounters": {
                                    "countersSum": {
                                        "droppedPackets": 4,
                                    },
                                },
                            },
                        }
                    },
                }
            }
        ],
        "inputs": {"interfaces": ["Ethernet48"], "traffic_classes": ["TC0"]},
        "expected": {"result": AntaTestStatus.SUCCESS},
    },
    (VerifyInterfacesVoqAndEgressQueueDrops, "failure"): {
        "eos_data": [
            {
                "interfaces": {
                    "Ethernet48": {
                        "trafficClasses": {
                            "TC0": {
                                "ingressVoqCounters": {
                                    "countersSum": {
                                        "droppedPackets": 3,
                                    },
                                },
                                "egressQueueCounters": {
                                    "countersSum": {
                                        "droppedPackets": 0,
                                    },
                                },
                            },
                            "TC1": {
                                "ingressVoqCounters": {
                                    "countersSum": {
                                        "droppedPackets": 4,
                                    },
                                },
                                "egressQueueCounters": {
                                    "countersSum": {
                                        "droppedPackets": 5,
                                    },
                                },
                            },
                        }
                    },
                    "Ethernet49": {
                        "trafficClasses": {
                            "TC0": {
                                "ingressVoqCounters": {
                                    "countersSum": {
                                        "droppedPackets": 5,
                                    },
                                },
                                "egressQueueCounters": {
                                    "countersSum": {
                                        "droppedPackets": 6,
                                    },
                                },
                            },
                            "TC1": {
                                "ingressVoqCounters": {
                                    "countersSum": {
                                        "droppedPackets": 7,
                                    },
                                },
                                "egressQueueCounters": {
                                    "countersSum": {
                                        "droppedPackets": 7,
                                    },
                                },
                            },
                        }
                    },
                }
            }
        ],
        "expected": {
            "result": AntaTestStatus.FAILURE,
            "messages": [
                "Interface: Ethernet48 Traffic Class: TC0 - Queue drops above threshold - Expected: <= 0 Actual VOQ: 3 Actual Egress: 0",
                "Interface: Ethernet48 Traffic Class: TC1 - Queue drops above threshold - Expected: <= 0 Actual VOQ: 4 Actual Egress: 5",
                "Interface: Ethernet49 Traffic Class: TC0 - Queue drops above threshold - Expected: <= 0 Actual VOQ: 5 Actual Egress: 6",
                "Interface: Ethernet49 Traffic Class: TC1 - Queue drops above threshold - Expected: <= 0 Actual VOQ: 7 Actual Egress: 7",
            ],
        },
    },
    (VerifyInterfacesVoqAndEgressQueueDrops, "failure-intf-not-found"): {
        "eos_data": [{"interfaces": {}}],
        "inputs": {"interfaces": ["Ethernet48"]},
        "expected": {
            "result": AntaTestStatus.FAILURE,
            "messages": [
                "Interface: Ethernet48 - Not found",
            ],
        },
    },
    (VerifyInterfacesVoqAndEgressQueueDrops, "failure-traffic-class-not-found"): {
        "eos_data": [
            {
                "interfaces": {
                    "Ethernet48": {
                        "trafficClasses": {
                            "TC0": {
                                "ingressVoqCounters": {
                                    "countersSum": {
                                        "droppedPackets": 3,
                                    },
                                },
                                "egressQueueCounters": {
                                    "countersSum": {
                                        "droppedPackets": 0,
                                    },
                                },
                            },
                        }
                    }
                }
            }
        ],
        "inputs": {"traffic_classes": ["TC1"]},
        "expected": {
            "result": AntaTestStatus.FAILURE,
            "messages": [
                "Interface: Ethernet48 Traffic Class: TC1 - Not found",
            ],
        },
    },
    (VerifyInterfacesVoqAndEgressQueueDrops, "failure-range-of-traffic-class"): {
        "eos_data": [
            {
                "interfaces": {
                    "Ethernet48": {
                        "trafficClasses": {
                            "TC0-5": {
                                "ingressVoqCounters": {
                                    "countersSum": {
                                        "droppedPackets": 1,
                                    },
                                },
                                "egressQueueCounters": {
                                    "countersSum": {
                                        "droppedPackets": 0,
                                    },
                                },
                            },
                        }
                    },
                    "Ethernet49": {
                        "trafficClasses": {
                            "TC0-5": {
                                "ingressVoqCounters": {
                                    "countersSum": {
                                        "droppedPackets": 1,
                                    },
                                },
                                "egressQueueCounters": {
                                    "countersSum": {
                                        "droppedPackets": 2,
                                    },
                                },
                            },
                        }
                    },
                }
            }
        ],
        "inputs": {"interfaces": ["Ethernet48", "Ethernet49"], "traffic_classes": ["TC0", "TC1", "TC2"]},
        "expected": {
            "result": AntaTestStatus.FAILURE,
            "messages": [
                "Interface: Ethernet48 Traffic Class: TC0 - Queue drops above threshold - Expected: <= 0 Actual VOQ: 1 Actual Egress: 0",
                "Interface: Ethernet48 Traffic Class: TC1 - Queue drops above threshold - Expected: <= 0 Actual VOQ: 1 Actual Egress: 0",
                "Interface: Ethernet48 Traffic Class: TC2 - Queue drops above threshold - Expected: <= 0 Actual VOQ: 1 Actual Egress: 0",
                "Interface: Ethernet49 Traffic Class: TC0 - Queue drops above threshold - Expected: <= 0 Actual VOQ: 1 Actual Egress: 2",
                "Interface: Ethernet49 Traffic Class: TC1 - Queue drops above threshold - Expected: <= 0 Actual VOQ: 1 Actual Egress: 2",
                "Interface: Ethernet49 Traffic Class: TC2 - Queue drops above threshold - Expected: <= 0 Actual VOQ: 1 Actual Egress: 2",
            ],
        },
    },
    (VerifyInterfacesTridentCounters, "success"): {
        "eos_data": [
            {
                "ethernet": {
                    "Ethernet48": {
                        "count": {
                            "drop": {
                                "nonCongestionDiscard": 0,
                                "ipv4L3Discard": 0,
                                "ipv6L3Discard": 0,
                                "rxUrpfDrop": 0,
                                "rxFpDrop": 0,
                                "rxMmuDrop": 0,
                                "rxPipelineDrop": 0,
                                "txMmuDrop": 0,
                                "txPipelineDrop": 0,
                                "rxMCDrop": 0,
                                "rxIngressNFDrop": 0,
                                "rxBufferPoolDiscard": 0,
                                "rxPolicyDiscard": 0,
                                "txL3UCAgedDrop": 0,
                                "txL2MCDrop": 0,
                                "txTTLDrop": 0,
                                "wredDropPktCounter": 0,
                            },
                            "error": {
                                "txMACError": 0,
                                "txL2MTUError": 0,
                                "ipv4L3HeaderError": 0,
                                "ipv6L3HeaderError": 0,
                                "rxVlanDrop": 0,
                                "rxTunnelError": 0,
                                "rxL2MTUError": 0,
                                "txUnknownDrop": 0,
                                "txInvalidVlan": 0,
                                "txSplitHorizonDrop": 0,
                                "txVxltMiss": 0,
                                "txFCSError": 0,
                                "txPCError": 0,
                            },
                            "ok": {},
                        }
                    },
                    "Ethernet3": {
                        "count": {
                            "drop": {
                                "nonCongestionDiscard": 0,
                                "ipv4L3Discard": 0,
                                "ipv6L3Discard": 0,
                                "rxUrpfDrop": 0,
                                "rxFpDrop": 0,
                                "rxMmuDrop": 0,
                                "rxPipelineDrop": 0,
                                "txMmuDrop": 0,
                                "txPipelineDrop": 0,
                                "rxMCDrop": 0,
                                "rxIngressNFDrop": 0,
                                "rxBufferPoolDiscard": 0,
                                "rxPolicyDiscard": 0,
                                "txL3UCAgedDrop": 0,
                                "txL2MCDrop": 0,
                                "txTTLDrop": 0,
                                "wredDropPktCounter": 0,
                            },
                            "error": {
                                "txMACError": 0,
                                "txL2MTUError": 0,
                                "ipv4L3HeaderError": 0,
                                "ipv6L3HeaderError": 0,
                                "rxVlanDrop": 0,
                                "rxTunnelError": 0,
                                "rxL2MTUError": 0,
                                "txUnknownDrop": 0,
                                "txInvalidVlan": 0,
                                "txSplitHorizonDrop": 0,
                                "txVxltMiss": 0,
                                "txFCSError": 0,
                                "txPCError": 0,
                            },
                            "ok": {},
                        }
                    },
                }
            }
        ],
        "inputs": {"ignored_counters": ["nonCongestionDiscard", "rxFpDrop"]},
        "expected": {"result": AntaTestStatus.SUCCESS},
    },
    (VerifyInterfacesTridentCounters, "success-drop-threshold"): {
        "eos_data": [
            {
                "ethernet": {
                    "Ethernet48": {
                        "count": {
                            "drop": {
                                "nonCongestionDiscard": 8,
                                "ipv4L3Discard": 0,
                                "ipv6L3Discard": 0,
                                "rxUrpfDrop": 4,
                                "rxFpDrop": 0,
                                "rxMmuDrop": 0,
                                "rxPipelineDrop": 0,
                                "txMmuDrop": 4,
                                "txPipelineDrop": 0,
                                "rxMCDrop": 0,
                                "rxIngressNFDrop": 0,
                                "rxBufferPoolDiscard": 0,
                                "rxPolicyDiscard": 0,
                                "txL3UCAgedDrop": 0,
                                "txL2MCDrop": 0,
                                "txTTLDrop": 0,
                                "wredDropPktCounter": 0,
                            },
                            "error": {
                                "txMACError": 0,
                                "txL2MTUError": 0,
                                "ipv4L3HeaderError": 0,
                                "ipv6L3HeaderError": 0,
                                "rxVlanDrop": 0,
                                "rxTunnelError": 0,
                                "rxL2MTUError": 0,
                                "txUnknownDrop": 0,
                                "txInvalidVlan": 0,
                                "txSplitHorizonDrop": 0,
                                "txVxltMiss": 0,
                                "txFCSError": 0,
                                "txPCError": 0,
                            },
                            "ok": {},
                        }
                    },
                    "Ethernet3": {
                        "count": {
                            "drop": {
                                "nonCongestionDiscard": 10,
                                "ipv4L3Discard": 0,
                                "ipv6L3Discard": 4,
                                "rxUrpfDrop": 0,
                                "rxFpDrop": 1,
                                "rxMmuDrop": 0,
                                "rxPipelineDrop": 0,
                                "txMmuDrop": 2,
                                "txPipelineDrop": 0,
                                "rxMCDrop": 0,
                                "rxIngressNFDrop": 0,
                                "rxBufferPoolDiscard": 3,
                                "rxPolicyDiscard": 0,
                                "txL3UCAgedDrop": 0,
                                "txL2MCDrop": 0,
                                "txTTLDrop": 0,
                                "wredDropPktCounter": 0,
                            },
                            "error": {
                                "txMACError": 0,
                                "txL2MTUError": 0,
                                "ipv4L3HeaderError": 0,
                                "ipv6L3HeaderError": 0,
                                "rxVlanDrop": 0,
                                "rxTunnelError": 0,
                                "rxL2MTUError": 0,
                                "txUnknownDrop": 5,
                                "txInvalidVlan": 0,
                                "txSplitHorizonDrop": 0,
                                "txVxltMiss": 0,
                                "txFCSError": 0,
                                "txPCError": 0,
                            },
                            "ok": {},
                        }
                    },
                }
            }
        ],
        "inputs": {"packet_drop_threshold": 10},
        "expected": {"result": AntaTestStatus.SUCCESS},
    },
    (VerifyInterfacesTridentCounters, "failure-drop-error-threshold"): {
        "eos_data": [
            {
                "ethernet": {
                    "Ethernet48": {
                        "count": {
                            "drop": {
                                "nonCongestionDiscard": 8,
                                "ipv4L3Discard": 0,
                                "ipv6L3Discard": 0,
                                "rxUrpfDrop": 0,
                                "rxFpDrop": 0,
                                "rxMmuDrop": 0,
                                "rxPipelineDrop": 0,
                                "txMmuDrop": 4,
                                "txPipelineDrop": 0,
                                "rxMCDrop": 0,
                                "rxIngressNFDrop": 0,
                                "rxBufferPoolDiscard": 0,
                                "rxPolicyDiscard": 0,
                                "txL3UCAgedDrop": 0,
                                "txL2MCDrop": 0,
                                "txTTLDrop": 0,
                                "wredDropPktCounter": 0,
                            },
                            "error": {
                                "txMACError": 0,
                                "txL2MTUError": 0,
                                "ipv4L3HeaderError": 20,
                                "ipv6L3HeaderError": 0,
                                "rxVlanDrop": 0,
                                "rxTunnelError": 0,
                                "rxL2MTUError": 0,
                                "txUnknownDrop": 0,
                                "txInvalidVlan": 0,
                                "txSplitHorizonDrop": 0,
                                "txVxltMiss": 0,
                                "txFCSError": 0,
                                "txPCError": 0,
                            },
                            "ok": {},
                        }
                    },
                    "Ethernet3": {
                        "count": {
                            "drop": {
                                "nonCongestionDiscard": 10,
                                "ipv4L3Discard": 0,
                                "ipv6L3Discard": 0,
                                "rxUrpfDrop": 0,
                                "rxFpDrop": 0,
                                "rxMmuDrop": 0,
                                "rxPipelineDrop": 0,
                                "txMmuDrop": 2,
                                "txPipelineDrop": 0,
                                "rxMCDrop": 0,
                                "rxIngressNFDrop": 0,
                                "rxBufferPoolDiscard": 0,
                                "rxPolicyDiscard": 0,
                                "txL3UCAgedDrop": 0,
                                "txL2MCDrop": 0,
                                "txTTLDrop": 0,
                                "wredDropPktCounter": 0,
                            },
                            "error": {
                                "txMACError": 0,
                                "txL2MTUError": 10,
                                "ipv4L3HeaderError": 0,
                                "ipv6L3HeaderError": 0,
                                "rxVlanDrop": 14,
                                "rxTunnelError": 0,
                                "rxL2MTUError": 0,
                                "txUnknownDrop": 0,
                                "txInvalidVlan": 0,
                                "txSplitHorizonDrop": 0,
                                "txVxltMiss": 0,
                                "txFCSError": 0,
                                "txPCError": 0,
                            },
                            "ok": {},
                        }
                    },
                }
            }
        ],
        "inputs": {"ignored_counters": ["nonCongestionDiscard", "rxFpDrop", "rxVlanDrop", "txMmuDrop"]},
        "expected": {
            "result": AntaTestStatus.FAILURE,
            "messages": [
                "Interface: Ethernet48 - Error counter ipv4L3HeaderError above threshold - Expected: <= 0 Actual: 20",
                "Interface: Ethernet3 - Error counter txL2MTUError above threshold - Expected: <= 0 Actual: 10",
            ],
        },
    },
    (VerifyInterfacesCounterDetails, "success"): {
        "eos_data": [
            {
                "interfaces": {
                    "Ethernet2": {
                        "name": "Ethernet2",
                        "forwardingModel": "bridged",
                        "lineProtocolStatus": "up",
                        "interfaceStatus": "connected",
                        "description": "",
                        "lastStatusChangeTimestamp": timestamp_one_day_ago,
                        "interfaceCounters": {
                            "inDiscards": 0,
                            "outDiscards": 0,
                            "outTotalPkts": 0,
                            "linkStatusChanges": 2,
                            "totalInErrors": 0,
                            "inputErrorsDetail": {"runtFrames": 0, "giantFrames": 0, "fcsErrors": 0, "alignmentErrors": 0, "symbolErrors": 0, "rxPause": 0},
                            "totalOutErrors": 0,
                            "outputErrorsDetail": {"collisions": 0, "lateCollisions": 0, "deferredTransmissions": 0, "txPause": 0},
                        },
                    },
                    "Ethernet4": {
                        "name": "Ethernet4",
                        "forwardingModel": "bridged",
                        "lineProtocolStatus": "up",
                        "interfaceStatus": "connected",
                        "description": "",
                        "lastStatusChangeTimestamp": timestamp_one_day_ago,
                        "interfaceCounters": {
                            "inDiscards": 0,
                            "outDiscards": 0,
                            "linkStatusChanges": 2,
                            "totalInErrors": 0,
                            "inputErrorsDetail": {"runtFrames": 0, "giantFrames": 0, "fcsErrors": 0, "alignmentErrors": 0, "symbolErrors": 0, "rxPause": 0},
                            "totalOutErrors": 0,
                            "outputErrorsDetail": {"collisions": 0, "lateCollisions": 0, "deferredTransmissions": 0, "txPause": 0},
                        },
                    },
                    "Ethernet1": {
                        "name": "Ethernet1",
                        "forwardingModel": "bridged",
                        "lineProtocolStatus": "up",
                        "interfaceStatus": "connected",
                        "lastStatusChangeTimestamp": timestamp_one_day_ago,
                        "interfaceCounters": {
                            "inDiscards": 0,
                            "outDiscards": 0,
                            "linkStatusChanges": 2,
                            "totalInErrors": 0,
                            "inputErrorsDetail": {"runtFrames": 0, "giantFrames": 0, "fcsErrors": 0, "alignmentErrors": 0, "symbolErrors": 0, "rxPause": 0},
                            "totalOutErrors": 0,
                            "outputErrorsDetail": {"collisions": 0, "lateCollisions": 0, "deferredTransmissions": 0, "txPause": 0},
                        },
                    },
                    "Ethernet3": {
                        "name": "Ethernet3",
                        "forwardingModel": "bridged",
                        "lineProtocolStatus": "up",
                        "interfaceStatus": "connected",
                        "description": "",
                        "lastStatusChangeTimestamp": timestamp_one_day_ago,
                        "interfaceCounters": {
                            "inDiscards": 0,
                            "outDiscards": 0,
                            "outTotalPkts": 0,
                            "linkStatusChanges": 2,
                            "totalInErrors": 0,
                            "inputErrorsDetail": {"runtFrames": 0, "giantFrames": 0, "fcsErrors": 0, "alignmentErrors": 0, "symbolErrors": 0, "rxPause": 0},
                            "totalOutErrors": 0,
                            "outputErrorsDetail": {"collisions": 0, "lateCollisions": 0, "deferredTransmissions": 0, "txPause": 0},
                        },
                    },
                }
            },
        ],
        "inputs": {
            "interfaces": ["Ethernet1", "Ethernet2", "Ethernet4"],
            "ignored_interfaces": ["Ethernet3"],
            "counters_threshold": 0,
            "link_status_changes_threshold": 100,
        },
        "expected": {
            "result": AntaTestStatus.SUCCESS,
        },
    },
    (VerifyInterfacesCounterDetails, "failure-multiple-issues"): {
        "eos_data": [
            {
                "interfaces": {
                    "Ethernet2": {
                        "name": "Ethernet2",
                        "lineProtocolStatus": "up",
                        "interfaceStatus": "connected",
                        "description": "",
                        "lastStatusChangeTimestamp": timestamp_one_day_ago,
                        "interfaceCounters": {
                            "inDiscards": 10,
                            "outDiscards": 0,
                            "linkStatusChanges": 12,
                            "totalInErrors": 0,
                            "inputErrorsDetail": {"runtFrames": 0, "giantFrames": 0, "fcsErrors": 0, "alignmentErrors": 0, "symbolErrors": 0, "rxPause": 0},
                            "totalOutErrors": 0,
                            "outputErrorsDetail": {"collisions": 0, "lateCollisions": 0, "deferredTransmissions": 0, "txPause": 0},
                        },
                    },
                    "Management0": {
                        "name": "Management0",
                        "lineProtocolStatus": "up",
                        "interfaceStatus": "connected",
                        "description": "OOB_MANAGEMENT",
                        "interfaceCounters": {
                            "inDiscards": 20,
                            "outDiscards": 0,
                            "linkStatusChanges": 1,
                            "totalInErrors": 0,
                            "inputErrorsDetail": {"runtFrames": 0, "giantFrames": 0, "fcsErrors": 0, "alignmentErrors": 0, "symbolErrors": 0, "rxPause": 0},
                            "totalOutErrors": 10,
                            "outputErrorsDetail": {"collisions": 0, "lateCollisions": 0, "deferredTransmissions": 0, "txPause": 10},
                        },
                    },
                    "Ethernet10": {
                        "name": "Ethernet10",
                        "lineProtocolStatus": "up",
                        "interfaceStatus": "connected",
                        "hardware": "ethernet",
                        "description": "",
                        "lastStatusChangeTimestamp": timestamp_one_day_ago,
                        "interfaceCounters": {
                            "inDiscards": 0,
                            "outDiscards": 10,
                            "linkStatusChanges": 12,
                            "totalInErrors": 10,
                            "inputErrorsDetail": {"runtFrames": 10, "giantFrames": 0, "fcsErrors": 0, "alignmentErrors": 0, "symbolErrors": 0, "rxPause": 0},
                            "totalOutErrors": 0,
                            "outputErrorsDetail": {"collisions": 0, "lateCollisions": 20, "deferredTransmissions": 0, "txPause": 0},
                        },
                    },
                }
            }
        ],
        "inputs": {"interfaces": ["Management0", "Ethernet10"], "link_status_changes_threshold": 2},
        "expected": {
            "result": AntaTestStatus.FAILURE,
            "messages": [
                "Interface: Management0 Description: OOB_MANAGEMENT - Input discards above threshold - Expected: <= 0 Actual: 20",
                "Interface: Management0 Description: OOB_MANAGEMENT - Output errors above threshold - Expected: <= 0 Actual: 10",
                "Interface: Ethernet10 Uptime: 1 day - Link status changes above threshold - Expected: <= 2 Actual: 12",
                "Interface: Ethernet10 Uptime: 1 day - Output discards above threshold - Expected: <= 0 Actual: 10",
                "Interface: Ethernet10 Uptime: 1 day - Input errors above threshold - Expected: <= 0 Actual: 10",
                "Interface: Ethernet10 Uptime: 1 day - Runt frames above threshold - Expected: <= 0 Actual: 10",
                "Interface: Ethernet10 Uptime: 1 day - Late collisions above threshold - Expected: <= 0 Actual: 20",
            ],
        },
    },
    (VerifyInterfacesCounterDetails, "failure-input-error"): {
        "eos_data": [
            {
                "interfaces": {
                    "Management1": {
                        "name": "Management1",
                        "forwardingModel": "bridged",
                        "lineProtocolStatus": "up",
                        "interfaceStatus": "connected",
                        "description": "",
                        "lastStatusChangeTimestamp": timestamp_one_day_ago,
                        "interfaceCounters": {
                            "inDiscards": 0,
                            "outDiscards": 0,
                            "outTotalPkts": 0,
                            "linkStatusChanges": 2,
                            "totalInErrors": 0,
                            "inputErrorsDetail": {"runtFrames": 30, "giantFrames": 0, "fcsErrors": 10, "alignmentErrors": 55, "symbolErrors": 20, "rxPause": 30},
                            "totalOutErrors": 0,
                            "outputErrorsDetail": {"collisions": 10, "lateCollisions": 10, "deferredTransmissions": 0, "txPause": 0},
                        },
                    },
                    "Ethernet4": {
                        "name": "Ethernet4",
                        "forwardingModel": "bridged",
                        "lineProtocolStatus": "up",
                        "interfaceStatus": "connected",
                        "description": "",
                        "lastStatusChangeTimestamp": timestamp_one_day_ago,
                        "interfaceCounters": {
                            "inDiscards": 0,
                            "outDiscards": 0,
                            "linkStatusChanges": 2,
                            "totalInErrors": 0,
                            "inputErrorsDetail": {"runtFrames": 0, "giantFrames": 30, "fcsErrors": 0, "alignmentErrors": 0, "symbolErrors": 0, "rxPause": 0},
                            "totalOutErrors": 0,
                            "outputErrorsDetail": {"collisions": 0, "lateCollisions": 30, "deferredTransmissions": 0, "txPause": 30},
                        },
                    },
                    "Loopback0": {
                        "name": "Loopback0",
                        "forwardingModel": "bridged",
                        "lineProtocolStatus": "up",
                        "interfaceStatus": "connected",
                        "description": "",
                        "lastStatusChangeTimestamp": timestamp_one_day_ago,
                        "interfaceCounters": {
                            "inDiscards": 0,
                            "outDiscards": 0,
                            "linkStatusChanges": 2,
                            "totalInErrors": 0,
                            "inputErrorsDetail": {"runtFrames": 0, "giantFrames": 30, "fcsErrors": 0, "alignmentErrors": 0, "symbolErrors": 0, "rxPause": 0},
                            "totalOutErrors": 0,
                            "outputErrorsDetail": {"collisions": 0, "lateCollisions": 30, "deferredTransmissions": 0, "txPause": 30},
                        },
                    },
                }
            },
        ],
        "inputs": {"ignored_interfaces": ["Ethernet4"], "counters_threshold": 10, "link_status_changes_threshold": 10},
        "expected": {
            "result": AntaTestStatus.FAILURE,
            "messages": [
                "Interface: Management1 Uptime: 1 day - Runt frames above threshold - Expected: <= 10 Actual: 30",
                "Interface: Management1 Uptime: 1 day - Alignment errors above threshold - Expected: <= 10 Actual: 55",
                "Interface: Management1 Uptime: 1 day - Symbol errors above threshold - Expected: <= 10 Actual: 20",
            ],
        },
    },
    (VerifyInterfacesCounterDetails, "failure-output-error"): {
        "eos_data": [
            {
                "interfaces": {
                    "Management1": {
                        "name": "Management1",
                        "forwardingModel": "bridged",
                        "lineProtocolStatus": "up",
                        "interfaceStatus": "connected",
                        "description": "",
                        "lastStatusChangeTimestamp": timestamp_one_day_ago,
                        "interfaceCounters": {
                            "inDiscards": 0,
                            "outDiscards": 0,
                            "outTotalPkts": 0,
                            "linkStatusChanges": 2,
                            "totalInErrors": 0,
                            "inputErrorsDetail": {"runtFrames": 10, "giantFrames": 0, "fcsErrors": 0, "alignmentErrors": 10, "symbolErrors": 20, "rxPause": 30},
                            "totalOutErrors": 0,
                            "outputErrorsDetail": {"collisions": 0, "lateCollisions": 0, "deferredTransmissions": 0, "txPause": 0},
                        },
                    },
                    "Ethernet4": {
                        "name": "Ethernet4",
                        "forwardingModel": "bridged",
                        "lineProtocolStatus": "up",
                        "interfaceStatus": "connected",
                        "description": "",
                        "lastStatusChangeTimestamp": timestamp_one_day_ago,
                        "interfaceCounters": {
                            "inDiscards": 0,
                            "outDiscards": 0,
                            "linkStatusChanges": 2,
                            "totalInErrors": 0,
                            "inputErrorsDetail": {"runtFrames": 0, "giantFrames": 0, "fcsErrors": 0, "alignmentErrors": 0, "symbolErrors": 0, "rxPause": 0},
                            "totalOutErrors": 0,
                            "outputErrorsDetail": {"collisions": 20, "lateCollisions": 30, "deferredTransmissions": 0, "txPause": 30},
                        },
                    },
                }
            },
        ],
        "inputs": {"counters_threshold": 0, "link_status_changes_threshold": 20},
        "expected": {
            "result": AntaTestStatus.FAILURE,
            "messages": [
                "Interface: Management1 Uptime: 1 day - Runt frames above threshold - Expected: <= 0 Actual: 10",
                "Interface: Management1 Uptime: 1 day - Alignment errors above threshold - Expected: <= 0 Actual: 10",
                "Interface: Management1 Uptime: 1 day - Symbol errors above threshold - Expected: <= 0 Actual: 20",
                "Interface: Ethernet4 Uptime: 1 day - Collisions above threshold - Expected: <= 0 Actual: 20",
                "Interface: Ethernet4 Uptime: 1 day - Late collisions above threshold - Expected: <= 0 Actual: 30",
            ],
        },
    },
    (VerifyInterfacesCounterDetails, "failure-total-int-out-error"): {
        "eos_data": [
            {
                "interfaces": {
                    "Management1": {
                        "name": "Management1",
                        "forwardingModel": "bridged",
                        "lineProtocolStatus": "up",
                        "interfaceStatus": "connected",
                        "description": "",
                        "lastStatusChangeTimestamp": timestamp_one_day_ago,
                        "interfaceCounters": {
                            "inDiscards": 0,
                            "outDiscards": 0,
                            "outTotalPkts": 0,
                            "linkStatusChanges": 2,
                            "totalInErrors": 10,
                            "inputErrorsDetail": {"runtFrames": 0, "giantFrames": 0, "fcsErrors": 0, "alignmentErrors": 0, "symbolErrors": 0, "rxPause": 30},
                            "totalOutErrors": 0,
                            "outputErrorsDetail": {"collisions": 0, "lateCollisions": 0, "deferredTransmissions": 0, "txPause": 30},
                        },
                    },
                    "Ethernet4": {
                        "name": "Ethernet4",
                        "forwardingModel": "bridged",
                        "lineProtocolStatus": "up",
                        "interfaceStatus": "connected",
                        "description": "",
                        "lastStatusChangeTimestamp": timestamp_one_day_ago,
                        "interfaceCounters": {
                            "inDiscards": 0,
                            "outDiscards": 0,
                            "linkStatusChanges": 2,
                            "totalInErrors": 0,
                            "inputErrorsDetail": {"runtFrames": 0, "giantFrames": 0, "fcsErrors": 0, "alignmentErrors": 0, "symbolErrors": 0, "rxPause": 20},
                            "totalOutErrors": 30,
                            "outputErrorsDetail": {"collisions": 0, "lateCollisions": 0, "deferredTransmissions": 0, "txPause": 30},
                        },
                    },
                }
            },
        ],
        "inputs": {"counters_threshold": 0, "link_status_changes_threshold": 20},
        "expected": {
            "result": AntaTestStatus.FAILURE,
            "messages": [
                "Interface: Management1 Uptime: 1 day - Input errors above threshold - Expected: <= 0 Actual: 10",
                "Interface: Ethernet4 Uptime: 1 day - Output errors above threshold - Expected: <= 0 Actual: 30",
            ],
        },
    },
    (VerifyInterfacesCounterDetails, "failure-int-out-packet-discard"): {
        "eos_data": [
            {
                "interfaces": {
                    "Management1": {
                        "name": "Management1",
                        "forwardingModel": "bridged",
                        "lineProtocolStatus": "up",
                        "interfaceStatus": "connected",
                        "description": "",
                        "lastStatusChangeTimestamp": timestamp_one_day_ago,
                        "interfaceCounters": {
                            "inDiscards": 0,
                            "outDiscards": 30,
                            "outTotalPkts": 0,
                            "linkStatusChanges": 2,
                            "totalInErrors": 10,
                            "inputErrorsDetail": {"runtFrames": 0, "giantFrames": 10, "fcsErrors": 0, "alignmentErrors": 0, "symbolErrors": 0, "rxPause": 30},
                            "totalOutErrors": 0,
                            "outputErrorsDetail": {"collisions": 0, "lateCollisions": 0, "deferredTransmissions": 0, "txPause": 30},
                        },
                    },
                    "Ethernet4": {
                        "name": "Ethernet4",
                        "forwardingModel": "bridged",
                        "lineProtocolStatus": "up",
                        "interfaceStatus": "connected",
                        "description": "",
                        "lastStatusChangeTimestamp": timestamp_one_day_ago,
                        "interfaceCounters": {
                            "inDiscards": 30,
                            "outDiscards": 10,
                            "linkStatusChanges": 2,
                            "totalInErrors": 0,
                            "inputErrorsDetail": {"runtFrames": 0, "giantFrames": 0, "fcsErrors": 0, "alignmentErrors": 10, "symbolErrors": 0, "rxPause": 20},
                            "totalOutErrors": 10,
                            "outputErrorsDetail": {"collisions": 0, "lateCollisions": 10, "deferredTransmissions": 0, "txPause": 30},
                        },
                    },
                }
            },
        ],
        "inputs": {"counters_threshold": 10, "link_status_changes_threshold": 20},
        "expected": {
            "result": AntaTestStatus.FAILURE,
            "messages": [
                "Interface: Management1 Uptime: 1 day - Output discards above threshold - Expected: <= 10 Actual: 30",
                "Interface: Ethernet4 Uptime: 1 day - Input discards above threshold - Expected: <= 10 Actual: 30",
            ],
        },
    },
    (VerifyInterfacesCounterDetails, "failure-link-status-changes"): {
        "eos_data": [
            {
                "interfaces": {
                    "Management1/1": {
                        "name": "Management1/1",
                        "forwardingModel": "bridged",
                        "lineProtocolStatus": "up",
                        "interfaceStatus": "connected",
                        "description": "",
                        "lastStatusChangeTimestamp": timestamp_one_day_ago,
                        "interfaceCounters": {
                            "inDiscards": 0,
                            "outDiscards": 30,
                            "outTotalPkts": 0,
                            "linkStatusChanges": 45,
                            "totalInErrors": 10,
                            "inputErrorsDetail": {"runtFrames": 0, "giantFrames": 10, "fcsErrors": 0, "alignmentErrors": 0, "symbolErrors": 0, "rxPause": 30},
                            "totalOutErrors": 0,
                            "outputErrorsDetail": {"collisions": 0, "lateCollisions": 0, "deferredTransmissions": 0, "txPause": 30},
                        },
                    },
                    "Ethernet4/1": {
                        "name": "Ethernet4/1",
                        "forwardingModel": "bridged",
                        "lineProtocolStatus": "down",
                        "interfaceStatus": "notconnected",
                        "description": "",
                        "lastStatusChangeTimestamp": timestamp_one_day_ago,
                        "interfaceCounters": {
                            "inDiscards": 30,
                            "outDiscards": 10,
                            "linkStatusChanges": 40,
                            "totalInErrors": 0,
                            "inputErrorsDetail": {"runtFrames": 0, "giantFrames": 0, "fcsErrors": 0, "alignmentErrors": 10, "symbolErrors": 0, "rxPause": 20},
                            "totalOutErrors": 10,
                            "outputErrorsDetail": {"collisions": 0, "lateCollisions": 10, "deferredTransmissions": 0, "txPause": 30},
                        },
                    },
                    "Management0": {
                        "name": "Management0",
                        "forwardingModel": "bridged",
                        "lineProtocolStatus": "down",
                        "interfaceStatus": "notconnected",
                        "description": "",
                        "lastStatusChangeTimestamp": timestamp_one_day_ago,
                    },
                }
            },
        ],
        "inputs": {"ignored_interfaces": ["Management1/1"], "counters_threshold": 40, "link_status_changes_threshold": 20},
        "expected": {
            "result": AntaTestStatus.FAILURE,
            "messages": ["Interface: Ethernet4/1 Downtime: 1 day - Link status changes above threshold - Expected: <= 20 Actual: 40"],
        },
    },
    (VerifyInterfacesCounterDetails, "failure-specific-interface-not-found"): {
        "eos_data": [
            {
                "interfaces": {
                    "Ethernet2/1": {
                        "name": "Ethernet2/1",
                        "forwardingModel": "bridged",
                        "lineProtocolStatus": "up",
                        "interfaceStatus": "connected",
                        "description": "",
                        "lastStatusChangeTimestamp": timestamp_one_day_ago,
                        "interfaceCounters": {
                            "inDiscards": 0,
                            "outDiscards": 0,
                            "outTotalPkts": 0,
                            "linkStatusChanges": 2,
                            "totalInErrors": 0,
                            "inputErrorsDetail": {"runtFrames": 0, "giantFrames": 0, "fcsErrors": 0, "alignmentErrors": 0, "symbolErrors": 0, "rxPause": 0},
                            "totalOutErrors": 0,
                            "outputErrorsDetail": {"collisions": 0, "lateCollisions": 0, "deferredTransmissions": 0, "txPause": 0},
                        },
                    },
                    "Ethernet4/2/1": {
                        "name": "Ethernet4/2/1",
                        "forwardingModel": "bridged",
                        "lineProtocolStatus": "up",
                        "interfaceStatus": "connected",
                        "description": "",
                        "lastStatusChangeTimestamp": timestamp_one_day_ago,
                        "interfaceCounters": {
                            "inDiscards": 0,
                            "outDiscards": 0,
                            "linkStatusChanges": 2,
                            "totalInErrors": 0,
                            "inputErrorsDetail": {"runtFrames": 0, "giantFrames": 0, "fcsErrors": 0, "alignmentErrors": 0, "symbolErrors": 0, "rxPause": 0},
                            "totalOutErrors": 0,
                            "outputErrorsDetail": {"collisions": 0, "lateCollisions": 0, "deferredTransmissions": 0, "txPause": 0},
                        },
                    },
                    "Ethernet1/1/1": {
                        "name": "Ethernet1/1/1",
                        "forwardingModel": "bridged",
                        "lineProtocolStatus": "up",
                        "interfaceStatus": "connected",
                        "lastStatusChangeTimestamp": timestamp_one_day_ago,
                        "interfaceCounters": {
                            "inDiscards": 0,
                            "outDiscards": 0,
                            "linkStatusChanges": 2,
                            "totalInErrors": 0,
                            "inputErrorsDetail": {"runtFrames": 0, "giantFrames": 0, "fcsErrors": 0, "alignmentErrors": 0, "symbolErrors": 0, "rxPause": 0},
                            "totalOutErrors": 0,
                            "outputErrorsDetail": {"collisions": 0, "lateCollisions": 0, "deferredTransmissions": 0, "txPause": 0},
                        },
                    },
                    "Ethernet3": {
                        "name": "Ethernet3",
                        "forwardingModel": "bridged",
                        "lineProtocolStatus": "up",
                        "interfaceStatus": "connected",
                        "description": "",
                        "lastStatusChangeTimestamp": timestamp_one_day_ago,
                        "interfaceCounters": {
                            "inDiscards": 0,
                            "outDiscards": 0,
                            "outTotalPkts": 0,
                            "linkStatusChanges": 2,
                            "totalInErrors": 0,
                            "inputErrorsDetail": {"runtFrames": 0, "giantFrames": 0, "fcsErrors": 0, "alignmentErrors": 0, "symbolErrors": 0, "rxPause": 0},
                            "totalOutErrors": 0,
                            "outputErrorsDetail": {"collisions": 0, "lateCollisions": 0, "deferredTransmissions": 0, "txPause": 0},
                        },
                    },
                }
            },
        ],
        "inputs": {"interfaces": ["Ethernet12/1/1", "Ethernet13/2", "Ethernet4/2/1"], "counters_threshold": 0, "link_status_changes_threshold": 100},
        "expected": {"result": AntaTestStatus.FAILURE, "messages": ["Interface: Ethernet12/1/1 - Not found", "Interface: Ethernet13/2 - Not found"]},
    },
    (VerifyInterfacesBER, "success"): {
        "eos_data": [
            {
                "interfacePhyStatuses": {
                    "Ethernet1/1": {
                        "phyStatuses": [
                            {
                                "description": {"phyChipName": "BCM88690-TSCBH", "location": "line"},
                                "fec": {
                                    "correctedCodewords": {"value": 3, "changes": 303, "lastChange": 1749635205.1726532},
                                    "uncorrectedCodewords": {"value": 0, "changes": 0, "lastChange": 0.0},
                                },
                                "preFecBer": {"value": 0.5378509864228316e-9},
                                "pma": {"laneTxStatus": {}},
                                "phyState": {"value": "linkUp", "changes": 2, "lastChange": 1749630055.512745},
                            },
                            {"description": {"phyChipName": "CRT50216"}},
                            {
                                "description": {"phyChipName": "CRT50216", "location": "system"},
                                "fec": {
                                    "correctedCodewords": {"value": 2, "changes": 382, "lastChange": 1749635233.8094382},
                                    "uncorrectedCodewords": {"value": 0, "changes": 0, "lastChange": 0.0},
                                },
                                "preFecBer": {"value": 1.3005834847433436e-12},
                            },
                            {
                                "description": {"phyChipName": "CRT50216", "location": "line"},
                                "fec": {
                                    "hiSer": {"value": False, "changes": 0, "lastChange": 0.0},
                                    "correctedCodewords": {"value": 0, "changes": 0, "lastChange": 0.0},
                                    "uncorrectedCodewords": {"value": 0, "changes": 0, "lastChange": 0.0},
                                    "laneMap": {"0": 0, "1": 1, "2": 2, "3": 3},
                                },
                                "preFecBer": {"value": 1.3399973239803202e-22},
                            },
                        ],
                        "interfaceState": {},
                        "transceiver": {},
                        "macFaults": {},
                    },
                    "Ethernet1/2": {
                        "phyStatuses": [
                            {
                                "description": {"phyChipName": "BCM88690-TSCBH", "location": "line"},
                                "chip": {},
                                "operSpeed": "unknown",
                                "fec": {
                                    "correctedCodewords": {"value": 3, "changes": 303, "lastChange": 1749635205.1726532},
                                    "uncorrectedCodewords": {"value": 0, "changes": 0, "lastChange": 0.0},
                                },
                                "preFecBer": {"value": 1.3005834847433436e-2},
                            },
                            {
                                "description": {"phyChipName": "CRT50216"},
                                "chip": {"oui": 10137034, "model": 0, "rev": 0, "hwRev": "B0", "modelName": "CRT50216"},
                                "firmwareRev": "02.21.02",
                            },
                            {"description": {"phyChipName": "CRT50216", "location": "system"}, "lanes": {}, "topPllVcoCap": {"txPllCap": 43, "rxPllCap": 43}},
                            {"description": {"phyChipName": "CRT50216", "location": "line"}, "lanes": {}, "topPllVcoCap": {}},
                        ],
                        "interfaceState": {},
                        "transceiver": {},
                        "macFaults": {},
                    },
                }
            },
            {
                "interfaceDescriptions": {
                    "Ethernet1/1": {"description": "To Arelion Sweden AB", "lineProtocolStatus": "up", "interfaceStatus": "up"},
                    "Ethernet1/2": {"description": "", "lineProtocolStatus": "up", "interfaceStatus": "up"},
                }
            },
        ],
        "inputs": {"interfaces": ["Ethernet1/1"], "ignored_interfaces": ["Ethernet1/2"], "max_ber_threshold": 1e-8},
        "expected": {"result": AntaTestStatus.SUCCESS},
    },
    (VerifyInterfacesBER, "success-default-input"): {
        "eos_data": [
            {
                "interfacePhyStatuses": {
                    "Ethernet1/1": {
                        "phyStatuses": [
                            {
                                "description": {"phyChipName": "BCM88690-TSCBH", "location": "line"},
                                "fec": {
                                    "correctedCodewords": {"value": 3, "changes": 303, "lastChange": 1749635205.1726532},
                                    "uncorrectedCodewords": {"value": 0, "changes": 0, "lastChange": 0.0},
                                },
                                "preFecBer": {"value": 1.5402777434414486e-13},
                                "pma": {"laneTxStatus": {}},
                                "phyState": {"value": "linkUp", "changes": 2, "lastChange": 1749630055.512745},
                            },
                            {"description": {"phyChipName": "CRT50216"}},
                            {
                                "description": {"phyChipName": "CRT50216", "location": "system"},
                                "fec": {
                                    "correctedCodewords": {"value": 2, "changes": 382, "lastChange": 1749635233.8094382},
                                    "uncorrectedCodewords": {"value": 0, "changes": 0, "lastChange": 0.0},
                                },
                                "preFecBer": {"value": 1.3005834847433436e-12},
                            },
                            {
                                "description": {"phyChipName": "CRT50216", "location": "line"},
                                "fec": {
                                    "hiSer": {"value": False, "changes": 0, "lastChange": 0.0},
                                    "correctedCodewords": {"value": 0, "changes": 0, "lastChange": 0.0},
                                    "uncorrectedCodewords": {"value": 0, "changes": 0, "lastChange": 0.0},
                                    "laneMap": {"0": 0, "1": 1, "2": 2, "3": 3},
                                },
                                "preFecBer": {"value": 1.3399973239803202e-22},
                            },
                        ],
                        "interfaceState": {},
                        "transceiver": {},
                        "macFaults": {},
                    },
                    "Ethernet1/2": {
                        "phyStatuses": [
                            {
                                "description": {"phyChipName": "BCM88690-TSCBH", "location": "line"},
                                "chip": {},
                                "operSpeed": "unknown",
                            },
                            {
                                "description": {"phyChipName": "CRT50216"},
                                "chip": {"oui": 10137034, "model": 0, "rev": 0, "hwRev": "B0", "modelName": "CRT50216"},
                                "firmwareRev": "02.21.02",
                            },
                            {"description": {"phyChipName": "CRT50216", "location": "system"}, "lanes": {}, "topPllVcoCap": {"txPllCap": 43, "rxPllCap": 43}},
                            {"description": {"phyChipName": "CRT50216", "location": "line"}, "lanes": {}, "topPllVcoCap": {}},
                        ],
                        "interfaceState": {},
                        "transceiver": {},
                        "macFaults": {},
                    },
                }
            },
            {
                "interfaceDescriptions": {
                    "Ethernet1/1": {"description": "To Arelion Sweden AB", "lineProtocolStatus": "up", "interfaceStatus": "up"},
                    "Ethernet1/2": {"description": "", "lineProtocolStatus": "up", "interfaceStatus": "up"},
                }
            },
        ],
        "expected": {"result": AntaTestStatus.SUCCESS},
    },
    (VerifyInterfacesBER, "failure-uncorrected-codewords"): {
        "eos_data": [
            {
                "interfacePhyStatuses": {
                    "Ethernet1/1": {
                        "phyStatuses": [
                            {
                                "description": {"phyChipName": "BCM88690-TSCBH", "location": "line"},
                                "fec": {
                                    "correctedCodewords": {"value": 3, "changes": 303, "lastChange": 1749635205.1726532},
                                    "uncorrectedCodewords": {"value": 10, "changes": 0, "lastChange": 0.0},
                                },
                                "preFecBer": {"value": 1.5402777434414486e-23},
                                "pma": {"laneTxStatus": {}},
                                "phyState": {"value": "linkUp", "changes": 2, "lastChange": 1749630055.512745},
                            },
                            {"description": {"phyChipName": "CRT50216"}},
                            {
                                "description": {"phyChipName": "CRT50216", "location": "system"},
                                "fec": {
                                    "correctedCodewords": {"value": 32, "changes": 382, "lastChange": 1749635233.8094382},
                                    "uncorrectedCodewords": {"value": 10, "changes": 0, "lastChange": 0.0},
                                },
                                "preFecBer": {"value": 1.3005834847433436e-22},
                            },
                            {
                                "description": {"phyChipName": "CRT50216", "location": "line"},
                                "fec": {
                                    "hiSer": {"value": False, "changes": 0, "lastChange": 0.0},
                                    "correctedCodewords": {"value": 0, "changes": 0, "lastChange": 0.0},
                                    "uncorrectedCodewords": {"value": 0, "changes": 0, "lastChange": 0.0},
                                    "laneMap": {"0": 0, "1": 1, "2": 2, "3": 3},
                                },
                                "preFecBer": {"value": 1.3399973239803202e-22},
                            },
                        ],
                        "interfaceState": {},
                        "transceiver": {},
                        "macFaults": {},
                    },
                    "Ethernet1/2": {
                        "phyStatuses": [
                            {
                                "description": {"phyChipName": "BCM88690-TSCBH", "location": "line"},
                                "chip": {},
                                "fec": {
                                    "hiSer": {"value": False, "changes": 0, "lastChange": 0.0},
                                    "correctedCodewords": {"value": 0, "changes": 0, "lastChange": 0.0},
                                    "uncorrectedCodewords": {"value": 0, "changes": 0, "lastChange": 0.0},
                                    "laneMap": {"0": 0, "1": 1, "2": 2, "3": 3},
                                },
                                "operSpeed": "unknown",
                            },
                            {
                                "description": {"phyChipName": "CRT50216"},
                                "chip": {"oui": 10137034, "model": 0, "rev": 0, "hwRev": "B0", "modelName": "CRT50216"},
                                "firmwareRev": "02.21.02",
                            },
                            {"description": {"phyChipName": "CRT50216", "location": "system"}, "lanes": {}, "topPllVcoCap": {"txPllCap": 43, "rxPllCap": 43}},
                            {"description": {"phyChipName": "CRT50216", "location": "line"}, "lanes": {}, "topPllVcoCap": {}},
                        ],
                        "interfaceState": {},
                        "transceiver": {},
                        "macFaults": {},
                    },
                }
            },
            {
                "interfaceDescriptions": {
                    "Ethernet1/1": {"description": "To Arelion Sweden AB", "lineProtocolStatus": "up", "interfaceStatus": "up"},
                    "Ethernet1/2": {"description": "", "lineProtocolStatus": "up", "interfaceStatus": "up"},
                }
            },
        ],
        "inputs": {"interfaces": ["Ethernet1/1"], "max_ber_threshold": 1e-8},
        "expected": {
            "result": AntaTestStatus.FAILURE,
            "messages": [
                "Interface: Ethernet1/1 Description: To Arelion Sweden AB - Uncorrected FEC codewords detected - Expected: 0 Actual: 10",
                "Interface: Ethernet1/1 Description: To Arelion Sweden AB - Uncorrected FEC codewords detected - Expected: 0 Actual: 10",
            ],
        },
    },
    (VerifyInterfacesBER, "failure-low-ber-threshold"): {
        "eos_data": [
            {
                "interfacePhyStatuses": {
                    "Ethernet1/1": {
                        "phyStatuses": [
                            {
                                "description": {"phyChipName": "BCM88690-TSCBH", "location": "line"},
                                "fec": {
                                    "correctedCodewords": {"value": 3, "changes": 303, "lastChange": 1749635205.1726532},
                                    "uncorrectedCodewords": {"value": 0, "changes": 0, "lastChange": 0.0},
                                },
                                "preFecBer": {"value": 2.5402777434414486e-2},
                                "pma": {"laneTxStatus": {}},
                                "phyState": {"value": "linkUp", "changes": 2, "lastChange": 1749630055.512745},
                            },
                            {"description": {"phyChipName": "CRT50216"}},
                            {
                                "description": {"phyChipName": "CRT50216", "location": "system"},
                                "fec": {
                                    "correctedCodewords": {"value": 2, "changes": 382, "lastChange": 1749635233.8094382},
                                    "uncorrectedCodewords": {"value": 0, "changes": 0, "lastChange": 0.0},
                                },
                                "preFecBer": {"value": 1.3005834847433436e-12},
                            },
                            {
                                "description": {"phyChipName": "CRT50216", "location": "line"},
                                "fec": {
                                    "hiSer": {"value": False, "changes": 0, "lastChange": 0.0},
                                    "correctedCodewords": {"value": 0, "changes": 0, "lastChange": 0.0},
                                    "uncorrectedCodewords": {"value": 0, "changes": 0, "lastChange": 0.0},
                                    "laneMap": {"0": 0, "1": 1, "2": 2, "3": 3},
                                },
                                "preFecBer": {"value": 1.3399973239803202e-3},
                            },
                        ],
                        "interfaceState": {},
                        "transceiver": {},
                        "macFaults": {},
                    },
                    "Ethernet3/1/1": {
                        "phyStatuses": [
                            {
                                "description": {"phyChipName": "BCM88690-TSCBH", "location": "line"},
                                "fec": {
                                    "correctedCodewords": {"value": 3, "changes": 303, "lastChange": 1749635205.1726532},
                                    "uncorrectedCodewords": {"value": 0, "changes": 0, "lastChange": 0.0},
                                },
                                "preFecBer": {"value": 2.5402777434414486e-2},
                                "pma": {"laneTxStatus": {}},
                                "phyState": {"value": "linkUp", "changes": 2, "lastChange": 1749630055.512745},
                            },
                            {"description": {"phyChipName": "CRT50216"}},
                            {
                                "description": {"phyChipName": "CRT50216", "location": "system"},
                                "fec": {
                                    "correctedCodewords": {"value": 2, "changes": 382, "lastChange": 1749635233.8094382},
                                    "uncorrectedCodewords": {"value": 0, "changes": 0, "lastChange": 0.0},
                                },
                                "preFecBer": {"value": 1.3005834847433436e-2},
                            },
                            {
                                "description": {"phyChipName": "CRT50216", "location": "line"},
                                "fec": {
                                    "hiSer": {"value": False, "changes": 0, "lastChange": 0.0},
                                    "correctedCodewords": {"value": 0, "changes": 0, "lastChange": 0.0},
                                    "uncorrectedCodewords": {"value": 0, "changes": 0, "lastChange": 0.0},
                                    "laneMap": {"0": 0, "1": 1, "2": 2, "3": 3},
                                },
                                "preFecBer": {"value": 1.3399973239803202e-3},
                            },
                        ],
                        "interfaceState": {},
                        "transceiver": {},
                        "macFaults": {},
                    },
                    "Ethernet1/2": {
                        "phyStatuses": [
                            {
                                "description": {"phyChipName": "BCM88690-TSCBH", "location": "line"},
                                "chip": {},
                                "operSpeed": "unknown",
                            },
                            {
                                "description": {"phyChipName": "CRT50216"},
                                "chip": {"oui": 10137034, "model": 0, "rev": 0, "hwRev": "B0", "modelName": "CRT50216"},
                                "firmwareRev": "02.21.02",
                            },
                            {"description": {"phyChipName": "CRT50216", "location": "system"}, "lanes": {}, "topPllVcoCap": {"txPllCap": 43, "rxPllCap": 43}},
                            {"description": {"phyChipName": "CRT50216", "location": "line"}, "lanes": {}, "topPllVcoCap": {}},
                        ],
                        "interfaceState": {},
                        "transceiver": {},
                        "macFaults": {},
                    },
                }
            },
            {
                "interfaceDescriptions": {
                    "Ethernet1/1": {"description": "To Arelion Sweden AB", "lineProtocolStatus": "up", "interfaceStatus": "up"},
                    "Ethernet1/2": {"description": "", "lineProtocolStatus": "up", "interfaceStatus": "up"},
                    "Ethernet3/1/1": {"description": "", "lineProtocolStatus": "up", "interfaceStatus": "up"},
                }
            },
        ],
        "inputs": {"ignored_interfaces": ["Ethernet3/1/1"]},
        "expected": {
            "result": AntaTestStatus.FAILURE,
            "messages": [
                "Interface: Ethernet1/1 Description: To Arelion Sweden AB FEC Corrected: 3 FEC Uncorrected: 0 - BER above threshold -"
                " Expected: <= 1.00e-07 Actual: 2.54e-02",
                "Interface: Ethernet1/1 Description: To Arelion Sweden AB FEC Corrected: 0 FEC Uncorrected: 0 - BER above threshold -"
                " Expected: <= 1.00e-07 Actual: 1.34e-03",
            ],
        },
    },
    (VerifyInterfacesBER, "interface-not-found"): {
        "eos_data": [
            {
                "interfacePhyStatuses": {
                    "Ethernet1/1": {
                        "phyStatuses": [
                            {
                                "description": {"phyChipName": "BCM88690-TSCBH", "location": "line"},
                                "fec": {
                                    "correctedCodewords": {"value": 3, "changes": 303, "lastChange": 1749635205.1726532},
                                    "uncorrectedCodewords": {"value": 0, "changes": 0, "lastChange": 0.0},
                                },
                                "preFecBer": {"value": 2.5402777434414486e-12},
                                "pma": {"laneTxStatus": {}},
                                "phyState": {"value": "linkUp", "changes": 2, "lastChange": 1749630055.512745},
                            },
                            {"description": {"phyChipName": "CRT50216"}},
                            {
                                "description": {"phyChipName": "CRT50216", "location": "system"},
                                "fec": {
                                    "correctedCodewords": {"value": 2, "changes": 382, "lastChange": 1749635233.8094382},
                                    "uncorrectedCodewords": {"value": 0, "changes": 0, "lastChange": 0.0},
                                },
                                "preFecBer": {"value": 1.3005834847433436e-8},
                            },
                            {
                                "description": {"phyChipName": "CRT50216", "location": "line"},
                                "fec": {
                                    "hiSer": {"value": False, "changes": 0, "lastChange": 0.0},
                                    "correctedCodewords": {"value": 0, "changes": 0, "lastChange": 0.0},
                                    "uncorrectedCodewords": {"value": 0, "changes": 0, "lastChange": 0.0},
                                    "laneMap": {"0": 0, "1": 1, "2": 2, "3": 3},
                                },
                                "preFecBer": {"value": 1.3399973239803202e-13},
                            },
                        ],
                        "interfaceState": {},
                        "transceiver": {},
                        "macFaults": {},
                    },
                }
            },
            {
                "interfaceDescriptions": {
                    "Ethernet1/1": {"description": "To Arelion Sweden AB", "lineProtocolStatus": "up", "interfaceStatus": "up"},
                    "Ethernet1/2": {"description": "", "lineProtocolStatus": "up", "interfaceStatus": "up"},
                }
            },
        ],
        "inputs": {"interfaces": ["Ethernet8/1"], "max_ber_threshold": 1e-9},
        "expected": {
            "result": AntaTestStatus.FAILURE,
            "messages": ["Interface: Ethernet8/1 - Not found"],
        },
    },
    (VerifyInterfacesOpticsReceivePower, "success"): {
        "eos_data": [
            {
                "interfaces": {
                    "Ethernet1/1": {"displayName": "Ethernet1/1"},
                    "Ethernet2/1": {
                        "displayName": "Ethernet2/1",
                        "vendorSn": "TEST05DA",
                        "mediaType": "100GBASE-SR4",
                        "parameters": {
                            "rxPower": {
                                "unit": "dBm",
                                "channels": {"1": -30.08242460465652002, "2": -0.09972101229705288, "3": -40.31236951802751634, "4": -1.4630178822382547},
                                "threshold": {
                                    "lowAlarm": -13.29754146925876,
                                    "lowAlarmOverridden": False,
                                    "lowWarn": -10.301183562535002,
                                    "lowWarnOverridden": False,
                                },
                            }
                        },
                    },
                    "Ethernet3/1": {"displayName": "Ethernet3/1"},
                    "Ethernet7/1": {
                        "displayName": "Ethernet7/1",
                        "vendorSn": "TEST08M",
                        "mediaType": "40GBASE-SR4",
                        "parameters": {
                            "rxPower": {
                                "unit": "dBm",
                                "channels": {"1": -2.6019040097864092, "2": -2.3657200643706275, "3": -2.2242819530858995, "4": -2.7018749283906445},
                                "threshold": {
                                    "lowAlarm": -12.502636844309393,
                                    "lowAlarmOverridden": False,
                                    "lowWarn": -9.500071430798577,
                                    "lowWarnOverridden": False,
                                },
                            }
                        },
                    },
                }
            },
            {
                "interfaceDescriptions": {
                    "Ethernet1/1": {"description": "", "lineProtocolStatus": "up", "interfaceStatus": "up"},
                    "Ethernet2/1": {"description": "To_HS-154", "lineProtocolStatus": "up", "interfaceStatus": "up"},
                    "Ethernet3/1": {"description": "", "lineProtocolStatus": "down", "interfaceStatus": "down"},
                    "Ethernet7/1": {"description": "GZ_CMCC_v6", "lineProtocolStatus": "down", "interfaceStatus": "down"},
                }
            },
        ],
        "inputs": {"ignored_interfaces": ["Ethernet2/1"], "failure_margin": 2},
        "expected": {
            "result": AntaTestStatus.SUCCESS,
        },
    },
    (VerifyInterfacesOpticsReceivePower, "success-valid-rx-power"): {
        "eos_data": [
            {
                "interfaces": {
                    "Ethernet1/1": {"displayName": "Ethernet1/1"},
                    "Ethernet2/1": {
                        "displayName": "Ethernet2/1",
                        "vendorSn": "TEST5DA",
                        "mediaType": "100GBASE-SR4",
                        "parameters": {
                            "rxPower": {
                                "unit": "dBm",
                                "channels": {"1": -30, "2": -0.09972101229705288, "3": -0.31236951802751634, "4": -1.4630178822382547},
                                "threshold": {
                                    "lowAlarm": -13.29754146925876,
                                    "lowAlarmOverridden": False,
                                    "lowWarn": -10.301183562535002,
                                    "lowWarnOverridden": False,
                                },
                            }
                        },
                    },
                    "Ethernet3/1": {"displayName": "Ethernet3/1"},
                    "Ethernet7/1": {
                        "displayName": "Ethernet7/1",
                        "vendorSn": "TEST8M",
                        "mediaType": "40GBASE-SR4",
                        "parameters": {
                            "rxPower": {
                                "unit": "dBm",
                                "channels": {"1": -30, "2": -2.3657200643706275, "3": -23.2242819530858995, "4": -2.7018749283906445},
                                "threshold": {
                                    "lowAlarm": -25.502636844309393,
                                    "lowAlarmOverridden": False,
                                    "lowWarn": -9.500071430798577,
                                    "lowWarnOverridden": False,
                                },
                            }
                        },
                    },
                }
            },
            {
                "interfaceDescriptions": {
                    "Ethernet1/1": {"description": "", "lineProtocolStatus": "up", "interfaceStatus": "up"},
                    "Ethernet2/1": {"description": "To_HS-154", "lineProtocolStatus": "up", "interfaceStatus": "up"},
                    "Ethernet3/1": {"description": "", "lineProtocolStatus": "down", "interfaceStatus": "down"},
                    "Ethernet7/1": {"description": "GZ_CMCC_v6", "lineProtocolStatus": "down", "interfaceStatus": "down"},
                }
            },
        ],
        "inputs": {"failure_margin": 2},
        "expected": {
            "result": AntaTestStatus.SUCCESS,
        },
    },
    (VerifyInterfacesOpticsReceivePower, "failure-optic-low-rx"): {
        "eos_data": [
            {
                "interfaces": {
                    "Ethernet1/1": {"displayName": "Ethernet1/1"},
                    "Ethernet2/1": {
                        "displayName": "Ethernet2/1",
                        "vendorSn": "TEST05DA",
                        "mediaType": "100GBASE-SR4",
                        "parameters": {
                            "rxPower": {
                                "unit": "dBm",
                                "channels": {"1": -30.08242460465652002, "2": -0.09972101229705288, "3": -40.31236951802751634, "4": -1.4630178822382547},
                                "threshold": {
                                    "lowAlarm": -13.29754146925876,
                                    "lowAlarmOverridden": False,
                                    "lowWarn": -10.301183562535002,
                                    "lowWarnOverridden": False,
                                },
                            }
                        },
                    },
                    "Ethernet3/1": {"displayName": "Ethernet3/1"},
                    "Ethernet7/1/1": {
                        "displayName": "Ethernet7/1/1",
                        "vendorSn": "TEST008M",
                        "mediaType": "40GBASE-SR4",
                        "parameters": {
                            "rxPower": {
                                "unit": "dBm",
                                "channels": {"1": -29.6019040097864092, "2": -2.3657200643706275, "3": -23.2242819530858995, "4": -2.7018749283906445},
                                "threshold": {
                                    "lowAlarm": -12.502636844309393,
                                    "lowAlarmOverridden": False,
                                    "lowWarn": -9.500071430798577,
                                    "lowWarnOverridden": False,
                                },
                            }
                        },
                    },
                    "Ethernet8/1/1": {
                        "displayName": "Ethernet8/1/1",
                        "vendorSn": "TEST8M",
                        "mediaType": "40GBASE-SR4",
                        "parameters": {
                            "rxPower": {
                                "unit": "dBm",
                                "channels": {"1": -29.6019040097864092, "2": -2.3657200643706275, "3": -23.2242819530858995, "4": -2.7018749283906445},
                                "threshold": {
                                    "lowAlarm": -12.502636844309393,
                                    "lowAlarmOverridden": False,
                                    "lowWarn": -9.500071430798577,
                                    "lowWarnOverridden": False,
                                },
                            }
                        },
                    },
                }
            },
            {
                "interfaceDescriptions": {
                    "Ethernet1/1": {"description": "", "lineProtocolStatus": "up", "interfaceStatus": "up"},
                    "Ethernet2/1": {"description": "", "lineProtocolStatus": "up", "interfaceStatus": "up"},
                    "Ethernet3/1": {"description": "", "lineProtocolStatus": "down", "interfaceStatus": "down"},
                    "Ethernet7/1/1": {"description": "GZ_CMCC_v6", "lineProtocolStatus": "down", "interfaceStatus": "down"},
                    "Ethernet8/1/1": {"description": "GZ_CMCC_v6", "lineProtocolStatus": "down", "interfaceStatus": "down"},
                }
            },
        ],
        "inputs": {"interfaces": ["Ethernet1/1", "Ethernet2/1", "Ethernet3/1"], "ignored_interfaces": ["Ethernet7/1/1"], "failure_margin": 2},
        "expected": {
            "result": AntaTestStatus.FAILURE,
            "messages": [
                "Interface: Ethernet1/1 - Receive power details are not found (DOM not supported)",
                "Interface: Ethernet2/1 Status: up Channel: 1 Optic: 100GBASE-SR4 - Low receive power detected - "
                "Expected: >= -11.30dBm (Alarm: -13.30dBm + Margin: 2dBm) Actual: -30.08dBm",
                "Interface: Ethernet2/1 Status: up Channel: 3 Optic: 100GBASE-SR4 - Low receive power detected - "
                "Expected: >= -11.30dBm (Alarm: -13.30dBm + Margin: 2dBm) Actual: -40.31dBm",
                "Interface: Ethernet3/1 - Receive power details are not found (DOM not supported)",
            ],
        },
    },
    (VerifyInterfacesOpticsReceivePower, "failure-due-to-margin"): {
        "eos_data": [
            {
                "interfaces": {
                    "Ethernet1/1": {
                        "displayName": "Ethernet1/1",
                        "mediaType": "100GBASE-SR4",
                        "parameters": {
                            "rxPower": {
                                "unit": "dBm",
                                "channels": {"1": -12.0},
                                "threshold": {"lowAlarm": -13.0},
                            }
                        },
                    },
                }
            },
            {
                "interfaceDescriptions": {
                    "Ethernet1/1": {"description": "Proactive failure test", "lineProtocolStatus": "up", "interfaceStatus": "up"},
                }
            },
        ],
        "inputs": {"failure_margin": 2},
        "expected": {
            "result": AntaTestStatus.FAILURE,
            "messages": [
                "Interface: Ethernet1/1 Status: up Channel: 1 Optic: 100GBASE-SR4 - Low receive power detected - "
                "Expected: >= -11.00dBm (Alarm: -13.00dBm + Margin: 2dBm) Actual: -12.00dBm"
            ],
        },
    },
    (VerifyInterfacesOpticsReceivePower, "interface-not-found"): {
        "eos_data": [
            {
                "interfaces": {
                    "Ethernet1/1": {"displayName": "Ethernet1/1"},
                    "Ethernet2/1": {
                        "displayName": "Ethernet2/1",
                        "vendorSn": "TEST5DA",
                        "mediaType": "100GBASE-SR4",
                        "parameters": {
                            "rxPower": {
                                "unit": "dBm",
                                "channels": {"1": -30.08242460465652002, "2": -0.09972101229705288, "3": -40.31236951802751634, "4": -1.4630178822382547},
                                "threshold": {
                                    "lowAlarm": -13.29754146925876,
                                    "lowAlarmOverridden": False,
                                    "lowWarn": -10.301183562535002,
                                    "lowWarnOverridden": False,
                                },
                            }
                        },
                    },
                    "Ethernet3/1": {"displayName": "Ethernet3/1"},
                }
            },
            {
                "interfaceDescriptions": {
                    "Ethernet1/1": {"description": "", "lineProtocolStatus": "up", "interfaceStatus": "up"},
                    "Ethernet2/1": {"description": "", "lineProtocolStatus": "up", "interfaceStatus": "up"},
                    "Ethernet3/1": {"description": "", "lineProtocolStatus": "down", "interfaceStatus": "down"},
                }
            },
        ],
        "inputs": {"interfaces": ["Ethernet13/1"], "failure_margin": 2},
        "expected": {
            "result": AntaTestStatus.FAILURE,
            "messages": ["Interface: Ethernet13/1 - Optic not found"],
        },
    },
    (VerifyInterfacesEgressQueueDrops, "success-all"): {
        "eos_data": [
            {
                "egressQueueCounters": {
                    "interfaces": {
                        "Ethernet1": {
                            "ucastQueues": {
                                "trafficClasses": {
                                    "TC0": {
                                        "dropPrecedences": {
                                            "DP0": {
                                                "droppedPackets": 0,
                                            }
                                        }
                                    },
                                    "TC1": {
                                        "dropPrecedences": {
                                            "DP0": {
                                                "droppedPackets": 0,
                                            }
                                        }
                                    },
                                }
                            },
                            "mcastQueues": {
                                "trafficClasses": {
                                    "TC0": {
                                        "dropPrecedences": {
                                            "DP0": {
                                                "droppedPackets": 0,
                                            }
                                        }
                                    },
                                    "TC1": {
                                        "dropPrecedences": {
                                            "DP0": {
                                                "droppedPackets": 0,
                                            }
                                        }
                                    },
                                }
                            },
                        },
                        "Ethernet2": {
                            "ucastQueues": {
                                "trafficClasses": {
                                    "TC0": {
                                        "dropPrecedences": {
                                            "DP0": {
                                                "droppedPackets": 0,
                                            }
                                        }
                                    },
                                    "TC1": {
                                        "dropPrecedences": {
                                            "DP0": {
                                                "droppedPackets": 0,
                                            }
                                        }
                                    },
                                }
                            },
                            "mcastQueues": {
                                "trafficClasses": {
                                    "TC0": {
                                        "dropPrecedences": {
                                            "DP0": {
                                                "droppedPackets": 0,
                                            }
                                        }
                                    },
                                    "TC1": {
                                        "dropPrecedences": {
                                            "DP0": {
                                                "droppedPackets": 4,
                                            }
                                        }
                                    },
                                }
                            },
                        },
                    }
                }
            }
        ],
        "inputs": {"ignored_interfaces": ["Ethernet2"]},
        "expected": {"result": AntaTestStatus.SUCCESS},
    },
    (VerifyInterfacesEgressQueueDrops, "success-all-modular"): {
        "eos_data": [
            {
                "egressQueueCounters": {
                    "interfaces": {
                        "Ethernet1/1": {
                            "ucastQueues": {
                                "trafficClasses": {
                                    "TC0": {
                                        "dropPrecedences": {
                                            "DP0": {
                                                "droppedPackets": 0,
                                            }
                                        }
                                    },
                                    "TC1": {
                                        "dropPrecedences": {
                                            "DP0": {
                                                "droppedPackets": 0,
                                            }
                                        }
                                    },
                                }
                            },
                            "mcastQueues": {
                                "trafficClasses": {
                                    "TC0": {
                                        "dropPrecedences": {
                                            "DP0": {
                                                "droppedPackets": 0,
                                            }
                                        }
                                    },
                                    "TC1": {
                                        "dropPrecedences": {
                                            "DP0": {
                                                "droppedPackets": 0,
                                            }
                                        }
                                    },
                                }
                            },
                        },
                        "Ethernet2/1": {
                            "ucastQueues": {
                                "trafficClasses": {
                                    "TC0": {
                                        "dropPrecedences": {
                                            "DP0": {
                                                "droppedPackets": 0,
                                            }
                                        }
                                    },
                                    "TC1": {
                                        "dropPrecedences": {
                                            "DP0": {
                                                "droppedPackets": 0,
                                            }
                                        }
                                    },
                                }
                            },
                            "mcastQueues": {
                                "trafficClasses": {
                                    "TC0": {
                                        "dropPrecedences": {
                                            "DP0": {
                                                "droppedPackets": 0,
                                            }
                                        }
                                    },
                                    "TC1": {
                                        "dropPrecedences": {
                                            "DP0": {
                                                "droppedPackets": 0,
                                            }
                                        }
                                    },
                                }
                            },
                        },
                    }
                }
            }
        ],
        "expected": {"result": AntaTestStatus.SUCCESS},
    },
    (VerifyInterfacesEgressQueueDrops, "success-traffic-claas-and-dp-range"): {
        "eos_data": [
            {
                "egressQueueCounters": {
                    "interfaces": {
                        "Ethernet1": {
                            "ucastQueues": {
                                "trafficClasses": {
                                    "TC0-2": {
                                        "dropPrecedences": {
                                            "DP0-2": {
                                                "droppedPackets": 0,
                                            }
                                        }
                                    },
                                }
                            },
                            "mcastQueues": {
                                "trafficClasses": {
                                    "TC0-2": {
                                        "dropPrecedences": {
                                            "DP0-2": {
                                                "droppedPackets": 0,
                                            }
                                        }
                                    },
                                }
                            },
                        },
                        "Ethernet2": {
                            "ucastQueues": {
                                "trafficClasses": {
                                    "TC0-2": {
                                        "dropPrecedences": {
                                            "DP0-2": {
                                                "droppedPackets": 0,
                                            }
                                        }
                                    },
                                }
                            },
                            "mcastQueues": {
                                "trafficClasses": {
                                    "TC0-2": {
                                        "dropPrecedences": {
                                            "DP0-2": {
                                                "droppedPackets": 0,
                                            }
                                        }
                                    },
                                }
                            },
                        },
                    }
                }
            }
        ],
        "inputs": {"traffic_classes": ["TC0", "TC1", "TC2"], "drop_precedences": ["DP0", "DP1", "DP2"]},
        "expected": {"result": AntaTestStatus.SUCCESS},
    },
    (VerifyInterfacesEgressQueueDrops, "success-unicast"): {
        "eos_data": [
            {
                "egressQueueCounters": {
                    "interfaces": {
                        "Ethernet1": {
                            "ucastQueues": {
                                "trafficClasses": {
                                    "TC0": {
                                        "dropPrecedences": {
                                            "DP0": {
                                                "droppedPackets": 0,
                                            }
                                        }
                                    },
                                    "TC1": {
                                        "dropPrecedences": {
                                            "DP0": {
                                                "droppedPackets": 0,
                                            }
                                        }
                                    },
                                }
                            },
                        }
                    }
                }
            }
        ],
        "inputs": {"queue_types": ["unicast"]},
        "expected": {"result": AntaTestStatus.SUCCESS},
    },
    (VerifyInterfacesEgressQueueDrops, "success-multicast"): {
        "eos_data": [
            {
                "egressQueueCounters": {
                    "interfaces": {
                        "Ethernet1": {
                            "mcastQueues": {
                                "trafficClasses": {
                                    "TC0": {
                                        "dropPrecedences": {
                                            "DP0": {
                                                "droppedPackets": 0,
                                            }
                                        }
                                    },
                                    "TC1": {
                                        "dropPrecedences": {
                                            "DP0": {
                                                "droppedPackets": 0,
                                            }
                                        }
                                    },
                                }
                            },
                        }
                    }
                }
            }
        ],
        "inputs": {"queue_types": ["multicast"]},
        "expected": {"result": AntaTestStatus.SUCCESS},
    },
    (VerifyInterfacesEgressQueueDrops, "success-specific-intf"): {
        "eos_data": [
            {
                "egressQueueCounters": {
                    "interfaces": {
                        "Ethernet1": {
                            "mcastQueues": {
                                "trafficClasses": {
                                    "TC0": {
                                        "dropPrecedences": {
                                            "DP0": {
                                                "droppedPackets": 0,
                                            }
                                        }
                                    },
                                    "TC1": {
                                        "dropPrecedences": {
                                            "DP0": {
                                                "droppedPackets": 0,
                                            }
                                        }
                                    },
                                }
                            },
                        },
                        "Ethernet2": {
                            "mcastQueues": {
                                "trafficClasses": {
                                    "TC0": {
                                        "dropPrecedences": {
                                            "DP0": {
                                                "droppedPackets": 4,
                                            }
                                        }
                                    },
                                    "TC1": {
                                        "dropPrecedences": {
                                            "DP0": {
                                                "droppedPackets": 4,
                                            }
                                        }
                                    },
                                }
                            },
                        },
                    }
                }
            }
        ],
        "inputs": {"interfaces": ["Ethernet1"], "queue_types": ["multicast"]},
        "expected": {"result": AntaTestStatus.SUCCESS},
    },
    (VerifyInterfacesEgressQueueDrops, "success-specific-traffic-class"): {
        "eos_data": [
            {
                "egressQueueCounters": {
                    "interfaces": {
                        "Ethernet1": {
                            "mcastQueues": {
                                "trafficClasses": {
                                    "TC0": {
                                        "dropPrecedences": {
                                            "DP0": {
                                                "droppedPackets": 0,
                                            }
                                        }
                                    },
                                    "TC1": {
                                        "dropPrecedences": {
                                            "DP0": {
                                                "droppedPackets": 3,
                                            }
                                        }
                                    },
                                }
                            },
                        },
                        "Ethernet2": {
                            "mcastQueues": {
                                "trafficClasses": {
                                    "TC0": {
                                        "dropPrecedences": {
                                            "DP0": {
                                                "droppedPackets": 0,
                                            }
                                        }
                                    },
                                    "TC1": {
                                        "dropPrecedences": {
                                            "DP0": {
                                                "droppedPackets": 4,
                                            }
                                        }
                                    },
                                }
                            },
                        },
                    }
                }
            }
        ],
        "inputs": {"traffic_classes": ["TC0"], "queue_types": ["multicast"]},
        "expected": {"result": AntaTestStatus.SUCCESS},
    },
    (VerifyInterfacesEgressQueueDrops, "failure"): {
        "eos_data": [
            {
                "egressQueueCounters": {
                    "interfaces": {
                        "Ethernet1": {
                            "ucastQueues": {
                                "trafficClasses": {
                                    "TC0": {
                                        "dropPrecedences": {
                                            "DP0": {
                                                "droppedPackets": 2,
                                            }
                                        }
                                    },
                                    "TC1": {
                                        "dropPrecedences": {
                                            "DP0": {
                                                "droppedPackets": 0,
                                            }
                                        }
                                    },
                                }
                            },
                            "mcastQueues": {
                                "trafficClasses": {
                                    "TC0": {
                                        "dropPrecedences": {
                                            "DP0": {
                                                "droppedPackets": 0,
                                            }
                                        }
                                    },
                                    "TC1": {
                                        "dropPrecedences": {
                                            "DP0": {
                                                "droppedPackets": 3,
                                            }
                                        }
                                    },
                                }
                            },
                        },
                        "Ethernet2": {
                            "ucastQueues": {
                                "trafficClasses": {
                                    "TC0": {
                                        "dropPrecedences": {
                                            "DP0": {
                                                "droppedPackets": 0,
                                            }
                                        }
                                    },
                                    "TC1": {
                                        "dropPrecedences": {
                                            "DP0": {
                                                "droppedPackets": 2,
                                            }
                                        }
                                    },
                                }
                            },
                            "mcastQueues": {
                                "trafficClasses": {
                                    "TC0": {
                                        "dropPrecedences": {
                                            "DP0": {
                                                "droppedPackets": 3,
                                            }
                                        }
                                    },
                                    "TC1": {
                                        "dropPrecedences": {
                                            "DP0": {
                                                "droppedPackets": 0,
                                            }
                                        }
                                    },
                                }
                            },
                        },
                    }
                }
            }
        ],
        "expected": {
            "result": AntaTestStatus.FAILURE,
            "messages": [
                "Interface: Ethernet1 Traffic Class: TC0 Queue Type: unicast Drop Precedence: DP0 - Queue drops above threshold - Expected: <= 0 Actual: 2",
                "Interface: Ethernet1 Traffic Class: TC1 Queue Type: multicast Drop Precedence: DP0 - Queue drops above threshold - Expected: <= 0 Actual: 3",
                "Interface: Ethernet2 Traffic Class: TC1 Queue Type: unicast Drop Precedence: DP0 - Queue drops above threshold - Expected: <= 0 Actual: 2",
                "Interface: Ethernet2 Traffic Class: TC0 Queue Type: multicast Drop Precedence: DP0 - Queue drops above threshold - Expected: <= 0 Actual: 3",
            ],
        },
    },
    (VerifyInterfacesEgressQueueDrops, "failure-specific-intf"): {
        "eos_data": [
            {
                "egressQueueCounters": {
                    "interfaces": {
                        "Ethernet2": {
                            "mcastQueues": {
                                "trafficClasses": {
                                    "TC0": {
                                        "dropPrecedences": {
                                            "DP0": {
                                                "droppedPackets": 4,
                                            }
                                        }
                                    },
                                    "TC1": {
                                        "dropPrecedences": {
                                            "DP0": {
                                                "droppedPackets": 4,
                                            }
                                        }
                                    },
                                }
                            },
                        }
                    }
                }
            }
        ],
        "inputs": {"interfaces": ["Ethernet1"], "queue_types": ["multicast"]},
        "expected": {"result": AntaTestStatus.FAILURE, "messages": ["Interface: Ethernet1 - Not found"]},
    },
    (VerifyInterfacesEgressQueueDrops, "failure-specific-traffic-class"): {
        "eos_data": [
            {
                "egressQueueCounters": {
                    "interfaces": {
                        "Ethernet1": {
                            "mcastQueues": {
                                "trafficClasses": {
                                    "TC1": {
                                        "dropPrecedences": {
                                            "DP0": {
                                                "droppedPackets": 3,
                                            }
                                        }
                                    }
                                }
                            },
                        },
                        "Ethernet2": {
                            "mcastQueues": {
                                "trafficClasses": {
                                    "TC1": {
                                        "dropPrecedences": {
                                            "DP0": {
                                                "droppedPackets": 4,
                                            }
                                        }
                                    }
                                }
                            },
                        },
                    }
                }
            }
        ],
        "inputs": {"traffic_classes": ["TC0"], "queue_types": ["multicast"]},
        "expected": {
            "result": AntaTestStatus.FAILURE,
            "messages": [
                "Interface: Ethernet1 Queue Type: multicast Traffic Class: TC0 - Not found",
                "Interface: Ethernet2 Queue Type: multicast Traffic Class: TC0 - Not found",
            ],
        },
    },
    (VerifyInterfacesEgressQueueDrops, "failure-traffic-claas-and-dp-range"): {
        "eos_data": [
            {
                "egressQueueCounters": {
                    "interfaces": {
                        "Ethernet1": {
                            "ucastQueues": {
                                "trafficClasses": {
                                    "TC0-2": {
                                        "dropPrecedences": {
                                            "DP0-2": {
                                                "droppedPackets": 2,
                                            }
                                        }
                                    },
                                }
                            },
                        },
                    }
                }
            }
        ],
        "inputs": {"traffic_classes": ["TC0", "TC1"], "drop_precedences": ["DP0", "DP1"], "queue_types": ["unicast"]},
        "expected": {
            "result": AntaTestStatus.FAILURE,
            "messages": [
                "Interface: Ethernet1 Traffic Class: TC0 Queue Type: unicast Drop Precedence: DP0 - Queue drops above threshold - Expected: <= 0 Actual: 2",
                "Interface: Ethernet1 Traffic Class: TC0 Queue Type: unicast Drop Precedence: DP1 - Queue drops above threshold - Expected: <= 0 Actual: 2",
                "Interface: Ethernet1 Traffic Class: TC1 Queue Type: unicast Drop Precedence: DP0 - Queue drops above threshold - Expected: <= 0 Actual: 2",
                "Interface: Ethernet1 Traffic Class: TC1 Queue Type: unicast Drop Precedence: DP1 - Queue drops above threshold - Expected: <= 0 Actual: 2",
            ],
        },
    },
    (VerifyInterfacesEgressQueueDrops, "failure-precedence-not-found"): {
        "eos_data": [
            {
                "egressQueueCounters": {
                    "interfaces": {
                        "Ethernet1": {
                            "ucastQueues": {
                                "trafficClasses": {
                                    "TC0-2": {"dropPrecedences": {}},
                                }
                            },
                        },
                    }
                }
            }
        ],
        "inputs": {"traffic_classes": ["TC0", "TC1"], "drop_precedences": ["DP0"], "queue_types": ["unicast"]},
        "expected": {
            "result": AntaTestStatus.FAILURE,
            "messages": [
                "Interface: Ethernet1 Traffic Class: TC0 Queue Type: unicast Drop Precedence: DP0 - Not found",
                "Interface: Ethernet1 Traffic Class: TC1 Queue Type: unicast Drop Precedence: DP0 - Not found",
            ],
        },
    },
    (VerifyInterfacesEgressQueueDrops, "failure-modular"): {
        "eos_data": [
            {
                "egressQueueCounters": {
                    "interfaces": {
                        "Ethernet1/1": {
                            "ucastQueues": {
                                "trafficClasses": {
                                    "TC0": {
                                        "dropPrecedences": {
                                            "DP0": {
                                                "droppedPackets": 2,
                                            }
                                        }
                                    },
                                    "TC1": {
                                        "dropPrecedences": {
                                            "DP0": {
                                                "droppedPackets": 2,
                                            }
                                        }
                                    },
                                }
                            },
                            "mcastQueues": {
                                "trafficClasses": {
                                    "TC0": {
                                        "dropPrecedences": {
                                            "DP0": {
                                                "droppedPackets": 1,
                                            }
                                        }
                                    },
                                    "TC1": {
                                        "dropPrecedences": {
                                            "DP0": {
                                                "droppedPackets": 0,
                                            }
                                        }
                                    },
                                }
                            },
                        },
                        "Ethernet2/1": {
                            "ucastQueues": {
                                "trafficClasses": {
                                    "TC0": {
                                        "dropPrecedences": {
                                            "DP0": {
                                                "droppedPackets": 0,
                                            }
                                        }
                                    },
                                    "TC1": {
                                        "dropPrecedences": {
                                            "DP0": {
                                                "droppedPackets": 0,
                                            }
                                        }
                                    },
                                }
                            },
                            "mcastQueues": {
                                "trafficClasses": {
                                    "TC0": {
                                        "dropPrecedences": {
                                            "DP0": {
                                                "droppedPackets": 0,
                                            }
                                        }
                                    },
                                    "TC1": {
                                        "dropPrecedences": {
                                            "DP0": {
                                                "droppedPackets": 0,
                                            }
                                        }
                                    },
                                }
                            },
                        },
                    }
                }
            }
        ],
        "expected": {
            "result": AntaTestStatus.FAILURE,
            "messages": [
                "Interface: Ethernet1/1 Traffic Class: TC0 Queue Type: unicast Drop Precedence: DP0 - Queue drops above threshold - Expected: <= 0 Actual: 2",
                "Interface: Ethernet1/1 Traffic Class: TC1 Queue Type: unicast Drop Precedence: DP0 - Queue drops above threshold - Expected: <= 0 Actual: 2",
                "Interface: Ethernet1/1 Traffic Class: TC0 Queue Type: multicast Drop Precedence: DP0 - Queue drops above threshold - Expected: <= 0 Actual: 1",
            ],
        },
    },
    (VerifyInterfacesOpticsTemperature, "success"): {
        "eos_data": [
            {
                "interfaces": {
                    "Ethernet1/1": {
                        "displayName": "Ethernet1/1",
                        "parameters": {
                            "temperature": {
                                "unit": "C",
                                "channels": {"-": 33.85546875},
                            },
                        },
                    },
                    "Ethernet1/2": {
                        "displayName": "Ethernet1/2",
                        "parameters": {
                            "temperature": {
                                "unit": "C",
                                "channels": {"-": 33.85546875},
                            },
                        },
                    },
                    "Ethernet1/3": {
                        "displayName": "Ethernet1/3",
                        "parameters": {
                            "temperature": {
                                "unit": "C",
                                "channels": {"-": 33.85546875},
                            },
                        },
                    },
                }
            }
        ],
        "expected": {"result": AntaTestStatus.SUCCESS},
    },
    (VerifyInterfacesOpticsTemperature, "success-specific-interface"): {
        "eos_data": [
            {
                "interfaces": {
                    "Ethernet25/8": {
                        "displayName": "Ethernet25/8",
                        "parameters": {
                            "temperature": {
                                "unit": "C",
                                "channels": {"-": 80.85546875},
                            },
                        },
                    },
                    "Ethernet1/1": {
                        "displayName": "Ethernet1/1",
                        "parameters": {
                            "temperature": {
                                "unit": "C",
                                "channels": {"-": 60.85546875},
                            },
                        },
                    },
                    "Ethernet1/2": {
                        "displayName": "Ethernet1/2",
                        "parameters": {
                            "temperature": {
                                "unit": "C",
                                "channels": {"-": 33.85546875},
                            },
                        },
                    },
                }
            }
        ],
        "inputs": {"interfaces": ["Ethernet1/1", "Ethernet1/2"], "max_transceiver_temperature": 70},
        "expected": {"result": AntaTestStatus.SUCCESS},
    },
    (VerifyInterfacesOpticsTemperature, "success-ignored-intf"): {
        "eos_data": [
            {
                "interfaces": {
                    "Ethernet1/1": {
                        "displayName": "Ethernet1/1",
                        "parameters": {
                            "temperature": {
                                "unit": "C",
                                "channels": {"-": 80.85546875},
                            },
                        },
                    },
                    "Ethernet1/2": {
                        "displayName": "Ethernet1/2",
                        "parameters": {
                            "temperature": {
                                "unit": "C",
                                "channels": {"-": 33.85546875},
                            },
                        },
                    },
                }
            }
        ],
        "inputs": {"ignored_interfaces": ["Ethernet1/1"], "max_transceiver_temperature": 70},
        "expected": {"result": AntaTestStatus.SUCCESS},
    },
    (VerifyInterfacesOpticsTemperature, "failure-no-optics-specific-interface"): {
        "eos_data": [
            {
                "interfaces": {
                    "Ethernet25/8": {},
                    "Ethernet1/1": {},
                    "Ethernet1/2": {},
                    "Ethernet1/3": {},
                }
            }
        ],
        "inputs": {"interfaces": ["Ethernet1/1"], "max_transceiver_temperature": 70},
        "expected": {"result": AntaTestStatus.FAILURE, "messages": ["Interface: Ethernet1/1 - Optic not found"]},
    },
    (VerifyInterfacesOpticsTemperature, "failure-all"): {
        "eos_data": [
            {
                "interfaces": {
                    "Ethernet1/1": {
                        "displayName": "Ethernet1/1",
                        "parameters": {
                            "temperature": {
                                "unit": "C",
                                "channels": {"-": 73.7575},
                            },
                        },
                    },
                    "Ethernet1/2": {
                        "displayName": "Ethernet1/2",
                        "parameters": {
                            "temperature": {
                                "unit": "C",
                                "channels": {"-": 75.7575},
                            },
                        },
                    },
                }
            }
        ],
        "expected": {
            "result": AntaTestStatus.FAILURE,
            "messages": [
                "Interface: Ethernet1/1 - High transceiver temperature detected - Expected: <= 68.0°C Actual: 73.76°C",
                "Interface: Ethernet1/2 - High transceiver temperature detected - Expected: <= 68.0°C Actual: 75.76°C",
            ],
        },
    },
    (VerifyInterfacesOpticsTemperature, "failure-specific-interface"): {
        "eos_data": [
            {
                "interfaces": {
                    "Ethernet25/8": {},
                    "Ethernet1/1": {
                        "displayName": "Ethernet1/1",
                        "parameters": {
                            "temperature": {
                                "unit": "C",
                                "channels": {"-": 73.7575},
                            },
                        },
                    },
                    "Ethernet1/2": {
                        "displayName": "Ethernet1/2",
                        "parameters": {
                            "temperature": {
                                "unit": "C",
                                "channels": {"-": 73.7575},
                            },
                        },
                    },
                }
            }
        ],
        "inputs": {"interfaces": ["Ethernet1/1"], "max_transceiver_temperature": 70},
        "expected": {
            "result": AntaTestStatus.FAILURE,
            "messages": [
                "Interface: Ethernet1/1 - High transceiver temperature detected - Expected: <= 70.0°C Actual: 73.76°C",
            ],
        },
    },
    (VerifyInterfacesOpticsTemperature, "failure-specific-interface-details-not-found"): {
        "eos_data": [
            {
                "interfaces": {
                    "Ethernet25/8": {},
                    "Ethernet1/1": {"displayName": "Ethernet1/1", "parameters": {}},
                    "Ethernet1/2": {
                        "displayName": "Ethernet1/2",
                        "parameters": {
                            "temperature": {
                                "unit": "C",
                                "channels": {"-": 73.7575},
                            },
                        },
                    },
                }
            }
        ],
        "inputs": {"interfaces": ["Ethernet1/1"], "max_transceiver_temperature": 70},
        "expected": {
            "result": AntaTestStatus.FAILURE,
            "messages": [
                "Interface: Ethernet1/1 - Temperature details are not found (DOM not supported)",
            ],
        },
    },
    (VerifyInterfacesECNCounters, "success"): {
        "eos_data": [
            {
                "intfQueueCounters": {
                    "Ethernet10/28/1": {
                        "queueCounters": {
                            "0": "0",
                            "1": "0",
                            "2": "0",
                        },
                    },
                    "Ethernet10/20/1": {
                        "queueCounters": {
                            "0": "0",
                            "1": "0",
                            "2": "0",
                        },
                    },
                    "Ethernet10/16/1": {
                        "queueCounters": {
                            "0": "0",
                            "1": "0",
                            "2": "0",
                        },
                    },
                    "Ethernet10/3/1": {
                        "queueCounters": {
                            "0": "0",
                            "1": "0",
                            "2": "0",
                        },
                    },
                }
            }
        ],
        "expected": {"result": AntaTestStatus.SUCCESS},
    },
    (VerifyInterfacesECNCounters, "success-specific-interface"): {
        "eos_data": [
            {
                "intfQueueCounters": {
                    "Ethernet10/28/1": {
                        "queueCounters": {
                            "0": "0",
                            "1": "0",
                            "2": "0",
                        },
                    },
                    "Ethernet10/20/1": {
                        "queueCounters": {
                            "0": "0",
                            "1": "0",
                            "2": "0",
                        },
                    },
                    "Ethernet10/16/1": {
                        "queueCounters": {
                            "0": "-",
                            "1": "0",
                            "2": "0",
                        },
                    },
                    "Ethernet10/3/1": {
                        "queueCounters": {
                            "0": "-",
                            "1": "0",
                            "2": "0",
                        },
                    },
                }
            }
        ],
        "inputs": {"interfaces": ["Ethernet10/28/1", "Ethernet10/20/1"]},
        "expected": {"result": AntaTestStatus.SUCCESS},
    },
    (VerifyInterfacesECNCounters, "success-ignored-interface"): {
        "eos_data": [
            {
                "intfQueueCounters": {
                    "Ethernet10/28/1": {
                        "queueCounters": {
                            "0": "0",
                            "1": "0",
                            "2": "0",
                        },
                    },
                    "Ethernet10/20/1": {
                        "queueCounters": {
                            "0": "0",
                            "1": "0",
                            "2": "0",
                        },
                    },
                    "Ethernet10/16/1": {
                        "queueCounters": {
                            "0": "-",
                            "1": "0",
                            "2": "0",
                        },
                    },
                    "Ethernet10/3/1": {
                        "queueCounters": {
                            "0": "-",
                            "1": "0",
                            "2": "0",
                        },
                    },
                }
            }
        ],
        "inputs": {"ignored_interfaces": ["Ethernet10/16/1", "Ethernet10/3/1"]},
        "expected": {"result": AntaTestStatus.SUCCESS},
    },
    (VerifyInterfacesECNCounters, "failure"): {
        "eos_data": [
            {
                "intfQueueCounters": {
                    "Ethernet10/28/1": {
                        "queueCounters": {
                            "0": "-",
                            "1": "0",
                            "2": "0",
                        },
                    },
                    "Ethernet10/20/1": {
                        "queueCounters": {
                            "0": "0",
                            "1": "2",
                            "2": "0",
                        },
                    },
                    "Ethernet10/16/1": {
                        "queueCounters": {
                            "0": "0",
                            "1": "0",
                            "2": "-",
                        },
                    },
                    "Ethernet10/3/1": {
                        "queueCounters": {
                            "0": "0",
                            "1": "0",
                            "2": "2",
                        },
                    },
                }
            }
        ],
        "expected": {
            "result": AntaTestStatus.FAILURE,
            "messages": [
                "Interface: Ethernet10/20/1 Queue: 1 - Counters above threshold - Expected: <= 0 Actual: 2",
                "Interface: Ethernet10/3/1 Queue: 2 - Counters above threshold - Expected: <= 0 Actual: 2",
            ],
        },
    },
    (VerifyInterfacesECNCounters, "failure-specific-interface"): {
        "eos_data": [
            {
                "intfQueueCounters": {
                    "Ethernet10/20/1": {
                        "queueCounters": {
                            "0": "-",
                            "1": "-",
                            "2": "0",
                        },
                    },
                    "Ethernet10/16/1": {
                        "queueCounters": {
                            "0": "-",
                            "1": "0",
                            "2": "0",
                        },
                    },
                    "Ethernet10/3/1": {
                        "queueCounters": {
                            "0": "-",
                            "1": "0",
                            "2": "0",
                        },
                    },
                }
            }
        ],
        "inputs": {"interfaces": ["Ethernet10/28/1", "Ethernet10/20/1"]},
        "expected": {
            "result": AntaTestStatus.FAILURE,
            "messages": [
                "Interface: Ethernet10/28/1 - Not found",
            ],
        },
    },
    (VerifyInterfacesPFCCounters, "success"): {
        "eos_data": [
            {
                "interfaceCounters": {
                    "Ethernet3/1/1": {"rxFrames": 0, "txFrames": 0},
                    "Ethernet3/2/1": {"rxFrames": 0, "txFrames": 0},
                    "Ethernet3/3/1": {"rxFrames": 0, "txFrames": 0},
                    "Ethernet3/4/1": {"rxFrames": 0, "txFrames": 0},
                }
            }
        ],
        "expected": {"result": AntaTestStatus.SUCCESS},
    },
    (VerifyInterfacesPFCCounters, "success-specific-interface"): {
        "eos_data": [
            {
                "interfaceCounters": {
                    "Ethernet3/1/1": {"rxFrames": 0, "txFrames": 0},
                    "Ethernet3/2/1": {"rxFrames": 0, "txFrames": 0},
                    "Ethernet3/3/1": {"rxFrames": 2, "txFrames": 0},
                    "Ethernet3/4/1": {"rxFrames": 0, "txFrames": 2},
                }
            }
        ],
        "inputs": {"interfaces": ["Ethernet3/1/1", "Ethernet3/2/1"]},
        "expected": {"result": AntaTestStatus.SUCCESS},
    },
    (VerifyInterfacesPFCCounters, "success-ignored-interface"): {
        "eos_data": [
            {
                "interfaceCounters": {
                    "Ethernet3/1/1": {"rxFrames": 0, "txFrames": 0},
                    "Ethernet3/2/1": {"rxFrames": 0, "txFrames": 0},
                    "Ethernet3/3/1": {"rxFrames": 2, "txFrames": 0},
                    "Ethernet3/4/1": {"rxFrames": 0, "txFrames": 2},
                }
            }
        ],
        "inputs": {"ignored_interfaces": ["Ethernet3/3/1", "Ethernet3/4/1"]},
        "expected": {"result": AntaTestStatus.SUCCESS},
    },
    (VerifyInterfacesPFCCounters, "failure"): {
        "eos_data": [
            {
                "interfaceCounters": {
                    "Ethernet3/1/1": {"rxFrames": 1, "txFrames": 0},
                    "Ethernet3/2/1": {"rxFrames": 0, "txFrames": 2},
                    "Ethernet3/3/1": {"rxFrames": 2, "txFrames": 0},
                    "Ethernet3/4/1": {"rxFrames": 0, "txFrames": 1},
                }
            }
        ],
        "expected": {
            "result": AntaTestStatus.FAILURE,
            "messages": [
                "Interface: Ethernet3/1/1 - Counters above threshold - Expected: <= 0 Actual RX PFC: 1 Actual TX PFC: 0",
                "Interface: Ethernet3/2/1 - Counters above threshold - Expected: <= 0 Actual RX PFC: 0 Actual TX PFC: 2",
                "Interface: Ethernet3/3/1 - Counters above threshold - Expected: <= 0 Actual RX PFC: 2 Actual TX PFC: 0",
                "Interface: Ethernet3/4/1 - Counters above threshold - Expected: <= 0 Actual RX PFC: 0 Actual TX PFC: 1",
            ],
        },
    },
    (VerifyInterfacesPFCCounters, "failure-specific-interface"): {
        "eos_data": [
            {
                "interfaceCounters": {
                    "Ethernet3/2/1": {
                        "rxFrames": 1,
                        "txFrames": 2,
                    },
                    "Ethernet3/3/1": {"rxFrames": 2, "txFrames": 0},
                    "Ethernet3/4/1": {"rxFrames": 0, "txFrames": 2},
                }
            }
        ],
        "inputs": {"interfaces": ["Ethernet3/1/1", "Ethernet3/2/1"]},
        "expected": {
            "result": AntaTestStatus.FAILURE,
            "messages": [
                "Interface: Ethernet3/1/1 - Not found",
                "Interface: Ethernet3/2/1 - Counters above threshold - Expected: <= 0 Actual RX PFC: 1 Actual TX PFC: 2",
            ],
        },
    },
}
