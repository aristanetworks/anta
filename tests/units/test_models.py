# Copyright (c) 2023-2026 Arista Networks, Inc.
# Use of this source code is governed by the Apache License 2.0
# that can be found in the LICENSE file.
"""test anta.models.py."""

# Pyright does not understand AntaTest.Input typing
# pyright: reportAttributeAccessIssue=false
from __future__ import annotations

import asyncio
import sys
from typing import TYPE_CHECKING, Any, ClassVar

import pytest

from anta.decorators import deprecated_test, skip_on_platforms
from anta.models import AntaCommand, AntaTemplate, AntaTest
from anta.result_manager.models import AntaTestStatus
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


ANTATEST_DATA: dict[tuple[type[AntaTest], str], Any] = {
    (FakeTest, "no input"): {"inputs": None, "expected": {"__init__": {"result": "unset"}, "test": {"result": "success"}}},
    (FakeTest, "extra input"): {
        "inputs": {"string": "culpa! veniam quas quas veniam molestias, esse"},
        "expected": {"__init__": {"result": "error", "messages": ["Extra inputs are not permitted"]}, "test": {"result": "error"}},
    },
    (FakeTestWithInput, "no input"): {"inputs": None, "expected": {"__init__": {"result": "error", "messages": ["Field required"]}, "test": {"result": "error"}}},
    (FakeTestWithInput, "wrong input type"): {
        "inputs": {"string": 1},
        "expected": {"__init__": {"result": "error", "messages": ["Input should be a valid string"]}, "test": {"result": "error"}},
    },
    (FakeTestWithInput, "good input"): {
        "inputs": {"string": "culpa! veniam quas quas veniam molestias, esse"},
        "expected": {"__init__": {"result": "unset"}, "test": {"result": "success", "messages": ["culpa! veniam quas quas veniam molestias, esse"]}},
    },
    (FakeTestWithTemplate, "good input"): {
        "inputs": {"interface": "Ethernet1"},
        "expected": {"__init__": {"result": "unset"}, "test": {"result": "success", "messages": ["show interface Ethernet1"]}},
    },
    (FakeTestWithTemplate, "wrong input type"): {
        "inputs": {"interface": 1},
        "expected": {"__init__": {"result": "error", "messages": ["Input should be a valid string"]}, "test": {"result": "error"}},
    },
    (FakeTestWithTemplateNoRender, "wrong render definition"): {
        "inputs": {"interface": "Ethernet1"},
        "expected": {
            "__init__": {
                "result": "error",
                "messages": ["AntaTemplate are provided but render() method has not been implemented for tests.units.test_models.FakeTestWithTemplateNoRender"],
            },
            "test": {"result": "error"},
        },
    },
    (FakeTestWithTemplateBadRender1, "AntaTemplateRenderError"): {
        "inputs": {"interface": "Ethernet1"},
        "expected": {
            "__init__": {
                "result": "error",
                "messages": ["Cannot render template {template='show interface {interface}' version='latest' revision=None ofmt='json' use_cache=True}"],
            },
            "test": {"result": "error"},
        },
    },
    (FakeTestWithTemplateBadRender2, "RuntimeError in render()"): {
        "inputs": {"interface": "Ethernet1"},
        "expected": {
            "__init__": {"result": "error", "messages": ["Exception in tests.units.test_models.FakeTestWithTemplateBadRender2.render(): RuntimeError"]},
            "test": {"result": "error"},
        },
    },
    (FakeTestWithTemplateBadRender3, "Extra template parameters in render()"): {
        "inputs": {"interface": "Ethernet1"},
        "expected": {
            "__init__": {
                "result": "error",
                "messages": [
                    "Exception in tests.units.test_models.FakeTestWithTemplateBadRender3.render(): ValidationError: 1 validation error for AntaParams\nextra\n"
                    "  Extra inputs are not permitted [type=extra_forbidden, input_value='blah', input_type=str]\n"
                ],
            },
            "test": {"result": "error"},
        },
    },
    (FakeTestWithTemplateBadTest, "Access undefined template param in test()"): {
        "inputs": {"interface": "Ethernet1"},
        "expected": {
            "__init__": {"result": "unset"},
            "test": {"result": "error", "messages": ["AttributeError: 'AntaParams' object has no attribute 'wrong_template_param'"]},
        },
    },
    (UnSkipOnPlatformTest, "unskip on platforms"): {"inputs": None, "expected": {"__init__": {"result": "unset"}, "test": {"result": "success"}}},
    (SkipOnPlatformTest, "skip on platforms, unset"): {"inputs": None, "expected": {"__init__": {"result": "unset"}, "test": {"result": "skipped"}}},
    (SkipOnPlatformTestWithInput, "skip on platforms, not unset"): {
        "inputs": None,
        "expected": {"__init__": {"result": "error", "messages": ["Field required"]}, "test": {"result": "error"}},
    },
    (DeprecatedTestWithoutNewTest, "deprecate test without new test"): {
        "inputs": None,
        "expected": {"__init__": {"result": "unset"}, "test": {"result": "success"}},
    },
    (DeprecatedTestWithNewTest, "deprecate test with new test"): {"inputs": None, "expected": {"__init__": {"result": "unset"}, "test": {"result": "success"}}},
    (FakeTestWithFailedCommand, "failed command"): {
        "inputs": None,
        "expected": {"__init__": {"result": "unset"}, "test": {"result": "error", "messages": ["show version has failed: failed command"]}},
    },
    (FakeTestWithUnsupportedCommand, "unsupported command"): {
        "inputs": None,
        "expected": {"__init__": {"result": "unset"}, "test": {"result": "skipped", "messages": ["'show hardware counter drop' is not supported on pytest"]}},
    },
    (FakeTestWithKnownEOSError, "known EOS error command"): {
        "inputs": None,
        "expected": {"__init__": {"result": "unset"}, "test": {"result": "failure", "messages": ["BGP inactive"]}},
    },
}

BLACKLIST_COMMANDS_PARAMS = ["reload", "reload now", "reload --force", "write", "wr mem", "write memory", "conf t", "configure terminal", "configure session"]


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
            match=r"Cannot set the description for class _WrongTestNoDescription, either set it in the class definition or add a docstring to the class.",
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
            for result_msg, expected_msg in zip(test.result.messages, expected["messages"], strict=True):
                assert expected_msg in result_msg

    @pytest.mark.parametrize(
        "data", ANTATEST_DATA.items(), ids=[f"{anta_test.__module__}.{anta_test.__name__}-{unit_test_name}" for (anta_test, unit_test_name) in ANTATEST_DATA]
    )
    def test__init__(self, device: AntaDevice, data: tuple[tuple[type[AntaTest], str], Any]) -> None:
        """Test the AntaTest constructor."""
        (anta_test, test_data) = data
        expected = test_data["expected"]["__init__"]
        test = anta_test[0](device, inputs=test_data["inputs"])
        self._assert_test(test, expected)

    @pytest.mark.parametrize(
        "data", ANTATEST_DATA.items(), ids=[f"{anta_test.__module__}.{anta_test.__name__}-{unit_test_name}" for (anta_test, unit_test_name) in ANTATEST_DATA]
    )
    def test_test(self, device: AntaDevice, data: tuple[tuple[type[AntaTest], str], Any]) -> None:
        """Test the AntaTest.test method."""
        (anta_test, test_data) = data
        expected = test_data["expected"]["test"]
        test = anta_test[0](device, inputs=test_data["inputs"])
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

    @pytest.mark.parametrize(
        ("categories", "description", "custom_field"),
        [
            pytest.param(["hardware"], "a description", "a custom field", id="all set"),
            pytest.param(["hardware"], "a description", None, id="no custom field"),
            pytest.param(["hardware"], None, "a custom field", id="no description"),
            pytest.param([], "a description", "a custom field", id="empty categories"),
            pytest.param(None, "a description", "a custom field", id="no categories"),
        ],
    )
    def test_result_overwrite(self, device: AntaDevice, categories: list[str] | None, description: str | None, custom_field: str) -> None:
        """Test the AntaTest.Input.ResultOverwrite model."""
        result_overwrite = {"categories": categories, "description": description, "custom_field": custom_field}
        test = FakeTest(device, inputs={"result_overwrite": result_overwrite})
        asyncio.run(test.test())

        assert test.result.result == AntaTestStatus.SUCCESS

        for category in categories or []:
            assert category in test.result.categories
        if description:
            assert test.result.description == description
        if custom_field:
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
            RuntimeError, match=r"Command 'show aaa methods accounting' has not been collected and has not returned an error. Call AntaDevice.collect()."
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
            RuntimeError, match=r"Command 'show ip interface Ethernet1' has not been collected and has not returned an error. Call AntaDevice.collect()."
        ):
            command.returned_known_eos_error
