# Create your own custom tests

!!! info ""
    This documentation applies for both create tests in ANTA package or your custom package.

ANTA is not only a CLI with a collection of built-in tests, it is also a framework you can extend by building your own tests library.

For that, you need to create your own Python package as described in this [hitchhiker's guide](https://the-hitchhikers-guide-to-packaging.readthedocs.io/en/latest/) to package Python code. We assume it is well known and we won't focus on this aspect. Thus, your package must be impartable by ANTA hence available in `$PYTHONPATH` by any method.

## Generic approach

ANTA comes with a class to use to build test. This class provides all the toolset required to define, collect and test data. The next code is an example of how to use ANTA to build a test

```python
from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional, cast

from anta.models import AntaTest, AntaCommand


class VerifyTemperature(AntaTest):
    """
    Verifies device temparture is currently OK.
    """

    name = "VerifyTemperature"
    description = "Verifies device temparture is currently OK"
    categories = ["hardware"]
    commands = [AntaCommand(command="show system environment temperature", ofmt="json")]

    @AntaTest.anta_test
    def test(self) -> None:
        """Run VerifyTemperature validation"""
        command_output = cast(Dict[str, Dict[Any, Any]], self.instance_commands[0].output)
        temperature_status = command_output["systemStatus"] if "systemStatus" in command_output.keys() else ""
        if temperature_status == "temperatureOk":
            self.result.is_success()
        else:
            self.result.is_failure(f"Device temperature is not OK, systemStatus: {temperature_status }")
```

## Python imports

### Mandatory imports

The following elements have to be imported:

- [anta.models.AntaTest](../api/models.md#anta.models.AntaTest): class that gives you all the tooling for your test
- [anta.models.AntaCommand](../api/models.md#anta.models.AntaCommand): A class to abstract an Arista EOS command

```python
from anta.models import AntaTest, AntaCommand


class VerifyTemperature(AntaTest):
    """
    Verifies device temparture is currently OK.
    """
    ...

    @AntaTest.anta_test
    def test(self) -> None:
        pass
```

### Optional ANTA imports

Besides these 3 main imports, anta provides some additional and optional decorators:

- `anta.decorators.skip_on_platforms`: To skip a test for a function not available for some platform
- `anta.decorators.check_bgp_family_enable`: To run tests only if specific BGP family is active.


```python
from anta.decorators import skip_on_platforms


class VerifyTransceiversManufacturers(AntaTest):
    ...
    @skip_on_platforms(["cEOSLab", "vEOS-lab"])
    @AntaTest.anta_test
    def test(self, manufacturers: Optional[List[str]] = None) -> None:
        pass
```

### Optional python imports

And finally, you are free to import any other python library you may want to use in your package.

!!! info "logging function"
    It is strongly recommended to import `logging` to help development process and being able to log some outputs usefull for test development.

If your test development is part of a pull request for ANTA, it is stringly advised to also import `typing` since our code testing requires to be compatible with Mypy.

## Code for a test

A test is a python class where a test function is defined and will be run by the framework. So first you need to declare your class and then define your test function.

### Create Test Class

To create class, you have to provide 4 elements:

__Metadata information__

- `name`: Name of the test
- `description`: A human readable description of your test
- `categories`: a list of categories to sort test.

__Commands to run__

- `commands`: a list of command to run. This list _must_ be a list of `AntaCommand` which is described in the next part of this document.
- `template`: a command template (`AntaTemplate`) to run where variables are provided during test execution.

```python
from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional, cast

from anta.models import AntaTest, AntaCommand


class <YourTestName>(AntaTest):
    """
    <a docstring description of your test>
    """

    name = "YourTestName"                                           # should be your class name
    description = "<test description in human reading format>"
    categories = ["<a list of arbitrary categories>"]
    commands = [
        AntaCommand(
            command="<eos command to run>",
            ofmt="<command format output>",
            version="<eapi version to use>",
            revision="<revision to use for the command>",           # revision has precedence over version
        )
    ]
```

This class will inherit methods from AntaTest and specfically the `__init__(self,...)` method to build your object. This function takes following arguments when you instantiate an object:

- `device (InventoryDevice)`: Device object where to test happens.
- `template_params`: If template is used in the test definition, then we provide data to build list of commands.
- `eos_data`: Potential EOS data to pass if we don't want to connect to device to grab data.
- `labels`: a list of labels. It is not used yet and it is for futur use.

### Function definition

The code here can be very simple as well as very complex and will depend of what you expect to do. But in all situation, the same baseline can be leverage:

```python
class <YourTestName>(AntaTest):
    ...
    @AntaTest.anta_test
    def test(self) -> None:
        pass
```

If you want to support option in your test, just declare your options in your test method:

```python
class <YourTestName>(AntaTest):
    ...
    @AntaTest.anta_test
    def test(self, my_param1: Optional[str] = None) -> None:
        pass
```

The options __must__ be optional keyword arguments.

### Check inputs

If your test has some user inputs, you first have to validate the supplied values are valid. If it is not valid, we expect `TestResult` to return `skipped` with a custom message.

```python
class <YourTestName>(AntaTest):
    ...
    @AntaTest.anta_test
    def test(self, minimum: Optional[int] = None) -> None:
        # Check if test option is correct
        if not minimum:
            self.result.is_skipped("verify_dynamic_vlan was run without minimum value set")
            return
        # continue test..
        ...
```

### Implement your logic

Here you implement your own logic. In general, the first action is to send command to devices and capture its response.

In the example below, we request the list of vlans configured on device and then count all the vlans marked as dynamic

```python
class <YourTestName>(AntaTest):
    ...
    @AntaTest.anta_test
    def test(self, minimum: Optional[int] = None) -> None:
        # Check if test option is correct
        if not minimum:
            self.result.is_skipped("verify_dynamic_vlan was run without minimum value set")
            return

        # Grab data for your command
        command_output = cast(Dict[str, Dict[Any, Any]], self.instance_commands[0].output)

        # Do your test: In this example we count number of vlans with field dynamic set to true
        num_dyn_vlan = len([ vlan for vlan,data in command_output['vlans'].items() if command_output['dynamic'] is True])
        if num_dyn_vlan >= minimum:
            self.result.is_success()
        else:
            self.result.is_failure(f"Device has {num_dyn_vlan} configured, we expect at least {minimum}")
```

As you can see there is no error management to do in your code. Everything is packaged in `anta_tests` and below is a simple example of error captured with an incorrect JSON key in the code above:

```bash
ERROR    Exception raised for test verify_dynamic_vlan (on device 192.168.0.10) - KeyError ('vlans')
```

!!! info "Get stack trace for debugging"
    If you want to access to the full exception stack, you can run your test with logging level set to `DEBUG`. With ANTA cli, it is available with following option:
    ```bash
    $ ANTA_DEBUG=True anta nrfu text --catalog test_custom.yml --log-level debug
    ```

## Create your catalog

!!! warning ""
    This section is required only if you are not merging your development into ANTA. Otherwise, just follow [contribution guide](../contribution.md).

It is very similar to what is documented in [catalog section](../usage-inventory-catalog.md) but you have to use your own package name.

Let say the custom catalog is `anta_titom73` and the test is configured in `anta_titom73.dc_project`, the test catalog would look like:

```yaml
anta_titom73.dc_project:
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

!!! warning "Install your python package"
    Anta uses Python path to access to your test. So it is critical to have your tests library installed correctly as explained at the begining of this page (in short, your module should be in your `PYTHONPATH` to be able to be loaded).
