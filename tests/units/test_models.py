"""
test anta.models.py
"""
from __future__ import annotations

import asyncio
from typing import Any, Dict, List
from unittest.mock import MagicMock

import pytest

from anta.models import AntaCommand, AntaTemplate, AntaTest
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

    name = "FakeTest"
    description = "ANTA test that always succeed"
    categories = []
    commands = []

    class Input(AntaTest.Input):
        string: str

    @AntaTest.anta_test
    def test(self) -> None:
        self.result.is_success(self.inputs.string)


class FakeTestWithTemplate(AntaTest):
    """ANTA test with inputs that always succeed"""

    name = "FakeTest"
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


ANTATEST_DATA: List[Dict[str, Any]] = [
    {"name": "no input", "test": FakeTest, "inputs": None, "expected": {"__init__": {"result": "unset"}, "test": {"result": "success"}}},
    {
        "name": "good input",
        "test": FakeTest,
        "inputs": {"string": "culpa! veniam quas quas veniam molestias, esse"},
        "expected": {"__init__": {"result": "error", "validation_error": "Extra inputs are not permitted"}, "test": {"result": "error"}},
    },
    {
        "name": "no input",
        "test": FakeTestWithInput,
        "inputs": None,
        "expected": {"__init__": {"result": "error", "validation_error": "Field required"}, "test": {"result": "error"}},
    },
    {
        "name": "wrong input type",
        "test": FakeTestWithInput,
        "inputs": {"string": 1},
        "expected": {"__init__": {"result": "error", "validation_error": "Input should be a valid string"}, "test": {"result": "error"}},
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
]


class Test_AntaTest:
    """
    Test for anta.models.AntaTest
    """

    @pytest.mark.parametrize("data", ANTATEST_DATA, ids=generate_test_ids(ANTATEST_DATA))
    def test__init__(self, mocked_device: MagicMock, data: Dict[str, Any]) -> None:
        test = data["test"](mocked_device, inputs=data["inputs"])
        assert test.result.result == data["expected"]["__init__"]["result"]
        # If provided, test that the pydantic ValidationError message matches what is expected
        if "validation_error" in data["expected"]["__init__"]:
            for err in test.result.error.errors():
                if err["type"] == "missing" or any(err["input"] == input for input in data["inputs"].values()):
                    assert err["msg"] == data["expected"]["__init__"]["validation_error"]
                    return
            assert False

    @pytest.mark.parametrize("data", ANTATEST_DATA, ids=generate_test_ids(ANTATEST_DATA))
    def test_test(self, mocked_device: MagicMock, data: Dict[str, Any]) -> None:
        test = data["test"](mocked_device, inputs=data["inputs"])
        asyncio.run(test.test())
        assert test.result.result == data["expected"]["test"]["result"]
        # Test that the test() code works as expected
        if "message" in data["expected"]["test"]:
            assert data["expected"]["test"]["message"] in test.result.messages
