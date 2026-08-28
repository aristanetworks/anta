# Copyright (c) 2026 Arista Networks, Inc.
# Use of this source code is governed by the Apache License 2.0
# that can be found in the LICENSE file.
"""Shared EOS platform-family patterns for security advisory tests."""

from __future__ import annotations

import re
from enum import Enum


class PlatformFamily(Enum):
    """Atomic platform families used by security advisories."""

    SERIES_720_D = "720D Series"
    SERIES_720_XP = "720XP Series"
    SERIES_722_XPM = "722XPM Series"
    SERIES_755_758 = "755/758 Series"
    SERIES_7010 = "7010 Series"
    SERIES_7010_X = "7010X Series"
    SERIES_7020_R = "7020R Series"
    SERIES_7160 = "7160 Series"
    SERIES_7050_X = "7050X Series"
    SERIES_7050_X2 = "7050X2 Series"
    SERIES_7050_X3 = "7050X3 Series"
    SERIES_7050_X4 = "7050X4 Series"
    SERIES_7060_X = "7060X Series"
    SERIES_7060_X2 = "7060X2 Series"
    SERIES_7060_X4 = "7060X4 Series"
    SERIES_7060_X5 = "7060X5 Series"
    SERIES_7060_X6 = "7060X6 Series"
    SERIES_7250_X = "7250X Series"
    SERIES_7260_X = "7260X Series"
    SERIES_7260_X3 = "7260X3 Series"
    SERIES_7280_E = "7280E Series"
    SERIES_7280_R = "7280R Series"
    SERIES_7280_R2 = "7280R2 Series"
    SERIES_7280_R3 = "7280R3 Series"
    SERIES_7280_R4 = "7280R4 Series"
    SERIES_7368_X4 = "7368X4 Series"


PLATFORM_FAMILY_PATTERNS: dict[PlatformFamily, tuple[re.Pattern[str], ...]] = {
    PlatformFamily.SERIES_720_D: (re.compile(r"^CCS-720D[FTP]-.*$"),),
    PlatformFamily.SERIES_720_XP: (re.compile(r"^CCS-720XP-.*$"),),
    PlatformFamily.SERIES_722_XPM: (re.compile(r"^CCS-722XPM-.*$"),),
    PlatformFamily.SERIES_755_758: (re.compile(r"^CCS-75[58]-CH.*$"),),
    PlatformFamily.SERIES_7010: (re.compile(r"^DCS-7010T-.*$"),),
    PlatformFamily.SERIES_7010_X: (re.compile(r"^DCS-7010TX-.*$"),),
    PlatformFamily.SERIES_7020_R: (re.compile(r"^DCS-7020[ST]R[A-Z]*-.*$"),),
    PlatformFamily.SERIES_7160: (re.compile(r"^DCS-7160-.*$"),),
    PlatformFamily.SERIES_7050_X: (re.compile(r"^DCS-7050[A-Z]*X(?!\d).*$"),),
    PlatformFamily.SERIES_7050_X2: (re.compile(r"^DCS-7050[A-Z]*X2.*$"),),
    PlatformFamily.SERIES_7050_X3: (re.compile(r"^DCS-7050[A-Z]*X3.*$"),),
    PlatformFamily.SERIES_7050_X4: (re.compile(r"^DCS-7050[A-Z]*X4.*$"),),
    PlatformFamily.SERIES_7060_X: (re.compile(r"^DCS-7060[A-Z]*X(?!\d).*$"),),
    PlatformFamily.SERIES_7060_X2: (re.compile(r"^DCS-7060[A-Z]*X2.*$"),),
    PlatformFamily.SERIES_7060_X4: (re.compile(r"^DCS-7060[A-Z]*X4.*$"),),
    PlatformFamily.SERIES_7060_X5: (re.compile(r"^DCS-7060[A-Z]*X5.*$"),),
    PlatformFamily.SERIES_7060_X6: (re.compile(r"^DCS-7060[A-Z]*X6.*$"),),
    PlatformFamily.SERIES_7250_X: (re.compile(r"^DCS-7250[A-WY-Z]*X.*$"),),
    PlatformFamily.SERIES_7260_X: (re.compile(r"^DCS-7260[A-Z]*X(?!\d).*$"),),
    PlatformFamily.SERIES_7260_X3: (re.compile(r"^DCS-7260[A-Z]*X3.*$"),),
    PlatformFamily.SERIES_7280_E: (re.compile(r"^DCS-7280SE-.*$"),),
    PlatformFamily.SERIES_7280_R: (re.compile(r"^DCS-7280[CQST]R(?!\d).*$"),),
    PlatformFamily.SERIES_7280_R2: (re.compile(r"^DCS-7280[CS]R2.*$"),),
    PlatformFamily.SERIES_7280_R3: (re.compile(r"^DCS-7280[CDPST]R3.*$"),),
    PlatformFamily.SERIES_7280_R4: (re.compile(r"^DCS-7280R4.*$"),),
    PlatformFamily.SERIES_7368_X4: (re.compile(r"^7368(?:-[FR])?$"),),
}


def patterns_for(*families: PlatformFamily) -> tuple[re.Pattern[str], ...]:
    """Return the combined patterns for the requested platform families."""
    return tuple(pattern for family in families for pattern in PLATFORM_FAMILY_PATTERNS[family])
