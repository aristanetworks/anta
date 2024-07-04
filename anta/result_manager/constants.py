# Copyright (c) 2023-2024 Arista Networks, Inc.
# Use of this source code is governed by the Apache License 2.0
# that can be found in the LICENSE file.
"""Constants used for reporting in ANTA."""

from __future__ import annotations

ACRONYM_CATEGORIES: set[str] = {"aaa", "mlag", "snmp", "bgp", "ospf", "vxlan", "stp", "igmp", "ip", "lldp", "ntp", "bfd", "ptp", "lanz", "stun", "vlan"}
"""A set of network protocol or feature acronyms that should be represented in uppercase in the eos_validate_state report."""

STAT_MAPPING = {
    "success": "tests_passed",
    "failure": "tests_failed",
    "error": "tests_failed",
    "unset": "tests_failed",
    "skipped": "tests_skipped",
}
"""Mapping of test result status to the corresponding statistics counter."""
