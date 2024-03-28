# Copyright (c) 2023-2024 Arista Networks, Inc.
# Use of this source code is governed by the Apache License 2.0
# that can be found in the LICENSE file.

"""Arista platform utilities."""

from __future__ import annotations

import logging
import re

from anta import GITHUB_SUGGESTION

logger = logging.getLogger(__name__)

SUPPORT_HARDWARE_COUNTERS_SERIES = ["7800R3", "7500R3", "7500R", "7280R3", "7280R2", "7280R"]

VIRTUAL_PLATFORMS = ["cEOSLab", "vEOS-lab", "cEOSCloudLab"]

HARDWARE_PLATFORMS = [
    # Data center chassis families. These series can have the same families but support different modules; linecards, supervisors, fabrics, etc.
    # The components of the system determine the series it belongs too. Chassis can also support linecards from different families.
    {
        "series": "7800R3",
        "families": [
            "7816",
            "7816B",
            "7812",
            "7808",
            "7804",
        ],
    },
    {
        "series": "7500R3",
        "families": [
            "7512N",
            "7508",
            "7508N",
            "7504",
            "7504N",
        ],
    },
    {
        "series": "7500R",
        "families": [
            "7516N",
            "7512N",
            "7508",
            "7508N",
            "7504",
            "7504N",
        ],
    },
    {
        "series": "7300X3",
        "families": [
            "7308",
            "7304",
        ],
    },
    {
        "series": "7300X",
        "families": [
            "7316",
            "7308",
            "7304",
        ],
    },
    {
        "series": "7388X5",
        "families": [
            "7388",
        ],
    },
    {
        "series": "7368X4",
        "families": [
            "7368",
        ],
    },
    {
        "series": "7358X4",
        "families": [
            "7358",
        ],
    },
    {
        "series": "7280R3",
        "families": [
            "7289",
        ],
    },
    # Data center fixed families.
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
            "7280DR3K"
            "7280CR3MK",
            "7280CR3",
            "7280CR3K",
            "7280SR3A",
            "7280SR3AM",
            "7280SR3AK",
            "7280SR3M"
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
    # Campus chassis families.
    {
        "series": "750",
        "families": [
            "755",
            "758",
        ],
    },
    # Campus fixed families.
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

def find_series_by_platform(platform: str) -> str | None:
    """Get the series of a platform based on the HARDWARE_PLATFORMS dictionary.

    The function extract the family from the platform name. Some chassis and modular systems do not have the DCS/CCS prefix, so we need to handle this case.

    !!! warning
        The virtual platforms are not supported by this function. You should use the `check_if_virtual_platform` function to check if the platform is virtual.

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
    >>> find_series_by_platform(platform="7368-F")
    '7368X4'
    >>> find_series_by_platform(platform="CCS-755-CH")
    '750'
    >>> find_series_by_platform(platform="DCS-7280CR3A-72-F")
    '7280R3'
    ```
    """
    regex_pattern = r"(?:DCS|CCS)-(.+?)-" if platform.startswith(("DCS-", "CCS-")) else r"(.+?)(?=-)"
    match = re.search(regex_pattern, platform)

    if match:
        platform_family = match.group(1)
    else:
        logger.warning("Platform %s does not match the expected Arista product name pattern. %s", platform, GITHUB_SUGGESTION)
        return None

    for series in HARDWARE_PLATFORMS:
        interesting_list = series.get("families", series.get("families"))
        for item in interesting_list:
            if item == platform_family:
                return series["series"]

    # If no match is found, we need to add a new family to the HARDWARE_PLATFORMS dictionary
    logger.warning("Platform %s series was not found in the ANTA Arista platforms database. %s", platform, GITHUB_SUGGESTION)
    return None
