# Copyright (c) 2023-2026 Arista Networks, Inc.
# Use of this source code is governed by the Apache License 2.0
# that can be found in the LICENSE file.
"""Tests for anta.tests module."""

from __future__ import annotations

import asyncio
from typing import TYPE_CHECKING, Any, Literal, TypedDict

from anta._advisory.results import _AdvisoryAtomicTestResult, _AdvisoryTestResult
from anta._eos.parsing import ParseSuccessful
from anta._eos.platform import parse_eos_platform_modules, parse_eos_platform_or_none
from anta._eos.version import parse_eos_version
from anta.models import AntaTest

if TYPE_CHECKING:
    import sys

    from anta.device import AntaDevice
    from anta.result_manager.models import AntaTestStatus

    if sys.version_info >= (3, 11):
        from typing import NotRequired
    else:
        from typing_extensions import NotRequired

    from typing import TypeAlias


class AtomicResult(TypedDict):
    """Expected atomic result of a unit test of an AntaTest subclass."""

    description: str
    result: Literal[
        AntaTestStatus.SUCCESS,
        AntaTestStatus.INCONCLUSIVE,
        AntaTestStatus.FAILURE,
        AntaTestStatus.ERROR,
        AntaTestStatus.SKIPPED,
    ]
    messages: NotRequired[list[str]]
    remediations: NotRequired[list[str]]
    inputs: NotRequired[dict[str, Any]]


class UnitTestResult(TypedDict):
    """Expected result of a unit test of an AntaTest subclass.

    For our AntaTest unit tests we expect a terminal result, never unset.
    """

    result: Literal[AntaTestStatus.SUCCESS, AntaTestStatus.INCONCLUSIVE, AntaTestStatus.FAILURE, AntaTestStatus.ERROR, AntaTestStatus.SKIPPED]
    messages: NotRequired[list[str]]
    remediations: NotRequired[list[str]]
    atomic_results: NotRequired[list[AtomicResult]]


class AntaUnitTest(TypedDict):
    """The parameters required for a unit test of an AntaTest subclass."""

    inputs: NotRequired[dict[str, Any]]
    eos_data: list[dict[str, Any] | str]
    version: NotRequired[str | None]
    platform: NotRequired[str | None]
    platform_modules: NotRequired[dict[str, Any] | None]
    expected: UnitTestResult


AntaUnitTestData: TypeAlias = dict[tuple[type[AntaTest], str], AntaUnitTest]


def _assert_text_items(actual: list[str], expected: list[str], *, item_name: str) -> None:
    """Assert ordered text substrings without coupling cases to complete prose."""
    assert len(actual) == len(expected), f"Expected {len(expected)} {item_name}, got {len(actual)}"
    for actual_item, expected_item in zip(actual, expected, strict=True):
        assert expected_item in actual_item, f"Expected {item_name} '{expected_item}' not found in '{actual_item}'"


def _set_device_metadata(device: AntaDevice, unit_test_data: AntaUnitTest) -> None:
    """Populate refreshed device metadata used by an ANTA test."""
    if "version" in unit_test_data:
        version = unit_test_data["version"]
        device.version = parse_eos_version(version) if version is not None else None
    if "platform" in unit_test_data:
        model = unit_test_data["platform"]
        device.hw_model = model
        platform = parse_eos_platform_or_none(model)
        if platform is not None and "platform_modules" in unit_test_data:
            module_result = parse_eos_platform_modules(platform, unit_test_data["platform_modules"])
            if isinstance(module_result, ParseSuccessful):
                platform = module_result.value
        device.platform = platform


def test(
    device: AntaDevice,
    anta_test: type[AntaTest],
    unit_test_data: AntaUnitTest,
) -> None:
    """Generic test function for AntaTest subclass.

    Generate unit tests for each AntaTest subclass.

    See `tests/units/anta_tests/README.md` for more information on how to use it.
    """
    _set_device_metadata(device, unit_test_data)

    # Instantiate the AntaTest subclass
    test_instance = anta_test(device, inputs=unit_test_data.get("inputs"), eos_data=unit_test_data["eos_data"])
    # Run the test() method
    asyncio.run(test_instance.test())

    # Assert expected result
    assert test_instance.result.result == unit_test_data["expected"]["result"], (
        f"Expected '{unit_test_data['expected']['result']}' result, got '{test_instance.result.result}'. Messages: {test_instance.result.messages}"
    )
    # Assert test messages
    if "messages" in unit_test_data["expected"]:
        _assert_text_items(test_instance.result.messages, unit_test_data["expected"]["messages"], item_name="messages")
    else:
        # Test result should not have messages
        assert test_instance.result.messages == [], "There are untested messages, see diffs with '-vv' option"

    expected_remediations = unit_test_data["expected"].get("remediations", [])
    if isinstance(test_instance.result, _AdvisoryTestResult):
        _assert_text_items(test_instance.result.remediations, expected_remediations, item_name="remediations")
    else:
        assert not expected_remediations

    # Assert atomic results
    if "atomic_results" in unit_test_data["expected"]:
        # Assert number of atomic results
        assert len(test_instance.result.atomic_results) == len(unit_test_data["expected"]["atomic_results"]), (
            f"Expected {len(unit_test_data['expected']['atomic_results'])} atomic results, got {len(test_instance.result.atomic_results)}"
        )
        # Assert each atomic result
        for atomic_result_model, expected_atomic_result_data in zip(
            test_instance.result.atomic_results,
            unit_test_data["expected"]["atomic_results"],
            strict=True,
        ):
            expected_atomic_result = expected_atomic_result_data.copy()
            atomic_result = atomic_result_model.model_dump(mode="json", exclude_none=True)
            messages = atomic_result.pop("messages")
            expected_messages = expected_atomic_result.pop("messages", [])
            expected_atomic_remediations = expected_atomic_result.pop("remediations", [])

            if isinstance(atomic_result_model, _AdvisoryAtomicTestResult):
                _assert_text_items(atomic_result_model.remediations, expected_atomic_remediations, item_name="atomic remediations")
            else:
                assert not expected_atomic_remediations

            # First assert the rest of the atomic result
            assert atomic_result == expected_atomic_result, "Expected atomic result did not match, see diffs with '-vv' option"

            # Then assert the messages if any
            if expected_messages:
                # We expect messages in atomic test result
                assert len(messages) == len(expected_messages), (
                    f"Expected {len(expected_messages)} messages, got {len(messages)} in atomic result "
                    f"with description '{atomic_result['description']}', see diffs with '-vv' option"
                )
                # Test will pass if the expected message is included in the atomic test result message
                for message, expected in zip(messages, expected_messages, strict=True):
                    assert expected in message, f"Expected message '{expected}' not found in '{message}'"
            else:
                # Atomic test result should not have messages
                assert messages == [], f"There are untested messages in atomic result with description '{atomic_result['description']}', see diffs with '-vv' option"
    else:
        # Test result should not have atomic results
        assert test_instance.result.atomic_results == [], "There are untested atomic results, see diffs with '-vv' option"
