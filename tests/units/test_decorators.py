# Copyright (c) 2023-2026 Arista Networks, Inc.
# Use of this source code is governed by the Apache License 2.0
# that can be found in the LICENSE file.
"""test anta.decorators.py."""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING, ClassVar

import pytest

from anta.decorators import deprecated_test, deprecated_test_class, preview_test_class, skip_on_platforms
from anta.models import AntaCommand, AntaTemplate, AntaTest

if TYPE_CHECKING:
    from anta.device import AntaDevice


class ExampleTest(AntaTest):
    """ANTA test that always succeed."""

    categories: ClassVar[list[str]] = []
    commands: ClassVar[list[AntaCommand | AntaTemplate]] = []

    @AntaTest.anta_test
    def test(self) -> None:
        """Test function."""
        self.result.is_success()


@pytest.mark.parametrize(
    "new_tests",
    [
        pytest.param(None, id="No new_tests"),
        pytest.param(["NewExampleTest"], id="one new_tests"),
        pytest.param(["NewExampleTest1", "NewExampleTest2"], id="multiple new_tests"),
    ],
)
def test_deprecated_test_class(caplog: pytest.LogCaptureFixture, device: AntaDevice, new_tests: list[str] | None) -> None:
    """Test deprecated_test_class decorator only logs the warning once per test class."""
    caplog.set_level(logging.INFO)

    decorated_test_class = deprecated_test_class(new_tests=new_tests)(ExampleTest)

    decorated_test_class(device)
    decorated_test_class(device)

    if new_tests is None:
        warning = "ExampleTest test is deprecated."
    else:
        warning = f"ExampleTest test is deprecated. Consider using the following new tests: {', '.join(new_tests)}."
    assert caplog.messages.count(warning) == 1


@pytest.mark.parametrize(
    "new_tests",
    [
        pytest.param(None, id="No new_tests"),
        pytest.param(["NewExampleTest"], id="one new_tests"),
        pytest.param(["NewExampleTest1", "NewExampleTest2"], id="multiple new_tests"),
    ],
)
async def test_deprecated_test(caplog: pytest.LogCaptureFixture, device: AntaDevice, new_tests: list[str] | None) -> None:
    """Test deprecated_test decorator only logs the warning once per test function."""
    test_instance = ExampleTest(device)
    caplog.clear()
    decorated_test = deprecated_test(new_tests=new_tests)(ExampleTest.test)

    await decorated_test(test_instance)
    await decorated_test(test_instance)

    if new_tests is None:
        warning = "ExampleTest test is deprecated."
    else:
        warning = f"ExampleTest test is deprecated. Consider using the following new tests: {', '.join(new_tests)}."
    assert caplog.messages.count(warning) == 1


def test_preview_test_class_warns_once(caplog: pytest.LogCaptureFixture, device: AntaDevice) -> None:
    """Test preview_test_class decorator only logs the warning once per test class."""
    caplog.set_level(logging.WARNING)
    decorated_test_class = preview_test_class(ExampleTest)

    decorated_test_class(device)
    decorated_test_class(device)

    warning = "ExampleTest test is in preview. Input models and behavior may change between minor releases."
    assert caplog.messages.count(warning) == 1


@pytest.mark.parametrize(
    ("platforms", "device_platform", "expected_result"),
    [
        pytest.param([], "cEOS-lab", "success", id="empty platforms"),
        pytest.param(["cEOS-lab"], "cEOS-lab", "skipped", id="skip on one platform - match"),
        pytest.param(["cEOS-lab"], "vEOS", "success", id="skip on one platform - no match"),
        pytest.param(["cEOS-lab", "vEOS"], "cEOS-lab", "skipped", id="skip on multiple platforms - match"),
    ],
)
async def test_skip_on_platforms(device: AntaDevice, platforms: list[str], device_platform: str, expected_result: str) -> None:
    """Test skip_on_platforms decorator.

    Leverage the ExampleTest defined at the top of the module.
    """
    # Apply the decorator - ignoring mypy warning - this is for testing
    ExampleTest.test = skip_on_platforms(platforms)(ExampleTest.test)  # type: ignore[method-assign]

    device.hw_model = device_platform

    test_instance = ExampleTest(device)
    await test_instance.test()

    assert test_instance.result.result == expected_result
