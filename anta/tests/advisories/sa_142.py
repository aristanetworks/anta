# Copyright (c) 2026 Arista Networks, Inc.
# Use of this source code is governed by the Apache License 2.0
# that can be found in the LICENSE file.
"""ANTA test for Arista Security Advisory 142."""

from __future__ import annotations

import re
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from typing import TYPE_CHECKING, ClassVar

from anta._advisory.base import _AntaAdvisoryTest
from anta._advisory.eos_versions import (
    AffectedStatus,
    VersionRule,
    evaluate_version,
)
from anta._advisory.models import (
    _AdvisoryMetadata,
    _AdvisoryVulnerability,
    _AdvisoryVulnerabilitySeverity,
)
from anta._advisory.optional_commands import (
    OptionalAntaCommand,
    OptionalCommandsMixin,
    is_unsupported_optional_command,
)
from anta._advisory.remediation import (
    FixedRelease,
    evidence_remediation,
    no_remediation,
    upgrade_remediation,
)
from anta._advisory.status import AdvisoryStatus, project_advisory_status
from anta._eos.platform import PlatformFamily, PlatformIdentity, platform_matches_families
from anta.decorators import preview_test_class

if TYPE_CHECKING:
    from anta._advisory.status import AdvisoryAssessment
    from anta.device import DeviceVersion
    from anta.models import AntaCommand, AntaTemplate

MTU_DROP_COMMAND = "ip software forwarding mtu exceed action drop"
MTU_DROP_SHOW_COMMAND = f"show running-config | include ^{MTU_DROP_COMMAND}$"

REDIRECT_VERSION_MATRIX: tuple[VersionRule, ...] = (
    VersionRule(major=4, minor=36, patch_eq=0, hotfix_lte=1),
    VersionRule(major=4, minor=35, patch_lt=4),
    VersionRule(major=4, minor=34, patch_lt=6),
    VersionRule(major=4, minor=33, patch_lt=8),
    VersionRule(major=4, minor=32, patch_lt=11),
)
SEGMENT_SECURITY_VERSION_MATRIX: tuple[VersionRule, ...] = REDIRECT_VERSION_MATRIX[1:]

FIXED_RELEASES = (
    FixedRelease("4.36.1F", "4.36"),
    FixedRelease("4.35.4M", "4.35"),
    FixedRelease("4.34.6M", "4.34"),
    FixedRelease("4.33.8M", "4.33"),
    FixedRelease("4.32.11M", "4.32"),
)


@dataclass(frozen=True)
class ExposurePath:
    """Advisory scope for one next-hop redirection feature."""

    name: str
    platform_families: tuple[PlatformFamily, ...]
    versions: tuple[VersionRule, ...]


@dataclass(frozen=True)
class PathEvidence:
    """Classified version and platform evidence for configured exposure paths."""

    applicable: tuple[str, ...]
    # Configured paths whose platform-family membership needs unavailable module evidence.
    conservative: tuple[str, ...]
    unknown_features: tuple[str, ...]
    applicability_error: str | None = None


PBR_PATH = ExposurePath(
    name="Policy-Based Routing",
    platform_families=(
        PlatformFamily.SERIES_720_XP,
        PlatformFamily.SERIES_722_XPM,
        PlatformFamily.SERIES_7010,
        PlatformFamily.SERIES_7010_X,
        PlatformFamily.SERIES_7020_R,
        PlatformFamily.SERIES_7160,
        PlatformFamily.SERIES_7050_X,
        PlatformFamily.SERIES_7050_X2,
        PlatformFamily.SERIES_7050_X3,
        PlatformFamily.SERIES_7050_X4,
        PlatformFamily.SERIES_7060_X,
        PlatformFamily.SERIES_7060_X2,
        PlatformFamily.SERIES_7060_X4,
        PlatformFamily.SERIES_7060_X5,
        PlatformFamily.SERIES_7060_X6,
        PlatformFamily.SERIES_7250_X,
        PlatformFamily.SERIES_7260_X,
        PlatformFamily.SERIES_7260_X3,
        PlatformFamily.SERIES_7280_E,
        PlatformFamily.SERIES_7280_R,
        PlatformFamily.SERIES_7280_R2,
        PlatformFamily.SERIES_7280_R3,
        PlatformFamily.SERIES_7300_X,
        PlatformFamily.SERIES_7300_X3,
        PlatformFamily.SERIES_7320_X,
        PlatformFamily.SERIES_7358_X4,
        PlatformFamily.SERIES_7368_X4,
        PlatformFamily.SERIES_7388_X5,
        PlatformFamily.SERIES_7500_E,
        PlatformFamily.SERIES_7500_R,
        PlatformFamily.SERIES_7500_R2,
        PlatformFamily.SERIES_7500_R3,
        PlatformFamily.SERIES_7800_R3,
        PlatformFamily.SERIES_7800_R4,
    ),
    versions=REDIRECT_VERSION_MATRIX,
)

FLOWSPEC_PATH = ExposurePath(
    name="BGP FlowSpec",
    platform_families=(
        PlatformFamily.SERIES_7020_R,
        PlatformFamily.SERIES_7280_E,
        PlatformFamily.SERIES_7280_R,
        PlatformFamily.SERIES_7280_R2,
        PlatformFamily.SERIES_7280_R3,
        PlatformFamily.SERIES_7500_E,
        PlatformFamily.SERIES_7500_R,
        PlatformFamily.SERIES_7500_R2,
        PlatformFamily.SERIES_7500_R3,
        PlatformFamily.SERIES_7800_R3,
        PlatformFamily.SERIES_7800_R4,
    ),
    versions=REDIRECT_VERSION_MATRIX,
)

TRAFFIC_POLICY_PATH = ExposurePath(
    name="Traffic Policy",
    platform_families=(
        PlatformFamily.SERIES_720_D,
        PlatformFamily.SERIES_720_XP,
        PlatformFamily.SERIES_722_XPM,
        PlatformFamily.SERIES_755_758,
        PlatformFamily.SERIES_7010_X,
        PlatformFamily.SERIES_7020_R,
        PlatformFamily.SERIES_7050_X3,
        PlatformFamily.SERIES_7050_X4,
        PlatformFamily.SERIES_7060_X5,
        PlatformFamily.SERIES_7060_X6,
        PlatformFamily.SERIES_7280_E,
        PlatformFamily.SERIES_7280_R,
        PlatformFamily.SERIES_7280_R2,
        PlatformFamily.SERIES_7280_R3,
        PlatformFamily.SERIES_7280_R4,
        PlatformFamily.SERIES_7300_X,
        PlatformFamily.SERIES_7300_X3,
        PlatformFamily.SERIES_7358_X4,
        PlatformFamily.SERIES_7388_X5,
        PlatformFamily.SERIES_7500_E,
        PlatformFamily.SERIES_7500_R,
        PlatformFamily.SERIES_7500_R2,
        PlatformFamily.SERIES_7500_R3,
        PlatformFamily.SERIES_7800_R3,
        PlatformFamily.SERIES_7800_R4,
    ),
    versions=REDIRECT_VERSION_MATRIX,
)

DIRECTFLOW_PATH = ExposurePath(
    name="DirectFlow",
    platform_families=(
        PlatformFamily.SERIES_720_XP,
        PlatformFamily.SERIES_755_758,
        PlatformFamily.SERIES_7010_X,
        PlatformFamily.SERIES_7050_X3,
        PlatformFamily.SERIES_7050_X4,
        PlatformFamily.SERIES_7060_X5,
        PlatformFamily.SERIES_7060_X6,
        PlatformFamily.SERIES_7250_X,
        PlatformFamily.SERIES_7260_X,
        PlatformFamily.SERIES_7260_X3,
        PlatformFamily.SERIES_7300_X,
        PlatformFamily.SERIES_7300_X3,
        PlatformFamily.SERIES_7320_X,
        PlatformFamily.SERIES_7368_X4,
    ),
    versions=REDIRECT_VERSION_MATRIX,
)

SEGMENT_SECURITY_PATH = ExposurePath(
    name="Segment Security",
    platform_families=(
        PlatformFamily.SERIES_720_D,
        PlatformFamily.SERIES_720_XP,
        PlatformFamily.SERIES_722_XPM,
        PlatformFamily.SERIES_755_758,
        PlatformFamily.SERIES_7010_X,
        PlatformFamily.SERIES_7050_X3,
        PlatformFamily.SERIES_7280_R3,
        PlatformFamily.SERIES_7300_X3,
        PlatformFamily.SERIES_7500_R3,
        PlatformFamily.SERIES_7800_R3,
    ),
    versions=SEGMENT_SECURITY_VERSION_MATRIX,
)

EXPOSURE_PATHS = (
    PBR_PATH,
    FLOWSPEC_PATH,
    TRAFFIC_POLICY_PATH,
    DIRECTFLOW_PATH,
    SEGMENT_SECURITY_PATH,
)
_NON_ALPHA_PATTERN = re.compile(r"[^a-z]")
_REDIRECT_TARGET_KEYS = {"nexthop", "nexthops", "resolvednexthop", "resolvednexthops", "outputnexthop"}

ADVISORY = _AdvisoryMetadata(
    sa_number="0142",
    title="Security Advisory 0142",
    vulnerabilities=(
        _AdvisoryVulnerability(
            id="CVE-2026-12546",
            severity=_AdvisoryVulnerabilitySeverity.MEDIUM,
            description=("Next-hop redirection bypass for packets requiring exception handling."),
        ),
    ),
    url=("https://www.arista.com/en/support/advisories-notices/security-advisory/24111-security-advisory-0142"),
    description=(
        "On affected platforms running Arista EOS (Extensible Operating System) configured "
        "with next-hop redirection features—such as Policy-Based Routing (PBR), Border Gateway "
        "Protocol (BGP) Flowspec, Traffic Policy, DirectFlow, or Segment Security—certain "
        "specific classes of IP packets requiring exception handling may bypass the configured "
        "redirection action. Instead of being redirected to the designated next hop, these "
        "packets may be handled via fallback software forwarding paths, which can result in the "
        "packets being routed according to the system's standard forwarding information."
    ),
)


def _has_meaningful_value(value: object) -> bool:
    """Return whether an action field contains a configured value."""
    if isinstance(value, str):
        return bool(value.strip())
    if isinstance(value, Mapping):
        return any(_has_meaningful_value(nested_value) for nested_value in value.values())
    if isinstance(value, Sequence) and not isinstance(value, bytes):
        return any(_has_meaningful_value(nested_value) for nested_value in value)
    if isinstance(value, bool):
        return value
    return value is not None


def _has_redirect_target(value: object) -> bool | None:
    """Return whether a redirect action contains a non-empty next-hop or output target."""
    if not isinstance(value, Mapping):
        return None

    return _mapping_has_redirect_target(value)


def _mapping_has_redirect_target(value: Mapping[object, object]) -> bool | None:
    """Search one mapping and its children for a meaningful redirect target."""
    for key, nested_value in value.items():
        if not isinstance(key, str):
            return None
        normalized_key = _NON_ALPHA_PATTERN.sub("", key.lower())
        if normalized_key in _REDIRECT_TARGET_KEYS and _has_meaningful_value(nested_value):
            return True
        nested_result = _nested_redirect_target(nested_value)
        if nested_result is not False:
            return nested_result
    return False


def _nested_redirect_target(value: object) -> bool | None:
    """Search a structured child while ignoring scalar values."""
    if isinstance(value, Mapping):
        return _mapping_has_redirect_target(value)
    if isinstance(value, Sequence) and not isinstance(value, str | bytes):
        for item in value:
            nested_result = _nested_redirect_target(item)
            if nested_result is not False:
                return nested_result
    return False


def _is_redirect_action(key: str, value: object) -> bool:
    """Return whether a key/value pair identifies a redirect action."""
    normalized_key = _NON_ALPHA_PATTERN.sub("", key.lower())
    normalized_value = _NON_ALPHA_PATTERN.sub("", value.lower()) if isinstance(value, str) else ""
    return (
        "redirect" in normalized_key
        or normalized_key in {"setnexthop", "outputnexthop"}
        or (normalized_key in {"action", "actiontype"} and "redirect" in normalized_value)
    )


def _contains_redirect_action(value: object) -> bool | None:
    """Find a structured next-hop redirect action without assuming one feature schema.

    EOS uses feature-specific names such as ``setNexthop``, ``redirectNexthop``,
    ``outputNexthop``, and ``statelessRedirect``. A malformed mapping key makes the
    observation unknown. Empty next-hop containers are not treated as actions.
    """
    if isinstance(value, Mapping):
        return _mapping_contains_redirect_action(value)
    if isinstance(value, Sequence) and not isinstance(value, str | bytes):
        for item in value:
            nested_result = _contains_redirect_action(item)
            if nested_result is not False:
                return nested_result
    return False


def _mapping_contains_redirect_action(value: Mapping[object, object]) -> bool | None:
    """Search one mapping and its children for a complete redirect action."""
    for key, nested_value in value.items():
        if not isinstance(key, str):
            return None
        if _is_redirect_action(key, nested_value):
            redirect_target = _has_redirect_target(value)
            if redirect_target is not False:
                return redirect_target
        nested_result = _contains_redirect_action(nested_value)
        if nested_result is not False:
            return nested_result
    return False


def _visit_configured_target(value: object) -> tuple[bool | None, bool]:
    """Return target state and whether a configured/applied target field was observed."""
    if isinstance(value, Mapping):
        return _visit_configured_target_mapping(value)
    if isinstance(value, Sequence) and not isinstance(value, str | bytes):
        return _visit_configured_target_sequence(value)
    return False, False


def _is_configured_target_key(key: str) -> bool:
    """Return whether a normalized key describes configured/applied attachment targets."""
    normalized_key = _NON_ALPHA_PATTERN.sub("", key.lower())
    scope_matches = "configured" in normalized_key or "applied" in normalized_key
    target_matches = "intf" in normalized_key or "interface" in normalized_key or "vni" in normalized_key
    return scope_matches and target_matches


def _configured_target_state(value: object) -> bool | None:
    """Return whether one observed attachment-target field contains entries."""
    if not isinstance(value, Sequence) or isinstance(value, str | bytes):
        return None
    return bool(value)


def _visit_configured_target_mapping(value: Mapping[object, object]) -> tuple[bool | None, bool]:
    """Visit configured/applied target evidence in one mapping."""
    observed = False
    for key, child in value.items():
        if not isinstance(key, str):
            return None, observed
        if _is_configured_target_key(key):
            observed = True
            target_state = _configured_target_state(child)
            if target_state is not False:
                return target_state, observed
        result, child_observed = _visit_configured_target(child)
        observed = observed or child_observed
        if result is not False:
            return result, observed
    return False, observed


def _visit_configured_target_sequence(value: Sequence[object]) -> tuple[bool | None, bool]:
    """Visit configured/applied target evidence in a sequence."""
    observed = False
    for child in value:
        result, child_observed = _visit_configured_target(child)
        observed = observed or child_observed
        if result is not False:
            return result, observed
    return False, observed


def _has_configured_or_applied_target(value: object) -> bool | None:
    """Return whether structured policy output names a configured or applied target."""
    result, observed_target_field = _visit_configured_target(value)
    if result is not False:
        return result
    return False if observed_target_field else None


def _has_pbr_redirect(output: object) -> bool | None:
    """Return whether an attached PBR policy has a configured next-hop action."""
    if not isinstance(output, Mapping):
        return None
    policy_maps = output.get("policyMaps")
    if not isinstance(policy_maps, Mapping):
        return None

    unknown = False
    for policy in policy_maps.values():
        if not isinstance(policy, Mapping):
            return None
        redirect = _contains_redirect_action(policy.get("classMap"))
        target = _has_configured_or_applied_target(policy)
        if redirect is True and target is True:
            return True
        unknown = unknown or redirect is None or (redirect is True and target is None)
    return None if unknown else False


def _has_flowspec_redirect(output: object) -> bool | None:
    """Return whether configured IPv4 FlowSpec redirects traffic to a next hop."""
    if not isinstance(output, str):
        return None
    if not output.strip():
        return False

    configured = re.search(r"(?m)^Configured on:\s+\S", output) is not None
    redirect = re.search(r"(?m)^\s+Redirect:\s+\S", output) is not None
    next_hop = re.search(r"(?m)^\s+Route via next hop\s+\S", output) is not None
    if configured and redirect and next_hop:
        return True
    if "Flow specification rules" in output and not redirect and not next_hop:
        return False
    return None


def _has_traffic_policy_redirect(output: object) -> bool | None:
    """Return whether an attached Traffic Policy has a next-hop action."""
    if not isinstance(output, Mapping):
        return None
    policies = output.get("trafficPolicies")
    if not isinstance(policies, Mapping):
        return None

    unknown = False
    for policy in policies.values():
        if not isinstance(policy, Mapping):
            return None
        redirect = _contains_redirect_action(policy.get("rules"))
        target = _has_configured_or_applied_target(policy)
        if redirect is True and target is True:
            return True
        unknown = unknown or redirect is None or (redirect is True and target is None)
    return None if unknown else False


def _has_directflow_redirect(output: object) -> bool | None:
    """Return whether a configured DirectFlow entry has a next-hop action.

    The text form is intentional: EOS 4.35.4M omitted a configured flow waiting for
    resources from the command's JSON output while the text output retained it.
    """
    if not isinstance(output, str):
        return None
    if not output.strip():
        return False
    if re.search(r"(?m)^\s+output nexthop:\s+\S", output) is not None:
        return True
    if re.search(r"(?m)^Flows:\s+\d+ programmed,\s+\d+ rejected\s*$", output) is not None:
        return False
    return None


def _has_segment_security_redirect(output: object) -> bool | None:  # noqa: PLR0911 - Each return represents distinct evidence quality.
    """Return whether a writable Segment Security policy redirects to a next hop."""
    if not isinstance(output, Mapping):
        return None
    policies = output.get("policies")
    if not isinstance(policies, Mapping):
        return None

    for policy in policies.values():
        if not isinstance(policy, Mapping):
            return None
        readonly = policy.get("readonly")
        if not isinstance(readonly, bool):
            return None
        if readonly:
            continue
        policy_defs = policy.get("policyDefs")
        if not isinstance(policy_defs, Mapping):
            return None
        redirect = _contains_redirect_action(policy_defs)
        if redirect is not False:
            return redirect
    return False


def _has_mtu_drop(command_output: str) -> bool:
    """Return whether the required IPv4 MTU-exceed drop action is configured."""
    return any(line.strip() == MTU_DROP_COMMAND for line in command_output.splitlines())


def _path_applies(
    path: ExposurePath,
    device_version: DeviceVersion | None,
    platform: PlatformIdentity | None,
) -> tuple[AffectedStatus, bool, str | None]:
    """Evaluate a configured path's documented EOS train and platform scope."""
    version_evaluation = evaluate_version(device_version, path.versions)
    if version_evaluation.affected_status is not AffectedStatus.AFFECTED:
        return version_evaluation.affected_status, False, None

    if platform is None:
        return AffectedStatus.UNKNOWN, False, None
    family_match = platform_matches_families(platform, path.platform_families)
    if family_match is True:
        return AffectedStatus.AFFECTED, False, str(platform)
    if family_match is None:
        return AffectedStatus.UNKNOWN, True, str(platform)
    return AffectedStatus.NOT_AFFECTED, False, str(platform)


def _resolution_remediation(*, inconclusive: bool = False) -> str:
    """Return the advisory's upgrade plus required post-upgrade action."""
    return upgrade_remediation(
        FIXED_RELEASES,
        inconclusive=inconclusive,
        additional_action=("Apply the required post-upgrade remediation described in the advisory."),
    )


def _classify_paths(
    path_states: Sequence[bool | None],
    device_version: DeviceVersion | None,
    platform: PlatformIdentity | None,
) -> PathEvidence:
    """Classify potential paths by version, platform, and evidence quality."""
    applicable_paths: list[str] = []
    conservative_paths: list[str] = []
    unknown_features: list[str] = []
    for path, state in zip(EXPOSURE_PATHS, path_states, strict=True):
        if state is False:
            continue
        status, conservative, _ = _path_applies(path, device_version, platform)
        if status is AffectedStatus.UNKNOWN:
            if conservative:
                if state is None:
                    unknown_features.append(path.name)
                else:
                    conservative_paths.append(path.name)
                continue
            return PathEvidence(
                applicable=tuple(applicable_paths),
                conservative=tuple(conservative_paths),
                unknown_features=tuple(unknown_features),
                applicability_error=path.name,
            )
        if status is AffectedStatus.AFFECTED and state is None:
            unknown_features.append(path.name)
        elif status is AffectedStatus.AFFECTED:
            applicable_paths.append(path.name)
    return PathEvidence(tuple(applicable_paths), tuple(conservative_paths), tuple(unknown_features))


def _assess_no_applicable_paths(unknown_features: tuple[str, ...]) -> AdvisoryAssessment:
    """Return an assessment when no configured path is in advisory scope."""
    if unknown_features:
        return (
            AdvisoryStatus.ERROR,
            f"The configured state could not be determined for: {', '.join(unknown_features)}.",
            evidence_remediation("valid output for the unresolved next-hop redirection commands"),
        )
    return (
        AdvisoryStatus.NOT_AFFECTED,
        "The device is not affected because its configured redirection paths are outside the advisory's EOS version and platform scope.",
        no_remediation(),
    )


def _assess_applicable_paths(
    evidence: PathEvidence,
    *,
    mtu_drop_configured: bool,
    mtu_command_unsupported: bool,
) -> AdvisoryAssessment:
    """Return an assessment when at least one configured path is in advisory scope."""
    applicable_paths = evidence.applicable
    conservative_paths = evidence.conservative
    potential_paths = (*applicable_paths, *conservative_paths)
    unknown_features = evidence.unknown_features
    if mtu_command_unsupported:
        return (
            AdvisoryStatus.ERROR,
            f"The MTU-exceed remediation state for configured {', '.join(potential_paths)} is unavailable because its show command is unsupported.",
            evidence_remediation("the MTU-exceed remediation configuration"),
        )

    if not applicable_paths and unknown_features:
        return (
            AdvisoryStatus.ERROR,
            f"The configured state could not be determined for: {', '.join(unknown_features)}.",
            evidence_remediation("valid output for the unresolved next-hop redirection commands"),
        )
    if not applicable_paths:
        mitigation_context = " The MTU-exceed drop control is configured." if mtu_drop_configured else " The MTU-exceed drop control is not configured."
        return (
            AdvisoryStatus.INCONCLUSIVE,
            (
                "The assessment is inconclusive and the device may be affected because chassis "
                "identity cannot establish the required modular generation for configured "
                f"{', '.join(conservative_paths)}.{mitigation_context}"
            ),
            _resolution_remediation(inconclusive=True),
        )
    if mtu_drop_configured:
        return (
            AdvisoryStatus.MITIGATED,
            f"The device is affected but mitigated because the configured path(s) {', '.join(applicable_paths)} are covered by the MTU-exceed drop control.",
            _resolution_remediation(),
        )
    return (
        AdvisoryStatus.AFFECTED,
        (
            "The device is affected because the configured redirection exposure falls within "
            "the advisory's EOS version and platform scope without the MTU-exceed drop control: "
            f"{', '.join(applicable_paths)}."
        ),
        _resolution_remediation(),
    )


def _assess_classified_paths(
    evidence: PathEvidence,
    *,
    mtu_drop_configured: bool,
    mtu_command_unsupported: bool,
) -> AdvisoryAssessment:
    """Return an advisory assessment from fully classified path evidence."""
    if not evidence.applicable and not evidence.conservative:
        return _assess_no_applicable_paths(evidence.unknown_features)
    return _assess_applicable_paths(
        evidence,
        mtu_drop_configured=mtu_drop_configured,
        mtu_command_unsupported=mtu_command_unsupported,
    )


def _assess_sa142(
    path_states: Sequence[bool | None],
    device_version: DeviceVersion | None,
    platform: PlatformIdentity | None,
    *,
    mtu_drop_configured: bool,
    mtu_command_unsupported: bool = False,
) -> AdvisoryAssessment:
    """Return the semantic vulnerability status, result message, and remediation text."""
    if all(state is False for state in path_states):
        return (
            AdvisoryStatus.NOT_AFFECTED,
            "The device is not affected because no next-hop redirection path is configured.",
            no_remediation(),
        )

    evidence = _classify_paths(path_states, device_version, platform)
    if evidence.applicability_error is not None:
        return (
            AdvisoryStatus.ERROR,
            (f"The EOS version or platform applicability for potential {evidence.applicability_error} is unavailable from the refreshed device metadata."),
            evidence_remediation("valid refreshed device EOS version and platform metadata"),
        )
    return _assess_classified_paths(
        evidence,
        mtu_drop_configured=mtu_drop_configured,
        mtu_command_unsupported=mtu_command_unsupported,
    )


@preview_test_class
class VerifySA142(OptionalCommandsMixin, _AntaAdvisoryTest):
    """Verify that Security Advisory 142 next-hop redirects are safely mitigated.

    Notes
    -----
    Modular component identity is resolved from inventory metadata collected during device refresh.
    If required module evidence is unavailable, matching remains conservative.

    Expected Results
    ----------------
    * Success: The test will pass if no affected redirect path is active.
    * Failure: The test will fail if an affected redirect path lacks the required MTU control.
    * Inconclusive: The test is inconclusive when required module evidence is unavailable or mitigation is verified.
    * Error: The test will error if evidence required for the applicable path is invalid.

    Examples
    --------
    ```yaml
    anta.tests.advisories.sa_142:
      - VerifySA142:
    ```
    """

    advisory: ClassVar[_AdvisoryMetadata] = ADVISORY
    commands: ClassVar[list[AntaCommand | AntaTemplate]] = [
        OptionalAntaCommand(command="show policy-map type pbr", revision=1),
        OptionalAntaCommand(command="show flow-spec ipv4", ofmt="text"),
        OptionalAntaCommand(command="show traffic-policy interface", revision=1),
        OptionalAntaCommand(command="show directflow detail", ofmt="text"),
        OptionalAntaCommand(command="show segment-security policy", revision=1),
        OptionalAntaCommand(command=MTU_DROP_SHOW_COMMAND, ofmt="text"),
    ]
    description = "Verify whether the device is impacted by SA 0142."
    _atomic_support = True

    @_AntaAdvisoryTest.anta_test
    def test(self) -> None:
        """Assess and project the advisory vulnerability."""
        parsers = (
            _has_pbr_redirect,
            _has_flowspec_redirect,
            _has_traffic_policy_redirect,
            _has_directflow_redirect,
            _has_segment_security_redirect,
        )
        path_states: list[bool | None] = []
        feature_commands = self.instance_commands[: len(EXPOSURE_PATHS)]
        for _path, parser, command in zip(EXPOSURE_PATHS, parsers, feature_commands, strict=True):
            if is_unsupported_optional_command(command):
                path_states.append(False)
            else:
                output = command.text_output if command.ofmt == "text" else command.json_output
                path_states.append(parser(output))

        mtu_command = next(command for command in self.instance_commands if command.command == MTU_DROP_SHOW_COMMAND)
        mtu_command_unsupported = is_unsupported_optional_command(mtu_command)
        platform = self.device.platform
        if not isinstance(platform, PlatformIdentity):
            platform = None
        status, message, remediation = _assess_sa142(
            path_states,
            self.device.version,
            platform,
            mtu_drop_configured=(False if mtu_command_unsupported else _has_mtu_drop(mtu_command.text_output)),
            mtu_command_unsupported=mtu_command_unsupported,
        )
        vulnerability = ADVISORY.vulnerabilities[0]
        atomic_result = self.result.add(
            f"Verify {vulnerability.id}.",
            vulnerability_ids=(vulnerability.id,),
        )
        project_advisory_status(atomic_result, status, message, remediation)
