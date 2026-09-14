# Copyright (c) 2026 Arista Networks, Inc.
# Use of this source code is governed by the Apache License 2.0
# that can be found in the LICENSE file.
# ruff: noqa: D102
# pylint: disable=duplicate-code, missing-function-docstring
"""Unit tests for Arista Security Advisory 151."""

from __future__ import annotations

import unittest
from functools import partial
from typing import TYPE_CHECKING

from anta._advisory.eos_versions import AffectedStatus, evaluate_version
from anta._advisory.facts.acl import SharedSviIngressAclFact
from anta._advisory.facts.eos import EosVersionFact
from anta._advisory.facts.models import (
    ConfigurationState,
    ConfigurationValue,
    Fact,
    FactProblemKind,
    FactSource,
    FactSourceKind,
    FeatureName,
    SubFeature,
)
from anta._advisory.facts.platform import PlatformIdentityFact
from anta._advisory.findings.models import AffectedResult, ErrorResult, NotAffectedResult
from anta._advisory.remediation import FixedRelease, software_version_plan
from anta._eos.platform import PlatformIdentity
from anta._eos.version import EOSVersion, parse_eos_version
from anta.result_manager.models import AntaTestStatus
from anta.tests.advisories.sa_151 import ADVISORY, AFFECTED_VERSION_MATRIX, SA151, _assess_sa151
from tests.units._advisory.facts.test_acl import EMPTY_ACL_OUTPUT, SHARED_ACL_OUTPUT
from tests.units.anta_tests import build_eos_platform, build_eos_version, test
from tests.units.anta_tests.advisories import build_expected_advisory_result

if TYPE_CHECKING:
    from tests.units.anta_tests import AntaUnitTestData

SOURCE = FactSource("unit test", FactSourceKind.DEVICE_METADATA)
EXPECTED_REMEDIATION = software_version_plan(
    (
        FixedRelease(EOSVersion(4, 36, 1, suffix="F")),
        FixedRelease(EOSVersion(4, 35, 5, suffix="M")),
        FixedRelease(EOSVersion(4, 34, 7, suffix="M")),
        FixedRelease(EOSVersion(4, 33, 9, suffix="M")),
    ),
    current_version=EOSVersion(4, 35, 4, suffix="M"),
)
expected = partial(build_expected_advisory_result, ADVISORY.vulnerabilities[0].id)


DATA: AntaUnitTestData = {
    (SA151, "affected-shared-acl"): {
        "version": build_eos_version("4.35.4M"),
        "platform": build_eos_platform("CCS-755-CH-F"),
        "eos_data": [SHARED_ACL_OUTPUT],
        "expected": expected(
            AntaTestStatus.FAILURE,
            "The device is affected because EOS version '4.35.4M' is affected, platform "
            "'CCS-755-CH-F' is within the affected platform scope, and the ACL shared SVI ingress configuration is configured",
            EXPECTED_REMEDIATION,
        ),
    },
    (SA151, "not-affected-no-shared-acl"): {
        "version": None,
        "platform": None,
        "eos_data": [EMPTY_ACL_OUTPUT],
        "expected": expected(AntaTestStatus.SUCCESS, "The device is not affected because the ACL shared SVI ingress configuration is not configured", None),
    },
    (SA151, "not-affected-platform"): {
        "version": build_eos_version("4.35.4M"),
        "platform": build_eos_platform("DCS-7280CR3"),
        "eos_data": [""],
        "expected": expected(AntaTestStatus.SUCCESS, "The device is not affected because platform 'DCS-7280CR3' is outside the affected platform scope", None),
    },
    (SA151, "not-affected-fixed-version"): {
        "version": build_eos_version("4.35.5M"),
        "platform": None,
        "eos_data": [""],
        "expected": expected(AntaTestStatus.SUCCESS, "The device is not affected because EOS version '4.35.5M' is outside the affected releases", None),
    },
    (SA151, "error-invalid-platform-command"): {
        "version": build_eos_version("4.35.4M"),
        "platform": build_eos_platform("CCS-755-CH-F"),
        "eos_data": [""],
        "expected": expected(
            AntaTestStatus.ERROR,
            "The test could not determine the shared SVI ingress ACL configuration because the 'show platform trident tcam acl' output is invalid",
            None,
        ),
    },
}


def version_fact(value: str) -> Fact[EOSVersion]:
    """Build an EOS version fact."""
    parsed = parse_eos_version(value).unwrap()
    return EosVersionFact.available(parsed, SOURCE)


def platform_fact(value: str):  # noqa: ANN201
    """Build a platform fact."""
    platform = build_eos_platform(value)
    assert platform is not None
    return PlatformIdentityFact.available(platform, SOURCE)


def acl_fact(state: ConfigurationState):  # noqa: ANN201
    """Build a shared SVI ingress ACL fact."""
    return SharedSviIngressAclFact.available(ConfigurationValue(SubFeature(FeatureName.ACL, "shared SVI ingress"), state), SOURCE)


class TestSA151Assessment(unittest.TestCase):
    """Validate pure assessment branches."""

    def test_version_boundaries(self) -> None:
        """Validate every affected and adjacent release boundary."""
        for version, state in (
            ("4.36.0F", AffectedStatus.AFFECTED),
            ("4.36.1F", AffectedStatus.NOT_AFFECTED),
            ("4.35.4M", AffectedStatus.AFFECTED),
            ("4.35.5M", AffectedStatus.NOT_AFFECTED),
            ("4.34.6M", AffectedStatus.AFFECTED),
            ("4.34.7M", AffectedStatus.NOT_AFFECTED),
            ("4.33.8M", AffectedStatus.AFFECTED),
            ("4.33.9M", AffectedStatus.NOT_AFFECTED),
            ("4.32.11M", AffectedStatus.AFFECTED),
            ("4.32.12M", AffectedStatus.NOT_AFFECTED),
            ("4.31.0F", AffectedStatus.NOT_AFFECTED),
            ("4.31.1F", AffectedStatus.AFFECTED),
            ("4.31.10M", AffectedStatus.AFFECTED),
            ("4.31.11M", AffectedStatus.NOT_AFFECTED),
            ("4.30.99M", AffectedStatus.NOT_AFFECTED),
        ):
            parsed = parse_eos_version(version).unwrap()
            assert evaluate_version(parsed, AFFECTED_VERSION_MATRIX).affected_status is state

    def test_states(self) -> None:
        version = version_fact("4.35.4M")
        configured = acl_fact(ConfigurationState.CONFIGURED)
        assert isinstance(_assess_sa151(version, platform_fact("CCS-755-CH-F"), configured), AffectedResult)
        assert isinstance(_assess_sa151(version, platform_fact("DCS-7280CR3"), configured), NotAffectedResult)
        assert isinstance(_assess_sa151(version, platform_fact("DCS-UNRECOGNIZED"), configured), ErrorResult)
        unavailable = SharedSviIngressAclFact.unavailable(FactProblemKind.UNSUPPORTED, SOURCE)
        assert isinstance(_assess_sa151(version, platform_fact("CCS-755-CH-F"), unavailable), ErrorResult)
