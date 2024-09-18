# Copyright (c) 2023-2024 Arista Networks, Inc.
# Use of this source code is governed by the Apache License 2.0
# that can be found in the LICENSE file.
"""Models to define a TestStructure."""

from __future__ import annotations

import hashlib
import logging
import re
from abc import ABC, abstractmethod
from functools import wraps
from string import Formatter
from typing import TYPE_CHECKING, Any, Callable, ClassVar, Literal, TypeVar

from pydantic import BaseModel, ConfigDict, ValidationError, create_model

from anta import GITHUB_SUGGESTION
from anta.custom_types import REGEXP_EOS_BLACKLIST_CMDS, Revision
from anta.logger import anta_log_exception, exc_to_str
from anta.result_manager.models import AntaTestStatus, TestResult

if TYPE_CHECKING:
    from collections.abc import Coroutine

    from rich.progress import Progress, TaskID

    from anta.device import AntaDevice

F = TypeVar("F", bound=Callable[..., Any])
# Proper way to type input class - revisit this later if we get any issue @gmuloc
# This would imply overhead to define classes
# https://stackoverflow.com/questions/74103528/type-hinting-an-instance-of-a-nested-class

logger = logging.getLogger(__name__)


class AntaParamsBaseModel(BaseModel):
    """Extends BaseModel and overwrite __getattr__ to return None on missing attribute."""

    model_config = ConfigDict(extra="forbid")


class AntaTemplate:
    """Class to define a command template as Python f-string.

    Can render a command from parameters.

    Attributes
    ----------
    template
        Python f-string. Example: 'show vlan {vlan_id}'.
    version
        eAPI version - valid values are 1 or "latest".
    revision
        Revision of the command. Valid values are 1 to 99. Revision has precedence over version.
    ofmt
        eAPI output - json or text.
    use_cache
        Enable or disable caching for this AntaTemplate if the AntaDevice supports it.
    """

    # pylint: disable=too-few-public-methods

    def __init__(
        self,
        template: str,
        version: Literal[1, "latest"] = "latest",
        revision: Revision | None = None,
        ofmt: Literal["json", "text"] = "json",
        *,
        use_cache: bool = True,
    ) -> None:
        self.template = template
        self.version = version
        self.revision = revision
        self.ofmt = ofmt
        self.use_cache = use_cache

        # Create a AntaTemplateParams model to elegantly store AntaTemplate variables
        field_names = [fname for _, fname, _, _ in Formatter().parse(self.template) if fname]
        # Extracting the type from the params based on the expected field_names from the template
        fields: dict[str, Any] = {key: (Any, ...) for key in field_names}
        self.params_schema = create_model(
            "AntaParams",
            __base__=AntaParamsBaseModel,
            **fields,
        )

    def __repr__(self) -> str:
        """Return the representation of the class.

        Copying pydantic model style, excluding `params_schema`
        """
        return " ".join(f"{a}={v!r}" for a, v in vars(self).items() if a != "params_schema")

    def render(self, **params: str | int | bool) -> AntaCommand:
        """Render an AntaCommand from an AntaTemplate instance.

        Keep the parameters used in the AntaTemplate instance.

        Parameters
        ----------
        params
            Dictionary of variables with string values to render the Python f-string.

        Returns
        -------
        AntaCommand
            The rendered AntaCommand.
            This AntaCommand instance have a template attribute that references this
            AntaTemplate instance.

        Raises
        ------
        AntaTemplateRenderError
            If a parameter is missing to render the AntaTemplate instance.
        """
        try:
            command = self.template.format(**params)
        except (KeyError, SyntaxError) as e:
            raise AntaTemplateRenderError(self, e.args[0]) from e
        return AntaCommand(
            command=command,
            ofmt=self.ofmt,
            version=self.version,
            revision=self.revision,
            template=self,
            params=self.params_schema(**params),
            use_cache=self.use_cache,
        )


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

    Attributes
    ----------
    command
        Device command.
    version
        eAPI version - valid values are 1 or "latest".
    revision
        eAPI revision of the command. Valid values are 1 to 99. Revision has precedence over version.
    ofmt
        eAPI output - json or text.
    output
        Output of the command. Only defined if there was no errors.
    template
        AntaTemplate object used to render this command.
    errors
        If the command execution fails, eAPI returns a list of strings detailing the error(s).
    params
        Pydantic Model containing the variables values used to render the template.
    use_cache
        Enable or disable caching for this AntaCommand if the AntaDevice supports it.

    """

    model_config = ConfigDict(arbitrary_types_allowed=True)

    command: str
    version: Literal[1, "latest"] = "latest"
    revision: Revision | None = None
    ofmt: Literal["json", "text"] = "json"
    output: dict[str, Any] | str | None = None
    template: AntaTemplate | None = None
    errors: list[str] = []
    params: AntaParamsBaseModel = AntaParamsBaseModel()
    use_cache: bool = True

    @property
    def uid(self) -> str:
        """Generate a unique identifier for this command."""
        uid_str = f"{self.command}_{self.version}_{self.revision or 'NA'}_{self.ofmt}"
        # Ignoring S324 probable use of insecure hash function - sha1 is enough for our needs.
        return hashlib.sha1(uid_str.encode()).hexdigest()  # noqa: S324

    @property
    def json_output(self) -> dict[str, Any]:
        """Get the command output as JSON."""
        if self.output is None:
            msg = f"There is no output for command '{self.command}'"
            raise RuntimeError(msg)
        if self.ofmt != "json" or not isinstance(self.output, dict):
            msg = f"Output of command '{self.command}' is invalid"
            raise RuntimeError(msg)
        return dict(self.output)

    @property
    def text_output(self) -> str:
        """Get the command output as a string."""
        if self.output is None:
            msg = f"There is no output for command '{self.command}'"
            raise RuntimeError(msg)
        if self.ofmt != "text" or not isinstance(self.output, str):
            msg = f"Output of command '{self.command}' is invalid"
            raise RuntimeError(msg)
        return str(self.output)

    @property
    def error(self) -> bool:
        """Return True if the command returned an error, False otherwise."""
        return len(self.errors) > 0

    @property
    def collected(self) -> bool:
        """Return True if the command has been collected, False otherwise.

        A command that has not been collected could have returned an error.
        See error property.
        """
        return not self.error and self.output is not None

    @property
    def requires_privileges(self) -> bool:
        """Return True if the command requires privileged mode, False otherwise.

        Raises
        ------
        RuntimeError
            If the command has not been collected and has not returned an error.
            AntaDevice.collect() must be called before this property.
        """
        if not self.collected and not self.error:
            msg = f"Command '{self.command}' has not been collected and has not returned an error. Call AntaDevice.collect()."
            raise RuntimeError(msg)
        return any("privileged mode required" in e for e in self.errors)

    @property
    def supported(self) -> bool:
        """Return True if the command is supported on the device hardware platform, False otherwise.

        Raises
        ------
        RuntimeError
            If the command has not been collected and has not returned an error.
            AntaDevice.collect() must be called before this property.
        """
        if not self.collected and not self.error:
            msg = f"Command '{self.command}' has not been collected and has not returned an error. Call AntaDevice.collect()."
            raise RuntimeError(msg)
        return not any("not supported on this hardware platform" in e for e in self.errors)


class AntaTemplateRenderError(RuntimeError):
    """Raised when an AntaTemplate object could not be rendered because of missing parameters."""

    def __init__(self, template: AntaTemplate, key: str) -> None:
        """Initialize an AntaTemplateRenderError.

        Parameters
        ----------
        template
            The AntaTemplate instance that failed to render.
        key
            Key that has not been provided to render the template.

        """
        self.template = template
        self.key = key
        super().__init__(f"'{self.key}' was not provided for template '{self.template.template}'")


class AntaTest(ABC):
    """Abstract class defining a test in ANTA.

    The goal of this class is to handle the heavy lifting and make
    writing a test as simple as possible.

    Examples
    --------
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
                    return [template.render(dst=host.dst, src=host.src, vrf=host.vrf) for host in self.inputs.hosts]

                @AntaTest.anta_test
                def test(self) -> None:
                    failures = []
                    for command in self.instance_commands:
                        src, dst = command.params.src, command.params.dst
                        if "2 received" not in command.json_output["messages"][0]:
                            failures.append((str(src), str(dst)))
                    if not failures:
                        self.result.is_success()
                    else:
                        self.result.is_failure(f"Connectivity test failed for the following source-destination pairs: {failures}")
        ```

    Attributes
    ----------
    device
        AntaDevice instance on which this test is run.
    inputs
        AntaTest.Input instance carrying the test inputs.
    instance_commands
        List of AntaCommand instances of this test.
    result
        TestResult instance representing the result of this test.
    logger
        Python logger for this test instance.
    """

    # Mandatory class attributes
    # TODO: find a way to tell mypy these are mandatory for child classes - maybe Protocol
    name: ClassVar[str]
    description: ClassVar[str]
    categories: ClassVar[list[str]]
    commands: ClassVar[list[AntaTemplate | AntaCommand]]
    # Class attributes to handle the progress bar of ANTA CLI
    progress: Progress | None = None
    nrfu_task: TaskID | None = None

    class Input(BaseModel):
        """Class defining inputs for a test in ANTA.

        Examples
        --------
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

        Attributes
        ----------
        result_overwrite
            Define fields to overwrite in the TestResult object.
        """

        model_config = ConfigDict(extra="forbid")
        result_overwrite: ResultOverwrite | None = None
        filters: Filters | None = None

        def __hash__(self) -> int:
            """Implement generic hashing for AntaTest.Input.

            This will work in most cases but this does not consider 2 lists with different ordering as equal.
            """
            return hash(self.model_dump_json())

        class ResultOverwrite(BaseModel):
            """Test inputs model to overwrite result fields.

            Attributes
            ----------
            description
                Overwrite `TestResult.description`.
            categories
                Overwrite `TestResult.categories`.
            custom_field
                A free string that will be included in the TestResult object.

            """

            model_config = ConfigDict(extra="forbid")
            description: str | None = None
            categories: list[str] | None = None
            custom_field: str | None = None

        class Filters(BaseModel):
            """Runtime filters to map tests with list of tags or devices.

            Attributes
            ----------
            tags
                Tag of devices on which to run the test.
            """

            model_config = ConfigDict(extra="forbid")
            tags: set[str] | None = None

    def __init__(
        self,
        device: AntaDevice,
        inputs: dict[str, Any] | AntaTest.Input | None = None,
        eos_data: list[dict[Any, Any] | str] | None = None,
    ) -> None:
        """AntaTest Constructor.

        Parameters
        ----------
        device
            AntaDevice instance on which the test will be run.
        inputs
            Dictionary of attributes used to instantiate the AntaTest.Input instance.
        eos_data
            Populate outputs of the test commands instead of collecting from devices.
            This list must have the same length and order than the `instance_commands` instance attribute.
        """
        self.logger: logging.Logger = logging.getLogger(f"{self.module}.{self.__class__.__name__}")
        self.device: AntaDevice = device
        self.inputs: AntaTest.Input
        self.instance_commands: list[AntaCommand] = []
        self.result: TestResult = TestResult(
            name=device.name,
            test=self.name,
            categories=self.categories,
            description=self.description,
        )
        self._init_inputs(inputs)
        if self.result.result == AntaTestStatus.UNSET:
            self._init_commands(eos_data)

    def _init_inputs(self, inputs: dict[str, Any] | AntaTest.Input | None) -> None:
        """Instantiate the `inputs` instance attribute with an `AntaTest.Input` instance to validate test inputs using the model.

        Overwrite result fields based on `ResultOverwrite` input definition.

        Any input validation error will set this test result status as 'error'.
        """
        try:
            if inputs is None:
                self.inputs = self.Input()
            elif isinstance(inputs, AntaTest.Input):
                self.inputs = inputs
            elif isinstance(inputs, dict):
                self.inputs = self.Input(**inputs)
        except ValidationError as e:
            message = f"{self.module}.{self.name}: Inputs are not valid\n{e}"
            self.logger.error(message)
            self.result.is_error(message=message)
            return
        if res_ow := self.inputs.result_overwrite:
            if res_ow.categories:
                self.result.categories = res_ow.categories
            if res_ow.description:
                self.result.description = res_ow.description
            self.result.custom_field = res_ow.custom_field

    def _init_commands(self, eos_data: list[dict[Any, Any] | str] | None) -> None:
        """Instantiate the `instance_commands` instance attribute from the `commands` class attribute.

        - Copy of the `AntaCommand` instances
        - Render all `AntaTemplate` instances using the `render()` method.

        Any template rendering error will set this test result status as 'error'.
        Any exception in user code in `render()` will set this test result status as 'error'.
        """
        if self.__class__.commands:
            for cmd in self.__class__.commands:
                if isinstance(cmd, AntaCommand):
                    self.instance_commands.append(cmd.model_copy())
                elif isinstance(cmd, AntaTemplate):
                    try:
                        self.instance_commands.extend(self.render(cmd))
                    except AntaTemplateRenderError as e:
                        self.result.is_error(message=f"Cannot render template {{{e.template}}}")
                        return
                    except NotImplementedError as e:
                        self.result.is_error(message=e.args[0])
                        return
                    except Exception as e:  # noqa: BLE001
                        # render() is user-defined code.
                        # We need to catch everything if we want the AntaTest object
                        # to live until the reporting
                        message = f"Exception in {self.module}.{self.__class__.__name__}.render()"
                        anta_log_exception(e, message, self.logger)
                        self.result.is_error(message=f"{message}: {exc_to_str(e)}")
                        return

        if eos_data is not None:
            self.logger.debug("Test %s initialized with input data", self.name)
            self.save_commands_data(eos_data)

    def save_commands_data(self, eos_data: list[dict[str, Any] | str]) -> None:
        """Populate output of all AntaCommand instances in `instance_commands`."""
        if len(eos_data) > len(self.instance_commands):
            self.result.is_error(message="Test initialization error: Trying to save more data than there are commands for the test")
            return
        if len(eos_data) < len(self.instance_commands):
            self.result.is_error(message="Test initialization error: Trying to save less data than there are commands for the test")
            return
        for index, data in enumerate(eos_data or []):
            self.instance_commands[index].output = data

    def __init_subclass__(cls) -> None:
        """Verify that the mandatory class attributes are defined."""
        mandatory_attributes = ["name", "description", "categories", "commands"]
        for attr in mandatory_attributes:
            if not hasattr(cls, attr):
                msg = f"Class {cls.__module__}.{cls.__name__} is missing required class attribute {attr}"
                raise NotImplementedError(msg)

    @property
    def module(self) -> str:
        """Return the Python module in which this AntaTest class is defined."""
        return self.__module__

    @property
    def collected(self) -> bool:
        """Return True if all commands for this test have been collected."""
        return all(command.collected for command in self.instance_commands)

    @property
    def failed_commands(self) -> list[AntaCommand]:
        """Return a list of all the commands that have failed."""
        return [command for command in self.instance_commands if command.error]

    def render(self, template: AntaTemplate) -> list[AntaCommand]:
        """Render an AntaTemplate instance of this AntaTest using the provided AntaTest.Input instance at self.inputs.

        This is not an abstract method because it does not need to be implemented if there is
        no AntaTemplate for this test.
        """
        _ = template
        msg = f"AntaTemplate are provided but render() method has not been implemented for {self.module}.{self.__class__.__name__}"
        raise NotImplementedError(msg)

    @property
    def blocked(self) -> bool:
        """Check if CLI commands contain a blocked keyword."""
        state = False
        for command in self.instance_commands:
            for pattern in REGEXP_EOS_BLACKLIST_CMDS:
                if re.match(pattern, command.command):
                    self.logger.error(
                        "Command <%s> is blocked for security reason matching %s",
                        command.command,
                        REGEXP_EOS_BLACKLIST_CMDS,
                    )
                    self.result.is_error(f"<{command.command}> is blocked for security reason")
                    state = True
        return state

    async def collect(self) -> None:
        """Collect outputs of all commands of this test class from the device of this test instance."""
        try:
            if self.blocked is False:
                await self.device.collect_commands(self.instance_commands, collection_id=self.name)
        except Exception as e:  # noqa: BLE001
            # device._collect() is user-defined code.
            # We need to catch everything if we want the AntaTest object
            # to live until the reporting
            message = f"Exception raised while collecting commands for test {self.name} (on device {self.device.name})"
            anta_log_exception(e, message, self.logger)
            self.result.is_error(message=exc_to_str(e))

    @staticmethod
    def anta_test(function: F) -> Callable[..., Coroutine[Any, Any, TestResult]]:
        """Decorate the `test()` method in child classes.

        This decorator implements (in this order):

        1. Instantiate the command outputs if `eos_data` is provided to the `test()` method
        2. Collect the commands from the device
        3. Run the `test()` method
        4. Catches any exception in `test()` user code and set the `result` instance attribute
        """

        @wraps(function)
        async def wrapper(
            self: AntaTest,
            eos_data: list[dict[Any, Any] | str] | None = None,
            **kwargs: dict[str, Any],
        ) -> TestResult:
            """Inner function for the anta_test decorator.

            Parameters
            ----------
            self
                The test instance.
            eos_data
                Populate outputs of the test commands instead of collecting from devices.
                This list must have the same length and order than the `instance_commands` instance attribute.
            kwargs
                Any keyword argument to pass to the test.

            Returns
            -------
            TestResult
                The TestResult instance attribute populated with error status if any.

            """
            if self.result.result != "unset":
                return self.result

            # Data
            if eos_data is not None:
                self.save_commands_data(eos_data)
                self.logger.debug("Test %s initialized with input data %s", self.name, eos_data)

            # If some data is missing, try to collect
            if not self.collected:
                await self.collect()
                if self.result.result != "unset":
                    AntaTest.update_progress()
                    return self.result

                if cmds := self.failed_commands:
                    unsupported_commands = [f"'{c.command}' is not supported on {self.device.hw_model}" for c in cmds if not c.supported]
                    if unsupported_commands:
                        msg = f"Test {self.name} has been skipped because it is not supported on {self.device.hw_model}: {GITHUB_SUGGESTION}"
                        self.logger.warning(msg)
                        self.result.is_skipped("\n".join(unsupported_commands))
                    else:
                        self.result.is_error(message="\n".join([f"{c.command} has failed: {', '.join(c.errors)}" for c in cmds]))
                    AntaTest.update_progress()
                    return self.result

            try:
                function(self, **kwargs)
            except Exception as e:  # noqa: BLE001
                # test() is user-defined code.
                # We need to catch everything if we want the AntaTest object
                # to live until the reporting
                message = f"Exception raised for test {self.name} (on device {self.device.name})"
                anta_log_exception(e, message, self.logger)
                self.result.is_error(message=exc_to_str(e))

            # TODO: find a correct way to time test execution
            AntaTest.update_progress()
            return self.result

        return wrapper

    @classmethod
    def update_progress(cls: type[AntaTest]) -> None:
        """Update progress bar for all AntaTest objects if it exists."""
        if cls.progress and (cls.nrfu_task is not None):
            cls.progress.update(cls.nrfu_task, advance=1)

    @abstractmethod
    def test(self) -> Coroutine[Any, Any, TestResult]:
        """Core of the test logic.

        This is an abstractmethod that must be implemented by child classes.
        It must set the correct status of the `result` instance attribute with the appropriate outcome of the test.

        Examples
        --------
        It must be implemented using the `AntaTest.anta_test` decorator:
            ```python
            @AntaTest.anta_test
            def test(self) -> None:
                self.result.is_success()
                for command in self.instance_commands:
                    if not self._test_command(command): # _test_command() is an arbitrary test logic
                        self.result.is_failure("Failure reason")
            ```

        """
