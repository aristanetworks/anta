# Copyright (c) 2023-2025 Arista Networks, Inc.
# Use of this source code is governed by the Apache License 2.0
# that can be found in the LICENSE file.
"""Tests for `anta.custom_types`.

The intention is only to test here what is not used already in other places.

TODO: Expand later.
"""

from __future__ import annotations

import re

import pytest

from anta.custom_types import (
    REGEX_TYPE_PORTCHANNEL,
    REGEXP_INTERFACE_ID,
    REGEXP_PATH_MARKERS,
    REGEXP_TYPE_EOS_INTERFACE,
    REGEXP_TYPE_HOSTNAME,
    REGEXP_TYPE_VXLAN_SRC_INTERFACE,
    aaa_group_prefix,
    bgp_multiprotocol_capabilities_abbreviations,
    interface_autocomplete,
    interface_case_sensitivity,
    snmp_v3_prefix,
    validate_regex,
)

# ------------------------------------------------------------------------------
# TEST custom_types.py regular expressions
# ------------------------------------------------------------------------------


def test_regexp_path_markers() -> None:
    """Test REGEXP_PATH_MARKERS."""
    # Test strings that should match the pattern
    assert re.search(REGEXP_PATH_MARKERS, "show/bgp/interfaces") is not None
    assert re.search(REGEXP_PATH_MARKERS, "show\\bgp") is not None
    assert re.search(REGEXP_PATH_MARKERS, "show bgp") is not None

    # Test strings that should not match the pattern
    assert re.search(REGEXP_PATH_MARKERS, "aaaa") is None
    assert re.search(REGEXP_PATH_MARKERS, "11111") is None
    assert re.search(REGEXP_PATH_MARKERS, ".[]?<>") is None


def test_regexp_type_interface_id() -> None:
    """Test REGEXP_INTERFACE_ID."""
    intf_id_re = re.compile(f"{REGEXP_INTERFACE_ID}")

    # Test strings that should match the pattern
    assert intf_id_re.search("123") is not None
    assert intf_id_re.search("123/456") is not None
    assert intf_id_re.search("123.456") is not None
    assert intf_id_re.search("123/456.789") is not None


def test_regexp_type_eos_interface() -> None:
    """Test REGEXP_TYPE_EOS_INTERFACE."""
    # Test strings that should match the pattern
    assert re.match(REGEXP_TYPE_EOS_INTERFACE, "Ethernet0") is not None
    assert re.match(REGEXP_TYPE_EOS_INTERFACE, "Vlan100") is not None
    assert re.match(REGEXP_TYPE_EOS_INTERFACE, "Port-Channel1/0") is not None
    assert re.match(REGEXP_TYPE_EOS_INTERFACE, "Loopback0.1") is not None
    assert re.match(REGEXP_TYPE_EOS_INTERFACE, "Management0/0/0") is not None
    assert re.match(REGEXP_TYPE_EOS_INTERFACE, "Tunnel1") is not None
    assert re.match(REGEXP_TYPE_EOS_INTERFACE, "Vxlan1") is not None
    assert re.match(REGEXP_TYPE_EOS_INTERFACE, "Fabric1") is not None
    assert re.match(REGEXP_TYPE_EOS_INTERFACE, "Dps1") is not None

    # Test strings that should not match the pattern
    assert re.match(REGEXP_TYPE_EOS_INTERFACE, "Ethernet") is None
    assert re.match(REGEXP_TYPE_EOS_INTERFACE, "Vlan") is None
    assert re.match(REGEXP_TYPE_EOS_INTERFACE, "Port-Channel") is None
    assert re.match(REGEXP_TYPE_EOS_INTERFACE, "Loopback.") is None
    assert re.match(REGEXP_TYPE_EOS_INTERFACE, "Management/") is None
    assert re.match(REGEXP_TYPE_EOS_INTERFACE, "Tunnel") is None
    assert re.match(REGEXP_TYPE_EOS_INTERFACE, "Vxlan") is None
    assert re.match(REGEXP_TYPE_EOS_INTERFACE, "Fabric") is None
    assert re.match(REGEXP_TYPE_EOS_INTERFACE, "Dps") is None

    assert re.match(REGEXP_TYPE_EOS_INTERFACE, "Ethernet1/a") is None
    assert re.match(REGEXP_TYPE_EOS_INTERFACE, "Port-Channel-100") is None
    assert re.match(REGEXP_TYPE_EOS_INTERFACE, "Loopback.10") is None
    assert re.match(REGEXP_TYPE_EOS_INTERFACE, "Management/10") is None


def test_regexp_type_vxlan_src_interface() -> None:
    """Test REGEXP_TYPE_VXLAN_SRC_INTERFACE."""
    # Test strings that should match the pattern
    assert re.match(REGEXP_TYPE_VXLAN_SRC_INTERFACE, "Loopback0") is not None
    assert re.match(REGEXP_TYPE_VXLAN_SRC_INTERFACE, "Loopback1") is not None
    assert re.match(REGEXP_TYPE_VXLAN_SRC_INTERFACE, "Loopback99") is not None
    assert re.match(REGEXP_TYPE_VXLAN_SRC_INTERFACE, "Loopback100") is not None
    assert re.match(REGEXP_TYPE_VXLAN_SRC_INTERFACE, "Loopback8190") is not None
    assert re.match(REGEXP_TYPE_VXLAN_SRC_INTERFACE, "Loopback8199") is not None

    # Test strings that should not match the pattern
    assert re.match(REGEXP_TYPE_VXLAN_SRC_INTERFACE, "Loopback") is None
    assert re.match(REGEXP_TYPE_VXLAN_SRC_INTERFACE, "Loopback9001") is None
    assert re.match(REGEXP_TYPE_VXLAN_SRC_INTERFACE, "Loopback9000") is None


def test_regexp_type_portchannel() -> None:
    """Test REGEX_TYPE_PORTCHANNEL."""
    # Test strings that should match the pattern
    assert re.match(REGEX_TYPE_PORTCHANNEL, "Port-Channel5") is not None
    assert re.match(REGEX_TYPE_PORTCHANNEL, "Port-Channel100") is not None
    assert re.match(REGEX_TYPE_PORTCHANNEL, "Port-Channel999") is not None
    assert re.match(REGEX_TYPE_PORTCHANNEL, "Port-Channel1000") is not None

    # Test strings that should not match the pattern
    assert re.match(REGEX_TYPE_PORTCHANNEL, "Port-Channel") is None
    assert re.match(REGEX_TYPE_PORTCHANNEL, "Port_Channel") is None
    assert re.match(REGEX_TYPE_PORTCHANNEL, "Port_Channel1000") is None
    assert re.match(REGEX_TYPE_PORTCHANNEL, "Port_Channel5/1") is None
    assert re.match(REGEX_TYPE_PORTCHANNEL, "Port-Channel-100") is None


def test_regexp_type_hostname() -> None:
    """Test REGEXP_TYPE_HOSTNAME."""
    # Test strings that should match the pattern
    assert re.match(REGEXP_TYPE_HOSTNAME, "hostname") is not None
    assert re.match(REGEXP_TYPE_HOSTNAME, "hostname.com") is not None
    assert re.match(REGEXP_TYPE_HOSTNAME, "host-name.com") is not None
    assert re.match(REGEXP_TYPE_HOSTNAME, "host.name.com") is not None
    assert re.match(REGEXP_TYPE_HOSTNAME, "host-name1.com") is not None

    # Test strings that should not match the pattern
    assert re.match(REGEXP_TYPE_HOSTNAME, "-hostname.com") is None
    assert re.match(REGEXP_TYPE_HOSTNAME, ".hostname.com") is None
    assert re.match(REGEXP_TYPE_HOSTNAME, "hostname-.com") is None
    assert re.match(REGEXP_TYPE_HOSTNAME, "hostname..com") is None


# ------------------------------------------------------------------------------
# TEST custom_types.py functions
# ------------------------------------------------------------------------------


def test_interface_autocomplete_success() -> None:
    """Test interface_autocomplete with valid inputs."""
    assert interface_autocomplete("et1") == "Ethernet1"
    assert interface_autocomplete("et1/1") == "Ethernet1/1"
    assert interface_autocomplete("et1.1") == "Ethernet1.1"
    assert interface_autocomplete("et1/1.1") == "Ethernet1/1.1"
    assert interface_autocomplete("eth2") == "Ethernet2"
    assert interface_autocomplete("po3") == "Port-Channel3"
    assert interface_autocomplete("lo4") == "Loopback4"
    assert interface_autocomplete("Po1000") == "Port-Channel1000"
    assert interface_autocomplete("Po 1000") == "Port-Channel1000"
    assert interface_autocomplete("Vl1000") == "Vlan1000"


def test_interface_autocomplete_no_alias() -> None:
    """Test interface_autocomplete with inputs that don't have aliases."""
    assert interface_autocomplete("GigabitEthernet1") == "GigabitEthernet1"
    assert interface_autocomplete("Vlan10") == "Vlan10"
    assert interface_autocomplete("Tunnel100") == "Tunnel100"


def test_interface_autocomplete_failure() -> None:
    """Trigger ValueError for interface_autocomplete."""
    with pytest.raises(ValueError, match="Could not parse interface ID in interface"):
        interface_autocomplete("ThisIsNotAnInterface")


@pytest.mark.parametrize(
    ("str_input", "expected_output"),
    [
        pytest.param("L2VPNEVPN", "l2VpnEvpn", id="l2VpnEvpn"),
        pytest.param("IPv4 Labeled Unicast", "ipv4MplsLabels", id="ipv4MplsLabels"),
        pytest.param("ipv4-mpls-vpn", "ipv4MplsVpn", id="ipv4MplsVpn"),
        pytest.param("ipv4_unicast", "ipv4Unicast", id="ipv4Unicast"),
        pytest.param("ipv4 Mvpn", "ipv4Mvpn", id="ipv4Mvpn"),
        pytest.param("ipv4_Flow-Spec Vpn", "ipv4FlowSpecVpn", id="ipv4FlowSpecVpn"),
        pytest.param("Dynamic-Path-Selection", "dps", id="dps"),
        pytest.param("ipv6unicast", "ipv6Unicast", id="ipv6Unicast"),
        pytest.param("IPv4-Multicast", "ipv4Multicast", id="ipv4Multicast"),
        pytest.param("IPv6_multicast", "ipv6Multicast", id="ipv6Multicast"),
        pytest.param("ipv6_Mpls-Labels", "ipv6MplsLabels", id="ipv6MplsLabels"),
        pytest.param("IPv4_SR_TE", "ipv4SrTe", id="ipv4SrTe"),
        pytest.param("iPv6-sR-tE", "ipv6SrTe", id="ipv6SrTe"),
        pytest.param("ipv6_mpls-vpn", "ipv6MplsVpn", id="ipv6MplsVpn"),
        pytest.param("IPv4 Flow-spec", "ipv4FlowSpec", id="ipv4FlowSpec"),
        pytest.param("IPv6Flow_spec", "ipv6FlowSpec", id="ipv6FlowSpec"),
        pytest.param("ipv6 Flow-Spec Vpn", "ipv6FlowSpecVpn", id="ipv6FlowSpecVpn"),
        pytest.param("L2VPN VPLS", "l2VpnVpls", id="l2VpnVpls"),
        pytest.param("link-state", "linkState", id="linkState"),
        pytest.param("RT_Membership", "rtMembership", id="rtMembership"),
        pytest.param("ipv4-RT_Membership", "rtMembership", id="rtMembership"),
    ],
)
def test_bgp_multiprotocol_capabilities_abbreviations(str_input: str, expected_output: str) -> None:
    """Test bgp_multiprotocol_capabilities_abbreviations."""
    assert bgp_multiprotocol_capabilities_abbreviations(str_input) == expected_output


def test_aaa_group_prefix_known_method() -> None:
    """Test aaa_group_prefix with a known method."""
    assert aaa_group_prefix("local") == "local"
    assert aaa_group_prefix("none") == "none"
    assert aaa_group_prefix("logging") == "logging"


def test_aaa_group_prefix_unknown_method() -> None:
    """Test aaa_group_prefix with an unknown method."""
    assert aaa_group_prefix("demo") == "group demo"
    assert aaa_group_prefix("group1") == "group group1"


def test_interface_case_sensitivity_lowercase() -> None:
    """Test interface_case_sensitivity with lowercase inputs."""
    assert interface_case_sensitivity("ethernet") == "Ethernet"
    assert interface_case_sensitivity("vlan") == "Vlan"
    assert interface_case_sensitivity("loopback") == "Loopback"


def test_interface_case_sensitivity_mixed_case() -> None:
    """Test interface_case_sensitivity with mixed case inputs."""
    assert interface_case_sensitivity("Ethernet") == "Ethernet"
    assert interface_case_sensitivity("Vlan") == "Vlan"
    assert interface_case_sensitivity("Loopback") == "Loopback"


def test_interface_case_sensitivity_uppercase() -> None:
    """Test interface_case_sensitivity with uppercase inputs."""
    assert interface_case_sensitivity("ETHERNET") == "ETHERNET"
    assert interface_case_sensitivity("VLAN") == "VLAN"
    assert interface_case_sensitivity("LOOPBACK") == "LOOPBACK"


@pytest.mark.parametrize(
    "str_input",
    [
        REGEX_TYPE_PORTCHANNEL,
        REGEXP_INTERFACE_ID,
        REGEXP_PATH_MARKERS,
        REGEXP_TYPE_EOS_INTERFACE,
        REGEXP_TYPE_HOSTNAME,
        REGEXP_TYPE_VXLAN_SRC_INTERFACE,
    ],
)
def test_validate_regex_valid(str_input: str) -> None:
    """Test validate_regex with valid regex."""
    assert validate_regex(str_input) == str_input


@pytest.mark.parametrize(
    ("str_input", "error"),
    [
        pytest.param("[", "Invalid regex: unterminated character set at position 0", id="unterminated character"),
        pytest.param("\\", r"Invalid regex: bad escape \(end of pattern\) at position 0", id="bad escape"),
    ],
)
def test_validate_regex_invalid(str_input: str, error: str) -> None:
    """Test validate_regex with invalid regex."""
    with pytest.raises(ValueError, match=error):
        validate_regex(str_input)


def test_snmp_v3_prefix_valid_input() -> None:
    """Test snmp_v3_prefix with valid authentication type."""
    assert snmp_v3_prefix("auth") == "v3Auth"
    assert snmp_v3_prefix("noauth") == "v3NoAuth"
    assert snmp_v3_prefix("priv") == "v3Priv"
