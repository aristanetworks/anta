# Copyright (c) 2026 Arista Networks, Inc.
# Use of this source code is governed by the Apache License 2.0
# that can be found in the LICENSE file.
# ruff: noqa: D102, E501, F811
# pylint: disable=missing-function-docstring, redefined-outer-name
"""Unit tests for Arista Security Advisory 142."""

from __future__ import annotations

import unittest
from typing import TYPE_CHECKING, Any, Literal, TypedDict, cast
from unittest.mock import AsyncMock

from anta._advisory.eos_versions import AffectedStatus, evaluate_version
from anta._advisory.results import _get_atomic_vulnerability_ids
from anta._advisory.status import AdvisoryAssessment, AdvisoryStatus
from anta._eos.version import parse_eos_version
from anta.result_manager.models import AntaTestStatus
from anta.tests.advisories.sa_142 import (
    ADVISORY,
    DIRECTFLOW_PATH,
    EXPOSURE_PATHS,
    MTU_DROP_COMMAND,
    PBR_PATH,
    REDIRECT_VERSION_MATRIX,
    SEGMENT_SECURITY_VERSION_MATRIX,
    VerifySA142,
    _assess_sa142,
    _has_configured_or_applied_target,
    _has_directflow_redirect,
    _has_flowspec_redirect,
    _has_mtu_drop,
    _has_pbr_redirect,
    _has_segment_security_redirect,
    _has_traffic_policy_redirect,
    _path_applies,
)
from tests.units.anta_tests import test
from tests.units.anta_tests.advisories import OfflineAntaDevice

if TYPE_CHECKING:
    from tests.units.anta_tests import AntaUnitTestData, UnitTestResult


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

    version: str | None
    platform: str | None
    eos_data: list[dict[str, Any] | str]


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
) -> SA142DeviceData:
    """Return device metadata and command data in declaration order."""
    return {
        "version": version,
        "platform": platform,
        "eos_data": [
            pbr if pbr is not None else {"policyMaps": {}},
            flowspec,
            traffic_policy if traffic_policy is not None else {"trafficPolicies": {}},
            directflow,
            segment_security if segment_security is not None else {"policies": {}},
            mitigation,
        ],
    }


def expected_result(
    status: Literal[
        AntaTestStatus.SUCCESS,
        AntaTestStatus.INCONCLUSIVE,
        AntaTestStatus.FAILURE,
        AntaTestStatus.ERROR,
    ],
    message: str,
    remediation: str,
) -> UnitTestResult:
    """Build matching parent and atomic expectations for one production case."""
    return {
        "result": status,
        "messages": [message],
        "remediations": [remediation] if remediation else [],
        "atomic_results": [
            {
                "description": ADVISORY.vulnerabilities[0].description,
                "result": status,
                "messages": [message],
                "remediations": [remediation] if remediation else [],
            }
        ],
    }


_DATA: AntaUnitTestData = {
    (VerifySA142, "failure-pbr-without-mtu-control"): {
        **sa142_eos_data(pbr=pbr_output()),
        "expected": expected_result(
            AntaTestStatus.FAILURE,
            "The device is affected because the configured redirection exposure falls within the "
            "advisory's EOS version and platform scope without the MTU-exceed drop control: Policy-Based Routing",
            "Upgrade to",
        ),
    },
    (VerifySA142, "inconclusive-pbr-mitigated"): {
        **sa142_eos_data(pbr=pbr_output(), mitigation=MTU_DROP_COMMAND),
        "expected": expected_result(
            AntaTestStatus.INCONCLUSIVE,
            "The device is affected but mitigated because the configured path(s) Policy-Based Routing are covered by the MTU-exceed drop control",
            "Upgrade to",
        ),
    },
    (VerifySA142, "failure-flowspec-without-mtu-control"): {
        **sa142_eos_data(
            flowspec=flowspec_output(),
            platform="DCS-7280SR3-48YC8",
        ),
        "expected": expected_result(
            AntaTestStatus.FAILURE,
            "The device is affected because the configured redirection exposure falls within the advisory's EOS version and platform scope without the MTU-exceed drop control: BGP FlowSpec",
            "Upgrade to",
        ),
    },
    (VerifySA142, "failure-traffic-policy-without-mtu-control"): {
        **sa142_eos_data(traffic_policy=traffic_policy_output()),
        "expected": expected_result(
            AntaTestStatus.FAILURE,
            "The device is affected because the configured redirection exposure falls within the advisory's EOS version and platform scope without the MTU-exceed drop control: Traffic Policy",
            "Upgrade to",
        ),
    },
    (VerifySA142, "failure-directflow-without-mtu-control"): {
        **sa142_eos_data(directflow=directflow_output()),
        "expected": expected_result(
            AntaTestStatus.FAILURE,
            "The device is affected because the configured redirection exposure falls within the advisory's EOS version and platform scope without the MTU-exceed drop control: DirectFlow",
            "Upgrade to",
        ),
    },
    (VerifySA142, "failure-segment-security-without-mtu-control"): {
        **sa142_eos_data(segment_security=segment_security_output()),
        "expected": expected_result(
            AntaTestStatus.FAILURE,
            "The device is affected because the configured redirection exposure falls within the advisory's EOS version and platform scope without the MTU-exceed drop control: Segment Security",
            "Upgrade to",
        ),
    },
    (VerifySA142, "failure-mixed-redirection-paths"): {
        **sa142_eos_data(
            pbr=pbr_output(),
            traffic_policy=traffic_policy_output(),
        ),
        "expected": expected_result(
            AntaTestStatus.FAILURE,
            "The device is affected because the configured redirection exposure falls within "
            "the advisory's EOS version and platform scope without the MTU-exceed drop control: "
            "Policy-Based Routing, Traffic Policy",
            "Upgrade to",
        ),
    },
    (VerifySA142, "failure-known-path-with-malformed-sibling"): {
        **sa142_eos_data(pbr=pbr_output(), traffic_policy={}),
        "expected": expected_result(
            AntaTestStatus.FAILURE,
            "The device is affected because the configured redirection exposure falls within the "
            "advisory's EOS version and platform scope without the MTU-exceed drop control: Policy-Based Routing",
            "Upgrade to",
        ),
    },
    (VerifySA142, "success-no-redirection-path"): {
        **sa142_eos_data(),
        "expected": expected_result(
            AntaTestStatus.SUCCESS,
            "The device is not affected because no next-hop redirection path is configured",
            "",
        ),
    },
    (VerifySA142, "inconclusive-conservative-modular-platform"): {
        **sa142_eos_data(
            pbr=pbr_output(),
            platform="DCS-7508N",
        ),
        "expected": expected_result(
            AntaTestStatus.INCONCLUSIVE,
            "The assessment is inconclusive and the device may be affected because chassis "
            "identity cannot establish the required modular generation for configured "
            "Policy-Based Routing. The MTU-exceed drop control is not configured",
            "unresolved condition",
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
            "The configured state could not be determined for: Traffic Policy",
            "Collect or correct valid output for the unresolved next-hop redirection commands",
        ),
    },
    (VerifySA142, "success-redirection-path-outside-scope"): {
        **sa142_eos_data(
            pbr=pbr_output(),
            platform="DCS-7132LB-48Y4C-R",
        ),
        "expected": expected_result(
            AntaTestStatus.SUCCESS,
            "The device is not affected because its configured redirection paths are outside the advisory's EOS version and platform scope",
            "",
        ),
    },
    (VerifySA142, "error-malformed-redirection-state"): {
        **sa142_eos_data(pbr={}),
        "expected": expected_result(
            AntaTestStatus.ERROR,
            "The configured state could not be determined for: Policy-Based Routing",
            "Collect or correct valid output for the unresolved next-hop redirection commands",
        ),
    },
    (VerifySA142, "error-missing-version-and-platform-evidence"): {
        **sa142_eos_data(pbr=pbr_output(), version=None, platform=None),
        "expected": expected_result(
            AntaTestStatus.ERROR,
            "The EOS version or platform applicability for potential Policy-Based Routing is unavailable from the refreshed device metadata",
            "Collect or correct valid refreshed device EOS version and platform metadata",
        ),
    },
}


class TestSA142VersionScope(unittest.TestCase):
    """Validate all documented feature trains and their adjacent boundaries."""

    def test_redirect_feature_trains(self) -> None:
        cases = (
            ("4.31.99M", AffectedStatus.NOT_AFFECTED),
            ("4.32.0F", AffectedStatus.AFFECTED),
            ("4.32.11M", AffectedStatus.AFFECTED),
            ("4.35.4M", AffectedStatus.AFFECTED),
            ("4.36.0.1F", AffectedStatus.AFFECTED),
            ("4.36.99M", AffectedStatus.AFFECTED),
            ("4.37.0F", AffectedStatus.NOT_AFFECTED),
        )
        for version, expected in cases:
            with self.subTest(version=version):
                assert evaluate_version(parse_eos_version(version), REDIRECT_VERSION_MATRIX).affected_status is expected

    def test_segment_security_excludes_436_train(self) -> None:
        assert evaluate_version(parse_eos_version("4.35.99M"), SEGMENT_SECURITY_VERSION_MATRIX).affected_status is AffectedStatus.AFFECTED
        assert evaluate_version(parse_eos_version("4.36.0F"), SEGMENT_SECURITY_VERSION_MATRIX).affected_status is AffectedStatus.NOT_AFFECTED


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
        assert _has_mtu_drop(MTU_DROP_COMMAND)
        assert not _has_mtu_drop("ip software forwarding mtu 1500")
        assert not _has_mtu_drop("")


class TestSA142PlatformScope(unittest.TestCase):
    """Validate precise and accepted conservative platform qualification."""

    def test_fixed_7050x3_match_is_precise(self) -> None:
        status, conservative, platform = _path_applies(
            PBR_PATH,
            parse_eos_version("4.35.4M"),
            "DCS-7050SX3-48YC12-F",
        )
        assert status is AffectedStatus.AFFECTED
        assert not conservative
        assert platform == "DCS-7050SX3-48YC12-F"

    def test_modular_chassis_match_is_conservative(self) -> None:
        status, conservative, _ = _path_applies(
            PBR_PATH,
            parse_eos_version("4.35.4M"),
            "DCS-7508N",
        )
        assert status is AffectedStatus.AFFECTED
        assert conservative

    def test_7320x_chassis_is_in_pbr_and_directflow_scope(self) -> None:
        for path in (PBR_PATH, DIRECTFLOW_PATH):
            with self.subTest(path=path.name):
                status, conservative, platform = _path_applies(
                    path,
                    parse_eos_version("4.35.4M"),
                    "DCS-7308-F",
                )
                assert status is AffectedStatus.AFFECTED
                assert conservative
                assert platform == "DCS-7308-F"

    def test_out_of_scope_platform_or_train(self) -> None:
        for version, platform in (
            ("4.35.4M", "DCS-7132LB-48Y4C-R"),
            ("4.37.0F", "DCS-7050SX3-48YC12-F"),
        ):
            with self.subTest(version=version, platform=platform):
                status, _, _ = _path_applies(PBR_PATH, parse_eos_version(version), platform)
                assert status is AffectedStatus.NOT_AFFECTED


class TestSA142Assessment(unittest.TestCase):
    """Validate semantic classification independently from ANTA projection."""

    precise_platform = "DCS-7050SX3-48YC12-F"
    conservative_platform = "DCS-7508N"

    def assess(
        self,
        states: tuple[bool | None, ...],
        *,
        version: str | None = "4.35.4M",
        platform: str | None = precise_platform,
        mitigation: bool = False,
        mitigation_unsupported: bool = False,
    ) -> AdvisoryAssessment:
        """Assess a compact combination of normalized evidence."""
        assert len(states) == len(EXPOSURE_PATHS)
        return _assess_sa142(
            states,
            parse_eos_version(version) if version is not None else None,
            platform,
            mtu_drop_configured=mitigation,
            mtu_command_unsupported=mitigation_unsupported,
        )

    def test_affected_mitigated_and_not_affected(self) -> None:
        affected, affected_message, affected_remediation = self.assess((True, False, False, False, False))
        mitigated, mitigated_message, mitigated_remediation = self.assess((True, False, False, False, False), mitigation=True)
        disabled, _, _ = self.assess((False, False, False, False, False), version=None, platform=None)
        outside_scope, _, _ = self.assess(
            (True, False, False, False, False),
            platform="DCS-7132LB-48Y4C-R",
        )

        assert affected is AdvisoryStatus.AFFECTED
        assert "affected" in affected_message
        assert mitigated is AdvisoryStatus.MITIGATED
        assert "mitigated" in mitigated_message
        assert disabled is AdvisoryStatus.NOT_AFFECTED
        assert outside_scope is AdvisoryStatus.NOT_AFFECTED
        assert "post-upgrade" in affected_remediation
        assert "post-upgrade" in mitigated_remediation
        assert "MTU-exceed drop control" not in mitigated_remediation
        assert "http" not in affected_remediation

    def test_conservative_platform_is_inconclusive_with_or_without_control(self) -> None:
        for mitigation in (False, True):
            with self.subTest(mitigation=mitigation):
                status, message, remediation = self.assess(
                    (True, False, False, False, False),
                    platform=self.conservative_platform,
                    mitigation=mitigation,
                )
                assert status is AdvisoryStatus.INCONCLUSIVE
                assert "inconclusive" in message
                assert "may be affected" in message
                assert "unresolved condition" in remediation

    def test_missing_observable_evidence_is_error(self) -> None:
        malformed_feature, _, _ = self.assess((None, False, False, False, False))
        missing_version, _, _ = self.assess((True, False, False, False, False), version=None)
        missing_control, _, _ = self.assess((True, False, False, False, False), mitigation_unsupported=True)

        assert malformed_feature is AdvisoryStatus.ERROR
        assert missing_version is AdvisoryStatus.ERROR
        assert missing_control is AdvisoryStatus.ERROR

    def test_known_exposure_precedes_unknown_sibling_and_safe_optional_short_circuits(self) -> None:
        mixed, _, _ = self.assess((True, False, None, False, False))
        conservative_with_unknown, _, _ = self.assess(
            (True, False, None, False, False),
            platform=self.conservative_platform,
        )
        no_path, _, _ = self.assess(
            (False, False, False, False, False),
            version=None,
            platform=None,
            mitigation_unsupported=True,
        )
        outside_scope, _, _ = self.assess(
            (True, False, False, False, False),
            version="4.37.0F",
            mitigation_unsupported=True,
        )
        irrelevant_malformed, _, _ = self.assess(
            (None, False, False, False, False),
            version="4.37.0F",
            mitigation_unsupported=True,
        )

        assert mixed is AdvisoryStatus.AFFECTED
        assert conservative_with_unknown is AdvisoryStatus.ERROR
        assert no_path is AdvisoryStatus.NOT_AFFECTED
        assert outside_scope is AdvisoryStatus.NOT_AFFECTED
        assert irrelevant_malformed is AdvisoryStatus.NOT_AFFECTED


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
    ) -> VerifySA142:
        """Run the ANTA test with synthetic EOS output in declaration order."""
        device = OfflineAntaDevice("unit-test")
        device.version = parse_eos_version(version) if version is not None else None
        device.hw_model = platform
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
        device.version = parse_eos_version("4.35.4M")
        device.hw_model = "DCS-7050SX3-48YC12-F"
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

    async def test_unsupported_required_control_command_is_error(self) -> None:
        device = OfflineAntaDevice("unit-test")
        device.version = parse_eos_version("4.35.4M")
        device.hw_model = "DCS-7050SX3-48YC12-F"
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
