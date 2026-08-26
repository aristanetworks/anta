# Copyright (c) 2026 Arista Networks, Inc.
# Use of this source code is governed by the Apache License 2.0
# that can be found in the LICENSE file.
"""Unit tests for the security advisory test base."""

from __future__ import annotations

import inspect
from typing import TYPE_CHECKING, ClassVar

import pytest

from anta._advisory.base import AntaAdvisoryTest
from anta.models import AntaCommand, AntaTemplate, AntaTest
from anta.result_manager.models import TestResult as AntaTestResult
from tests.units._advisory.conftest import ADVISORY

if TYPE_CHECKING:
    from anta._advisory.models import AdvisoryMetadata
    from anta.device import AntaDevice


class FakeAdvisoryTest(AntaAdvisoryTest):
    """Fake security advisory test."""

    advisory: ClassVar[AdvisoryMetadata] = ADVISORY
    commands: ClassVar[list[AntaCommand | AntaTemplate]] = [AntaCommand(command="show version")]

    @AntaAdvisoryTest.anta_test
    def test(self) -> None:
        """Set the test result to success."""
        self.result.is_success()


def test_advisory_base_is_abstract() -> None:
    """Verify the advisory base inherits the abstract test contract."""
    assert inspect.isabstract(AntaAdvisoryTest)
    assert AntaAdvisoryTest.test is AntaTest.test
    assert not AntaAdvisoryTest.commands


def test_advisory_result(device: AntaDevice) -> None:
    """Verify advisory metadata is attached to results and serializes to JSON-compatible data."""
    test_instance = FakeAdvisoryTest(
        device=device,
        inputs={
            "result_overwrite": {
                "categories": ["overridden"],
                "description": "Overridden description.",
                "custom_field": "Overridden custom field.",
            }
        },
        eos_data=[{"version": "4.36.1F"}],
    )

    assert test_instance.categories == ["advisories"]
    assert test_instance.result.categories == ["overridden"]
    assert test_instance.result.description == "Overridden description."
    assert test_instance.result.custom_field == "Overridden custom field."
    assert test_instance.result.metadata is not None
    assert test_instance.result.metadata.security_advisory is not None
    assert test_instance.result.metadata.security_advisory.data is ADVISORY
    dumped_result = test_instance.result.model_dump(mode="json", exclude_none=True)
    assert dumped_result["metadata"] == {
        "security_advisory": {
            "data": {
                "sa_number": "0001",
                "title": "Test advisory",
                "severity": "high",
                "cves": [
                    {
                        "cve_id": "CVE-2026-0001",
                        "severity": "medium",
                        "cvss_scores": [
                            {"version": "3.1", "score": 6.5, "vector": "CVSS:3.1/TEST"},
                            {"version": "4.0", "score": 7.0, "vector": "CVSS:4.0/TEST"},
                        ],
                    }
                ],
                "url": "https://example.com/advisory",
                "description": "Test advisory description.",
                "resolutions": [
                    {
                        "name": "Upgrade",
                        "details": "Upgrade to a fixed release.",
                        "url": "https://example.com/resolution",
                    }
                ],
                "mitigations": [
                    {
                        "name": "Workaround",
                        "details": "Apply the temporary workaround.",
                        "url": "https://example.com/mitigation",
                    }
                ],
            }
        }
    }
    restored_result = AntaTestResult.model_validate(dumped_result)
    assert restored_result.metadata is not None
    assert restored_result.metadata.security_advisory is not None
    assert restored_result.metadata.security_advisory.data == ADVISORY


def test_non_advisory_result_has_no_metadata() -> None:
    """Verify advisory metadata remains optional for ordinary test results."""
    result = AntaTestResult(name="device", test="test", categories=["test"], description="Test description.")

    assert result.metadata is None
    assert "metadata" not in result.model_dump(mode="json", exclude_none=True)


def test_advisory_test_requires_metadata() -> None:
    """Verify each advisory test must declare its own metadata."""
    with pytest.raises(AttributeError, match="missing required class attribute: advisory"):

        class MissingAdvisoryTest(AntaAdvisoryTest):
            """Advisory test without metadata."""

            commands: ClassVar[list[AntaCommand | AntaTemplate]] = [AntaCommand(command="show version")]

            @AntaAdvisoryTest.anta_test
            def test(self) -> None:
                """Set the test result to success."""
                self.result.is_success()


def test_advisory_test_rejects_invalid_metadata() -> None:
    """Verify advisory metadata must use the private metadata model."""
    with pytest.raises(TypeError, match="must be an AdvisoryMetadata instance"):

        class InvalidAdvisoryTest(AntaAdvisoryTest):
            """Advisory test with invalid metadata."""

            advisory: ClassVar[AdvisoryMetadata] = "invalid"  # type: ignore[assignment]
            commands: ClassVar[list[AntaCommand | AntaTemplate]] = [AntaCommand(command="show version")]

            @AntaAdvisoryTest.anta_test
            def test(self) -> None:
                """Set the test result to success."""
                self.result.is_success()


def test_advisory_test_requires_commands() -> None:
    """Verify advisory tests must collect evidence."""
    with pytest.raises(AttributeError, match="must define at least one command"):

        class MissingCommandsAdvisoryTest(AntaAdvisoryTest):
            """Advisory test without commands."""

            advisory: ClassVar[AdvisoryMetadata] = ADVISORY

            @AntaAdvisoryTest.anta_test
            def test(self) -> None:
                """Set the test result to success."""
                self.result.is_success()


def test_advisory_test_requires_description() -> None:
    """Verify advisory tests must declare a description or docstring."""
    with pytest.raises(AttributeError, match="Cannot set the description"):

        class MissingDescriptionAdvisoryTest(AntaAdvisoryTest):  # pylint: disable=missing-class-docstring
            advisory: ClassVar[AdvisoryMetadata] = ADVISORY
            commands: ClassVar[list[AntaCommand | AntaTemplate]] = [AntaCommand(command="show version")]

            @AntaAdvisoryTest.anta_test
            def test(self) -> None:
                """Set the test result to success."""
                self.result.is_success()


def test_advisory_test_preserves_explicit_identity() -> None:
    """Verify explicit names and descriptions are preserved while the category remains fixed."""

    class CustomAdvisoryTest(AntaAdvisoryTest):
        """Advisory test with an explicit identity."""

        name: ClassVar[str] = "CustomAdvisoryName"
        description: ClassVar[str] = "Custom advisory description."
        categories: ClassVar[list[str]] = ["overridden"]
        advisory: ClassVar[AdvisoryMetadata] = ADVISORY
        commands: ClassVar[list[AntaCommand | AntaTemplate]] = [AntaCommand(command="show version")]

        @AntaAdvisoryTest.anta_test
        def test(self) -> None:
            """Set the test result to success."""
            self.result.is_success()

    assert CustomAdvisoryTest.name == "CustomAdvisoryName"
    assert CustomAdvisoryTest.description == "Custom advisory description."
    assert CustomAdvisoryTest.categories == ["advisories"]
