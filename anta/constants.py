# Copyright (c) 2023-2025 Arista Networks, Inc.
# Use of this source code is governed by the Apache License 2.0
# that can be found in the LICENSE file.
"""Constants used in ANTA."""

from __future__ import annotations

ACRONYM_CATEGORIES: set[str] = {
    "aaa",
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

KNOWN_EOS_ERRORS = [
    r"BGP inactive",
    r"VRF '.*' is not active",
    r".* does not support IP",
    r"IS-IS (.*) is disabled because: .*",
    r"No source interface .*",
]
"""List of known EOS errors that should set a test status to 'failure' with the error message."""
