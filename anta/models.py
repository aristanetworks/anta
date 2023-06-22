"""
Models to define a TestStructure
"""

from __future__ import annotations

import asyncio
import logging
from abc import ABC, abstractmethod
from copy import deepcopy
from functools import wraps
from typing import TYPE_CHECKING, Any, Callable, ClassVar, Coroutine, Dict, Literal, Optional, Type, TypeVar, Union

from pydantic import BaseModel, validator

from anta.result_manager.models import TestResult
from anta.tools.misc import exc_to_str, tb_to_str

if TYPE_CHECKING:
    from anta.inventory.models import AntaDevice

F = TypeVar("F", bound=Callable[..., Any])

logger = logging.getLogger(__name__)


class AntaTestTemplate(BaseModel):
    """Class to define a test command with its API version

    Attributes:
        command(str): Test command
        version: eAPI version - valid values are integers or the string "latest" - default is "latest"
        ofmt(str):  eAPI output - json or text - default is json
        output: collected output either dict for json or str for text
    """

    template: str
    version: Union[int, Literal["latest"]] = "latest"
    ofmt: str = "json"


class AntaTestCommand(BaseModel):
    """Class to define a test command with its API version

    Attributes:
        command(str): Test command
        version: eAPI version - valid values are integers or the string "latest" - default is "latest"
        ofmt(str):  eAPI output - json or text - default is json
        output: collected output either dict for json or str for text
        template Optional(AntaTestTemplate): Template used to generate the command
        template_params Optional(dict): params used in the template to generate the command
    """

    command: str
    version: Union[int, Literal["latest"]] = "latest"
    ofmt: str = "json"
    output: Optional[Union[Dict[str, Any], str]]
    template: Optional[AntaTestTemplate] = None
    template_params: Optional[Dict[str, str]]

    @validator("template_params")
    def prevent_none_when_template_is_set(cls: Type[AntaTestTemplate], value: Optional[Dict[str, str]]) -> Optional[Dict[str, str]]:  # type: ignore
        """
        Raises if template is set but no params are given
        """
        if hasattr(cls, "template") and cls.template is not None:
            assert value is not None

        return value


class AntaTestFilter(ABC):
    """Class to define a test Filter"""

    # pylint: disable=too-few-public-methods

    @abstractmethod
    def should_skip(
        self,
        device: AntaDevice,
        result: TestResult,
        *args: list[Any],
        **kwagrs: dict[str, Any],
    ) -> bool:
        """
        Sets the TestResult status to skip with the appropriate skip message

        Returns:
            bool: True if the test should be skipped, False otherwise
        """


class AntaTest(ABC):
    """Abstract class defining a test for Anta

    The goal of this class is to handle the heavy lifting and make
    writing a test as simple as possible.

    TODO - complete doctstring with example
    """

    # Mandatory class attributes
    # TODO - find a way to tell mypy these are mandatory for child classes - maybe Protocol
    name: ClassVar[str]
    description: ClassVar[str]
    categories: ClassVar[list[str]]
    # Or any child type
    commands: ClassVar[list[AntaTestCommand]]
    # TODO - today we support only one template per Test
    template: ClassVar[AntaTestTemplate]

    # Optional class attributes
    test_filters: ClassVar[list[AntaTestFilter]]

    def __init__(
        self,
        device: AntaDevice,
        template_params: list[dict[str, Any]] | None = None,
        # TODO document very well the order of eos_data
        eos_data: list[dict[Any, Any] | str] | None = None,
        labels: list[str] | None = None,
    ):
        """Class constructor"""
        self.device = device
        self.result = TestResult(name=device.name, test=self.name, test_category=self.categories, test_description=self.description)
        self.labels = labels or []

        # TODO - check optimization for deepcopy
        # Generating instance_commands from list of commands and template
        self.instance_commands = []
        if hasattr(self.__class__, "commands") and (cmds := self.__class__.commands) is not None:
            self.instance_commands.extend(deepcopy(cmds))
        if hasattr(self.__class__, "template") and (tpl := self.__class__.template) is not None:
            if template_params is None:
                self.result.is_error("Command has template but no params were given")
                return
            self.template_params = template_params
            self.instance_commands.extend(
                AntaTestCommand(
                    command=tpl.template.format(**param),
                    ofmt=tpl.ofmt,
                    version=tpl.version,
                    template=tpl,
                    template_params=param,
                )
                for param in template_params
            )

        if eos_data is not None:
            logger.debug("Test initialized with input data")
            self.save_commands_data(eos_data)

    def save_commands_data(self, eos_data: list[dict[Any, Any] | str]) -> None:
        """Called at init or at test execution time"""
        if len(eos_data) != len(self.instance_commands):
            self.result.is_error("Test initialization error: Trying to save more data than there are commands for the test")
            return
        for index, data in enumerate(eos_data or []):
            self.instance_commands[index].output = data

    def all_data_collected(self) -> bool:
        """returns True if output is populated for every command"""
        return all(command.output is not None for command in self.instance_commands)

    def __init_subclass__(cls) -> None:
        """
        Verify that the mandatory class attributes are defined
        """
        mandatory_attributes = ["name", "description", "categories"]
        for attr in mandatory_attributes:
            if not hasattr(cls, attr):
                raise NotImplementedError(f"Class {cls} is missing required class attribute {attr}")
        # Check that either commands or template exist
        if not (hasattr(cls, "commands") or hasattr(cls, "template")):
            raise NotImplementedError(f"Class {cls} is missing required either commands or template attribute")

    async def collect(self) -> None:
        """
        Method used to collect outputs of all commands of this test class from the device of this test instance.
        """
        logger.debug(f"Test {self.name} on device {self.device.name}: running command outputs collection")
        try:
            await asyncio.gather(*(self.device.collect(command=command) for command in self.instance_commands))
        except Exception as e:  # pylint: disable=broad-exception-caught
            logger.error(f"Exception raised while collecting commands for test {self.name} (on device {self.device.name}) - {exc_to_str(e)}")
            logger.debug(tb_to_str(e))
            self.result.is_error(exc_to_str(e))

    @staticmethod
    def anta_test(function: F) -> Callable[..., Coroutine[Any, Any, TestResult]]:
        """
        Decorator for anta_test that handles injecting test data if given and collecting it using asyncio if missing
        """

        @wraps(function)
        async def wrapper(
            self: AntaTest,
            eos_data: list[dict[Any, Any] | str] | None = None,
            **kwargs: dict[str, Any],
        ) -> TestResult:
            """
            Wraps the test function and implement (in this order):
            1. Instantiate the command outputs if `eos_data` is provided
            2. Collect missing command outputs from the device
            3. Run the test function
            4. Catches and set the result if the test function raises an exception

            Returns:
                TestResult: self.result, populated with the correct exit status
            """
            if self.result.result != "unset":
                return self.result

            # TODO maybe_skip decorators

            # Data
            if eos_data is not None:
                logger.debug("Test initialized with input data")
                self.save_commands_data(eos_data)

            # No test data is present, try to collect
            if not self.all_data_collected():
                await self.collect()
                if self.result.result != "unset":
                    return self.result

            try:
                if not self.all_data_collected():
                    raise ValueError("Some command output is missing")
                logger.debug(f"Test {self.name} on device {self.device.name}: running test")
                function(self, **kwargs)
            except Exception as e:  # pylint: disable=broad-exception-caught
                logger.error(f"Exception raised for test {self.name} (on device {self.device.name}) - {exc_to_str(e)}")
                logger.debug(tb_to_str(e))
                self.result.is_error(exc_to_str(e))
            return self.result

        return wrapper

    @abstractmethod
    def test(self) -> Coroutine[Any, Any, TestResult]:
        """
        This abstract method is the core of the test.
        It MUST set the correct status of self.result with the appropriate error messages

        it must be implemented as follow

        @AntaTest.anta_test
        def test(self) -> None:
           '''
           assert code
           '''
        """
