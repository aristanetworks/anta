# Copyright (c) 2023 Arista Networks, Inc.
# Use of this source code is governed by the Apache License 2.0
# that can be found in the LICENSE file.
"""
Models to define a TestStructure
"""
from __future__ import annotations

import logging
import time
from abc import ABC, abstractmethod
from copy import deepcopy
from datetime import timedelta
from functools import wraps
from typing import TYPE_CHECKING, Any, Callable, ClassVar, Coroutine, Dict, List, Literal, Optional, TypeVar, Union

from pydantic import BaseModel, ConfigDict, ValidationError, conint
from rich.progress import Progress, TaskID

from anta.result_manager.models import TestResult
from anta.tools.misc import anta_log_exception, exc_to_str

if TYPE_CHECKING:
    from anta.device import AntaDevice

F = TypeVar("F", bound=Callable[..., Any])
DEFAULT_TAG = "all"

logger = logging.getLogger(__name__)

# TODO: Notes on eAPI version/revision
# eAPI models are revisioned, this means that if a model is modified in a non-backwards compatible way, then its revision will be bumped up
# (revisions are numbers, default value is 1).
# By default an eAPI request will return revision 1 of the model instance,
# this ensures that older management software will not suddenly stop working when a switch is upgraded.
# A "revision" applies to a particular CLI command whereas a "version" is global and is internally
# translated to a specific "revision" for each CLI command in the rpc.


class AntaTemplate(BaseModel):
    """Class to define a test command with its API version

    Attributes:
        template: Python f-string. Example: 'show vlan {vlan_id}'
        version: eAPI version - valid values are 1 or "latest" - default is "latest"
        revision: Revision of the command. Valid values are 1 to 99. Revision has precedence over version.
        ofmt: eAPI output - json or text - default is json
    """

    template: str
    version: Literal[1, "latest"] = "latest"
    revision: Optional[conint(ge=1, le=99)] = None  # type: ignore
    ofmt: Literal["json", "text"] = "json"

    def render(self, params: dict[str, Any]) -> AntaCommand:
        """Render an AntaCommand from an AntaTemplate instance.
        Keep the parameters used in the AntaTemplate instance.

         Args:
             params: dictionary of variables with string values to render the Python f-string

         Returns:
             AntaCommand: The rendered AntaCommand.
                          This AntaCommand instance have a template attribute that references this
                          AntaTemplate instance.
        """
        try:
            return AntaCommand(command=self.template.format(**params), ofmt=self.ofmt, version=self.version, revision=self.revision, template=self, params=params)
        except KeyError as e:
            raise AntaTemplateRenderError(self, e.args[0]) from e


class AntaCommand(BaseModel):
    """Class to define a test command with its API version

    Attributes:
        command: Device command
        version: eAPI version - valid values are 1 or "latest" - default is "latest"
        revision: Revision of the command. Valid values are 1 to 99. Revision has precedence over version.
        ofmt: eAPI output - json or text - default is json
        template: AntaTemplate object used to render this command
        params: dictionary of variables with string values to render the template
        failed: If the command execution fails, the Exception object is stored in this field
    """

    # This is required if we want to keep an Exception object in the failed field
    model_config = ConfigDict(arbitrary_types_allowed=True)

    command: str
    version: Literal[1, "latest"] = "latest"
    revision: Optional[conint(ge=1, le=99)] = None  # type: ignore
    ofmt: Literal["json", "text"] = "json"
    output: Optional[Union[Dict[str, Any], str]] = None
    template: Optional[AntaTemplate] = None
    failed: Optional[Exception] = None
    params: Optional[Dict[str, Any]] = None

    @property
    def json_output(self) -> dict[str, Any]:
        """Get the command output as JSON"""
        if self.output is None:
            raise RuntimeError(f"There is no output for command {self.command}")
        if self.ofmt != "json" or not isinstance(self.output, dict):
            raise RuntimeError(f"Output of command {self.command} is invalid")
        return dict(self.output)

    @property
    def text_output(self) -> str:
        """Get the command output as a string"""
        if self.output is None:
            raise RuntimeError(f"There is no output for command {self.command}")
        if self.ofmt != "text" or not isinstance(self.output, str):
            raise RuntimeError(f"Output of command {self.command} is invalid")
        return str(self.output)

    @property
    def collected(self) -> bool:
        """Return True if the command has been collected"""
        return self.output is not None and self.failed is None


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


class AntaTemplateRenderError(RuntimeError):
    """
    Raised when an AntaTemplate object could not be rendered
    because of missing parameters
    """

    def __init__(self, template: AntaTemplate, key: str):
        """Constructor for AntaTemplateRenderError

        Args:
            template: The AntaTemplate instance that failed to render
            key: Key that has not been provided to render the template
        """
        self.template = template
        self.key = key
        super().__init__()

    def __str__(self) -> str:
        """Returns the error message associated with the exception"""
        return f"{self.template}: Missing template parameter {self.key}"


class AntaTest(ABC):
    """Abstract class defining a test in ANTA

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
    commands: ClassVar[list[Union[AntaTemplate, AntaCommand]]]
    progress: Optional[Progress] = None
    nrfu_task: Optional[TaskID] = None

    # Optional class attributes
    test_filters: ClassVar[list[AntaTestFilter]]

    class Input(ABC, BaseModel):
        """Abstract class defining inputs for a test in ANTA.

        A valid test catalog will looks like:

        <Python module>:
            - <AntaTest subclass>:
                result_overwrite:
                    categories:
                        - "Overwritten category 1"
                    description: "Test with overwritten description"
                    custom_field: "Test run by John Doe"

        Args:
            result_overwrite: Define fields to overwrite in the TestResult object
        """

        class ResultOverwrite(BaseModel):
            """Test inputs model to overwrite result fields

            Args:
                custom_field: a free string that will be included in the TestResult object
            """

            description: Optional[str] = None
            categories: Optional[List[str]] = None
            custom_field: Optional[str] = None

        result_overwrite: Optional[ResultOverwrite] = None

    def __init__(
        self,
        device: AntaDevice,
        inputs: dict[str, Any] | None,
        # TODO document very well the order of eos_data
        eos_data: list[dict[Any, Any] | str] | None = None,
        labels: list[str] | None = None,
    ):
        """AntaTest Constructor"""
        self.logger: logging.Logger = logging.getLogger(f"{self.__module__}.{self.__class__.__name__}")
        self.device: AntaDevice = device
        self.labels: list[str] = labels or []
        self.instance_commands: list[AntaCommand] = []
        self.result: TestResult = TestResult(name=device.name, test=self.name, categories=self.categories, description=self.description)
        # Instantiate AntaTest.TestInput to validate test inputs from defined model
        try:
            if inputs:
                self.inputs = self.Input(**inputs)  # type: ignore[attr-defined]
            else:
                self.inputs = self.Input()  # type: ignore[attr-defined]
        except ValidationError as e:
            self.logger.error(f"{self.__module__}.{self.__class__.__name__}: inputs are not valid: {e}")
            self.result.is_error(str(e))
            return
        if res_ow := self.inputs.result_overwrite:
            if res_ow.categories:
                self.result.categories = res_ow.categories
            if res_ow.description:
                self.result.description = res_ow.description
            self.result.custom_field = res_ow.custom_field

        if self.__class__.commands:
            for cmd in self.__class__.commands:
                if isinstance(cmd, AntaCommand):
                    self.instance_commands.append(deepcopy(cmd))
                elif isinstance(cmd, AntaTemplate):
                    try:
                        self.instance_commands.extend(self.render(cmd))
                    except AntaTemplateRenderError as e:
                        self.result.is_error(f"Cannot render template {{{e.template}}}")
                        return
                    except Exception as e:  # pylint: disable=broad-exception-caught
                        # render() is user-defined code.
                        # We need to catch everything if we want the AntaTest object
                        # to live until the reporting
                        message = f"Exception in {self.__module__}.{self.__class__.__name__}.render()"
                        anta_log_exception(e, message, logger)
                        self.result.is_error(f"{message}: {exc_to_str(e)}")
                        return

        if eos_data is not None:
            self.logger.debug(f"Test {self.name} initialized with input data")
            self.save_commands_data(eos_data)

    def render(self, template: AntaTemplate) -> list[AntaCommand]:
        """Render an AntaTemplate instance of this AntaTest using the provided
           AntaTest.Input instance at self.inputs.

        This is not an abstract method because it does not need to be implemented if there is
        no AntaTemplate for this test."""
        raise NotImplementedError(f"render() method has not been implemented for {self.__module__}.{self.name}")

    def save_commands_data(self, eos_data: list[dict[str, Any] | str]) -> None:
        """Called at init or at test execution time"""
        if len(eos_data) != len(self.instance_commands):
            self.result.is_error("Test initialization error: Trying to save more data than there are commands for the test")
            return
        for index, data in enumerate(eos_data or []):
            self.instance_commands[index].output = data

    def all_data_collected(self) -> bool:
        """returns True if output is populated for every command"""
        return all(command.collected for command in self.instance_commands)

    def get_failed_commands(self) -> list[AntaCommand]:
        """returns a list of all the commands that have a populated failed field"""
        return [command for command in self.instance_commands if command.failed is not None]

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
        try:
            await self.device.collect_commands(self.instance_commands)
        except Exception as e:  # pylint: disable=broad-exception-caught
            message = f"Exception raised while collecting commands for test {self.name} (on device {self.device.name})"
            anta_log_exception(e, message, self.logger)
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
            **kwargs: Any,
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

            def format_td(seconds: float, digits: int = 3) -> str:
                isec, fsec = divmod(round(seconds * 10**digits), 10**digits)
                return f"{timedelta(seconds=isec)}.{fsec:0{digits}.0f}"

            start_time = time.time()
            if self.result.result != "unset":
                return self.result

            # TODO maybe_skip decorators

            # Data
            if eos_data is not None:
                self.save_commands_data(eos_data)
                self.logger.debug(f"Test {self.name} initialized with input data {eos_data}")

            # If some data is missing, try to collect
            if not self.all_data_collected():
                await self.collect()
                if self.result.result != "unset":
                    return self.result

            try:
                if cmds := self.get_failed_commands():
                    self.result.is_error(
                        "\n".join([f"{cmd.command} has failed: {exc_to_str(cmd.failed)}" if cmd.failed else f"{cmd.command} has failed" for cmd in cmds])
                    )
                    return self.result
                function(self, **kwargs)
            except Exception as e:  # pylint: disable=broad-exception-caught
                message = f"Exception raised for test {self.name} (on device {self.device.name})"
                anta_log_exception(e, message, self.logger)
                self.result.is_error(exc_to_str(e))

            test_duration = time.time() - start_time
            self.logger.debug(f"Executing test {self.name} on device {self.device.name} took {format_td(test_duration)}")

            AntaTest.update_progress()
            return self.result

        return wrapper

    @classmethod
    def update_progress(cls) -> None:
        """
        Update progress bar for all AntaTest objects if it exists
        """
        if cls.progress and (cls.nrfu_task is not None):
            cls.progress.update(cls.nrfu_task, advance=1)

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
