# Copyright (c) 2023-2025 Arista Networks, Inc.
# Use of this source code is governed by the Apache License 2.0
# that can be found in the LICENSE file.
"""test anta.decorators.py."""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING, ClassVar

import pytest

from anta.decorators import deprecated_test_class, skip_on_platforms
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
    """Test deprecated_test_class decorator."""
    caplog.set_level(logging.INFO)

    decorated_test_class = deprecated_test_class(new_tests=new_tests)(ExampleTest)

    # Initialize the decorated test
    decorated_test_class(device)

    if new_tests is None:
        assert "ExampleTest test is deprecated." in caplog.messages
    else:
        assert f"ExampleTest test is deprecated. Consider using the following new tests: {', '.join(new_tests)}." in caplog.messages


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
