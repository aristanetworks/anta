# Copyright (c) 2023-2024 Arista Networks, Inc.
# Use of this source code is governed by the Apache License 2.0
# that can be found in the LICENSE file.

"""Arista platform utilities."""

from __future__ import annotations

import logging

from anta import GITHUB_SUGGESTION

logger = logging.getLogger(__name__)

SUPPORT_HARDWARE_COUNTERS_SERIES = ["7500R3", "7500R", "7280R3"]
SUPPORT_VXLAN_COUNTERS_SERIES = ["7500R3", "7500R", "7280R3", "7050X3"]
SUPPORT_VNI_COUNTERS_SERIES = ["7050X3"]

ARISTA_PLATFORMS = {
    "7050X3": {
        "chipset": "Trident3",
        "families": [
            "7050TX3",
            "7050SX3",
            "7050CX3M",
        ],
    },
    "7280R3": {
        "chipset": "Jericho2",
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
}

def get_model_series(model: str) -> str | None:
    """Get an Arista model series based on the model name."""
    for series, data in ARISTA_PLATFORMS.items():
        for family in data["families"]:
            if family in model:
                return series

    # If no match is found, we need to add a new family to the ARISTA_PLATFORMS dictionary
    logger.warning("Model %s series was not found in the ANTA Arista platforms database. %s", model, GITHUB_SUGGESTION)
    return None
