# Copyright (c) 2023-2024 Arista Networks, Inc.
# Use of this source code is governed by the Apache License 2.0
# that can be found in the LICENSE file.

"""Arista platform utilities."""

from __future__ import annotations

import logging

from anta import GITHUB_SUGGESTION

logger = logging.getLogger(__name__)

SUPPORT_HARDWARE_COUNTERS_SERIES = ["7800R3", "7500R3", "7500R", "7280R3", "7280R2", "7280R"]

# TODO: For chassis, check if the hardware commands return the linecard model. If so, we can remove the chassis families from the list.
ARISTA_PLATFORMS = {
    "7800R3": {
        "chipsets": ["Ramon"],
        "families": [
            "7800R3",  # This is a linecard. The chipset is Jericho2
            "7800R3A",  # This is a linecard. The chipset is Jericho2C
            "7800R3K",  # This is a linecard. The chipset is Jericho2C
            "7816LR3",
            "7816R3",
            "7812R3",
            "7808R3",
            "7804R3",
        ],
    },
    "7500R3": {
        "chipsets": ["Ramon"],
        "families": [
            "7500R3",  # This is a linecard. The chipset is Jericho
            "7500R3K",  # This is a linecard. The chipset is Jericho2C
            "7512R3",
            "7508R3",
            "7504R3",
        ],
    },
    "7500R": {
        "chipsets": ["FE3600"],
        "families": [
            "7500R2"  # This is a linecard. The chipset is Jericho+
            "7516R",
            "7512R",
            "7508R",
            "7504R",
        ],
    },
    "7300X3": {
        "chipsets": ["Tomahawk"],
        "families": [
            "7300X3",  # This is a linecard. The chipset is Trident3X7
            "7308X3",
            "7304X3",
        ],
    },
    "7300X": {
        "chipsets": ["Trident2"],
        "families": [
            "7300X"  # This is a linecard. The chipset is Trident2
            "7316X"
            "7308X",
            "7304X",
        ],
    },
    "7388X5": {
        "chipsets": ["Tomahawk4"],
        "families": [
            "7388X5",
        ],
    },
    "7368X4": {
        "chipsets": ["Tomahawk3"],
        "families": [
            "7368X4",
        ],
    },
    "7280R3": {
        "chipsets": ["Jericho2", "Jericho2c", "Jericho2c+", "Qumran2C"],
        "families": [
            "7280DR3A",
            "7280R3A",
            "7280CR3A",
            "7280PR3",
            "7280DR3",
            "7280CR3MK",
            "7280CR3",
            "7280SR3A",
            "7280SR3",
        ],
    },
    "7280R2": {
        "chipsets": ["Jericho+", "Jericho2"],
        "families": [
            "7280CR2",
            "7280SR2",
        ],
    },
    "7280R": {
        "chipsets": ["Jericho", "Qumran-MX", "Arad+"],
        "families": [
            "7280CR",
            "7280QR",
            "7280SE",
            "7280SR",
            "7280TR",
        ],
    },
    "7170": {
        "chipsets": ["Tofino", "Tofino2"],
        "families": [
            "7170",
            "7170B",
        ],
    },
    "7130": {
        "chipsets": ["Jericho2"],
        "families": [
            "7130LBR",
            "7130B",
            "7132LB",
            "7135LB",
            "7130",
        ],
    },
    "7060X": {
        "chipsets": ["Tomahawk", "Tomahawk+", "Tomahawk3", "Tomahawk4"],
        "families": [
            "7060DX5",
            "7060PX5",
            "7060PX4",
            "7060DX4",
            "7060SX2",
            "7060CX2",
            "7060CX",
        ],
    },
    "7260X": {
        "chipsets": ["Tomahawk", "Tomahawk2"],
        "families": [
            "7260QX",
            "7260CX3",
            "7260CX",
        ],
    },
    "7358X4": {
        "chipsets": ["Trident4X11"],
        "families": [
            "7358X4",
        ],
    },
    "7050X4": {
        "chipsets": ["Trident4X9", "Trident4X11"],
        "families": [
            "7050PX4",
            "7050DX4",
            "7050SDX4",
            "7050SPX4",
            "7050CX4",
            "7050CX4M",
        ],
    },
    "7050X3": {
        "chipsets": ["Trident3X5", "Trident3X7"],
        "families": [
            "7050TX3",
            "7050SX3",
            "7050CX3M",
        ],
    },
    "7050X": {
        "chipsets": ["Trident2", "Trident2+"],
        "families": [
            "7050QX",
        ],
    },
    "7020TR": {
        "chipsets": ["Qumran-AX"],
        "families": [
            "7020SR",
            "7020TR",
            "7020TRA",
        ],
    },
    "7010TX": {
        "chipsets": ["Trident3X2"],
        "families": [
            "7010TX",
        ],
    },
    "750": {
        "chipsets": ["Firelight"],
        "families": [
            "750X",  # This is a linecard. The chipset is Firelight
        ],
    },
    "720X": {
        "chipsets": ["Trident3X3"],
        "families": [
            "720XP",
        ],
    },
    "720D": {
        "chipsets": ["Trident3X1, Trident3X2, Trident3X3"],
        "families": [
            "720DP",
            "720DT",
            "720DF",
        ],
    },
    "722XPM": {
        "chipsets": ["Trident3X2"],
        "families": [
            "722XPM",
        ],
    },
    "710P": {
        "chipsets": ["Trident3X1"],
        "families": [
            "710P",
        ],
    },
}


def find_series_by_model(model: str) -> str | None:
    """Get the series of a model based on the ARISTA_PLATFORMS dictionary."""
    for series, data in ARISTA_PLATFORMS.items():
        for family in data["families"]:
            if family in model:
                return series

    # If no match is found, we need to add a new family to the ARISTA_PLATFORMS dictionary
    logger.warning("Model %s series was not found in the ANTA Arista platforms database. %s", model, GITHUB_SUGGESTION)
    return None
