# Copyright (c) 2026 Arista Networks, Inc.
# Use of this source code is governed by the Apache License 2.0
# that can be found in the LICENSE file.
"""Facts for next-hop redirection configuration and its MTU control."""

from __future__ import annotations

import re
from collections.abc import Mapping, Sequence
from typing import TYPE_CHECKING, ClassVar

from anta._advisory.facts.models import (
    CommandFactDefinition,
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
)
from anta._advisory.optional_commands import OptionalAntaCommand, is_unsupported_optional_command

if TYPE_CHECKING:
    from anta.models import AntaCommand

MTU_DROP_COMMAND = "ip software forwarding mtu exceed action drop"
MTU_DROP_SHOW_COMMAND = f"show running-config | include ^{MTU_DROP_COMMAND}$"
_NON_ALPHA_PATTERN = re.compile(r"[^a-z]")
_REDIRECT_TARGET_KEYS = {"nexthop", "nexthops", "resolvednexthop", "resolvednexthops", "outputnexthop"}


def _has_meaningful_value(value: object) -> bool:
    if isinstance(value, str):
        return bool(value.strip())
    if isinstance(value, Mapping):
        return any(_has_meaningful_value(child) for child in value.values())
    if isinstance(value, Sequence) and not isinstance(value, bytes):
        return any(_has_meaningful_value(child) for child in value)
    if isinstance(value, bool):
        return value
    return value is not None


def _nested_redirect_target(value: object) -> bool | None:
    if isinstance(value, Mapping):
        return _mapping_has_redirect_target(value)
    if isinstance(value, Sequence) and not isinstance(value, str | bytes):
        for item in value:
            result = _nested_redirect_target(item)
            if result is not False:
                return result
    return False


def _mapping_has_redirect_target(value: Mapping[object, object]) -> bool | None:
    for key, child in value.items():
        if not isinstance(key, str):
            return None
        if _NON_ALPHA_PATTERN.sub("", key.lower()) in _REDIRECT_TARGET_KEYS and _has_meaningful_value(child):
            return True
        result = _nested_redirect_target(child)
        if result is not False:
            return result
    return False


def _contains_redirect_action(value: object) -> bool | None:
    if isinstance(value, Mapping):
        return _mapping_contains_redirect_action(value)
    if isinstance(value, Sequence) and not isinstance(value, str | bytes):
        for item in value:
            result = _contains_redirect_action(item)
            if result is not False:
                return result
    return False


def _mapping_contains_redirect_action(value: Mapping[object, object]) -> bool | None:
    for key, child in value.items():
        if not isinstance(key, str):
            return None
        normalized_key = _NON_ALPHA_PATTERN.sub("", key.lower())
        normalized_value = _NON_ALPHA_PATTERN.sub("", child.lower()) if isinstance(child, str) else ""
        is_redirect = (
            "redirect" in normalized_key
            or normalized_key in {"setnexthop", "outputnexthop"}
            or (normalized_key in {"action", "actiontype"} and "redirect" in normalized_value)
        )
        if is_redirect:
            target = _mapping_has_redirect_target(value)
            if target is not False:
                return target
        result = _contains_redirect_action(child)
        if result is not False:
            return result
    return False


def _visit_configured_target(value: object) -> tuple[bool | None, bool]:  # noqa: C901, PLR0911
    if isinstance(value, Mapping):
        observed = False
        for key, child in value.items():
            if not isinstance(key, str):
                return None, observed
            normalized = _NON_ALPHA_PATTERN.sub("", key.lower())
            if ("configured" in normalized or "applied" in normalized) and any(token in normalized for token in ("intf", "interface", "vni")):
                observed = True
                if not isinstance(child, Sequence) or isinstance(child, str | bytes):
                    return None, observed
                if child:
                    return True, observed
            result, child_observed = _visit_configured_target(child)
            observed = observed or child_observed
            if result is not False:
                return result, observed
        return False, observed
    if isinstance(value, Sequence) and not isinstance(value, str | bytes):
        observed = False
        for child in value:
            result, child_observed = _visit_configured_target(child)
            observed = observed or child_observed
            if result is not False:
                return result, observed
        return False, observed
    return False, False


def _has_configured_or_applied_target(value: object) -> bool | None:
    result, observed = _visit_configured_target(value)
    if result is not False:
        return result
    return False if observed else None


def _has_pbr_redirect(output: object) -> bool | None:
    if not isinstance(output, Mapping) or not isinstance((policies := output.get("policyMaps")), Mapping):
        return None
    unknown = False
    for policy in policies.values():
        if not isinstance(policy, Mapping):
            return None
        redirect = _contains_redirect_action(policy.get("classMap"))
        target = _has_configured_or_applied_target(policy)
        if redirect is True and target is True:
            return True
        unknown = unknown or redirect is None or (redirect is True and target is None)
    return None if unknown else False


def _has_flowspec_redirect(output: object) -> bool | None:
    if not isinstance(output, str):
        return None
    if not output.strip():
        return False
    configured = re.search(r"(?m)^Configured on:\s+\S", output) is not None
    redirect = re.search(r"(?m)^\s+Redirect:\s+\S", output) is not None
    next_hop = re.search(r"(?m)^\s+Route via next hop\s+\S", output) is not None
    if configured and redirect and next_hop:
        return True
    return False if "Flow specification rules" in output and not redirect and not next_hop else None


def _has_traffic_policy_redirect(output: object) -> bool | None:
    if not isinstance(output, Mapping) or not isinstance((policies := output.get("trafficPolicies")), Mapping):
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
    if not isinstance(output, str):
        return None
    if not output.strip():
        return False
    if re.search(r"(?m)^\s+output nexthop:\s+\S", output):
        return True
    return False if re.search(r"(?m)^Flows:\s+\d+ programmed,\s+\d+ rejected\s*$", output) else None


def _has_segment_security_redirect(output: object) -> bool | None:
    if not isinstance(output, Mapping) or not isinstance((policies := output.get("policies")), Mapping):
        return None
    for policy in policies.values():
        if not isinstance(policy, Mapping) or not isinstance((readonly := policy.get("readonly")), bool):
            return None
        if readonly:
            continue
        definitions = policy.get("policyDefs")
        if not isinstance(definitions, Mapping):
            return None
        redirect = _contains_redirect_action(definitions)
        if redirect is not False:
            return redirect
    return False


class RedirectConfigurationFact(CommandFactDefinition[ConfigurationValue]):
    """Base fact for one next-hop redirection path."""

    path_name: ClassVar[str]

    @classmethod
    def configured(cls, command: AntaCommand, *, state: bool | None) -> Fact[ConfigurationValue]:
        """Build a normalized configured state from one parser result."""
        source = FactSource(command.command, FactSourceKind.COMMAND)
        feature = SubFeature(FeatureName.NEXT_HOP_REDIRECTION, f"path using {cls.path_name}")
        if is_unsupported_optional_command(command):
            return cls.available(ConfigurationValue(feature, ConfigurationState.NOT_CONFIGURED), source)
        if state is None:
            return cls.unavailable(FactProblemKind.MALFORMED, source)
        value = ConfigurationState.CONFIGURED if state else ConfigurationState.NOT_CONFIGURED
        return cls.available(ConfigurationValue(feature, value), source)


class PbrRedirectFact(RedirectConfigurationFact):
    """Policy-Based Routing next-hop redirection configuration."""

    key = "configuration.redirect.pbr"
    label = "Policy-Based Routing redirect configuration"
    path_name = "Policy-Based Routing"
    command = OptionalAntaCommand(command="show policy-map type pbr", revision=1)

    @classmethod
    def parse(cls, command: AntaCommand) -> Fact[ConfigurationValue]:
        if is_unsupported_optional_command(command):
            return cls.configured(command, state=False)
        return cls.configured(command, state=_has_pbr_redirect(command.json_output))


class FlowSpecRedirectFact(RedirectConfigurationFact):
    """BGP FlowSpec next-hop redirection configuration."""

    key = "configuration.redirect.flowspec"
    label = "BGP FlowSpec redirect configuration"
    path_name = "BGP FlowSpec"
    command = OptionalAntaCommand(command="show flow-spec ipv4", ofmt="text")

    @classmethod
    def parse(cls, command: AntaCommand) -> Fact[ConfigurationValue]:
        if is_unsupported_optional_command(command):
            return cls.configured(command, state=False)
        return cls.configured(command, state=_has_flowspec_redirect(command.text_output))


class TrafficPolicyRedirectFact(RedirectConfigurationFact):
    """Traffic Policy next-hop redirection configuration."""

    key = "configuration.redirect.traffic_policy"
    label = "Traffic Policy redirect configuration"
    path_name = "Traffic Policy"
    command = OptionalAntaCommand(command="show traffic-policy interface", revision=1)

    @classmethod
    def parse(cls, command: AntaCommand) -> Fact[ConfigurationValue]:
        if is_unsupported_optional_command(command):
            return cls.configured(command, state=False)
        return cls.configured(command, state=_has_traffic_policy_redirect(command.json_output))


class DirectFlowRedirectFact(RedirectConfigurationFact):
    """DirectFlow next-hop redirection configuration."""

    key = "configuration.redirect.directflow"
    label = "DirectFlow redirect configuration"
    path_name = "DirectFlow"
    command = OptionalAntaCommand(command="show directflow detail", ofmt="text")

    @classmethod
    def parse(cls, command: AntaCommand) -> Fact[ConfigurationValue]:
        if is_unsupported_optional_command(command):
            return cls.configured(command, state=False)
        return cls.configured(command, state=_has_directflow_redirect(command.text_output))


class SegmentSecurityRedirectFact(RedirectConfigurationFact):
    """Segment Security next-hop redirection configuration."""

    key = "configuration.redirect.segment_security"
    label = "Segment Security redirect configuration"
    path_name = "Segment Security"
    command = OptionalAntaCommand(command="show segment-security policy", revision=1)

    @classmethod
    def parse(cls, command: AntaCommand) -> Fact[ConfigurationValue]:
        if is_unsupported_optional_command(command):
            return cls.configured(command, state=False)
        return cls.configured(command, state=_has_segment_security_redirect(command.json_output))


class MtuDropMitigationFact(CommandFactDefinition[MitigationValue]):
    """Required MTU-exceed drop control."""

    key = "mitigation.forwarding.mtu_exceed_drop"
    label = "MTU-exceed drop control"
    command = OptionalAntaCommand(command=MTU_DROP_SHOW_COMMAND, ofmt="text")

    @classmethod
    def parse(cls, command: AntaCommand) -> Fact[MitigationValue]:
        source = FactSource(command.command, FactSourceKind.COMMAND)
        if is_unsupported_optional_command(command):
            return cls.unavailable(FactProblemKind.UNSUPPORTED, source)
        configured = any(line.strip() == MTU_DROP_COMMAND for line in command.text_output.splitlines())
        state = MitigationState.EFFECTIVE if configured else MitigationState.INEFFECTIVE
        return cls.available(MitigationValue("MTU-exceed drop control", state), source)
