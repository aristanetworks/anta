# Copyright (c) 2026 Arista Networks, Inc.
# Use of this source code is governed by the Apache License 2.0
# that can be found in the LICENSE file.
"""Platform-family unit tests for Arista Security Advisory 219."""

from __future__ import annotations

import pytest

from anta._advisory.facts.eos import EosVersionFact
from anta._advisory.facts.ip_security import IpsecKeyControllerFact, IpsecSaAntiReplayFact
from anta._advisory.facts.models import FactSource, FactSourceKind, FeatureState
from anta._advisory.facts.platform import PlatformIdentityFact
from anta._advisory.findings.models import AffectedResult, NotAffectedResult
from anta._eos.platform import PlatformFamily, PlatformType
from anta._eos.version import EOSVersion
from anta.tests.advisories.sa_219 import _assess_sa219


@pytest.mark.parametrize("family", list(PlatformFamily))
def test_source_platform_families(family: PlatformFamily) -> None:
    """Only the three source-listed families are affected for unambiguous identity."""
    source = FactSource("unit test", FactSourceKind.DEVICE_METADATA)
    identity = PlatformIdentityFact(model=family.value, type=PlatformType.APPLIANCE, modules=(), platform_families=frozenset({family}))
    finding = _assess_sa219(
        EosVersionFact.from_version(EOSVersion(4, 35, 0, suffix="F")).available(source),
        identity.available(source),
        IpsecKeyControllerFact(FeatureState.ENABLED).available(source),
        IpsecSaAntiReplayFact(FeatureState.ENABLED).available(source),
    )
    source_affected = family in {PlatformFamily.AWE_5000, PlatformFamily.AWE_7200_R, PlatformFamily.CLOUDEOS}
    assert isinstance(finding, AffectedResult if source_affected else NotAffectedResult)
