# Copyright (c) 2023-2024 Arista Networks, Inc.
# Use of this source code is governed by the Apache License 2.0
# that can be found in the LICENSE file.
"""Tests for `anta.custom_types`.

The intention is only to test here what is not used already in other places.

TODO: Expand later.
"""

from __future__ import annotations

import pytest

from anta.custom_types import bgp_multiprotocol_capabilities_abbreviations, interface_autocomplete


def test_interface_autocomplete_failure() -> None:
    """Trigger ValueError for interface_autocomplete."""
    with pytest.raises(ValueError, match="Could not parse interface ID in interface"):
        interface_autocomplete("ThisIsNotAnInterface")


@pytest.mark.parametrize(
    ("str_input", "expected_output"),
    [
        pytest.param("L2VPNEVPN", "l2VpnEvpn", id="l2VpnEvpn"),
        pytest.param("ipv4-mplsLabels", "ipv4MplsLabels", id="ipv4MplsLabels"),
        pytest.param("ipv4-mpls-vpn", "ipv4MplsVpn", id="ipv4MplsVpn"),
        pytest.param("ipv4-unicast", "ipv4Unicast", id="ipv4Unicast"),
        pytest.param("BLAH", "BLAH", id="unmatched"),
    ],
)
def test_bgp_multiprotocol_capabilities_abbreviationsh(str_input: str, expected_output: str) -> None:
    """Test bgp_multiprotocol_capabilities_abbreviations."""
    assert bgp_multiprotocol_capabilities_abbreviations(str_input) == expected_output
