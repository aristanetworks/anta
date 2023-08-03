"""
test anta.models.py
"""
# Mypy does not understand AntaTest.Input typing
# mypy: disable-error-code=attr-defined
from __future__ import annotations

import asyncio
from typing import Any, Dict, List
from unittest.mock import MagicMock

import pytest

from pydantic import ValidationError
from anta.models import AntaCommand, AntaTemplate, AntaTest, AntaTemplateRenderError
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


class FakeTestWithInput(AntaTest):
    """ANTA test with inputs that always succeed"""

    name = "FakeTestWithInput"
    description = "ANTA test that always succeed"
    categories = []
    commands = []

    class Input(AntaTest.Input):
        string: str

    @AntaTest.anta_test
    def test(self) -> None:
        self.result.is_success(self.inputs.string)


class FakeTestWithTemplate(AntaTest):
    """ANTA test with template that always succeed"""

    name = "FakeTestWithTemplate"
    description = "ANTA test that always succeed"
    categories = []
    commands = [AntaTemplate(template="show interface {interface}")]

    class Input(AntaTest.Input):
        interface: str

    def render(self, template: AntaTemplate) -> list[AntaCommand]:
        return [template.render(interface=self.inputs.interface)]

    @AntaTest.anta_test
    def test(self) -> None:
        self.result.is_success(self.instance_commands[0].command)


class FakeTestWithTemplateNoRender(AntaTest):
    """ANTA test with template that always succeed"""

    name = "FakeTestWithTemplate"
    description = "ANTA test that always succeed"
    categories = []
    commands = [AntaTemplate(template="show interface {interface}")]

    class Input(AntaTest.Input):
        interface: str

    @AntaTest.anta_test
    def test(self) -> None:
        self.result.is_success(self.instance_commands[0].command)


class FakeTestWithTemplateWrongRender(AntaTest):
    """ANTA test with template that always succeed"""

    name = "FakeTestWithTemplate"
    description = "ANTA test that always succeed"
    categories = []
    commands = [AntaTemplate(template="show interface {interface}")]

    class Input(AntaTest.Input):
        interface: str

    def render(self, template: AntaTemplate) -> list[AntaCommand]:
        return [template.render(wrong_template_param=self.inputs.interface)]

    @AntaTest.anta_test
    def test(self) -> None:
        self.result.is_success(self.instance_commands[0].command)


ANTATEST_DATA: List[Dict[str, Any]] = [
    {"name": "no input", "test": FakeTest, "inputs": None, "expected": {"__init__": {"result": "unset"}, "test": {"result": "success"}}},
    {
        "name": "good input",
        "test": FakeTest,
        "inputs": {"string": "culpa! veniam quas quas veniam molestias, esse"},
        "expected": {"__init__": {"result": "error", "error": ValidationError, "message": "Extra inputs are not permitted"}, "test": {"result": "error"}},
    },
    {
        "name": "no input",
        "test": FakeTestWithInput,
        "inputs": None,
        "expected": {"__init__": {"result": "error", "error": ValidationError, "message": "Field required"}, "test": {"result": "error"}},
    },
    {
        "name": "wrong input type",
        "test": FakeTestWithInput,
        "inputs": {"string": 1},
        "expected": {"__init__": {"result": "error", "error": ValidationError, "message": "Input should be a valid string"}, "test": {"result": "error"}},
    },
    {
        "name": "good input",
        "test": FakeTestWithInput,
        "inputs": {"string": "culpa! veniam quas quas veniam molestias, esse"},
        "expected": {"__init__": {"result": "unset"}, "test": {"result": "success", "message": "culpa! veniam quas quas veniam molestias, esse"}},
    },
    {
        "name": "good input",
        "test": FakeTestWithTemplate,
        "inputs": {"interface": "Ethernet1"},
        "expected": {"__init__": {"result": "unset"}, "test": {"result": "success", "message": "show interface Ethernet1"}},
    },
    {
        "name": "wrong input type",
        "test": FakeTestWithTemplate,
        "inputs": {"interface": 1},
        "expected": {"__init__": {"result": "error", "error": ValidationError, "message": "Input should be a valid string"}, "test": {"result": "error"}},
    },
    {
        "name": "wrong render definition",
        "test": FakeTestWithTemplateNoRender,
        "inputs": {"interface": "Ethernet1"},
        "expected": {
            "__init__": {
                "result": "error",
                "error": NotImplementedError,
                "message": "AntaTemplate are provided but render() method has not been implemented for tests.units.test_models.FakeTestWithTemplate",
            },
            "test": {"result": "error"},
        },
    },
    {
        "name": "wrong render logic",
        "test": FakeTestWithTemplateWrongRender,
        "inputs": {"interface": "Ethernet1"},
        "expected": {
            "__init__": {"result": "error", "error": AntaTemplateRenderError, "template": FakeTestWithTemplateWrongRender.commands[0], "key": "interface"},
            "test": {"result": "error"},
        },
    },
]


class Test_AntaTest:
    """
    Test for anta.models.AntaTest
    """

    def test__init_subclass__name(self) -> None:
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

    @pytest.mark.parametrize("data", ANTATEST_DATA, ids=generate_test_ids(ANTATEST_DATA))
    def test__init__(self, mocked_device: MagicMock, data: Dict[str, Any]) -> None:
        test = data["test"](mocked_device, inputs=data["inputs"])
        assert test.result.result == data["expected"]["__init__"]["result"]
        # If provided, test that the Exception message matches what is expected
        if "error" in data["expected"]["__init__"]:
            if hasattr(test.result, "error"):
                if isinstance(test.result.error, data["expected"]["__init__"]["error"]):
                    if isinstance(test.result.error, ValidationError):
                        for err in test.result.error.errors():
                            if err["type"] == "missing" or any(err["input"] == input for input in data["inputs"].values()):
                                assert err["msg"] == data["expected"]["__init__"]["message"]
                                return
                        pytest.fail("Did not find expected ValidationError when instantiating AntaTest")
                    if isinstance(test.result.error, AntaTemplateRenderError):
                        assert test.result.error.template == data["expected"]["__init__"]["template"]
                        assert test.result.error.key == data["expected"]["__init__"]["key"]
                        return
                    if isinstance(test.result.error, Exception):
                        assert test.result.error.args[0] == data["expected"]["__init__"]["message"]
                        return
            pytest.fail("Did not find expected Exception when instantiating AntaTest")

    @pytest.mark.parametrize("data", ANTATEST_DATA, ids=generate_test_ids(ANTATEST_DATA))
    def test_test(self, mocked_device: MagicMock, data: Dict[str, Any]) -> None:
        test = data["test"](mocked_device, inputs=data["inputs"])
        asyncio.run(test.test())
        assert test.result.result == data["expected"]["test"]["result"]
        # Test that the test() code works as expected
        if "message" in data["expected"]["test"]:
            assert data["expected"]["test"]["message"] in test.result.messages
