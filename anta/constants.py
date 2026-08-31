# Copyright (c) 2023-2026 Arista Networks, Inc.
# Use of this source code is governed by the Apache License 2.0
# that can be found in the LICENSE file.
"""Constants used in ANTA."""

from __future__ import annotations

ACRONYM_CATEGORIES: set[str] = {
    "aaa",
    "anta",
    "avt",
    "bfd",
    "bgp",
    "igmp",
    "ip",
    "isis",
    "lanz",
    "lldp",
    "mlag",
    "ntp",
    "ospf",
    "ptp",
    "snmp",
    "stp",
    "stun",
    "vlan",
    "vxlan",
}
"""A set of network protocol or feature acronyms that should be represented in uppercase."""

MD_REPORT_TOC = """**Table of Contents:**

- [ANTA Report](#anta-report)
  - [Test Results Summary](#test-results-summary)
    - [Summary Totals](#summary-totals)
    - [Summary Totals Device Under Test](#summary-totals-device-under-test)
    - [Summary Totals Per Category](#summary-totals-per-category)
  - [Test Results](#test-results)"""
"""Table of Contents for the Markdown report."""

MD_REPORT_TOC_WITH_RUN_OVERVIEW = """**Table of Contents:**

- [ANTA Report](#anta-report)
  - [Run Overview](#run-overview)
  - [Test Results Summary](#test-results-summary)
    - [Summary Totals](#summary-totals)
    - [Summary Totals Device Under Test](#summary-totals-device-under-test)
    - [Summary Totals Per Category](#summary-totals-per-category)
  - [Test Results](#test-results)"""
"""Table of Contents for the Markdown report, including Run Overview."""

KNOWN_EOS_ERRORS = [
    r"BGP inactive",
    r"VRF '.*' is not active",
    r".* does not support IP",
    r"IS-IS (.*) is disabled because: .*",
    r"No source interface .*",
    r".*controller\snot\sready.*",
    r"could not run command",
    r"There seem to be no power supplies connected.",
    r"IP Routing table for VRF .*",
]
"""List of known EOS errors.

!!! failure "Generic EOS Error Handling"
    When catching these errors, **ANTA will fail the affected test** and report the error message.
"""

EOS_BLACKLIST_CMDS = [
    r"^reload.*",
    r"^conf.*",
    r"^wr.*",
]
"""List of blacklisted EOS commands.

!!! success "Disruptive commands safeguard"
    ANTA implements a mechanism to **prevent the execution of disruptive commands** such as `reload`, `write erase` or `configure terminal`.
"""

UNSUPPORTED_PLATFORM_ERROR_PREFIXES = (
    "Invalid input (at token ",
    "Incomplete command (at token ",
)
"""Error prefixes indicating commands unavailable on a given EOS platform."""

UNSUPPORTED_PLATFORM_ERROR_FRAGMENT = "not supported on this hardware platform"
"""Error fragment indicating a command unsupported by the device hardware.

!!! tip "Running EOS commands unsupported by hardware"
    When catching these errors, ANTA will skip the affected test and raise a warning. The **test catalog must be updated** to remove execution of the affected test
    on unsupported devices.
"""
