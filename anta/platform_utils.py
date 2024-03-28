# Copyright (c) 2023-2024 Arista Networks, Inc.
# Use of this source code is governed by the Apache License 2.0
# that can be found in the LICENSE file.

"""Arista platform utilities."""

from __future__ import annotations

import logging
import re
from typing import Any

from anta import GITHUB_SUGGESTION

logger = logging.getLogger(__name__)

SUPPORT_HARDWARE_COUNTERS_SERIES: list[str] = ["7800R3", "7500R3", "7500R", "7280R3", "7280R2", "7280R"]

TRIDENT_SERIES: list[str] = ["7300X3", "7300X", "7358X4", "7050X4", "7050X3", "7050X", "7010TX", "720X", "720D", "722XPM", "710P"]

VIRTUAL_PLATFORMS: list[str] = ["cEOSLab", "vEOS-lab", "cEOSCloudLab"]

HARDWARE_PLATFORMS: list[dict[str, Any]] = [
    # Data center chassis/modular series. These series support different modules; linecards, supervisors, fabrics, etc.
    # The modules of the system determine the series it belongs too, e.g. the 7800R3-36P-LC linecard belongs to the 7800R3 series.
    {
        "series": "7800R3",
        "families": [
            "7800R3",
            "7800R3K",
            "7800R3A",
            "7800R3AK",
        ],
    },
    {
        "series": "7500R3",
        "families": [
            "7500R3",
            "7500R3K",
        ],
    },
    {
        "series": "7500R",
        "families": [
            "7500R",
            "7500R2",
            "7500R2A",
            "7500R2AK",
            "7500R2AM",
            "7500R2M",
            "7500RM",
        ],
    },
    {
        "series": "7500E",
        "families": [
            "7500E",
        ],
    },
    {
        "series": "7300X3",
        "families": [
            "7300X3",
        ],
    },
    {
        "series": "7300X",
        "families": [
            "7300X",
        ],
    },
    {
        "series": "7388X5",
        "families": [
            "7388",
            "7388X5",
        ],
    },
    {
        "series": "7368X4",
        "families": [
            "7368",
            "7368X4",
        ],
    },
    {
        "series": "7358X4",
        "families": [
            "7358",
            "7358X4",
        ],
    },
    {
        "series": "7280R3",
        "families": [
            "7289",
            "7289R3A",
            "7289R3AK",
            "7289R3AM",
        ],
    },
    # Data center fixed series.
    {
        "series": "7280R3",
        "families": [
            "7280DR3A",
            "7280DR3AM",
            "7280DR3AK",
            "7280CR3A",
            "7280CR3AM",
            "7280CR3AK",
            "7280PR3",
            "7280PR3K",
            "7280DR3",
            "7280DR3K",
            "7280CR3MK",
            "7280CR3",
            "7280CR3K",
            "7280SR3A",
            "7280SR3AM",
            "7280SR3AK",
            "7280SR3M",
            "7280SR3MK",
            "7280SR3",
            "7280SR3K",
            "7280SR3E",
            "7280TR3",
        ],
    },
    {
        "series": "7280R2",
        "families": [
            "7280CR2",
            "7280CR2A",
            "7280CR2K",
            "7280CR2M",
            "7280SR2",
            "7280SR2A",
            "7280SR2K",
        ],
    },
    {
        "series": "7280R",
        "families": [
            "7280CR",
            "7280QR",
            "7280QRA",
            "7280SE",
            "7280SR",
            "7280SRA",
            "7280SRAM",
            "7280SRM",
            "7280TR",
            "7280TRA",
        ],
    },
    {
        "series": "7170",
        "families": [
            "7170",
            "7170B",
        ],
    },
    {
        "series": "7130",
        "families": [
            "7130LBR",
            "7130B",
            "7132LB",
            "7135LB",
            "7130",
        ],
    },
    {
        "series": "7060X",
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
    {
        "series": "7260X",
        "families": [
            "7260QX",
            "7260CX3",
            "7260CX",
        ],
    },
    {
        "series": "7050X4",
        "families": [
            "7050PX4",
            "7050DX4",
            "7050SDX4",
            "7050SPX4",
            "7050CX4",
            "7050CX4M",
        ],
    },
    {
        "series": "7050X3",
        "families": [
            "7050TX3",
            "7050SX3",
            "7050CX3",
            "7050CX3M",
        ],
    },
    {
        "series": "7050X",
        "families": [
            "7050QX",
        ],
    },
    {
        "series": "7020TR",
        "families": [
            "7020SR",
            "7020TR",
            "7020TRA",
        ],
    },
    {
        "series": "7010TX",
        "families": [
            "7010TX",
        ],
    },
    # Campus chassis/modular series.
    {
        "series": "750",
        "families": [
            "750",
            "750X",
        ],
    },
    # Campus fixed series.
    {
        "series": "720X",
        "families": [
            "720XP",
        ],
    },
    {
        "series": "720D",
        "families": [
            "720DP",
            "720DT",
            "720DF",
        ],
    },
    {
        "series": "722XPM",
        "families": [
            "722XPM",
        ],
    },
    {
        "series": "710P",
        "families": [
            "710P",
        ],
    },
]


def check_if_virtual_platform(platform: str) -> bool:
    """Check if the platform is a virtual platform.

    Arguments:
    ----------
        platform (str): The platform model to check.

    Returns
    -------
        bool: True if the platform is a virtual platform, otherwise False.

    Examples
    --------
    ```python
    >>> from anta.platform_utils import check_if_virtual_platform
    >>> check_if_virtual_platform(platform="vEOS-lab")
    True
    >>> check_if_virtual_platform(platform="DCS-7280CR3A-72-F")
    False
    ```
    """
    return platform in VIRTUAL_PLATFORMS


def find_series_by_modules(modules: dict[str, dict[str, Any]]) -> str | None:
    """TODO: Document this function."""
    regex_pattern = r"\b(\d{3,}\w*)\b"
    for module_data in modules.values():
        module_name = str(module_data.get("modelName"))

        # We extract the family from the module name, e.g. CCS-750X-48THP-LC -> 750X
        match = re.search(regex_pattern, module_name)
        if match:
            platform_family = match.group(1)
        else:
            logger.warning("Module %s does not match the expected Arista product name pattern. %s", module_name, GITHUB_SUGGESTION)
            continue

        for series in HARDWARE_PLATFORMS:
            for family in series["families"]:
                if family == platform_family:
                    return series["series"]

        # If no series is found, we need to add a new family to the HARDWARE_PLATFORMS dictionary
        logger.warning("Module %s series was not found in the ANTA hardware platforms database. %s", module_name, GITHUB_SUGGESTION)

    return None


def find_series_by_platform(platform: str) -> str | None:
    """Get the series of a platform based on the HARDWARE_PLATFORMS dictionary of this module.

    The function extract the family from the platform name and then searches for the series.

    If the platform is a virtual platform, the function will return the platform name as is.

    Arguments:
    ----------
        platform (str): The platform model to find the series for.

    Returns
    -------
        str | None: The series of the platform if found, otherwise None.

    Examples
    --------
    ```python
    >>> from anta.platform_utils import find_series_by_platform
    >>> find_series_by_platform(platform="DCS-7280CR3A-72-F")
    '7280R3'
    >>> find_series_by_platform(platform="cEOSLab")
    'cEOSLab'
    ```
    """
    # If the platform is a virtual platform, we return the platform name as is.
    if check_if_virtual_platform(platform):
        return platform

    # We extract the family from the platform name, e.g. DCS-7280CR3A-72-F -> 7280CR3A
    regex_pattern = r"\b(\d{3,}\w*)\b"
    match = re.search(regex_pattern, platform)

    if match:
        platform_family = match.group(1)
    else:
        logger.warning("Platform %s does not match the expected Arista product name pattern. %s", platform, GITHUB_SUGGESTION)
        return None

    for series in HARDWARE_PLATFORMS:
        for family in series["families"]:
            if family == platform_family:
                return series["series"]

    # If no series is found, we need to add a new family to the HARDWARE_PLATFORMS dictionary
    logger.warning("Platform %s series was not found in the ANTA hardware platforms database. %s", platform, GITHUB_SUGGESTION)
    return None
