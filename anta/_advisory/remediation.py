# Copyright (c) 2026 Arista Networks, Inc.
# Use of this source code is governed by the Apache License 2.0
# that can be found in the LICENSE file.
"""Typed remediation plans and their presentation-independent aggregation."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import TYPE_CHECKING, TypeAlias

from anta._advisory.version import SemanticVersion
from anta._eos.version import EOSVersion

if TYPE_CHECKING:
    from collections.abc import Iterable
    from collections.abc import Sequence as SequenceCollection

    from anta._advisory.results import _AdvisoryAtomicTestResult, _AdvisoryTestResult

PAIR_COUNT = 2


class SoftwareTarget(str, Enum):
    """Software products with independently actionable upgrade guidance."""

    EOS = "EOS"
    TERMINATTR = "TerminAttr"


ReleaseVersion: TypeAlias = EOSVersion | SemanticVersion


@dataclass(frozen=True, order=True, slots=True)
class FixedRelease:
    """First fixed release in one software train."""

    version: ReleaseVersion

    def __post_init__(self) -> None:
        if not isinstance(self.version, (EOSVersion, SemanticVersion)):
            msg = "Fixed releases require a supported typed version"
            raise TypeError(msg)


@dataclass(frozen=True, slots=True)
class KnownFixedReleases:
    """Alternative fixed trains for one software target."""

    releases: tuple[FixedRelease, ...]

    def __post_init__(self) -> None:
        if not self.releases:
            msg = "Known fixed releases must contain at least one release"
            raise ValueError(msg)
        trains = tuple(_release_train(release.version) for release in self.releases)
        if len(trains) != len(set(trains)):
            msg = "Known fixed releases must not repeat a software train"
            raise ValueError(msg)


@dataclass(frozen=True, slots=True)
class NextPublishedRemediatedRelease:
    """A remediated release not yet identified by the advisory."""


UpgradeDestination: TypeAlias = KnownFixedReleases | NextPublishedRemediatedRelease


@dataclass(frozen=True, slots=True)
class Upgrade:
    """Upgrade one software product to one of its remediated releases."""

    software: SoftwareTarget
    current_version: ReleaseVersion
    destination: UpgradeDestination

    def __post_init__(self) -> None:
        version_type = EOSVersion if self.software is SoftwareTarget.EOS else SemanticVersion
        if not isinstance(self.current_version, version_type):
            msg = f"{self.software.value} upgrades require a current {version_type.__name__} value"
            raise TypeError(msg)
        if isinstance(self.destination, KnownFixedReleases) and any(not isinstance(release.version, version_type) for release in self.destination.releases):
            msg = f"{self.software.value} fixed releases require {version_type.__name__} values"
            raise TypeError(msg)


@dataclass(frozen=True, slots=True)
class ApplyConfiguration:
    """Apply persistent EOS configuration lines."""

    commands: tuple[str, ...]

    def __post_init__(self) -> None:
        _validate_commands(self.commands)


@dataclass(frozen=True, slots=True)
class RunCommand:
    """Run one or more one-shot EOS commands."""

    commands: tuple[str, ...]

    def __post_init__(self) -> None:
        _validate_commands(self.commands)


@dataclass(frozen=True, slots=True)
class OperationalAction:
    """Perform an uncommon source-backed operational action."""

    instruction: str

    def __post_init__(self) -> None:
        _validate_text(self.instruction, "Operational instructions")


@dataclass(frozen=True, slots=True)
class ConditionalAction:
    """Perform an action only when its source-backed condition applies."""

    condition: str
    action: RemediationAction

    def __post_init__(self) -> None:
        _validate_text(self.condition, "Remediation conditions")
        if not isinstance(self.action, _REMEDIATION_ACTION_TYPES):
            msg = "Conditional remediation requires an action"
            raise TypeError(msg)


RemediationAction: TypeAlias = Upgrade | ApplyConfiguration | RunCommand | OperationalAction | ConditionalAction


@dataclass(frozen=True, slots=True)
class AnyOf:
    """Alternative children where any one completely resolves the condition."""

    items: tuple[RemediationNode, ...]

    def __post_init__(self) -> None:
        _validate_composition(self.items)


@dataclass(frozen=True, slots=True)
class AllOf:
    """Cumulative children that are all required without an ordering claim."""

    items: tuple[RemediationNode, ...]

    def __post_init__(self) -> None:
        _validate_composition(self.items)


@dataclass(frozen=True, slots=True)
class Sequence:
    """Children that are all required in the declared order."""

    items: tuple[RemediationNode, ...]

    def __post_init__(self) -> None:
        _validate_composition(self.items)


RemediationNode: TypeAlias = RemediationAction | AnyOf | AllOf | Sequence


@dataclass(frozen=True, slots=True)
class RemediationPlan:
    """Complete remaining resolution for one vulnerability result."""

    resolution: RemediationNode

    def __post_init__(self) -> None:
        if not isinstance(self.resolution, _REMEDIATION_NODE_TYPES):
            msg = "Remediation plans require a supported resolution node"
            raise TypeError(msg)


class RemediationGuidance(str, Enum):
    """Advisory guidance derived from result context rather than plan identity."""

    NEW_RELEASES = "new releases"
    CURRENT_MITIGATIONS = "current mitigations"
    UNRESOLVED_CONDITIONS = "unresolved conditions"


@dataclass(frozen=True, slots=True)
class ConsolidatedRemediation:
    """One structurally unique plan with its vulnerability attribution and guidance."""

    plan: RemediationPlan
    vulnerability_ids: tuple[str, ...]
    guidance: frozenset[RemediationGuidance]


_REMEDIATION_ACTION_TYPES = (Upgrade, ApplyConfiguration, RunCommand, OperationalAction, ConditionalAction)
_REMEDIATION_NODE_TYPES = (*_REMEDIATION_ACTION_TYPES, AnyOf, AllOf, Sequence)


def _validate_text(value: str, subject: str) -> None:
    """Require concise values that are non-empty and single-line."""
    if not value.strip() or "\n" in value or "\r" in value:
        msg = f"{subject} must be non-empty and single-line"
        raise ValueError(msg)


def _release_train(version: ReleaseVersion) -> str:
    """Derive the displayed major/minor software train from a typed release."""
    prefix = version.prefix if isinstance(version, SemanticVersion) else ""
    return f"{prefix}{version.major}.{version.minor}"


def _validate_commands(commands: tuple[str, ...]) -> None:
    """Validate a non-empty ordered command tuple."""
    if not commands:
        msg = "Command remediations must contain at least one command"
        raise ValueError(msg)
    for command in commands:
        _validate_text(command, "Remediation commands")


def _validate_composition(items: tuple[RemediationNode, ...]) -> None:
    """Validate a meaningful remediation composition."""
    if len(items) < PAIR_COUNT:
        msg = "Remediation compositions must contain at least two children"
        raise ValueError(msg)
    if any(not isinstance(item, _REMEDIATION_NODE_TYPES) for item in items):
        msg = "Remediation compositions contain an unsupported child"
        raise TypeError(msg)


def upgrade_action(
    fixed_releases: SequenceCollection[FixedRelease],
    *,
    current_version: ReleaseVersion,
    software: SoftwareTarget = SoftwareTarget.EOS,
) -> Upgrade:
    """Build one upgrade action from source-backed release guidance."""
    destination: UpgradeDestination = KnownFixedReleases(tuple(fixed_releases)) if fixed_releases else NextPublishedRemediatedRelease()
    return Upgrade(software=software, current_version=current_version, destination=destination)


def upgrade_plan(
    fixed_releases: SequenceCollection[FixedRelease],
    *,
    current_version: ReleaseVersion,
    software: SoftwareTarget = SoftwareTarget.EOS,
) -> RemediationPlan:
    """Build a complete single-product upgrade plan."""
    return RemediationPlan(upgrade_action(fixed_releases, current_version=current_version, software=software))


def remediation_plan(actions: SequenceCollection[RemediationAction]) -> RemediationPlan:
    """Build a plan requiring all supplied actions without ordering them."""
    items = tuple(actions)
    if len(items) == 1:
        return RemediationPlan(items[0])
    return RemediationPlan(AllOf(items))


def _join_alternatives(values: SequenceCollection[str]) -> str:
    """Join alternatives using deterministic prose."""
    if len(values) == 1:
        return values[0]
    if len(values) == PAIR_COUNT:
        return f"{values[0]} or {values[1]}"
    return f"{', '.join(values[:-1])}, or {values[-1]}"


def _render_upgrade(action: Upgrade) -> str:
    """Render one software upgrade action."""
    if isinstance(action.destination, NextPublishedRemediatedRelease):
        return f"Upgrade {action.software.value} to a remediated release when one is published."
    newer_releases = tuple(release for release in action.destination.releases if release.version > action.current_version)
    suggested_releases = newer_releases or (max(action.destination.releases),)
    releases = tuple(f"{action.software.value} {release.version} or later in the {_release_train(release.version)} train" for release in suggested_releases)
    return f"Upgrade to {_join_alternatives(releases)}."


def _render_commands(prefix: str, commands: tuple[str, ...], *, markdown: bool) -> str:
    """Render exact EOS commands in their declared order."""
    rendered = tuple(f"`{command}`" if markdown else f"'{command}'" for command in commands)
    return f"{prefix} {'; then '.join(rendered)}."


def _render_node(node: RemediationNode, *, markdown: bool) -> str:
    """Render one remediation action or composition."""
    if isinstance(node, Upgrade):
        return _render_upgrade(node)
    if isinstance(node, ApplyConfiguration):
        return _render_commands("Apply EOS configuration", node.commands, markdown=markdown)
    if isinstance(node, RunCommand):
        return _render_commands("Run", node.commands, markdown=markdown)
    if isinstance(node, OperationalAction):
        return node.instruction
    if isinstance(node, ConditionalAction):
        return f"If {node.condition}, then {_render_node(node.action, markdown=markdown)}"

    children = tuple(_render_node(item, markdown=markdown) for item in node.items)
    if isinstance(node, AnyOf):
        heading = "Complete any one of the following:"
        marker = "-"
    elif isinstance(node, AllOf):
        heading = "Complete all of the following:"
        marker = "-"
    else:
        heading = "Complete these steps in order:"
        marker = None
    lines = [heading]
    for index, child in enumerate(children, start=1):
        lines.append(f"{marker} {child}" if marker is not None else f"{index}. {child}")
    return "\n".join(lines)


def _render_guidance(guidance: frozenset[RemediationGuidance]) -> str:
    """Render status-derived advisory consultation guidance."""
    if RemediationGuidance.UNRESOLVED_CONDITIONS in guidance:
        return "Refer to the advisory to determine whether the unresolved condition applies, for newly remediated releases, and for current mitigation guidance."
    if guidance:
        return "Refer to the advisory for newly remediated releases and current mitigation guidance."
    return ""


def render_remediation_plain(plan: RemediationPlan, guidance: frozenset[RemediationGuidance] = frozenset()) -> str:
    """Render a remediation plan as deterministic plain text."""
    resolution = _render_node(plan.resolution, markdown=False)
    advisory_guidance = _render_guidance(guidance)
    return f"{resolution}\n{advisory_guidance}" if advisory_guidance else resolution


def render_remediation_markdown(plan: RemediationPlan, guidance: frozenset[RemediationGuidance] = frozenset()) -> str:
    """Render a remediation plan as deterministic Markdown."""
    resolution = _render_node(plan.resolution, markdown=True)
    advisory_guidance = _render_guidance(guidance)
    return f"{resolution}\n{advisory_guidance}" if advisory_guidance else resolution


def consolidate_remediations(result: _AdvisoryTestResult | _AdvisoryAtomicTestResult) -> tuple[ConsolidatedRemediation, ...]:
    """Group equal atomic plans and retain vulnerability attribution and guidance."""
    from anta._advisory.results import _AdvisoryAtomicTestResult  # noqa: PLC0415

    atomic_results: Iterable[_AdvisoryAtomicTestResult]
    if isinstance(result, _AdvisoryAtomicTestResult):
        atomic_results = (result,)
    else:
        atomic_results = (atomic for atomic in result.atomic_results if isinstance(atomic, _AdvisoryAtomicTestResult))

    grouped: dict[RemediationPlan, tuple[list[str], set[RemediationGuidance], bool]] = {}
    for atomic in atomic_results:
        if atomic.remediation is None:
            continue
        vulnerability_ids, guidance, unassociated = grouped.setdefault(atomic.remediation, ([], set(), False))
        if atomic.vulnerability_ids is None:
            unassociated = True
        else:
            vulnerability_ids.extend(vulnerability_id for vulnerability_id in atomic.vulnerability_ids if vulnerability_id not in vulnerability_ids)
        guidance.update(atomic.remediation_guidance)
        grouped[atomic.remediation] = (vulnerability_ids, guidance, unassociated)

    consolidated = []
    for plan, (vulnerability_ids, guidance, unassociated) in grouped.items():
        ordered_ids = () if unassociated else tuple(vulnerability_ids)
        consolidated.append(ConsolidatedRemediation(plan, ordered_ids, frozenset(guidance)))
    return tuple(consolidated)
