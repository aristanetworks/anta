# Copyright (c) 2026 Arista Networks, Inc.
# Use of this source code is governed by the Apache License 2.0
# that can be found in the LICENSE file.
"""Unit tests for structured advisory finding projection."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, cast

import pytest

from anta._advisory.facts.models import (
    ComponentSoftwareVersion,
    Fact,
    FactDefinition,
    FactProblemKind,
    FactSource,
    FactSourceKind,
    FeatureName,
    FeatureState,
    FeatureValue,
    MitigationState,
    MitigationValue,
)
from anta._advisory.findings.models import (
    AffectedResult,
    ComponentVersionAssessment,
    ErrorResult,
    MitigatedCondition,
    MitigatedResult,
    NotAffectedResult,
    VersionRelation,
)
from anta._advisory.findings.projection import project_vulnerability_result
from anta._advisory.models import _AdvisoryMetadata, _AdvisoryVulnerability, _AdvisoryVulnerabilitySeverity
from anta._advisory.results import _AdvisoryTestResult
from anta.result_manager.models import AntaTestStatus

if TYPE_CHECKING:
    from anta.device import AntaDevice
    from anta.models import AntaCommand


class ExampleFeatureFact(FactDefinition[FeatureValue]):
    """Feature fact identity for projection tests."""

    key = "feature.example"
    label = "Example feature"

    @classmethod
    def derive(cls, device: AntaDevice, commands: tuple[AntaCommand, ...] = ()) -> Fact[FeatureValue]:
        """Reject derivation because these tests provide already normalized values."""
        _ = cls, device, commands
        pytest.fail("Projection tests do not derive facts")


class ExampleMitigationFact(FactDefinition[MitigationValue]):
    """Mitigation fact identity for projection tests."""

    key = "mitigation.example"
    label = "Example mitigation"

    @classmethod
    def derive(cls, device: AntaDevice, commands: tuple[AntaCommand, ...] = ()) -> Fact[MitigationValue]:
        """Reject derivation because these tests provide already normalized values."""
        _ = cls, device, commands
        pytest.fail("Projection tests do not derive facts")


class ExampleComponentVersionFact(FactDefinition[ComponentSoftwareVersion]):
    """Component-version fact identity for projection tests."""

    key = "component.example.version"
    label = "Example component version"

    @classmethod
    def derive(cls, device: AntaDevice, commands: tuple[AntaCommand, ...] = ()) -> Fact[ComponentSoftwareVersion]:
        """Reject derivation because these tests provide already normalized values."""
        _ = cls, device, commands
        pytest.fail("Projection tests do not derive facts")


VULNERABILITY_ID = "CVE-2026-0001"
ADVISORY = _AdvisoryMetadata(
    sa_number="TBD",
    title="Projection test",
    vulnerabilities=(
        _AdvisoryVulnerability(
            id=VULNERABILITY_ID,
            severity=_AdvisoryVulnerabilitySeverity.UNKNOWN,
            description="Projection test vulnerability.",
        ),
    ),
    url="TBD",
    description="Projection test advisory.",
)
SOURCE = FactSource("show example", FactSourceKind.COMMAND)


def _parent() -> _AdvisoryTestResult:
    """Return a fresh advisory result for projection tests."""
    return _AdvisoryTestResult(name="unit-test", test="VerifyAdvisory", categories=[], description="", advisory=ADVISORY)


def test_project_affected_result() -> None:
    """Render a retained exposure fact and project its semantic status."""
    exposure = ExampleFeatureFact.available(FeatureValue(FeatureName.SECURE_BOOT, FeatureState.ENABLED), SOURCE)
    parent = _parent()
    atomic = parent.add("Verify vulnerability.", vulnerability_ids=(VULNERABILITY_ID,))

    project_vulnerability_result(
        atomic,
        AffectedResult(vulnerability_id=VULNERABILITY_ID, conditions=(exposure,), remediation="Upgrade EOS."),
    )

    assert atomic.result is AntaTestStatus.FAILURE
    assert atomic.messages == ["The device is affected because the Secure Boot feature is enabled."]
    assert atomic.remediations == ["Upgrade EOS."]


def test_project_not_affected_result() -> None:
    """Render a decisive retained feature fact without remediation."""
    decisive = ExampleFeatureFact.available(FeatureValue(FeatureName.SECURE_BOOT, FeatureState.DISABLED), SOURCE)
    parent = _parent()
    atomic = parent.add("Verify vulnerability.", vulnerability_ids=(VULNERABILITY_ID,))

    project_vulnerability_result(
        atomic,
        NotAffectedResult(vulnerability_id=VULNERABILITY_ID, decisive=(decisive,)),
    )

    assert atomic.result is AntaTestStatus.SUCCESS
    assert atomic.messages == ["The device is not affected because the Secure Boot feature is disabled."]
    assert not atomic.remediations


def test_project_error_result_without_remediation() -> None:
    """Render unavailable evidence as an error without remediation advice."""
    problem = ExampleFeatureFact.unavailable(FactProblemKind.MISSING, SOURCE)
    parent = _parent()
    atomic = parent.add("Verify vulnerability.", vulnerability_ids=(VULNERABILITY_ID,))

    project_vulnerability_result(
        atomic,
        ErrorResult(vulnerability_id=VULNERABILITY_ID, problems=(problem,)),
    )

    assert atomic.result is AntaTestStatus.ERROR
    assert atomic.messages == ["The test could not determine the Example feature because the 'show example' output is incomplete."]
    assert not atomic.remediations


def test_project_mitigated_result_renders_relationship() -> None:
    """Render the assessment-owned relationship between exposure and mitigation facts."""
    exposure = ExampleFeatureFact.available(FeatureValue(FeatureName.SECURE_BOOT, FeatureState.ENABLED), SOURCE)
    mitigation = ExampleMitigationFact.available(MitigationValue("example", MitigationState.EFFECTIVE), SOURCE)
    parent = _parent()
    atomic = parent.add("Verify vulnerability.", vulnerability_ids=(VULNERABILITY_ID,))

    project_vulnerability_result(
        atomic,
        MitigatedResult(
            vulnerability_id=VULNERABILITY_ID,
            mitigated_conditions=(MitigatedCondition(exposure, (mitigation,)),),
            remediation="Maintain the mitigation.",
        ),
    )

    assert atomic.result is AntaTestStatus.INCONCLUSIVE
    assert atomic.messages == ["The device is affected but mitigated because the Secure Boot feature is enabled and Example mitigation is effective."]


def test_mitigated_exposure_rejects_ineffective_mitigation() -> None:
    """Prevent an ineffective mitigation fact from closing an exposure."""
    exposure = ExampleFeatureFact.available(FeatureValue(FeatureName.SECURE_BOOT, FeatureState.ENABLED), SOURCE)
    mitigation = ExampleMitigationFact.available(MitigationValue("example", MitigationState.INEFFECTIVE), SOURCE)

    with pytest.raises(ValueError, match="effective mitigation"):
        MitigatedCondition(exposure, (mitigation,))


def test_mitigated_condition_rejects_fixed_component_version() -> None:
    """Prevent a fixed component assessment from serving as an affected condition."""
    version = ExampleComponentVersionFact.available(ComponentSoftwareVersion("example", "2.0.0"), SOURCE)
    fixed = ComponentVersionAssessment(version, VersionRelation.FIXED)
    mitigation = ExampleMitigationFact.available(MitigationValue("example", MitigationState.EFFECTIVE), SOURCE)

    with pytest.raises(ValueError, match="confirmed affected condition"):
        MitigatedCondition(cast("Any", fixed), (mitigation,))


def test_mitigated_condition_rejects_inactive_feature() -> None:
    """Prevent a disabled feature from serving as an affected condition."""
    inactive = ExampleFeatureFact.available(FeatureValue(FeatureName.SECURE_BOOT, FeatureState.DISABLED), SOURCE)
    mitigation = ExampleMitigationFact.available(MitigationValue("example", MitigationState.EFFECTIVE), SOURCE)

    with pytest.raises(ValueError, match="confirmed affected condition"):
        MitigatedCondition(inactive, (mitigation,))


def test_projection_rejects_mismatched_vulnerability() -> None:
    """Require a finding to match its atomic vulnerability association."""
    decisive = ExampleFeatureFact.available(FeatureValue(FeatureName.SECURE_BOOT, FeatureState.DISABLED), SOURCE)
    parent = _parent()
    atomic = parent.add("Verify vulnerability.", vulnerability_ids=(VULNERABILITY_ID,))

    with pytest.raises(ValueError, match="must match"):
        project_vulnerability_result(
            atomic,
            NotAffectedResult(vulnerability_id="CVE-2026-9999", decisive=(decisive,)),
        )
