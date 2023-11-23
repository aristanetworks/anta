# Copyright (c) 2023 Arista Networks, Inc.
# Use of this source code is governed by the Apache License 2.0
# that can be found in the LICENSE file.
"""
test anta.models.py
"""
# Mypy does not understand AntaTest.Input typing
# mypy: disable-error-code=attr-defined
from __future__ import annotations

import asyncio
from typing import Any

import pytest

from anta.decorators import deprecated_test, skip_on_platforms
from anta.device import AntaDevice
from anta.models import AntaCommand, AntaTemplate, AntaTest
from tests.lib.fixture import DEVICE_HW_MODEL
from tests.lib.utils import generate_test_ids


class FakeTest(AntaTest):
    """ANTA test that always succeed"""

    name = "FakeTest"
    description = "ANTA test that always succeed"
    categories = []
    commands = []

    @AntaTest.anta_test
    def test(self) -> None:
        self.result.is_success()


class FakeTestWithFailedCommand(AntaTest):
    """ANTA test with a command that failed"""

    name = "FakeTestWithFailedCommand"
    description = "ANTA test with a command that failed"
    categories = []
    commands = [AntaCommand(command="show version", errors=["failed command"])]

    @AntaTest.anta_test
    def test(self) -> None:
        self.result.is_success()


class FakeTestWithUnsupportedCommand(AntaTest):
    """ANTA test with an unsupported command"""

    name = "FakeTestWithUnsupportedCommand"
    description = "ANTA test with an unsupported command"
    categories = []
    commands = [AntaCommand(command="show hardware counter drop", errors=["Unavailable command (not supported on this hardware platform) (at token 2: 'counter')"])]

    @AntaTest.anta_test
    def test(self) -> None:
        self.result.is_success()


class FakeTestWithInput(AntaTest):
    """ANTA test with inputs that always succeed"""

    name = "FakeTestWithInput"
    description = "ANTA test with inputs that always succeed"
    categories = []
    commands = []

    class Input(AntaTest.Input):  # pylint: disable=missing-class-docstring
        string: str

    @AntaTest.anta_test
    def test(self) -> None:
        self.result.is_success(self.inputs.string)


class FakeTestWithTemplate(AntaTest):
    """ANTA test with template that always succeed"""

    name = "FakeTestWithTemplate"
    description = "ANTA test with template that always succeed"
    categories = []
    commands = [AntaTemplate(template="show interface {interface}")]

    class Input(AntaTest.Input):  # pylint: disable=missing-class-docstring
        interface: str

    def render(self, template: AntaTemplate) -> list[AntaCommand]:
        return [template.render(interface=self.inputs.interface)]

    @AntaTest.anta_test
    def test(self) -> None:
        self.result.is_success(self.instance_commands[0].command)


class FakeTestWithTemplateNoRender(AntaTest):
    """ANTA test with template that miss the render() method"""

    name = "FakeTestWithTemplateNoRender"
    description = "ANTA test with template that miss the render() method"
    categories = []
    commands = [AntaTemplate(template="show interface {interface}")]

    class Input(AntaTest.Input):  # pylint: disable=missing-class-docstring
        interface: str

    @AntaTest.anta_test
    def test(self) -> None:
        self.result.is_success(self.instance_commands[0].command)


class FakeTestWithTemplateWrongRender(AntaTest):
    """ANTA test with template that raises a AntaTemplateRenderError exception"""

    name = "FakeTestWithTemplateWrongRender"
    description = "ANTA test with template that raises a AntaTemplateRenderError exception"
    categories = []
    commands = [AntaTemplate(template="show interface {interface}")]

    class Input(AntaTest.Input):  # pylint: disable=missing-class-docstring
        interface: str

    def render(self, template: AntaTemplate) -> list[AntaCommand]:
        return [template.render(wrong_template_param=self.inputs.interface)]

    @AntaTest.anta_test
    def test(self) -> None:
        self.result.is_success(self.instance_commands[0].command)


class SkipOnPlatformTest(AntaTest):
    """ANTA test that is skipped"""

    name = "SkipOnPlatformTest"
    description = "ANTA test that is skipped on a specific platform"
    categories = []
    commands = []

    @skip_on_platforms([DEVICE_HW_MODEL])
    @AntaTest.anta_test
    def test(self) -> None:
        self.result.is_success()


class UnSkipOnPlatformTest(AntaTest):
    """ANTA test that is skipped"""

    name = "UnSkipOnPlatformTest"
    description = "ANTA test that is skipped on a specific platform"
    categories = []
    commands = []

    @skip_on_platforms(["dummy"])
    @AntaTest.anta_test
    def test(self) -> None:
        self.result.is_success()


class SkipOnPlatformTestWithInput(AntaTest):
    """ANTA test skipped on platforms but with Input"""

    name = "SkipOnPlatformTestWithInput"
    description = "ANTA test skipped on platforms but with Input"
    categories = []
    commands = []

    class Input(AntaTest.Input):  # pylint: disable=missing-class-docstring
        string: str

    @skip_on_platforms([DEVICE_HW_MODEL])
    @AntaTest.anta_test
    def test(self) -> None:
        self.result.is_success(self.inputs.string)


class DeprecatedTestWithoutNewTest(AntaTest):
    """ANTA test that is deprecated without new test"""

    name = "DeprecatedTestWitouthNewTest"
    description = "ANTA test that is deprecated without new test"
    categories = []
    commands = []

    @deprecated_test()
    @AntaTest.anta_test
    def test(self) -> None:
        self.result.is_success()


class DeprecatedTestWithNewTest(AntaTest):
    """ANTA test that is deprecated with new test."""

    name = "DeprecatedTestWithNewTest"
    description = "ANTA deprecated test with New Test"
    categories = []
    commands = []

    @deprecated_test(new_tests=["NewTest"])
    @AntaTest.anta_test
    def test(self) -> None:
        self.result.is_success()


ANTATEST_DATA: list[dict[str, Any]] = [
    {"name": "no input", "test": FakeTest, "inputs": None, "expected": {"__init__": {"result": "unset"}, "test": {"result": "success"}}},
    {
        "name": "extra input",
        "test": FakeTest,
        "inputs": {"string": "culpa! veniam quas quas veniam molestias, esse"},
        "expected": {"__init__": {"result": "error", "messages": ["Extra inputs are not permitted"]}, "test": {"result": "error"}},
    },
    {
        "name": "no input",
        "test": FakeTestWithInput,
        "inputs": None,
        "expected": {"__init__": {"result": "error", "messages": ["Field required"]}, "test": {"result": "error"}},
    },
    {
        "name": "wrong input type",
        "test": FakeTestWithInput,
        "inputs": {"string": 1},
        "expected": {"__init__": {"result": "error", "messages": ["Input should be a valid string"]}, "test": {"result": "error"}},
    },
    {
        "name": "good input",
        "test": FakeTestWithInput,
        "inputs": {"string": "culpa! veniam quas quas veniam molestias, esse"},
        "expected": {"__init__": {"result": "unset"}, "test": {"result": "success", "messages": ["culpa! veniam quas quas veniam molestias, esse"]}},
    },
    {
        "name": "good input",
        "test": FakeTestWithTemplate,
        "inputs": {"interface": "Ethernet1"},
        "expected": {"__init__": {"result": "unset"}, "test": {"result": "success", "messages": ["show interface Ethernet1"]}},
    },
    {
        "name": "wrong input type",
        "test": FakeTestWithTemplate,
        "inputs": {"interface": 1},
        "expected": {"__init__": {"result": "error", "messages": ["Input should be a valid string"]}, "test": {"result": "error"}},
    },
    {
        "name": "wrong render definition",
        "test": FakeTestWithTemplateNoRender,
        "inputs": {"interface": "Ethernet1"},
        "expected": {
            "__init__": {
                "result": "error",
                "messages": ["AntaTemplate are provided but render() method has not been implemented for tests.units.test_models.FakeTestWithTemplateNoRender"],
            },
            "test": {"result": "error"},
        },
    },
    {
        "name": "wrong render logic",
        "test": FakeTestWithTemplateWrongRender,
        "inputs": {"interface": "Ethernet1"},
        "expected": {
            "__init__": {
                "result": "error",
                "messages": ["Cannot render template {template='show interface {interface}' version='latest' revision=None ofmt='json' use_cache=True}"],
            },
            "test": {"result": "error"},
        },
    },
    {
        "name": "unskip on platforms",
        "test": UnSkipOnPlatformTest,
        "inputs": None,
        "expected": {
            "__init__": {"result": "unset"},
            "test": {"result": "success"},
        },
    },
    {
        "name": "skip on platforms, unset",
        "test": SkipOnPlatformTest,
        "inputs": None,
        "expected": {
            "__init__": {"result": "unset"},
            "test": {"result": "skipped"},
        },
    },
    {
        "name": "skip on platforms, not unset",
        "test": SkipOnPlatformTestWithInput,
        "inputs": None,
        "expected": {"__init__": {"result": "error", "messages": ["Field required"]}, "test": {"result": "error"}},
    },
    {
        "name": "deprecate test without new test",
        "test": DeprecatedTestWithoutNewTest,
        "inputs": None,
        "expected": {
            "__init__": {"result": "unset"},
            "test": {"result": "success"},
        },
    },
    {
        "name": "deprecate test with new test",
        "test": DeprecatedTestWithNewTest,
        "inputs": None,
        "expected": {
            "__init__": {"result": "unset"},
            "test": {"result": "success"},
        },
    },
    {
        "name": "failed command",
        "test": FakeTestWithFailedCommand,
        "inputs": None,
        "expected": {"__init__": {"result": "unset"}, "test": {"result": "error", "messages": ["show version has failed: failed command"]}},
    },
    {
        "name": "unsupported command",
        "test": FakeTestWithUnsupportedCommand,
        "inputs": None,
        "expected": {
            "__init__": {"result": "unset"},
            "test": {"result": "skipped", "messages": ["Skipped because show hardware counter drop is not supported on pytest"]},
        },
    },
]


class Test_AntaTest:
    """
    Test for anta.models.AntaTest
    """

    def test__init_subclass__name(self) -> None:
        """Test __init_subclass__"""
        # Pylint detects all the classes in here as unused which is on purpose
        # pylint: disable=unused-variable
        with pytest.raises(NotImplementedError) as exec_info:

            class WrongTestNoName(AntaTest):
                """ANTA test that is missing a name"""

                description = "ANTA test that is missing a name"
                categories = []
                commands = []

                @AntaTest.anta_test
                def test(self) -> None:
                    self.result.is_success()

        assert exec_info.value.args[0] == "Class tests.units.test_models.WrongTestNoName is missing required class attribute name"

        with pytest.raises(NotImplementedError) as exec_info:

            class WrongTestNoDescription(AntaTest):
                """ANTA test that is missing a description"""

                name = "WrongTestNoDescription"
                categories = []
                commands = []

                @AntaTest.anta_test
                def test(self) -> None:
                    self.result.is_success()

        assert exec_info.value.args[0] == "Class tests.units.test_models.WrongTestNoDescription is missing required class attribute description"

        with pytest.raises(NotImplementedError) as exec_info:

            class WrongTestNoCategories(AntaTest):
                """ANTA test that is missing categories"""

                name = "WrongTestNoCategories"
                description = "ANTA test that is missing categories"
                commands = []

                @AntaTest.anta_test
                def test(self) -> None:
                    self.result.is_success()

        assert exec_info.value.args[0] == "Class tests.units.test_models.WrongTestNoCategories is missing required class attribute categories"

        with pytest.raises(NotImplementedError) as exec_info:

            class WrongTestNoCommands(AntaTest):
                """ANTA test that is missing commands"""

                name = "WrongTestNoCommands"
                description = "ANTA test that is missing commands"
                categories = []

                @AntaTest.anta_test
                def test(self) -> None:
                    self.result.is_success()

        assert exec_info.value.args[0] == "Class tests.units.test_models.WrongTestNoCommands is missing required class attribute commands"

    def _assert_test(self, test: AntaTest, expected: dict[str, Any]) -> None:
        assert test.result.result == expected["result"]
        if "messages" in expected:
            for result_msg, expected_msg in zip(test.result.messages, expected["messages"]):  # NOTE: zip(strict=True) has been added in Python 3.10
                assert expected_msg in result_msg

    @pytest.mark.parametrize("data", ANTATEST_DATA, ids=generate_test_ids(ANTATEST_DATA))
    def test__init__(self, device: AntaDevice, data: dict[str, Any]) -> None:
        """Test the AntaTest constructor"""
        expected = data["expected"]["__init__"]
        test = data["test"](device, inputs=data["inputs"])
        self._assert_test(test, expected)

    @pytest.mark.parametrize("data", ANTATEST_DATA, ids=generate_test_ids(ANTATEST_DATA))
    def test_test(self, device: AntaDevice, data: dict[str, Any]) -> None:
        """Test the AntaTest.test method"""
        expected = data["expected"]["test"]
        test = data["test"](device, inputs=data["inputs"])
        asyncio.run(test.test())
        self._assert_test(test, expected)


ANTATEST_BLACKLIST_DATA = ["reload", "reload --force", "write", "wr mem"]


@pytest.mark.parametrize("data", ANTATEST_BLACKLIST_DATA)
def test_blacklist(device: AntaDevice, data: str) -> None:
    """Test for blacklisting function."""

    class FakeTestWithBlacklist(AntaTest):
        """Fake Test for blacklist"""

        name = "FakeTestWithBlacklist"
        description = "ANTA test that has blacklisted command"
        categories = []
        commands = [AntaCommand(command=data)]

        @AntaTest.anta_test
        def test(self) -> None:
            self.result.is_success()

    test_instance = FakeTestWithBlacklist(device)

    # Run the test() method
    asyncio.run(test_instance.test())
    assert test_instance.result.result == "error"
