# Copyright (c) 2026 Arista Networks, Inc.
# Use of this source code is governed by the Apache License 2.0
# that can be found in the LICENSE file.
# ruff: noqa: D102, E501, F811
# pylint: disable=missing-function-docstring, redefined-outer-name
"""Unit tests for Arista Security Advisory 142."""

from __future__ import annotations

import unittest
from functools import partial
from typing import TYPE_CHECKING, Any, TypedDict, cast
from unittest.mock import AsyncMock

from anta._advisory.eos_versions import AffectedStatus, evaluate_version
from anta._advisory.facts.eos import EosVersionFact
from anta._advisory.facts.models import (
    AvailableFact,
    ConfigurationState,
    ConfigurationValue,
    Fact,
    FactProblemKind,
    FactSource,
    FactSourceKind,
    FeatureName,
    MitigationState,
    MitigationValue,
    SubFeature,
    UnavailableFact,
)
from anta._advisory.facts.platform import PlatformIdentityFact
from anta._advisory.facts.redirection import (
    DirectFlowRedirectFact,
    FlowSpecRedirectFact,
    MtuDropMitigationFact,
    PbrRedirectFact,
    SegmentSecurityRedirectFact,
    TrafficPolicyRedirectFact,
    _has_configured_or_applied_target,
    _has_directflow_redirect,
    _has_flowspec_redirect,
    _has_pbr_redirect,
    _has_segment_security_redirect,
    _has_traffic_policy_redirect,
)
from anta._advisory.findings.models import AffectedResult, ErrorResult, InconclusiveResult, NotAffectedResult, VersionRelation, VulnerabilityResult
from anta._advisory.remediation import ApplyConfiguration, FixedRelease, RemediationPlan, Sequence, software_version_action
from anta._advisory.results import _get_atomic_vulnerability_ids
from anta._eos.platform import PlatformFamily, PlatformIdentity
from anta._eos.version import EOSVersion, parse_eos_version
from anta.result_manager.models import AntaTestStatus
from anta.tests.advisories.sa_142 import (
    ADVISORY,
    CONDITIONAL_FIXED_VERSION_MATRIX,
    DIRECTFLOW_PATH,
    EXPOSURE_PATHS,
    PBR_PATH,
    REDIRECT_AFFECTED_VERSION_MATRIX,
    SEGMENT_SECURITY_AFFECTED_VERSION_MATRIX,
    SEGMENT_SECURITY_PATH,
    TRAFFIC_POLICY_PATH,
    VerifySA142,
    _assess_sa142,
    _path_applies,
    _version_relation,
)
from tests.units.anta_tests import build_eos_platform, build_eos_version, test
from tests.units.anta_tests.advisories import OfflineAntaDevice, build_expected_advisory_result

MTU_DROP_COMMAND = "ip software forwarding mtu exceed action drop"
EXPECTED_FIXED_RELEASES = (
    FixedRelease(EOSVersion(4, 36, 1, suffix="F")),
    FixedRelease(EOSVersion(4, 35, 4, suffix="M")),
    FixedRelease(EOSVersion(4, 34, 6, suffix="M")),
    FixedRelease(EOSVersion(4, 33, 8, suffix="M")),
    FixedRelease(EOSVersion(4, 32, 11, suffix="M")),
)
EXPECTED_FULL_REMEDIATION = RemediationPlan(
    Sequence(
        (
            software_version_action(EXPECTED_FIXED_RELEASES, current_version=EOSVersion(4, 35, 3, suffix="M")),
            ApplyConfiguration((MTU_DROP_COMMAND,)),
        )
    )
)
EXPECTED_CONFIGURATION_REMEDIATION = RemediationPlan(ApplyConfiguration((MTU_DROP_COMMAND,)))

MTU_DROP_COMMAND = "ip software forwarding mtu exceed action drop"

if TYPE_CHECKING:
    from anta.device import DevicePlatform, DeviceVersion
    from tests.units.anta_tests import AntaUnitTestData


def pbr_output(*, attached: bool = True) -> dict[str, Any]:
    """Return compact structured PBR output matching the observed EOS schema."""
    return {
        "policyMaps": {
            "redirect": {
                "configuredIngressIntfs": ["Ethernet1"] if attached else [],
                "configuredIngressIntfsAsFallback": [],
                "classMap": {
                    "10": {
                        "configuredAction": {
                            "setNexthop": {
                                "actionType": "setNexthop",
                                "nexthops": {"0": {"ip": "192.0.2.1"}},
                            }
                        }
                    }
                },
            }
        }
    }


def traffic_policy_output(*, attached: bool = True) -> dict[str, Any]:
    """Return compact structured Traffic Policy output matching the observed schema."""
    return {
        "trafficPolicies": {
            "redirect": {
                "input": {
                    "configuredIntfs": ["Ethernet1"] if attached else [],
                    "configuredVni": [],
                    "ipv4AppliedIntfs": [],
                    "ipv4AppliedVni": [],
                },
                "rules": [
                    {
                        "ruleString": "redirect-rule",
                        "actions": {
                            "redirectNexthop": {
                                "nexthops": ["192.0.2.1"],
                                "resolvedNexthops": {},
                            }
                        },
                    }
                ],
            }
        }
    }


def flowspec_output() -> str:
    """Return compact FlowSpec text with a configured next-hop redirect."""
    return """Flow specification rules for VRF default
Configured on: Ethernet1
Applied on: Ethernet1
  Flow-spec rule: 192.0.2.0/24;*;
    Actions:
      Redirect: VRF default
                Route via next hop 192.0.2.1
"""


def directflow_output() -> str:
    """Return compact DirectFlow text with a configured next-hop action."""
    return """Flow redirect: (Waiting for a resource to be allocated)
  actions:
    output nexthop: 192.0.2.1
  source: config
Flows: 0 programmed, 1 rejected
"""


def segment_security_output() -> dict[str, Any]:
    """Return compact Segment Security output with a writable redirect policy."""
    return {
        "policies": {
            "redirect": {
                "policyDefs": {"10": {"action": "statelessRedirect", "nexthop": "192.0.2.1"}},
                "readonly": False,
            }
        }
    }


class SA142DeviceData(TypedDict):
    """Device metadata and command outputs for one SA142 production case."""

    version: DeviceVersion | None
    platform: DevicePlatform | None
    eos_data: list[dict[str, Any] | str]


def platform_identity(model: str | None, modules: dict[str, Any] | None = None) -> PlatformIdentity | None:
    """Build structured platform metadata for SA142 unit tests."""
    return build_eos_platform(model, modules)


def sa142_eos_data(
    *,
    pbr: dict[str, Any] | None = None,
    flowspec: str = "",
    traffic_policy: dict[str, Any] | None = None,
    directflow: str = "Flows: 0 programmed, 0 rejected",
    segment_security: dict[str, Any] | None = None,
    mitigation: str = "",
    version: str | None = "4.35.4M",
    platform: str | None = "DCS-7050SX3-48YC12-F",
    platform_modules: dict[str, Any] | None = None,
) -> SA142DeviceData:
    """Return device metadata and command data in declaration order."""
    return {
        "version": build_eos_version(version),
        "platform": platform_identity(platform, platform_modules),
        "eos_data": [
            pbr if pbr is not None else {"policyMaps": {}},
            flowspec,
            traffic_policy if traffic_policy is not None else {"trafficPolicies": {}},
            directflow,
            segment_security if segment_security is not None else {"policies": {}},
            mitigation,
        ],
    }


expected_result = partial(build_expected_advisory_result, ADVISORY.vulnerabilities[0].id)


_DATA: AntaUnitTestData = {
    (VerifySA142, "failure-conditional-fixed-pbr-without-mtu-control"): {
        **sa142_eos_data(pbr=pbr_output()),
        "expected": expected_result(
            AntaTestStatus.FAILURE,
            "The device is affected because EOS version '4.35.4M' is conditionally fixed, platform 'DCS-7050SX3-48YC12-F' is within "
            "the affected platform scope, the next-hop redirection path using Policy-Based Routing configuration is configured, and "
            "MTU-exceed drop control is ineffective.",
            EXPECTED_CONFIGURATION_REMEDIATION,
        ),
    },
    (VerifySA142, "success-conditional-fixed-pbr-with-required-control"): {
        **sa142_eos_data(pbr=pbr_output(), mitigation=MTU_DROP_COMMAND),
        "expected": expected_result(
            AntaTestStatus.SUCCESS,
            "The device is not affected because EOS version '4.35.4M' is conditionally fixed and MTU-exceed drop control is effective.",
            None,
        ),
    },
    (VerifySA142, "failure-affected-pbr-with-required-control"): {
        **sa142_eos_data(pbr=pbr_output(), mitigation=MTU_DROP_COMMAND, version="4.35.3M"),
        "expected": expected_result(
            AntaTestStatus.FAILURE,
            "The device is affected because EOS version '4.35.3M' is affected, platform 'DCS-7050SX3-48YC12-F' is within "
            "the affected platform scope, and the next-hop redirection path using Policy-Based Routing configuration is configured.",
            EXPECTED_FULL_REMEDIATION,
        ),
    },
    (VerifySA142, "failure-flowspec-without-mtu-control"): {
        **sa142_eos_data(
            flowspec=flowspec_output(),
            platform="DCS-7280SR3-48YC8",
        ),
        "expected": expected_result(
            AntaTestStatus.FAILURE,
            "The device is affected because EOS version '4.35.4M' is conditionally fixed, platform 'DCS-7280SR3-48YC8' is within the affected "
            "platform scope, the next-hop redirection path using BGP FlowSpec configuration is configured, and MTU-exceed drop control is ineffective.",
            EXPECTED_CONFIGURATION_REMEDIATION,
        ),
    },
    (VerifySA142, "failure-traffic-policy-without-mtu-control"): {
        **sa142_eos_data(traffic_policy=traffic_policy_output()),
        "expected": expected_result(
            AntaTestStatus.FAILURE,
            "the next-hop redirection path using Traffic Policy configuration is configured, and MTU-exceed drop control is ineffective.",
            EXPECTED_CONFIGURATION_REMEDIATION,
        ),
    },
    (VerifySA142, "failure-directflow-without-mtu-control"): {
        **sa142_eos_data(directflow=directflow_output()),
        "expected": expected_result(
            AntaTestStatus.FAILURE,
            "the next-hop redirection path using DirectFlow configuration is configured, and MTU-exceed drop control is ineffective.",
            EXPECTED_CONFIGURATION_REMEDIATION,
        ),
    },
    (VerifySA142, "failure-segment-security-without-mtu-control"): {
        **sa142_eos_data(segment_security=segment_security_output()),
        "expected": expected_result(
            AntaTestStatus.FAILURE,
            "the next-hop redirection path using Segment Security configuration is configured, and MTU-exceed drop control is ineffective.",
            EXPECTED_CONFIGURATION_REMEDIATION,
        ),
    },
    (VerifySA142, "failure-mixed-redirection-paths"): {
        **sa142_eos_data(
            pbr=pbr_output(),
            traffic_policy=traffic_policy_output(),
        ),
        "expected": expected_result(
            AntaTestStatus.FAILURE,
            "the next-hop redirection path using Policy-Based Routing configuration is configured, the next-hop redirection path using "
            "Traffic Policy configuration is configured, and MTU-exceed drop control is ineffective.",
            EXPECTED_CONFIGURATION_REMEDIATION,
        ),
    },
    (VerifySA142, "failure-known-path-with-malformed-sibling"): {
        **sa142_eos_data(pbr=pbr_output(), traffic_policy={}),
        "expected": expected_result(
            AntaTestStatus.FAILURE,
            "the next-hop redirection path using Policy-Based Routing configuration is configured, and MTU-exceed drop control is ineffective.",
            EXPECTED_CONFIGURATION_REMEDIATION,
        ),
    },
    (VerifySA142, "success-no-redirection-path"): {
        **sa142_eos_data(),
        "expected": expected_result(
            AntaTestStatus.SUCCESS,
            "The device is not affected because the next-hop redirection path using Policy-Based Routing configuration is not configured",
            None,
        ),
    },
    (VerifySA142, "inconclusive-conservative-modular-platform"): {
        **sa142_eos_data(
            pbr=pbr_output(),
            platform="DCS-7508N",
        ),
        "expected": expected_result(
            AntaTestStatus.INCONCLUSIVE,
            "The assessment is inconclusive and the device may be affected. Indications: EOS version '4.35.4M' is conditionally fixed, the next-hop "
            "redirection path using Policy-Based Routing configuration is configured, and MTU-exceed drop control is ineffective. Unresolved: modular switch generation is "
            "incomplete platform identity.",
            EXPECTED_CONFIGURATION_REMEDIATION,
        ),
    },
    (VerifySA142, "error-conservative-path-with-malformed-sibling"): {
        **sa142_eos_data(
            pbr=pbr_output(),
            traffic_policy={},
            platform="DCS-7508N",
        ),
        "expected": expected_result(
            AntaTestStatus.ERROR,
            "The test could not determine the Traffic Policy redirect configuration because the 'show traffic-policy interface' output is invalid.",
            None,
        ),
    },
    (VerifySA142, "success-redirection-path-outside-scope"): {
        **sa142_eos_data(
            pbr=pbr_output(),
            platform="DCS-7132LB-48Y4C-R",
        ),
        "expected": expected_result(
            AntaTestStatus.SUCCESS,
            "The device is not affected because platform 'DCS-7132LB-48Y4C-R' is outside the affected platform scope",
            None,
        ),
    },
    (VerifySA142, "error-malformed-redirection-state"): {
        **sa142_eos_data(pbr={}),
        "expected": expected_result(
            AntaTestStatus.ERROR,
            "The test could not determine the Policy-Based Routing redirect configuration because the 'show policy-map type pbr' output is invalid.",
            None,
        ),
    },
    (VerifySA142, "error-missing-version-and-platform-evidence"): {
        **sa142_eos_data(pbr=pbr_output(), version=None, platform=None),
        "expected": expected_result(
            AntaTestStatus.ERROR,
            "The test could not determine the EOS version because it is missing from device metadata.",
            None,
        ),
    },
    (VerifySA142, "error-missing-platform-evidence"): {
        **sa142_eos_data(pbr=pbr_output(), platform=None),
        "expected": expected_result(
            AntaTestStatus.ERROR,
            "The test could not determine the platform identity because it is missing from device metadata.",
            None,
        ),
    },
}


class TestSA142VersionScope(unittest.TestCase):
    """Validate all documented feature trains and their adjacent boundaries."""

    def test_redirect_feature_trains(self) -> None:
        cases = (
            ("4.31.99M", VersionRelation.OUTSIDE_SCOPE),
            ("4.32.10M", VersionRelation.AFFECTED),
            ("4.32.11M", VersionRelation.CONDITIONAL_FIXED),
            ("4.35.3M", VersionRelation.AFFECTED),
            ("4.35.4M", VersionRelation.CONDITIONAL_FIXED),
            ("4.36.0.1F", VersionRelation.AFFECTED),
            ("4.36.1F", VersionRelation.CONDITIONAL_FIXED),
            ("4.36.99M", VersionRelation.CONDITIONAL_FIXED),
            ("4.37.0F", VersionRelation.OUTSIDE_SCOPE),
        )
        for version, expected in cases:
            with self.subTest(version=version):
                assert _version_relation(PBR_PATH, parse_eos_version(version).unwrap()) is expected

    def test_segment_security_436_is_only_conditional_fixed_from_the_documented_release(self) -> None:
        assert _version_relation(SEGMENT_SECURITY_PATH, parse_eos_version("4.35.3M").unwrap()) is VersionRelation.AFFECTED
        assert _version_relation(SEGMENT_SECURITY_PATH, parse_eos_version("4.35.4M").unwrap()) is VersionRelation.CONDITIONAL_FIXED
        assert _version_relation(SEGMENT_SECURITY_PATH, parse_eos_version("4.36.0.1F").unwrap()) is VersionRelation.OUTSIDE_SCOPE
        assert _version_relation(SEGMENT_SECURITY_PATH, parse_eos_version("4.36.1F").unwrap()) is VersionRelation.CONDITIONAL_FIXED

    def test_version_matrices_preserve_the_published_boundaries(self) -> None:
        assert evaluate_version(parse_eos_version("4.35.3M").unwrap(), REDIRECT_AFFECTED_VERSION_MATRIX).affected_status is AffectedStatus.AFFECTED
        assert evaluate_version(parse_eos_version("4.35.4M").unwrap(), REDIRECT_AFFECTED_VERSION_MATRIX).affected_status is AffectedStatus.NOT_AFFECTED
        assert evaluate_version(parse_eos_version("4.35.3M").unwrap(), SEGMENT_SECURITY_AFFECTED_VERSION_MATRIX).affected_status is AffectedStatus.AFFECTED
        assert evaluate_version(parse_eos_version("4.35.4M").unwrap(), CONDITIONAL_FIXED_VERSION_MATRIX).affected_status is AffectedStatus.AFFECTED


class TestSA142FeatureDetection(unittest.TestCase):
    """Validate each independent redirection path and the required control."""

    def test_pbr_requires_action_and_attachment(self) -> None:
        assert _has_pbr_redirect(pbr_output())
        assert not _has_pbr_redirect(pbr_output(attached=False))
        output = pbr_output()
        output["policyMaps"]["redirect"]["classMap"]["10"]["configuredAction"]["setNexthop"]["nexthops"] = {}
        assert not _has_pbr_redirect(output)
        assert not _has_pbr_redirect({"policyMaps": {}})
        assert _has_pbr_redirect({}) is None

    def test_attachment_evidence_distinguishes_empty_absent_and_malformed_fields(self) -> None:
        assert _has_configured_or_applied_target({"configuredIngressIntfs": ["Ethernet1"]})
        assert not _has_configured_or_applied_target({"configuredIngressIntfs": []})
        assert _has_configured_or_applied_target({}) is None
        assert _has_configured_or_applied_target({"configuredIngressIntfs": "Ethernet1"}) is None

    def test_flowspec_redirect(self) -> None:
        assert _has_flowspec_redirect(
            """Flow specification rules for VRF default\nConfigured on: Ethernet1\nApplied on: Ethernet1\n  Flow-spec rule: 192.0.2.0/24;*;\n    Actions:\n      Redirect: VRF default\n                Route via next hop 192.0.2.1\n"""
        )
        assert not _has_flowspec_redirect("")
        assert _has_flowspec_redirect("unexpected output") is None

    def test_traffic_policy_requires_action_and_attachment(self) -> None:
        assert _has_traffic_policy_redirect(traffic_policy_output())
        assert not _has_traffic_policy_redirect(traffic_policy_output(attached=False))
        output = traffic_policy_output()
        output["trafficPolicies"]["redirect"]["rules"][0]["actions"]["redirectNexthop"] = {"nexthops": [], "resolvedNexthops": {}}
        assert not _has_traffic_policy_redirect(output)
        assert not _has_traffic_policy_redirect({"trafficPolicies": {}})

    def test_directflow_redirect(self) -> None:
        output = """Flow redirect: (Waiting for a resource to be allocated)
  actions:
    output nexthop: 192.0.2.1
  source: config
Flows: 0 programmed, 1 rejected
"""
        assert _has_directflow_redirect(output)
        assert not _has_directflow_redirect("Flows: 0 programmed, 0 rejected")
        assert _has_directflow_redirect("unexpected output") is None

    def test_segment_security_redirect(self) -> None:
        output = {
            "policies": {
                "policy-forward-all": {
                    "policyDefs": {"10": {"action": "statelessPermit"}},
                    "readonly": True,
                },
                "redirect": {
                    "policyDefs": {"10": {"action": "statelessRedirect", "nexthop": "192.0.2.1"}},
                    "readonly": False,
                },
            }
        }
        assert _has_segment_security_redirect(output)
        output["policies"]["redirect"]["policyDefs"]["10"]["nexthop"] = ""
        assert not _has_segment_security_redirect(output)
        assert not _has_segment_security_redirect({"policies": {"policy-forward-all": {"policyDefs": {"10": {"action": "statelessPermit"}}, "readonly": True}}})
        assert _has_segment_security_redirect({}) is None

    def test_mtu_drop_requires_exact_command(self) -> None:
        for output, expected in (
            (MTU_DROP_COMMAND, MitigationState.EFFECTIVE),
            ("ip software forwarding mtu 1500", MitigationState.INEFFECTIVE),
            ("", MitigationState.INEFFECTIVE),
        ):
            with self.subTest(output=output):
                command = MtuDropMitigationFact.commands[0].model_copy()
                command.output = output
                fact = MtuDropMitigationFact.parse((command,))
                assert isinstance(fact, AvailableFact)
                assert fact.value.state is expected


class TestSA142PlatformScope(unittest.TestCase):
    """Validate precise and accepted conservative platform qualification."""

    def test_platform_fact_uses_refreshed_platform_identity(self) -> None:
        """Do not reconstruct advisory platform facts from the legacy hardware model."""
        device = OfflineAntaDevice("unit-test")
        device.hw_model = "DCS-7050SX3-48YC12-F"

        missing = PlatformIdentityFact.derive(device)
        assert isinstance(missing, UnavailableFact)

        device.platform = platform_identity("DCS-7050SX3-48YC12-F")
        available = PlatformIdentityFact.derive(device)
        assert isinstance(available, AvailableFact)
        assert available.value is device.platform

    def test_platform_fact_rejects_non_eos_platform_identity(self) -> None:
        """Return invalid evidence for a generic platform identity instead of raising at assessment time."""

        class GenericPlatformIdentity:
            """Platform metadata implementing the public device protocol without EOS families."""

            def __str__(self) -> str:
                return "generic-platform"

            def to_dict(self) -> dict[str, object]:
                return {"model": "generic-platform"}

        device = OfflineAntaDevice("unit-test")
        device.platform = GenericPlatformIdentity()

        fact = PlatformIdentityFact.derive(device)

        assert isinstance(fact, UnavailableFact)
        assert fact.problem is FactProblemKind.INVALID

    def test_fixed_7050x3_match_is_precise(self) -> None:
        status, conservative, platform = _path_applies(
            PBR_PATH,
            parse_eos_version("4.35.4M").unwrap(),
            platform_identity("DCS-7050SX3-48YC12-F"),
        )
        assert status is AffectedStatus.AFFECTED
        assert not conservative
        assert platform == "DCS-7050SX3-48YC12-F"

    def test_missing_modular_evidence_is_conservative(self) -> None:
        status, conservative, _ = _path_applies(
            PBR_PATH,
            parse_eos_version("4.35.4M").unwrap(),
            platform_identity("DCS-7508N"),
        )
        assert status is AffectedStatus.UNKNOWN
        assert conservative

    def test_7320x_chassis_is_in_pbr_and_directflow_scope(self) -> None:
        for path, platform in (
            (PBR_PATH, "DCS-7324"),
            (DIRECTFLOW_PATH, "DCS-7328-F"),
        ):
            with self.subTest(path=path.name, platform=platform):
                status, conservative, matched_platform = _path_applies(
                    path,
                    parse_eos_version("4.35.4M").unwrap(),
                    platform_identity(platform),
                )
                assert status is AffectedStatus.AFFECTED
                assert not conservative
                assert matched_platform == platform

    def test_out_of_scope_platform_or_train(self) -> None:
        for version, platform in (
            ("4.35.4M", "DCS-7132LB-48Y4C-R"),
            ("4.37.0F", "DCS-7050SX3-48YC12-F"),
        ):
            with self.subTest(version=version, platform=platform):
                status, _, _ = _path_applies(PBR_PATH, parse_eos_version(version).unwrap(), platform_identity(platform))
                assert status is AffectedStatus.NOT_AFFECTED

    def test_shared_chassis_uses_installed_switch_card_family(self) -> None:
        """Distinguish 7358X4 and 7368X4 switch cards in a shared chassis."""
        version = parse_eos_version("4.35.4M").unwrap()
        cases = {
            "7358": ({"modules": {"Switchcard1": {"modelName": "7358X4-SC"}}}, AffectedStatus.AFFECTED, AffectedStatus.NOT_AFFECTED),
            "7368": ({"modules": {"Switchcard1": {"modelName": "7368X4-SC"}}}, AffectedStatus.NOT_AFFECTED, AffectedStatus.AFFECTED),
        }
        for name, (modules, expected_traffic_policy, expected_directflow) in cases.items():
            with self.subTest(name=name):
                platform = platform_identity("7368-F", modules)
                assert _path_applies(TRAFFIC_POLICY_PATH, version, platform)[0] is expected_traffic_policy
                assert _path_applies(DIRECTFLOW_PATH, version, platform)[0] is expected_directflow

    def test_advisory_scope_uses_platform_families(self) -> None:
        """Keep similarly named and shared-chassis families distinct."""
        assert PlatformFamily.SERIES_720_XP in PBR_PATH.platform_families
        assert PlatformFamily.SERIES_722_XPM in PBR_PATH.platform_families
        assert PlatformFamily.SERIES_7368_X4 not in TRAFFIC_POLICY_PATH.platform_families
        assert PlatformFamily.SERIES_7358_X4 not in DIRECTFLOW_PATH.platform_families

    def test_720xpm_uses_722xpm_advisory_scope(self) -> None:
        """Verify shared platform resolution places 720XPM in the documented 722XPM scope."""
        platform = platform_identity("CCS-720XPM-48TH-6SY-F")
        for path in (PBR_PATH, TRAFFIC_POLICY_PATH, SEGMENT_SECURITY_PATH):
            with self.subTest(path=path.name):
                status, conservative, _ = _path_applies(path, parse_eos_version("4.35.4M").unwrap(), platform)
                assert status is AffectedStatus.AFFECTED
                assert not conservative


class TestSA142Assessment(unittest.TestCase):
    """Validate semantic classification independently from ANTA projection."""

    precise_platform = "DCS-7050SX3-48YC12-F"
    conservative_platform = "DCS-7508N"
    source = FactSource("unit test", FactSourceKind.DEVICE_METADATA)
    affected_version = EosVersionFact.available(EOSVersion(4, 35, 3, suffix="M"), source)
    conditional_fixed_version = EosVersionFact.available(EOSVersion(4, 35, 4, suffix="M"), source)
    outside_scope_version = EosVersionFact.available(EOSVersion(4, 37, 0, suffix="F"), source)
    missing_version = EosVersionFact.unavailable(FactProblemKind.MISSING, source)
    invalid_version = EosVersionFact.unavailable(FactProblemKind.INVALID, source)

    def assess(
        self,
        states: tuple[bool | None, ...],
        *,
        version: Fact[EOSVersion],
        platform: str | None = precise_platform,
        mitigation: bool = False,
        mitigation_unsupported: bool = False,
    ) -> VulnerabilityResult:
        """Assess a compact combination of normalized facts."""
        assert len(states) == len(EXPOSURE_PATHS)
        definitions = (PbrRedirectFact, FlowSpecRedirectFact, TrafficPolicyRedirectFact, DirectFlowRedirectFact, SegmentSecurityRedirectFact)
        path_facts = tuple(
            definition.unavailable(FactProblemKind.MALFORMED, self.source)
            if state is None
            else definition.available(
                ConfigurationValue(
                    SubFeature(FeatureName.NEXT_HOP_REDIRECTION, f"path using {definition.path_name}"),
                    ConfigurationState.CONFIGURED if state else ConfigurationState.NOT_CONFIGURED,
                ),
                self.source,
            )
            for definition, state in zip(definitions, states, strict=True)
        )
        platform_value = platform_identity(platform)
        platform_fact: Fact[PlatformIdentity] = (
            PlatformIdentityFact.unavailable(FactProblemKind.MISSING, self.source)
            if platform_value is None
            else PlatformIdentityFact.available(platform_value, self.source)
        )
        mitigation_fact = (
            MtuDropMitigationFact.unavailable(FactProblemKind.UNSUPPORTED, self.source)
            if mitigation_unsupported
            else MtuDropMitigationFact.available(
                MitigationValue(MitigationState.EFFECTIVE if mitigation else MitigationState.INEFFECTIVE),
                self.source,
            )
        )
        return _assess_sa142(
            path_facts,
            version,
            platform_fact,
            mitigation_fact,
        )

    def test_affected_conditional_fixed_and_not_affected(self) -> None:
        affected = self.assess((True, False, False, False, False), version=self.affected_version)
        affected_with_control = self.assess((True, False, False, False, False), version=self.affected_version, mitigation=True)
        incomplete_conditional_fix = self.assess((True, False, False, False, False), version=self.conditional_fixed_version)
        complete_conditional_fix = self.assess((True, False, False, False, False), version=self.conditional_fixed_version, mitigation=True)
        disabled = self.assess((False, False, False, False, False), version=self.missing_version, platform=None)
        outside_scope = self.assess(
            (True, False, False, False, False),
            version=self.conditional_fixed_version,
            platform="DCS-7132LB-48Y4C-R",
        )

        assert isinstance(affected, AffectedResult)
        assert isinstance(affected_with_control, AffectedResult)
        assert isinstance(incomplete_conditional_fix, AffectedResult)
        assert isinstance(complete_conditional_fix, NotAffectedResult)
        assert isinstance(disabled, NotAffectedResult)
        assert isinstance(outside_scope, NotAffectedResult)
        assert affected.remediation == EXPECTED_FULL_REMEDIATION
        assert affected_with_control.remediation == EXPECTED_FULL_REMEDIATION
        assert incomplete_conditional_fix.remediation == EXPECTED_CONFIGURATION_REMEDIATION

    def test_affected_release_with_conservative_platform_is_inconclusive_regardless_of_control(self) -> None:
        for mitigation in (False, True):
            with self.subTest(mitigation=mitigation):
                finding = self.assess(
                    (True, False, False, False, False),
                    version=self.affected_version,
                    platform=self.conservative_platform,
                    mitigation=mitigation,
                )
                assert isinstance(finding, InconclusiveResult)
                assert finding.remediation == EXPECTED_FULL_REMEDIATION

    def test_conditional_fixed_release_with_conservative_platform_depends_on_control(self) -> None:
        incomplete = self.assess(
            (True, False, False, False, False),
            version=self.conditional_fixed_version,
            platform=self.conservative_platform,
        )
        complete = self.assess(
            (True, False, False, False, False),
            version=self.conditional_fixed_version,
            platform=self.conservative_platform,
            mitigation=True,
        )

        assert isinstance(incomplete, InconclusiveResult)
        assert isinstance(complete, NotAffectedResult)

    def test_missing_observable_evidence_is_error(self) -> None:
        malformed_feature = self.assess((None, False, False, False, False), version=self.conditional_fixed_version)
        missing_version = self.assess((True, False, False, False, False), version=self.missing_version)
        invalid_version = self.assess((True, False, False, False, False), version=self.invalid_version)
        missing_control = self.assess((True, False, False, False, False), version=self.conditional_fixed_version, mitigation_unsupported=True)
        irrelevant_missing_control = self.assess(
            (True, False, False, False, False),
            version=self.affected_version,
            mitigation_unsupported=True,
        )

        assert isinstance(malformed_feature, ErrorResult)
        assert isinstance(missing_version, ErrorResult)
        assert isinstance(invalid_version, ErrorResult)
        assert invalid_version.problems[0].problem is FactProblemKind.INVALID
        assert isinstance(missing_control, ErrorResult)
        assert isinstance(irrelevant_missing_control, AffectedResult)

    def test_known_exposure_precedes_unknown_sibling_and_safe_optional_short_circuits(self) -> None:
        mixed = self.assess((True, False, None, False, False), version=self.conditional_fixed_version)
        conservative_with_unknown = self.assess(
            (True, False, None, False, False),
            version=self.conditional_fixed_version,
            platform=self.conservative_platform,
        )
        no_path = self.assess(
            (False, False, False, False, False),
            version=self.missing_version,
            platform=None,
            mitigation_unsupported=True,
        )
        outside_scope = self.assess(
            (True, False, False, False, False),
            version=self.outside_scope_version,
            mitigation_unsupported=True,
        )
        irrelevant_malformed = self.assess(
            (None, False, False, False, False),
            version=self.outside_scope_version,
            mitigation_unsupported=True,
        )

        assert isinstance(mixed, AffectedResult)
        assert isinstance(conservative_with_unknown, ErrorResult)
        assert isinstance(no_path, NotAffectedResult)
        assert isinstance(outside_scope, NotAffectedResult)
        assert isinstance(irrelevant_malformed, NotAffectedResult)


class TestVerifySA142(unittest.IsolatedAsyncioTestCase):
    """Validate atomic projection and optional-command handling."""

    async def run_test(
        self,
        *,
        pbr: dict[str, Any] | None = None,
        flowspec: str = "",
        traffic_policy: dict[str, Any] | None = None,
        directflow: str = "Flows: 0 programmed, 0 rejected",
        segment_security: dict[str, Any] | None = None,
        mitigation: str = "",
        version: str | None = "4.35.4M",
        platform: str | None = "DCS-7050SX3-48YC12-F",
        platform_modules: dict[str, Any] | None = None,
    ) -> VerifySA142:
        """Run the ANTA test with synthetic EOS output in declaration order."""
        device = OfflineAntaDevice("unit-test")
        device.version = parse_eos_version(version).unwrap() if version is not None else None
        device.platform = platform_identity(platform, platform_modules)
        await device.refresh()
        eos_data = [
            pbr if pbr is not None else {"policyMaps": {}},
            flowspec,
            traffic_policy if traffic_policy is not None else {"trafficPolicies": {}},
            directflow,
            segment_security if segment_security is not None else {"policies": {}},
            mitigation,
        ]
        test = cast("Any", VerifySA142)(device=device, eos_data=eos_data)
        await test.test(eos_data=eos_data)
        return test

    async def test_error_atomic_result_preserves_vulnerability_association(self) -> None:
        test = await self.run_test(pbr={})

        assert len(test.result.atomic_results) == 1
        assert _get_atomic_vulnerability_ids(test.result.atomic_results[0]) == ("CVE-2026-12546",)

    async def test_unsupported_feature_command_proves_path_absent(self) -> None:
        device = OfflineAntaDevice("unit-test")
        device.version = parse_eos_version("4.35.4M").unwrap()
        device.platform = platform_identity("DCS-7050SX3-48YC12-F")
        await device.refresh()
        eos_data = [
            {},
            "",
            {"trafficPolicies": {}},
            "Flows: 0 programmed, 0 rejected",
            {"policies": {}},
            "",
        ]
        test = cast("Any", VerifySA142)(device=device, eos_data=eos_data)
        test.instance_commands[0].output = None
        test.instance_commands[0].errors = ["This command is not supported on this hardware platform"]
        test.collect = AsyncMock()
        await test.test()

        assert test.result.result is AntaTestStatus.SUCCESS

    async def test_unsupported_directflow_parser_rejection_proves_path_absent(self) -> None:
        device = OfflineAntaDevice("unit-test")
        device.version = parse_eos_version("4.33.0F").unwrap()
        device.platform = platform_identity("cEOSLab")
        await device.refresh()
        eos_data = [
            {"policyMaps": {}},
            "",
            {"trafficPolicies": {}},
            "Flows: 0 programmed, 0 rejected",
            {"policies": {}},
            "",
        ]
        test = cast("Any", VerifySA142)(device=device, eos_data=eos_data)
        test.instance_commands[3].output = None
        test.instance_commands[3].errors = ["Invalid input (at token 1: 'directflow')"]
        test.collect = AsyncMock()
        await test.test()

        assert test.result.result is AntaTestStatus.SUCCESS

    async def test_unsupported_required_control_command_is_error(self) -> None:
        device = OfflineAntaDevice("unit-test")
        device.version = parse_eos_version("4.35.4M").unwrap()
        device.platform = platform_identity("DCS-7050SX3-48YC12-F")
        await device.refresh()
        eos_data = [
            pbr_output(),
            "",
            {"trafficPolicies": {}},
            "Flows: 0 programmed, 0 rejected",
            {"policies": {}},
            "",
        ]
        test = cast("Any", VerifySA142)(device=device, eos_data=eos_data)
        test.instance_commands[5].output = None
        test.instance_commands[5].errors = ["This command is not supported on this hardware platform"]
        test.collect = AsyncMock()
        await test.test()

        assert test.result.result is AntaTestStatus.ERROR
        assert "MTU-exceed" in test.result.messages[0]
