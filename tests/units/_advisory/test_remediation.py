# Copyright (c) 2026 Arista Networks, Inc.
# Use of this source code is governed by the Apache License 2.0
# that can be found in the LICENSE file.
"""Unit tests for structured advisory remediation plans."""

from __future__ import annotations

from typing import cast

import pytest

from anta._advisory.models import _AdvisoryMetadata, _AdvisoryVulnerability
from anta._advisory.remediation import (
    AllOf,
    AnyOf,
    ApplyConfiguration,
    ChangeSoftwareVersion,
    ConditionalAction,
    FixedRelease,
    KnownFixedReleases,
    NextPublishedFixedRelease,
    OperationalAction,
    ReleaseVersion,
    RemediationGuidance,
    RemediationPlan,
    RunCommand,
    Sequence,
    SoftwareTarget,
    consolidate_remediations,
    remediation_plan,
    render_remediation_markdown,
    render_remediation_plain,
    software_version_action,
    software_version_plan,
)
from anta._advisory.results import _AdvisoryTestResult
from anta._advisory.version import SemanticVersion
from anta._eos.version import EOSVersion

RELEASES = (
    FixedRelease(EOSVersion(4, 36, 3, suffix="F")),
    FixedRelease(EOSVersion(4, 35, 6, suffix="M")),
    FixedRelease(EOSVersion(4, 34, 8, suffix="M")),
)
CURRENT_EOS_VERSION = EOSVersion(4, 33, 1, suffix="F")


def test_known_fixed_release_rendering() -> None:
    """Render every published train as an alternative without embedding a URL."""
    rendered = render_remediation_plain(software_version_plan(RELEASES, current_version=CURRENT_EOS_VERSION))
    assert rendered == ("Upgrade to EOS 4.36.3F or later in the 4.36 train, EOS 4.35.6M or later in the 4.35 train, or EOS 4.34.8M or later in the 4.34 train.")
    assert "http" not in rendered


def test_pending_release_rendering_with_inconclusive_guidance() -> None:
    """Render an unknown fixed release and status-derived unresolved guidance."""
    guidance = frozenset({RemediationGuidance.NEW_RELEASES, RemediationGuidance.CURRENT_MITIGATIONS, RemediationGuidance.UNRESOLVED_CONDITIONS})
    assert render_remediation_plain(software_version_plan((), current_version=CURRENT_EOS_VERSION), guidance) == (
        "Upgrade EOS to a fixed release when one is published.\n"
        "Refer to the advisory to determine whether the unresolved condition applies, for newly fixed releases, and for current mitigation guidance."
    )


def test_fixed_release_rejects_untyped_version() -> None:
    """Reject an opaque version string even when static typing is bypassed."""
    with pytest.raises(TypeError, match="supported typed version"):
        FixedRelease(cast("ReleaseVersion", "4.36.3F"))


def test_known_fixed_releases_rejects_duplicate_train() -> None:
    """Require one first-fixed release per software train."""
    with pytest.raises(ValueError, match="must not repeat"):
        KnownFixedReleases((FixedRelease(EOSVersion(4, 36, 3, suffix="F")), FixedRelease(EOSVersion(4, 36, 4, suffix="M"))))


def test_fixed_release_versions_support_min_and_max() -> None:
    """Expose comparable typed versions for later cross-advisory consolidation."""
    versions = tuple(release.version for release in RELEASES)
    assert min(versions) == EOSVersion(4, 34, 8, suffix="M")
    assert max(versions) == EOSVersion(4, 36, 3, suffix="F")


def test_semantic_versions_support_min_and_max() -> None:
    """Order non-EOS stable semantic releases independently of their display prefix."""
    versions = (SemanticVersion(1, 45, 1, prefix="v"), SemanticVersion(1, 46, 0, prefix="v"))
    assert min(versions) == SemanticVersion(1, 45, 1, prefix="v")
    assert max(versions) == SemanticVersion(1, 46, 0, prefix="v")


@pytest.mark.parametrize("action_type", [ApplyConfiguration, RunCommand])
def test_command_action_rejects_empty_commands(action_type: type[ApplyConfiguration | RunCommand]) -> None:
    """Require at least one command for command-bearing actions."""
    with pytest.raises(ValueError, match="at least one command"):
        action_type(())


@pytest.mark.parametrize("composition_type", [AnyOf, AllOf, Sequence])
def test_composition_requires_two_children(composition_type: type[AnyOf | AllOf | Sequence]) -> None:
    """Reject compositions that do not express a real relationship."""
    with pytest.raises(ValueError, match="at least two children"):
        composition_type((software_version_action(RELEASES, current_version=CURRENT_EOS_VERSION),))


def test_structural_equality_and_hashing() -> None:
    """Make independently built equivalent plans equal and hashable."""
    first = software_version_plan(RELEASES, current_version=CURRENT_EOS_VERSION)
    second = RemediationPlan(ChangeSoftwareVersion(SoftwareTarget.EOS, CURRENT_EOS_VERSION, KnownFixedReleases(RELEASES)))
    assert first == second
    assert hash(first) == hash(second)
    assert len({first, second}) == 1


def test_composition_rendering() -> None:
    """Render alternative, cumulative, and ordered action relationships distinctly."""
    version_change = software_version_action((FixedRelease(EOSVersion(4, 36, 3, suffix="F")),), current_version=CURRENT_EOS_VERSION)
    configure = ApplyConfiguration(("management ssh", "idle-timeout 10"))
    assert render_remediation_markdown(RemediationPlan(AnyOf((version_change, configure)))) == (
        "Complete any one of the following:\n- Upgrade to EOS 4.36.3F or later in the 4.36 train.\n"
        "- Apply EOS configuration `management ssh`; then `idle-timeout 10`."
    )
    assert render_remediation_plain(RemediationPlan(AllOf((version_change, configure)))) == (
        "Complete all of the following:\n- Upgrade to EOS 4.36.3F or later in the 4.36 train.\n- Apply EOS configuration 'management ssh'; then 'idle-timeout 10'."
    )
    assert render_remediation_plain(RemediationPlan(Sequence((version_change, configure)))) == (
        "Complete these steps in order:\n1. Upgrade to EOS 4.36.3F or later in the 4.36 train.\n2. Apply EOS configuration 'management ssh'; then 'idle-timeout 10'."
    )


def test_conditional_action_rendering() -> None:
    """Retain the source-backed condition around an operational action."""
    plan = RemediationPlan(ConditionalAction("the stale state is present", RunCommand(("clear state",))))
    assert render_remediation_markdown(plan) == "If the stale state is present, then Run `clear state`."


def test_remediation_plan_helper() -> None:
    """Use one action directly and multiple actions as cumulative requirements."""
    version_change = software_version_action(RELEASES, current_version=CURRENT_EOS_VERSION)
    operation = OperationalAction("Reload the affected process.")
    assert remediation_plan((version_change,)) == RemediationPlan(version_change)
    assert remediation_plan((version_change, operation)) == RemediationPlan(AllOf((version_change, operation)))


def test_consolidate_remediations() -> None:
    """Group structurally equal plans while preserving attribution and combined guidance."""
    advisory = _AdvisoryMetadata(
        sa_number="0001",
        title="Example",
        vulnerabilities=(_AdvisoryVulnerability(id="CVE-1", description="One."), _AdvisoryVulnerability(id="CVE-2", description="Two.")),
        url="TBD",
        description="Example advisory.",
    )
    result = _AdvisoryTestResult(name="leaf1", test="VerifySA1", categories=[], description="", advisory=advisory)
    plan = software_version_plan(RELEASES, current_version=CURRENT_EOS_VERSION)
    result.add("One", vulnerability_ids=("CVE-1",), remediation=plan, remediation_guidance=frozenset({RemediationGuidance.NEW_RELEASES}))
    result.add(
        "Two",
        vulnerability_ids=("CVE-2",),
        remediation=software_version_plan(RELEASES, current_version=CURRENT_EOS_VERSION),
        remediation_guidance=frozenset({RemediationGuidance.CURRENT_MITIGATIONS}),
    )
    consolidated = consolidate_remediations(result)
    assert len(consolidated) == 1
    assert consolidated[0].plan == plan
    assert consolidated[0].vulnerability_ids == ("CVE-1", "CVE-2")
    assert consolidated[0].guidance == frozenset({RemediationGuidance.NEW_RELEASES, RemediationGuidance.CURRENT_MITIGATIONS})


def test_software_version_models_distinguish_targets_and_destinations() -> None:
    """Represent each software target and pending destination explicitly."""
    current_version = SemanticVersion(1, 45, 0, prefix="v")
    assert software_version_action((), current_version=current_version, software=SoftwareTarget.TERMINATTR) == ChangeSoftwareVersion(
        SoftwareTarget.TERMINATTR, current_version, NextPublishedFixedRelease()
    )


def test_terminattr_rendering_derives_semantic_version_train() -> None:
    """Derive a prefixed TerminAttr train from the typed release."""
    plan = software_version_plan(
        (FixedRelease(SemanticVersion(1, 46, 0, prefix="v")),),
        current_version=SemanticVersion(1, 45, 0, prefix="v"),
        software=SoftwareTarget.TERMINATTR,
    )
    assert render_remediation_plain(plan) == "Upgrade to TerminAttr v1.46.0 or later in the v1.46 train."


def test_software_version_change_rejects_version_type_for_another_software_target() -> None:
    """Prevent EOS and component releases from being mixed under one target."""
    releases = KnownFixedReleases((FixedRelease(SemanticVersion(1, 46, 0, prefix="v")),))
    with pytest.raises(TypeError, match="EOS fixed releases require EOSVersion"):
        ChangeSoftwareVersion(SoftwareTarget.EOS, EOSVersion(4, 35, 1, suffix="F"), releases)


def test_software_version_rendering_only_suggests_newer_fixed_releases() -> None:
    """Exclude older fixed releases when newer alternatives exist."""
    plan = software_version_plan(RELEASES, current_version=EOSVersion(4, 35, 5, suffix="M"))
    rendered = render_remediation_plain(plan)
    assert rendered == ("Upgrade to EOS 4.36.3F or later in the 4.36 train or EOS 4.35.6M or later in the 4.35 train.")
    assert "4.34.8M" not in rendered


def test_software_version_rendering_falls_back_to_newest_fixed_release() -> None:
    """Suggest the newest known fix when no fixed release is newer than the detected version."""
    plan = software_version_plan(RELEASES, current_version=EOSVersion(4, 37, 0, suffix="F"))
    assert render_remediation_plain(plan) == "Downgrade to EOS 4.36.3F or later in the 4.36 train."


def test_software_version_rendering_does_not_treat_equal_fixed_release_as_newer() -> None:
    """Exclude an equal fixed release while retaining a genuinely newer alternative."""
    plan = software_version_plan(RELEASES, current_version=EOSVersion(4, 35, 6, suffix="M"))
    assert render_remediation_plain(plan) == "Upgrade to EOS 4.36.3F or later in the 4.36 train."


def test_software_version_rendering_handles_equal_only_fixed_release() -> None:
    """Avoid describing an equal release as an upgrade or downgrade."""
    release = FixedRelease(EOSVersion(4, 35, 6, suffix="M"))
    plan = software_version_plan((release,), current_version=release.version)
    assert render_remediation_plain(plan) == "Use EOS 4.35.6M or later in the 4.35 train."
