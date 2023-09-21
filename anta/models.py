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

# Need to keep Dict and List for pydantic in python 3.8
from typing import TYPE_CHECKING, Any, Callable, ClassVar, Coroutine, Dict, List, Literal, Optional, TypeVar, Union

from pydantic import BaseModel, ConfigDict, ValidationError, conint
from rich.progress import Progress, TaskID

from anta.result_manager.models import TestResult
from anta.tools.misc import anta_log_exception, exc_to_str

if TYPE_CHECKING:
    from anta.device import AntaDevice

F = TypeVar("F", bound=Callable[..., Any])
# Proper way to type input class - revisit this later if we get any issue @gmuloc
# This would imply overhead to define classes
# https://stackoverflow.com/questions/74103528/type-hinting-an-instance-of-a-nested-class
# N = TypeVar("N", bound="AntaTest.Input")

DEFAULT_TAG = "all"

logger = logging.getLogger(__name__)


class AntaMissingParamException(Exception):
    """
    This Exception should be used when an expected key in an AntaCommand.params dictionary
    was not found.

    This Exception should in general never be raised in normal usage of ANTA.
    """

    GITHUB_SUGGESTION = [
        "This Exception should not have been raised in a normal usage of ANTA.",
        "Please reach out to the maintainer team on Github: https://github.com/arista-netdevops-community/anta.",
    ]

    def __init__(self, message: str) -> None:
        self.message = "\n".join([message] + AntaMissingParamException.GITHUB_SUGGESTION)
        super().__init__(self.message)


class AntaTemplate(BaseModel):
    """Class to define a command template as Python f-string.
    Can render a command from parameters.

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

    def render(self, **params: dict[str, Any]) -> AntaCommand:
        """Render an AntaCommand from an AntaTemplate instance.
        Keep the parameters used in the AntaTemplate instance.

        Args:
            params: dictionary of variables with string values to render the Python f-string

        Returns:
            command: The rendered AntaCommand.
                     This AntaCommand instance have a template attribute that references this
                     AntaTemplate instance.
        """
        try:
            return AntaCommand(command=self.template.format(**params), ofmt=self.ofmt, version=self.version, revision=self.revision, template=self, params=params)
        except KeyError as e:
            raise AntaTemplateRenderError(self, e.args[0]) from e


class AntaCommand(BaseModel):
    """Class to define a command.

    !!! info
        eAPI models are revisioned, this means that if a model is modified in a non-backwards compatible way, then its revision will be bumped up
        (revisions are numbers, default value is 1).

        By default an eAPI request will return revision 1 of the model instance,
        this ensures that older management software will not suddenly stop working when a switch is upgraded.
        A **revision** applies to a particular CLI command whereas a **version** is global and is internally
        translated to a specific **revision** for each CLI command in the RPC.

        __Revision has precedence over version.__

    Attributes:
        command: Device command
        version: eAPI version - valid values are 1 or "latest" - default is "latest"
        revision: eAPI revision of the command. Valid values are 1 to 99. Revision has precedence over version.
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
    params: Dict[str, Any] = {}

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
        super().__init__(f"'{self.key}' was not provided for template '{self.template.template}'")


class AntaTest(ABC):
    """Abstract class defining a test in ANTA

    The goal of this class is to handle the heavy lifting and make
    writing a test as simple as possible.

    Examples:
    The following is an example of an AntaTest subclass implementation:
        ```python
            class VerifyReachability(AntaTest):
                name = "VerifyReachability"
                description = "Test the network reachability to one or many destination IP(s)."
                categories = ["connectivity"]
                commands = [AntaTemplate(template="ping vrf {vrf} {dst} source {src} repeat 2")]

                class Input(AntaTest.Input):
                    hosts: list[Host]
                    class Host(BaseModel):
                        dst: IPv4Address
                        src: IPv4Address
                        vrf: str = "default"

                def render(self, template: AntaTemplate) -> list[AntaCommand]:
                    return [template.render({"dst": host.dst, "src": host.src, "vrf": host.vrf}) for host in self.inputs.hosts]

                @AntaTest.anta_test
                def test(self) -> None:
                    failures = []
                    for command in self.instance_commands:
                        if command.params and ("src" and "dst") in command.params:
                            src, dst = command.params["src"], command.params["dst"]
                        if "2 received" not in command.json_output["messages"][0]:
                            failures.append((str(src), str(dst)))
                    if not failures:
                        self.result.is_success()
                    else:
                        self.result.is_failure(f"Connectivity test failed for the following source-destination pairs: {failures}")
        ```
    Attributes:
        device: AntaDevice instance on which this test is run
        inputs: AntaTest.Input instance carrying the test inputs
        instance_commands: List of AntaCommand instances of this test
        result: TestResult instance representing the result of this test
        logger: Python logger for this test instance
    """

    # Mandatory class attributes
    # TODO - find a way to tell mypy these are mandatory for child classes - maybe Protocol
    name: ClassVar[str]
    description: ClassVar[str]
    categories: ClassVar[list[str]]
    commands: ClassVar[list[Union[AntaTemplate, AntaCommand]]]
    # Optional class attributes
    test_filters: ClassVar[list[AntaTestFilter]]
    # Class attributes to handle the progress bar of ANTA CLI
    progress: Optional[Progress] = None
    nrfu_task: Optional[TaskID] = None

    class Input(BaseModel):
        """Class defining inputs for a test in ANTA.

        Examples:
        A valid test catalog will look like the following:
            ```yaml
            <Python module>:
            - <AntaTest subclass>:
                result_overwrite:
                    categories:
                    - "Overwritten category 1"
                    description: "Test with overwritten description"
                    custom_field: "Test run by John Doe"
            ```
        Attributes:
            result_overwrite: Define fields to overwrite in the TestResult object
        """

        model_config = ConfigDict(extra="forbid")
        result_overwrite: Optional[ResultOverwrite] = None

        class ResultOverwrite(BaseModel):
            """Test inputs model to overwrite result fields

            Attributes:
                description: overwrite TestResult.description
                categories: overwrite TestResult.categories
                custom_field: a free string that will be included in the TestResult object
            """

            description: Optional[str] = None
            categories: Optional[List[str]] = None
            custom_field: Optional[str] = None

    def __init__(
        self,
        device: AntaDevice,
        inputs: Optional[dict[str, Any]],
        eos_data: Optional[list[dict[Any, Any] | str]] = None,
    ):
        """AntaTest Constructor

        Args:
            device: AntaDevice instance on which the test will be run
            inputs: dictionary of attributes used to instantiate the AntaTest.Input instance
            eos_data: Populate outputs of the test commands instead of collecting from devices.
                      This list must have the same length and order than the `instance_commands` instance attribute.
        """
        self.logger: logging.Logger = logging.getLogger(f"{self.__module__}.{self.__class__.__name__}")
        self.device: AntaDevice = device
        self.inputs: AntaTest.Input
        self.instance_commands: list[AntaCommand] = []
        self.result: TestResult = TestResult(name=device.name, test=self.name, categories=self.categories, description=self.description)
        self._init_inputs(inputs)
        if self.result.result == "unset":
            self._init_commands(eos_data)

    def _init_inputs(self, inputs: Optional[dict[str, Any]]) -> None:
        """Instantiate the `inputs` instance attribute with an `AntaTest.Input` instance
        to validate test inputs from defined model.
        Overwrite result fields based on `ResultOverwrite` input definition.

        Any input validation error will set this test result status as 'error'."""
        try:
            self.inputs = self.Input(**inputs) if inputs is not None else self.Input()
        except ValidationError as e:
            message = f"{self.__module__}.{self.__class__.__name__}: Inputs are not valid\n{e}"
            self.logger.error(message)
            self.result.is_error(message=message, exception=e)
            return
        if res_ow := self.inputs.result_overwrite:
            if res_ow.categories:
                self.result.categories = res_ow.categories
            if res_ow.description:
                self.result.description = res_ow.description
            self.result.custom_field = res_ow.custom_field

    def _init_commands(self, eos_data: Optional[list[dict[Any, Any] | str]]) -> None:
        """Instantiate the `instance_commands` instance attribute from the `commands` class attribute.
        - Copy of the `AntaCommand` instances
        - Render all `AntaTemplate` instances using the `render()` method

        Any template rendering error will set this test result status as 'error'.
        Any exception in user code in `render()` will set this test result status as 'error'.
        """
        if self.__class__.commands:
            for cmd in self.__class__.commands:
                if isinstance(cmd, AntaCommand):
                    self.instance_commands.append(deepcopy(cmd))
                elif isinstance(cmd, AntaTemplate):
                    try:
                        self.instance_commands.extend(self.render(cmd))
                    except AntaTemplateRenderError as e:
                        self.result.is_error(message=f"Cannot render template {{{e.template}}}", exception=e)
                        return
                    except NotImplementedError as e:
                        self.result.is_error(message=e.args[0], exception=e)
                        return
                    except Exception as e:  # pylint: disable=broad-exception-caught
                        # render() is user-defined code.
                        # We need to catch everything if we want the AntaTest object
                        # to live until the reporting
                        message = f"Exception in {self.__module__}.{self.__class__.__name__}.render()"
                        anta_log_exception(e, message, self.logger)
                        self.result.is_error(message=f"{message}: {exc_to_str(e)}", exception=e)
                        return

        if eos_data is not None:
            self.logger.debug(f"Test {self.name} initialized with input data")
            self.save_commands_data(eos_data)

    def save_commands_data(self, eos_data: list[dict[str, Any] | str]) -> None:
        """Populate output of all AntaCommand instances in `instance_commands`"""
        if len(eos_data) != len(self.instance_commands):
            self.result.is_error(message="Test initialization error: Trying to save more data than there are commands for the test")
            return
        for index, data in enumerate(eos_data or []):
            self.instance_commands[index].output = data

    def __init_subclass__(cls) -> None:
        """Verify that the mandatory class attributes are defined"""
        mandatory_attributes = ["name", "description", "categories", "commands"]
        for attr in mandatory_attributes:
            if not hasattr(cls, attr):
                raise NotImplementedError(f"Class {cls.__module__}.{cls.__name__} is missing required class attribute {attr}")

    @property
    def collected(self) -> bool:
        """Returns True if all commands for this test have been collected."""
        return all(command.collected for command in self.instance_commands)

    @property
    def failed_commands(self) -> list[AntaCommand]:
        """Returns a list of all the commands that have failed."""
        return [command for command in self.instance_commands if command.failed is not None]

    def render(self, template: AntaTemplate) -> list[AntaCommand]:
        """Render an AntaTemplate instance of this AntaTest using the provided
           AntaTest.Input instance at self.inputs.

        This is not an abstract method because it does not need to be implemented if there is
        no AntaTemplate for this test."""
        raise NotImplementedError(f"AntaTemplate are provided but render() method has not been implemented for {self.__module__}.{self.name}")

    async def collect(self) -> None:
        """
        Method used to collect outputs of all commands of this test class from the device of this test instance.
        """
        try:
            await self.device.collect_commands(self.instance_commands)
        except Exception as e:  # pylint: disable=broad-exception-caught
            message = f"Exception raised while collecting commands for test {self.name} (on device {self.device.name})"
            anta_log_exception(e, message, self.logger)
            self.result.is_error(message=exc_to_str(e))

    @staticmethod
    def anta_test(function: F) -> Callable[..., Coroutine[Any, Any, TestResult]]:
        """
        Decorator for the `test()` method.

        This decorator implements (in this order):

        1. Instantiate the command outputs if `eos_data` is provided to the `test()` method
        2. Collect the commands from the device
        3. Run the `test()` method
        4. Catches any exception in `test()` user code and set the `result` instance attribute
        """

        @wraps(function)
        async def wrapper(
            self: AntaTest,
            eos_data: Optional[list[dict[Any, Any] | str]] = None,
            **kwargs: Any,
        ) -> TestResult:
            """
            Args:
                eos_data: Populate outputs of the test commands instead of collecting from devices.
                          This list must have the same length and order than the `instance_commands` instance attribute.

            Returns:
                result: TestResult instance attribute populated with error status if any
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
            if not self.collected:
                await self.collect()
                if self.result.result != "unset":
                    return self.result

            try:
                if self.failed_commands:
                    self.result.is_error(
                        message="\n".join(
                            [f"{cmd.command} has failed: {exc_to_str(cmd.failed)}" if cmd.failed else f"{cmd.command} has failed" for cmd in self.failed_commands]
                        )
                    )
                    return self.result
                function(self, **kwargs)
            except Exception as e:  # pylint: disable=broad-exception-caught
                message = f"Exception raised for test {self.name} (on device {self.device.name})"
                anta_log_exception(e, message, self.logger)
                self.result.is_error(message=exc_to_str(e))

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
        This abstract method is the core of the test logic.
        It must set the correct status of the `result` instance attribute
        with the appropriate outcome of the test.

        Examples:
        It must be implemented using the `AntaTest.anta_test` decorator:
            ```python
            @AntaTest.anta_test
            def test(self) -> None:
                self.result.is_success()
                for command in self.instance_commands:
                    if not self._test_command(command): # _test_command() is an arbitrary test logic
                        self.result.is_failure("Failure reson")
            ```
        """
