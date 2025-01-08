# Copyright (c) 2023-2025 Arista Networks, Inc.
# Use of this source code is governed by the Apache License 2.0
# that can be found in the LICENSE file.
"""test anta.models.py."""

# Mypy does not understand AntaTest.Input typing
# mypy: disable-error-code=attr-defined
from __future__ import annotations

import asyncio
import sys
from typing import TYPE_CHECKING, Any, ClassVar

import pytest

from anta.decorators import deprecated_test, skip_on_platforms
from anta.models import AntaCommand, AntaTemplate, AntaTest
from anta.result_manager.models import AntaTestStatus
from tests.units.anta_tests.conftest import build_test_id
from tests.units.conftest import DEVICE_HW_MODEL

if TYPE_CHECKING:
    from anta.device import AntaDevice


class FakeTest(AntaTest):
    """ANTA test that always succeed."""

    categories: ClassVar[list[str]] = []
    commands: ClassVar[list[AntaCommand | AntaTemplate]] = []

    @AntaTest.anta_test
    def test(self) -> None:
        """Test function."""
        self.result.is_success()


class FakeTestWithFailedCommand(AntaTest):
    """ANTA test with a command that failed."""

    categories: ClassVar[list[str]] = []
    commands: ClassVar[list[AntaCommand | AntaTemplate]] = [AntaCommand(command="show version", errors=["failed command"])]

    @AntaTest.anta_test
    def test(self) -> None:
        """Test function."""
        self.result.is_success()


class FakeTestWithUnsupportedCommand(AntaTest):
    """ANTA test with an unsupported command."""

    categories: ClassVar[list[str]] = []
    commands: ClassVar[list[AntaCommand | AntaTemplate]] = [
        AntaCommand(
            command="show hardware counter drop",
            errors=["Unavailable command (not supported on this hardware platform) (at token 2: 'counter')"],
        )
    ]

    @AntaTest.anta_test
    def test(self) -> None:
        """Test function."""
        self.result.is_success()


class FakeTestWithKnownEOSError(AntaTest):
    """ANTA test triggering a known EOS Error that should translate to failure of the test."""

    categories: ClassVar[list[str]] = []
    commands: ClassVar[list[AntaCommand | AntaTemplate]] = [
        AntaCommand(
            command="show bgp evpn route-type mac-ip aa:c1:ab:de:50:ad vni 10010",
            errors=["BGP inactive"],
        )
    ]

    @AntaTest.anta_test
    def test(self) -> None:
        """Test function."""
        self.result.is_success()


class FakeTestWithInput(AntaTest):
    """ANTA test with inputs that always succeed."""

    categories: ClassVar[list[str]] = []
    commands: ClassVar[list[AntaCommand | AntaTemplate]] = []

    class Input(AntaTest.Input):
        """Inputs for FakeTestWithInput test."""

        string: str

    @AntaTest.anta_test
    def test(self) -> None:
        """Test function."""
        self.result.is_success(self.inputs.string)


class FakeTestWithTemplate(AntaTest):
    """ANTA test with template that always succeed."""

    categories: ClassVar[list[str]] = []
    commands: ClassVar[list[AntaCommand | AntaTemplate]] = [AntaTemplate(template="show interface {interface}")]

    class Input(AntaTest.Input):
        """Inputs for FakeTestWithTemplate test."""

        interface: str

    def render(self, template: AntaTemplate) -> list[AntaCommand]:
        """Render function."""
        return [template.render(interface=self.inputs.interface)]

    @AntaTest.anta_test
    def test(self) -> None:
        """Test function."""
        self.result.is_success(self.instance_commands[0].command)


class FakeTestWithTemplateNoRender(AntaTest):
    """ANTA test with template that miss the render() method."""

    categories: ClassVar[list[str]] = []
    commands: ClassVar[list[AntaCommand | AntaTemplate]] = [AntaTemplate(template="show interface {interface}")]

    class Input(AntaTest.Input):
        """Inputs for FakeTestWithTemplateNoRender test."""

        interface: str

    @AntaTest.anta_test
    def test(self) -> None:
        """Test function."""
        self.result.is_success(self.instance_commands[0].command)


class FakeTestWithTemplateBadRender1(AntaTest):
    """ANTA test with template that raises a AntaTemplateRenderError exception."""

    categories: ClassVar[list[str]] = []
    commands: ClassVar[list[AntaCommand | AntaTemplate]] = [AntaTemplate(template="show interface {interface}")]

    class Input(AntaTest.Input):
        """Inputs for FakeTestWithTemplateBadRender1 test."""

        interface: str

    def render(self, template: AntaTemplate) -> list[AntaCommand]:
        """Render function."""
        return [template.render(wrong_template_param=self.inputs.interface)]

    @AntaTest.anta_test
    def test(self) -> None:
        """Test function."""
        self.result.is_success(self.instance_commands[0].command)


class FakeTestWithTemplateBadRender2(AntaTest):
    """ANTA test with template that raises an arbitrary exception in render()."""

    categories: ClassVar[list[str]] = []
    commands: ClassVar[list[AntaCommand | AntaTemplate]] = [AntaTemplate(template="show interface {interface}")]

    class Input(AntaTest.Input):
        """Inputs for FakeTestWithTemplateBadRender2 test."""

        interface: str

    def render(self, template: AntaTemplate) -> list[AntaCommand]:
        """Render function."""
        raise RuntimeError(template)

    @AntaTest.anta_test
    def test(self) -> None:
        """Test function."""
        self.result.is_success(self.instance_commands[0].command)


class FakeTestWithTemplateBadRender3(AntaTest):
    """ANTA test with template that gives extra template parameters in render()."""

    categories: ClassVar[list[str]] = []
    commands: ClassVar[list[AntaCommand | AntaTemplate]] = [AntaTemplate(template="show interface {interface}")]

    class Input(AntaTest.Input):
        """Inputs for FakeTestWithTemplateBadRender3 test."""

        interface: str

    def render(self, template: AntaTemplate) -> list[AntaCommand]:
        """Render function."""
        return [template.render(interface=self.inputs.interface, extra="blah")]

    @AntaTest.anta_test
    def test(self) -> None:
        """Test function."""
        self.result.is_success(self.instance_commands[0].command)


class FakeTestWithTemplateBadTest(AntaTest):
    """ANTA test with template that tries to access an undefined template parameter in test()."""

    categories: ClassVar[list[str]] = []
    commands: ClassVar[list[AntaCommand | AntaTemplate]] = [AntaTemplate(template="show interface {interface}")]

    class Input(AntaTest.Input):
        """Inputs for FakeTestWithTemplateBadTest test."""

        interface: str

    def render(self, template: AntaTemplate) -> list[AntaCommand]:
        """Render function."""
        return [template.render(interface=self.inputs.interface)]

    @AntaTest.anta_test
    def test(self) -> None:
        """Test function."""
        # The following line must raise AttributeError at runtime
        self.result.is_success(self.instance_commands[0].params.wrong_template_param)


class SkipOnPlatformTest(AntaTest):
    """ANTA test that is skipped."""

    categories: ClassVar[list[str]] = []
    commands: ClassVar[list[AntaCommand | AntaTemplate]] = []

    @skip_on_platforms([DEVICE_HW_MODEL])
    @AntaTest.anta_test
    def test(self) -> None:
        """Test function."""
        self.result.is_success()


class UnSkipOnPlatformTest(AntaTest):
    """ANTA test that is skipped."""

    categories: ClassVar[list[str]] = []
    commands: ClassVar[list[AntaCommand | AntaTemplate]] = []

    @skip_on_platforms(["dummy"])
    @AntaTest.anta_test
    def test(self) -> None:
        """Test function."""
        self.result.is_success()


class SkipOnPlatformTestWithInput(AntaTest):
    """ANTA test skipped on platforms but with Input."""

    categories: ClassVar[list[str]] = []
    commands: ClassVar[list[AntaCommand | AntaTemplate]] = []

    class Input(AntaTest.Input):
        """Inputs for SkipOnPlatformTestWithInput test."""

        string: str

    @skip_on_platforms([DEVICE_HW_MODEL])
    @AntaTest.anta_test
    def test(self) -> None:
        """Test function."""
        self.result.is_success(self.inputs.string)


class DeprecatedTestWithoutNewTest(AntaTest):
    """ANTA test that is deprecated without new test."""

    categories: ClassVar[list[str]] = []
    commands: ClassVar[list[AntaCommand | AntaTemplate]] = []

    @deprecated_test()
    @AntaTest.anta_test
    def test(self) -> None:
        """Test function."""
        self.result.is_success()


class DeprecatedTestWithNewTest(AntaTest):
    """ANTA test that is deprecated with new test."""

    categories: ClassVar[list[str]] = []
    commands: ClassVar[list[AntaCommand | AntaTemplate]] = []

    @deprecated_test(new_tests=["NewTest"])
    @AntaTest.anta_test
    def test(self) -> None:
        """Test function."""
        self.result.is_success()


class FakeTestWithMissingTest(AntaTest):
    """ANTA test with missing test() method implementation."""

    categories: ClassVar[list[str]] = []
    commands: ClassVar[list[AntaCommand | AntaTemplate]] = []


ANTATEST_DATA: list[dict[str, Any]] = [
    {
        "name": "no input",
        "test": FakeTest,
        "inputs": None,
        "expected": {"__init__": {"result": "unset"}, "test": {"result": "success"}},
    },
    {
        "name": "extra input",
        "test": FakeTest,
        "inputs": {"string": "culpa! veniam quas quas veniam molestias, esse"},
        "expected": {
            "__init__": {
                "result": "error",
                "messages": ["Extra inputs are not permitted"],
            },
            "test": {"result": "error"},
        },
    },
    {
        "name": "no input",
        "test": FakeTestWithInput,
        "inputs": None,
        "expected": {
            "__init__": {"result": "error", "messages": ["Field required"]},
            "test": {"result": "error"},
        },
    },
    {
        "name": "wrong input type",
        "test": FakeTestWithInput,
        "inputs": {"string": 1},
        "expected": {
            "__init__": {
                "result": "error",
                "messages": ["Input should be a valid string"],
            },
            "test": {"result": "error"},
        },
    },
    {
        "name": "good input",
        "test": FakeTestWithInput,
        "inputs": {"string": "culpa! veniam quas quas veniam molestias, esse"},
        "expected": {
            "__init__": {"result": "unset"},
            "test": {
                "result": "success",
                "messages": ["culpa! veniam quas quas veniam molestias, esse"],
            },
        },
    },
    {
        "name": "good input",
        "test": FakeTestWithTemplate,
        "inputs": {"interface": "Ethernet1"},
        "expected": {
            "__init__": {"result": "unset"},
            "test": {"result": "success", "messages": ["show interface Ethernet1"]},
        },
    },
    {
        "name": "wrong input type",
        "test": FakeTestWithTemplate,
        "inputs": {"interface": 1},
        "expected": {
            "__init__": {
                "result": "error",
                "messages": ["Input should be a valid string"],
            },
            "test": {"result": "error"},
        },
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
        "name": "AntaTemplateRenderError",
        "test": FakeTestWithTemplateBadRender1,
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
        "name": "RuntimeError in render()",
        "test": FakeTestWithTemplateBadRender2,
        "inputs": {"interface": "Ethernet1"},
        "expected": {
            "__init__": {
                "result": "error",
                "messages": ["Exception in tests.units.test_models.FakeTestWithTemplateBadRender2.render(): RuntimeError"],
            },
            "test": {"result": "error"},
        },
    },
    {
        "name": "Extra template parameters in render()",
        "test": FakeTestWithTemplateBadRender3,
        "inputs": {"interface": "Ethernet1"},
        "expected": {
            "__init__": {
                "result": "error",
                "messages": [
                    "Exception in tests.units.test_models.FakeTestWithTemplateBadRender3.render(): ValidationError: 1 validation error for AntaParams\n"
                    "extra\n"
                    "  Extra inputs are not permitted [type=extra_forbidden, input_value='blah', input_type=str]\n"
                ],
            },
            "test": {"result": "error"},
        },
    },
    {
        "name": "Access undefined template param in test()",
        "test": FakeTestWithTemplateBadTest,
        "inputs": {"interface": "Ethernet1"},
        "expected": {
            "__init__": {"result": "unset"},
            "test": {"result": "error", "messages": ["AttributeError: 'AntaParams' object has no attribute 'wrong_template_param'"]},
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
        "expected": {
            "__init__": {"result": "error", "messages": ["Field required"]},
            "test": {"result": "error"},
        },
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
        "expected": {
            "__init__": {"result": "unset"},
            "test": {
                "result": "error",
                "messages": ["show version has failed: failed command"],
            },
        },
    },
    {
        "name": "unsupported command",
        "test": FakeTestWithUnsupportedCommand,
        "inputs": None,
        "expected": {
            "__init__": {"result": "unset"},
            "test": {
                "result": "skipped",
                "messages": ["'show hardware counter drop' is not supported on pytest"],
            },
        },
    },
    {
        "name": "known EOS error command",
        "test": FakeTestWithKnownEOSError,
        "inputs": None,
        "expected": {
            "__init__": {"result": "unset"},
            "test": {
                "result": "failure",
                "messages": ["BGP inactive"],
            },
        },
    },
]

BLACKLIST_COMMANDS_PARAMS = ["reload", "reload --force", "write", "wr mem"]


class TestAntaTest:
    """Test for anta.models.AntaTest."""

    def test__init_subclass__(self) -> None:
        """Test __init_subclass__."""
        with pytest.raises(AttributeError) as exec_info:

            class _WrongTestNoCategories(AntaTest):
                """ANTA test that is missing categories."""

                commands: ClassVar[list[AntaCommand | AntaTemplate]] = []

                @AntaTest.anta_test
                def test(self) -> None:
                    self.result.is_success()

        assert exec_info.value.args[0] == "Class tests.units.test_models._WrongTestNoCategories is missing required class attribute(s): categories"

        with pytest.raises(AttributeError) as exec_info:

            class _WrongTestNoCommands(AntaTest):
                """ANTA test that is missing commands."""

                categories: ClassVar[list[str]] = []

                @AntaTest.anta_test
                def test(self) -> None:
                    self.result.is_success()

        assert exec_info.value.args[0] == "Class tests.units.test_models._WrongTestNoCommands is missing required class attribute(s): commands"

        with pytest.raises(
            AttributeError,
            match="Cannot set the description for class _WrongTestNoDescription, either set it in the class definition or add a docstring to the class.",
        ):

            class _WrongTestNoDescription(AntaTest):
                # ANTA test that is missing a description and does not have a doctstring.

                commands: ClassVar[list[AntaCommand | AntaTemplate]] = []
                categories: ClassVar[list[str]] = []

                @AntaTest.anta_test
                def test(self) -> None:
                    self.result.is_success()

        class _TestOverwriteNameAndDescription(AntaTest):
            """ANTA test where both the test name and description are overwritten in the class definition."""

            name: ClassVar[str] = "CustomName"
            description: ClassVar[str] = "Custom description"
            commands: ClassVar[list[AntaCommand | AntaTemplate]] = []
            categories: ClassVar[list[str]] = []

            @AntaTest.anta_test
            def test(self) -> None:
                self.result.is_success()

        assert _TestOverwriteNameAndDescription.name == "CustomName"
        assert _TestOverwriteNameAndDescription.description == "Custom description"

    def test_abc(self) -> None:
        """Test that an error is raised if AntaTest is not implemented."""
        with pytest.raises(TypeError) as exec_info:
            FakeTestWithMissingTest()  # type: ignore[abstract,call-arg]
        msg = (
            "Can't instantiate abstract class FakeTestWithMissingTest without an implementation for abstract method 'test'"
            if sys.version_info >= (3, 12)
            else "Can't instantiate abstract class FakeTestWithMissingTest with abstract method test"
        )
        assert exec_info.value.args[0] == msg

    def _assert_test(self, test: AntaTest, expected: dict[str, Any]) -> None:
        assert test.result.result == expected["result"]
        if "messages" in expected:
            assert len(test.result.messages) == len(expected["messages"])
            for result_msg, expected_msg in zip(test.result.messages, expected["messages"]):  # NOTE: zip(strict=True) has been added in Python 3.10
                assert expected_msg in result_msg

    @pytest.mark.parametrize("data", ANTATEST_DATA, ids=build_test_id)
    def test__init__(self, device: AntaDevice, data: dict[str, Any]) -> None:
        """Test the AntaTest constructor."""
        expected = data["expected"]["__init__"]
        test = data["test"](device, inputs=data["inputs"])
        self._assert_test(test, expected)

    @pytest.mark.parametrize("data", ANTATEST_DATA, ids=build_test_id)
    def test_test(self, device: AntaDevice, data: dict[str, Any]) -> None:
        """Test the AntaTest.test method."""
        expected = data["expected"]["test"]
        test = data["test"](device, inputs=data["inputs"])
        asyncio.run(test.test())
        self._assert_test(test, expected)

    @pytest.mark.parametrize("command", BLACKLIST_COMMANDS_PARAMS)
    def test_blacklist(self, device: AntaDevice, command: str) -> None:
        """Test that blacklisted commands are not collected."""

        class FakeTestWithBlacklist(AntaTest):
            """Fake Test for blacklist."""

            categories: ClassVar[list[str]] = []
            commands: ClassVar[list[AntaCommand | AntaTemplate]] = [AntaCommand(command=command)]

            @AntaTest.anta_test
            def test(self) -> None:
                self.result.is_success()

        test = FakeTestWithBlacklist(device)
        asyncio.run(test.test())
        assert test.result.result == AntaTestStatus.ERROR
        assert f"<{command}> is blocked for security reason" in test.result.messages
        assert test.instance_commands[0].collected is False

    def test_result_overwrite(self, device: AntaDevice) -> None:
        """Test the AntaTest.Input.ResultOverwrite model."""
        test = FakeTest(device, inputs={"result_overwrite": {"categories": ["hardware"], "description": "a description", "custom_field": "a custom field"}})
        asyncio.run(test.test())
        assert test.result.result == AntaTestStatus.SUCCESS
        assert "hardware" in test.result.categories
        assert test.result.description == "a description"
        assert test.result.custom_field == "a custom field"


class TestAntaCommand:
    """Test for anta.models.AntaCommand."""

    # ruff: noqa: B018

    def test_empty_output_access(self) -> None:
        """Test for both json and text ofmt."""
        json_cmd = AntaCommand(command="show dummy")
        text_cmd = AntaCommand(command="show dummy", ofmt="text")
        msg = "There is no output for command 'show dummy'"
        with pytest.raises(RuntimeError, match=msg):
            json_cmd.json_output
        with pytest.raises(RuntimeError, match=msg):
            text_cmd.text_output

    def test_wrong_format_output_access(self) -> None:
        """Test for both json and text ofmt."""
        json_cmd = AntaCommand(command="show dummy", output={})
        json_cmd_2 = AntaCommand(command="show dummy", output="not_json")
        text_cmd = AntaCommand(command="show dummy", ofmt="text", output="blah")
        text_cmd_2 = AntaCommand(command="show dummy", ofmt="text", output={"not_a": "string"})
        msg = "Output of command 'show dummy' is invalid"
        with pytest.raises(RuntimeError, match=msg):
            json_cmd.text_output
        with pytest.raises(RuntimeError, match=msg):
            text_cmd.json_output
        with pytest.raises(RuntimeError, match=msg):
            json_cmd_2.text_output
        with pytest.raises(RuntimeError, match=msg):
            text_cmd_2.json_output

    def test_supported(self) -> None:
        """Test the supported property."""
        command = AntaCommand(command="show hardware counter drop", errors=["Unavailable command (not supported on this hardware platform) (at token 2: 'counter')"])
        assert command.supported is False
        command = AntaCommand(
            command="show hardware counter drop", output={"totalAdverseDrops": 0, "totalCongestionDrops": 0, "totalPacketProcessorDrops": 0, "dropEvents": {}}
        )
        assert command.supported is True
        command = AntaCommand(command="show hardware counter drop")
        with pytest.raises(RuntimeError) as exec_info:
            command.supported
        assert exec_info.value.args[0] == "Command 'show hardware counter drop' has not been collected and has not returned an error. Call AntaDevice.collect()."

    def test_requires_privileges(self) -> None:
        """Test the requires_privileges property."""
        command = AntaCommand(command="show aaa methods accounting", errors=["Invalid input (privileged mode required)"])
        assert command.requires_privileges is True
        command = AntaCommand(
            command="show aaa methods accounting",
            output={
                "commandsAcctMethods": {"privilege0-15": {"defaultMethods": [], "consoleMethods": []}},
                "execAcctMethods": {"exec": {"defaultMethods": [], "consoleMethods": []}},
                "systemAcctMethods": {"system": {"defaultMethods": [], "consoleMethods": []}},
                "dot1xAcctMethods": {"dot1x": {"defaultMethods": [], "consoleMethods": []}},
            },
        )
        assert command.requires_privileges is False
        command = AntaCommand(command="show aaa methods accounting")
        with pytest.raises(
            RuntimeError, match="Command 'show aaa methods accounting' has not been collected and has not returned an error. Call AntaDevice.collect()."
        ):
            command.requires_privileges

    @pytest.mark.parametrize(
        ("command_str", "error", "is_known"),
        [
            ("show ip interface Ethernet1", "Ethernet1 does not support IP", True),
            ("ping vrf MGMT 1.1.1.1 source Management0 size 100 df-bit repeat 2", "VRF 'MGMT' is not active", True),
            ("ping vrf MGMT 1.1.1.1 source Management1 size 100 df-bit repeat 2", "No source interface Management1", True),
            ("show bgp evpn route-type mac-ip aa:c1:ab:de:50:ad vni 10010", "BGP inactive", True),
            ("show isis BLAH  neighbors", "IS-IS (BLAH) is disabled because: IS-IS Network Entity Title (NET) configuration is not present", True),
            ("show ip interface Ethernet1", None, False),
        ],
    )
    def test_returned_known_eos_error(self, command_str: str, error: str | None, is_known: bool) -> None:
        """Test the returned_known_eos_error property."""
        # Adding fake output when no error is present to mimic that the command has been collected
        command = AntaCommand(command=command_str, errors=[error] if error else [], output=None if error else "{}")
        assert command.returned_known_eos_error is is_known

    def test_returned_known_eos_error_failure(self) -> None:
        """Test the returned_known_eos_error property unset."""
        command = AntaCommand(command="show ip interface Ethernet1")
        with pytest.raises(
            RuntimeError, match="Command 'show ip interface Ethernet1' has not been collected and has not returned an error. Call AntaDevice.collect()."
        ):
            command.returned_known_eos_error
