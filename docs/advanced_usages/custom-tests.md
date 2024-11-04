<!--
  ~ Copyright (c) 2023-2024 Arista Networks, Inc.
  ~ Use of this source code is governed by the Apache License 2.0
  ~ that can be found in the LICENSE file.
  -->

!!! info
    This documentation applies for both creating tests in ANTA or creating your own test package.

ANTA is not only a Python library with a CLI and a collection of built-in tests, it is also a framework you can extend by building your own tests.

## Generic approach

A test is a Python class where a test function is defined and will be run by the framework.

ANTA provides an abstract class [AntaTest](../api/models.md#anta.models.AntaTest). This class does the heavy lifting and provide the logic to define, collect and test data. The code below is an example of a simple test in ANTA, which is an [AntaTest](../api/models.md#anta.models.AntaTest) subclass:

```python
from anta.models import AntaTest, AntaCommand
from anta.decorators import skip_on_platforms


class VerifyTemperature(AntaTest):
    """Verifies if the device temperature is within acceptable limits.

    Expected Results
    ----------------
    * Success: The test will pass if the device temperature is currently OK: 'temperatureOk'.
    * Failure: The test will fail if the device temperature is NOT OK.

    Examples
    --------
    ```yaml
    anta.tests.hardware:
      - VerifyTemperature:
    ```
    """

    categories: ClassVar[list[str]] = ["hardware"]
    commands: ClassVar[list[AntaCommand | AntaTemplate]] = [AntaCommand(command="show system environment temperature", revision=1)]

    @skip_on_platforms(["cEOSLab", "vEOS-lab", "cEOSCloudLab"])
    @AntaTest.anta_test
    def test(self) -> None:
        """Main test function for VerifyTemperature."""
        command_output = self.instance_commands[0].json_output
        temperature_status = command_output.get("systemStatus", "")
        if temperature_status == "temperatureOk":
            self.result.is_success()
        else:
            self.result.is_failure(f"Device temperature exceeds acceptable limits. Current system status: '{temperature_status}'")
```

[AntaTest](../api/models.md#anta.models.AntaTest) also provide more advanced capabilities like [AntaCommand](../api/models.md#anta.models.AntaCommand) templating using the [AntaTemplate](../api/models.md#anta.models.AntaTemplate) class or test inputs definition and validation using [AntaTest.Input](../api/models.md#anta.models.AntaTest.Input) [pydantic](https://docs.pydantic.dev/latest/) model. This will be discussed in the sections below.

## AntaTest structure

Full AntaTest API documentation is available in the [API documentation section](../api/models.md#anta.models.AntaTest)

### Class Attributes

- `name` (`str`, `optional`): Name of the test. Used during reporting. By default set to the Class name.
- `description` (`str`, `optional`): A human readable description of your test. By default set to the first line of the docstring.
- `categories` (`list[str]`): A list of categories in which the test belongs.
- `commands` (`[list[AntaCommand | AntaTemplate]]`): A list of command to collect from devices. This list **must** be a list of [AntaCommand](../api/models.md#anta.models.AntaCommand) or [AntaTemplate](../api/models.md#anta.models.AntaTemplate) instances. Rendering [AntaTemplate](../api/models.md#anta.models.AntaTemplate) instances will be discussed later.

!!! info
    All these class attributes are mandatory. If any attribute is missing, a `NotImplementedError` exception will be raised during class instantiation.

### Instance Attributes

::: anta.models.AntaTest
    options:
        show_docstring_attributes: true
        show_root_heading: false
        show_bases: false
        show_docstring_description: false
        show_docstring_examples: false
        show_docstring_parameters: false
        members: false
        show_source: false
        show_root_toc_entry: false
        heading_level: 10

!!! note "Logger object"
    ANTA already provides comprehensive logging at every steps of a test execution. The [AntaTest](../api/models.md#anta.models.AntaTest) class also provides a `logger` attribute that is a Python logger specific to the test instance. See [Python documentation](https://docs.python.org/3/library/logging.html) for more information.

!!! note "AntaDevice object"
    Even if `device` is not a private attribute, you should not need to access this object in your code.

### Test Inputs

[AntaTest.Input](../api/models.md#anta.models.AntaTest.Input) is a [pydantic model](https://docs.pydantic.dev/latest/usage/models/) that allow test developers to define their test inputs. [pydantic](https://docs.pydantic.dev/latest/) provides out of the box [error handling](https://docs.pydantic.dev/latest/usage/models/#error-handling) for test input validation based on the type hints defined by the test developer.

The base definition of [AntaTest.Input](../api/models.md#anta.models.AntaTest.Input) provides common test inputs for all [AntaTest](../api/models.md#anta.models.AntaTest) instances:

#### Input model

Full `Input` model documentation is available in [API documentation section](../api/models.md#anta.models.AntaTest.Input)

::: anta.models.AntaTest.Input
    options:
        show_docstring_attributes: true
        show_root_heading: false
        show_category_heading: false
        show_bases: false
        show_docstring_description: false
        show_docstring_examples: false
        show_docstring_parameters: false
        show_source: false
        members: false
        show_root_toc_entry: false
        heading_level: 10

#### ResultOverwrite model

Full `ResultOverwrite` model documentation is available in [API documentation section](../api/models.md#anta.models.AntaTest.Input.ResultOverwrite)

::: anta.models.AntaTest.Input.ResultOverwrite
    options:
        show_docstring_attributes: true
        show_root_heading: false
        show_category_heading: false
        show_bases: false
        show_docstring_description: false
        show_docstring_examples: false
        show_docstring_parameters: false
        show_source: false
        show_root_toc_entry: false
        heading_level: 10

!!! note
    The pydantic model is configured using the [`extra=forbid`](https://docs.pydantic.dev/latest/usage/model_config/#extra-attributes) that will fail input validation if extra fields are provided.

### Methods

- [test(self) -> None](../api/models.md#anta.models.AntaTest.test): This is an abstract method that **must** be implemented. It contains the test logic that can access the collected command outputs using the `instance_commands` instance attribute, access the test inputs using the `inputs` instance attribute and **must** set the `result` instance attribute accordingly. It must be implemented using the `AntaTest.anta_test` decorator that provides logging and will collect commands before executing the `test()` method.
- [render(self, template: AntaTemplate) -> list[AntaCommand]](../api/models.md#anta.models.AntaTest.render): This method only needs to be implemented if [AntaTemplate](../api/models.md#anta.models.AntaTemplate) instances are present in the `commands` class attribute. It will be called for every [AntaTemplate](../api/models.md#anta.models.AntaTemplate) occurrence and **must** return a list of [AntaCommand](../api/models.md#anta.models.AntaCommand) using the [AntaTemplate.render()](../api/models.md#anta.models.AntaTemplate.render) method. It can access test inputs using the `inputs` instance attribute.

## Test execution

Below is a high level description of the test execution flow in ANTA:

1. ANTA will parse the test catalog to get the list of [AntaTest](../api/models.md#anta.models.AntaTest) subclasses to instantiate and their associated input values. We consider a single [AntaTest](../api/models.md#anta.models.AntaTest) subclass in the following steps.

2. ANTA will instantiate the [AntaTest](../api/models.md#anta.models.AntaTest) subclass and a single device will be provided to the test instance. The `Input` model defined in the class will also be instantiated at this moment. If any [ValidationError](https://docs.pydantic.dev/latest/errors/errors/) is raised, the test execution will be stopped.

3. If there is any [AntaTemplate](../api/models.md#anta.models.AntaTemplate) instance in the `commands` class attribute, [render()](../api/models.md#anta.models.AntaTest.render) will be called for every occurrence. At this moment, the `instance_commands` attribute has been initialized. If any rendering error occurs, the test execution will be stopped.

4. The `AntaTest.anta_test` decorator will collect the commands from the device and update the `instance_commands` attribute with the outputs. If any collection error occurs, the test execution will be stopped.

5. The [test()](../api/models.md#anta.models.AntaTest.test) method is executed.

## Writing an AntaTest subclass

In this section, we will go into all the details of writing an [AntaTest](../api/models.md#anta.models.AntaTest) subclass.

### Class definition

Import [anta.models.AntaTest](../api/models.md#anta.models.AntaTest) and define your own class.
Define the mandatory class attributes using [anta.models.AntaCommand](../api/models.md#anta.models.AntaCommand), [anta.models.AntaTemplate](../api/models.md#anta.models.AntaTemplate) or both.

!!! info
    Caching can be disabled per `AntaCommand` or `AntaTemplate` by setting the `use_cache` argument to `False`. For more details about how caching is implemented in ANTA, please refer to [Caching in ANTA](../advanced_usages/caching.md).

```python
from anta.models import AntaTest, AntaCommand, AntaTemplate


class <YourTestName>(AntaTest):
    """
    <a docstring description of your test, the first line is used as description of the test by default>
    """

    # name = <override>        # uncomment to override default behavior of name=Class Name
    # description = <override> # uncomment to override default behavior of description=first line of docstring
    categories = ["<arbitrary category>", "<another arbitrary category>"]
    commands = [
        AntaCommand(
            command="<EOS command to run>",
            ofmt="<command format output>",
            version="<eAPI version to use>",
            revision="<revision to use for the command>",           # revision has precedence over version
            use_cache="<Use cache for the command>",
        ),
        AntaTemplate(
            template="<Python f-string to render an EOS command>",
            ofmt="<command format output>",
            version="<eAPI version to use>",
            revision="<revision to use for the command>",           # revision has precedence over version
            use_cache="<Use cache for the command>",
        )
    ]
```

!!! tip "Command revision and version"
    * Most of EOS commands return a JSON structure according to a model (some commands may not be modeled hence the necessity to use `text` outformat sometimes.
    * The model can change across time (adding feature, ... ) and when the model is changed in a non backward-compatible way, the **revision** number is bumped. The initial model starts with **revision** 1.
    * A **revision** applies to a particular CLI command whereas a **version** is global to an eAPI call. The **version** is internally translated to a specific **revision** for each CLI command in the RPC call. The currently supported **version** values  are `1` and `latest`.
    * A **revision takes precedence over a version** (e.g. if a command is run with version="latest" and revision=1, the first revision of the model is returned)
    * By default, eAPI returns the first revision of each model to ensure that when upgrading, integrations with existing tools are not broken. This is done by using by default `version=1` in eAPI calls.

    By default, ANTA uses `version="latest"` in AntaCommand, but when developing tests, the revision MUST be provided when the outformat of the command is `json`. As explained earlier, this is to ensure that the eAPI always returns the same output model and that the test remains always valid from the day it was created. For some commands, you may also want to run them with a different revision or version.

    For instance, the `VerifyBFDPeersHealth` test leverages the first revision of `show bfd peers`:

    ```
    # revision 1 as later revision introduce additional nesting for type
    commands = [AntaCommand(command="show bfd peers", revision=1)]
    ```

### Inputs definition

If the user needs to provide inputs for your test, you need to define a [pydantic model](https://docs.pydantic.dev/latest/usage/models/) that defines the schema of the test inputs:

```python
class <YourTestName>(AntaTest):
    """Verifies ...

    Expected Results
    ----------------
    * Success: The test will pass if ...
    * Failure: The test will fail if ...

    Examples
    --------
    ```yaml
    your.module.path:
      - YourTestName:
        field_name: example_field_value
    ```
    """
    ...
    class Input(AntaTest.Input):
        """Inputs for my awesome test."""
        <input field name>: <input field type>
        """<input field docstring>"""
```

To define an input field type, refer to the [pydantic documentation](https://docs.pydantic.dev/latest/usage/types/types/) about types.
You can also leverage [anta.custom_types](../api/types.md) that provides reusable types defined in ANTA tests.

Regarding required, optional and nullable fields, refer to this [documentation](https://docs.pydantic.dev/latest/migration/#required-optional-and-nullable-fields) on how to define them.

!!! note
    All the `pydantic` features are supported. For instance you can define [validators](https://docs.pydantic.dev/latest/usage/validators/) for complex input validation.

### Template rendering

Define the `render()` method if you have [AntaTemplate](../api/models.md#anta.models.AntaTemplate) instances in your `commands` class attribute:

```python
class <YourTestName>(AntaTest):
    ...
    def render(self, template: AntaTemplate) -> list[AntaCommand]:
        return [template.render(<template param>=input_value) for input_value in self.inputs.<input_field>]
```

You can access test inputs and render as many [AntaCommand](../api/models.md#anta.models.AntaCommand) as desired.

### Test definition

Implement the `test()` method with your test logic:

```python
class <YourTestName>(AntaTest):
    ...
    @AntaTest.anta_test
    def test(self) -> None:
        pass
```

The logic usually includes the following different stages:

1. Parse the command outputs using the `self.instance_commands` instance attribute.
2. If needed, access the test inputs using the `self.inputs` instance attribute and write your conditional logic.
3. Set the `result` instance attribute to reflect the test result by either calling `self.result.is_success()` or `self.result.is_failure("<FAILURE REASON>")`. Sometimes, setting the test result to `skipped` using `self.result.is_skipped("<SKIPPED REASON>")` can make sense (e.g. testing the OSPF neighbor states but no neighbor was found). However, you should not need to catch any exception and set the test result to `error` since the error handling is done by the framework, see below.

The example below is based on the [VerifyTemperature](../api/tests.hardware.md#anta.tests.hardware.VerifyTemperature) test.

```python
class VerifyTemperature(AntaTest):
    ...
    @AntaTest.anta_test
    def test(self) -> None:
        # Grab output of the collected command
        command_output = self.instance_commands[0].json_output

        # Do your test: In this example we check a specific field of the JSON output from EOS
        temperature_status = command_output["systemStatus"] if "systemStatus" in command_output.keys() else ""
        if temperature_status == "temperatureOk":
            self.result.is_success()
        else:
            self.result.is_failure(f"Device temperature exceeds acceptable limits. Current system status: '{temperature_status}'")
```

As you can see there is no error handling to do in your code. Everything is packaged in the `AntaTest.anta_tests` decorator and below is a simple example of error captured when trying to access a dictionary with an incorrect key:

```python
class VerifyTemperature(AntaTest):
    ...
    @AntaTest.anta_test
    def test(self) -> None:
        # Grab output of the collected command
        command_output = self.instance_commands[0].json_output

        # Access the dictionary with an incorrect key
        command_output['incorrectKey']
```

```bash
ERROR    Exception raised for test VerifyTemperature (on device 192.168.0.10) - KeyError ('incorrectKey')
```

!!! info "Get stack trace for debugging"
    If you want to access to the full exception stack, you can run ANTA in debug mode by setting the `ANTA_DEBUG` environment variable to `true`. Example:
    ```bash
    $ ANTA_DEBUG=true anta nrfu --catalog test_custom.yml text
    ```

### Test decorators

In addition to the required `AntaTest.anta_tests` decorator, ANTA offers a set of optional decorators for further test customization:

- `anta.decorators.deprecated_test`: Use this to log a message of WARNING severity when a test is deprecated.
- `anta.decorators.skip_on_platforms`: Use this to skip tests for functionalities that are not supported on specific platforms.

```python
from anta.decorators import skip_on_platforms

class VerifyTemperature(AntaTest):
    ...
    @skip_on_platforms(["cEOSLab", "vEOS-lab"])
    @AntaTest.anta_test
    def test(self) -> None:
        pass
```

## Access your custom tests in the test catalog

!!! warning ""
    This section is required only if you are not merging your development into ANTA. Otherwise, just follow [contribution guide](../contribution.md).

For that, you need to create your own Python package as described in this [hitchhiker's guide](https://the-hitchhikers-guide-to-packaging.readthedocs.io/en/latest/) to package Python code. We assume it is well known and we won't focus on this aspect. Thus, your package must be impartable by ANTA hence available in the module search path `sys.path` (you can use `PYTHONPATH` for example).

It is very similar to what is documented in [catalog section](../usage-inventory-catalog.md) but you have to use your own package name.2

Let say the custom Python package is `anta_custom` and the test is defined in `anta_custom.dc_project` Python module, the test catalog would look like:

```yaml
anta_custom.dc_project:
  - VerifyFeatureX:
      minimum: 1
```

And now you can run your NRFU tests with the CLI:

```bash
anta nrfu text --catalog test_custom.yml
spine01 :: verify_dynamic_vlan :: FAILURE (Device has 0 configured, we expect at least 1)
spine02 :: verify_dynamic_vlan :: FAILURE (Device has 0 configured, we expect at least 1)
leaf01 :: verify_dynamic_vlan :: SUCCESS
leaf02 :: verify_dynamic_vlan :: SUCCESS
leaf03 :: verify_dynamic_vlan :: SUCCESS
leaf04 :: verify_dynamic_vlan :: SUCCESS
```
