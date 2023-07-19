ANTA is a Python library that can be used in user applications. This section describes how you can leverage ANTA Python modules to help you create your own NRFU solution.

!!! tip
    If you are unfamiliar with asyncio, refer to the Python documentation relevant to your Python version - https://docs.python.org/3/library/asyncio.html

## [AntaDevice](../api/device.md#anta.device.AntaDevice) Abstract Class

A device is represented in ANTA as a instance of a subclass of the [AntaDevice](../api/device.md### ::: anta.device.AntaDevice) abstract class.
There are few abstract methods that needs to be implemented by child classes:

- The [collect()](../api/device.md#anta.device.AntaDevice.collect) coroutine is in charge of collecting outputs of [AntaCommand](../api/models.md#anta.models.AntaCommand) instances.
- The [refresh()](../api/device.md#anta.device.AntaDevice.refresh) coroutine is in charge of updating attributes of the [AntaDevice](../api/device.md### ::: anta.device.AntaDevice) instance. These attributes are used by [AntaInventory](../api/inventory.md#anta.inventory.AntaInventory) to filter out unreachable devices or by [AntaTest](../api/models.md#anta.models.AntaTest) to skip devices based on their hardware models.

The [copy()](../api/device.md#anta.device.AntaDevice.copy) coroutine is used to copy files to and from the device. It does not need to be implemented if tests are not using it.

### [AsyncEOSDevice](../api/device.md#anta.device.AsyncEOSDevice) Class

The [AsyncEOSDevice](../api/device.md#anta.device.AsyncEOSDevice) class is an implementation of [AntaDevice](../api/device.md#anta.device.AntaDevice) for Arista EOS.
It uses the [aio-eapi](https://github.com/jeremyschulman/aio-eapi) eAPI client and the [AsyncSSH](https://github.com/ronf/asyncssh) library.

- The [collect()](../api/device.md#anta.device.AsyncEOSDevice.collect) coroutine collects [AntaCommand](../api/models.md#anta.models.AntaCommand) outputs using eAPI.
- The [refresh()](../api/device.md#anta.device.AsyncEOSDevice.refresh) coroutine tries to open a TCP connection on the eAPI port and update the `is_online` attribute accordingly. If the TCP connection succeeds, it sends a `show version` command to gather the hardware model of the device and updates the `established` and `hw_model` attributes.
- The [copy()](../api/device.md#anta.device.AsyncEOSDevice.copy) coroutine copies files to and from the device using the SCP protocol.

## [AntaInventory](../api/inventory.md#anta.inventory.AntaInventory) Class

The [AntaInventory](../api/inventory.md#anta.inventory.AntaInventory) class is a subclass of the standard Python type [dict](https://docs.python.org/3/library/stdtypes.html#dict). The keys of this dictionary are the device names, the values are [AntaDevice](../api/device.md#anta.device.AntaDevice) instances.


[AntaInventory](../api/inventory.md#anta.inventory.AntaInventory) provides methods to interact with the ANTA inventory:

- The [add_device()](../api/inventory.md#anta.inventory.AntaInventory.add_device) method adds an [AntaDevice](../api/device.md### ::: anta.device.AntaDevice) instance to the inventory. Adding an entry to [AntaInventory](../api/inventory.md#anta.inventory.AntaInventory) with a key different from the device name is not allowed.
- The [get_inventory()](../api/inventory.md#anta.inventory.AntaInventory.get_inventory) returns a new [AntaInventory](../api/inventory.md#anta.inventory.AntaInventory) instance with filtered out devices based on the method inputs.
- The [connect_inventory()](../api/inventory.md#anta.inventory.AntaInventory.connect_inventory) coroutine will execute the [refresh()](../api/device.md#anta.device.AntaDevice.refresh) coroutines of all the devices in the inventory.
- The [parse()](../api/inventory.md#anta.inventory.AntaInventory.parse) static method creates an [AntaInventory](../api/inventory.md#anta.inventory.AntaInventory) instance from a YAML file and returns it. The devices are [AsyncEOSDevice](../api/device.md#anta.device.AsyncEOSDevice) instances.


To parse a YAML inventory file and print the devices connection status:

```python
"""
Example
"""
import asyncio

from anta.inventory import AntaInventory


async def main(inv: AntaInventory) -> None:
    """
    Take an AntaInventory and:
    1. try to connect to every device in the inventory
    2. print a message for every device connection status
    """
    await inv.connect_inventory()

    for device in inv.values():
        if device.established:
            print(f"Device {device.name} is online")
        else:
            print(f"Could not connect to device {device.name}")

if __name__ == "__main__":
    # Create the AntaInventory instance
    inventory = AntaInventory.parse(
        inventory_file="inv.yml",
        username="arista",
        password="@rista123",
        timeout=15,
    )

    # Run the main coroutine
    res = asyncio.run(main(inventory))
```

??? note "How to create your inventory file"
    Please visit this [dedicated section](../usage-inventory-catalog.md) for how to use inventory and catalog files.

To run an EOS commands list on the reachable devices from the inventory:
```python
"""
Example
"""
# This is needed to run the script for python < 3.10 for typing annotations
from __future__ import annotations

import asyncio
from pprint import pprint

from anta.inventory import AntaInventory
from anta.models import AntaCommand


async def main(inv: AntaInventory, commands: list[str]) -> dict[str, list[AntaCommand]]:
    """
    Take an AntaInventory and a list of commands as string and:
    1. try to connect to every device in the inventory
    2. collect the results of the commands from each device

    Returns:
      a dictionary where key is the device name and the value is the list of AntaCommand ran towards the device
    """
    await inv.connect_inventory()

    # Make a list of coroutine to run commands towards each connected device
    coros = []
    # dict to keep track of the commands per device
    result_dict = {}
    for name, device in inv.get_inventory(established_only=True).items():
        anta_commands = [AntaCommand(command=command, ofmt="json") for command in commands]
        result_dict[name] = anta_commands
        coros.append(device.collect_commands(anta_commands))

    # Run the coroutines
    await asyncio.gather(*coros)

    return result_dict


if __name__ == "__main__":
    # Create the AntaInventory instance
    inventory = AntaInventory.parse(
        inventory_file="inv.yml",
        username="arista",
        password="@rista123",
        timeout=15,
    )

    # Create a list of commands with json output
    commands = ["show version", "show ip bgp summary"]

    # Run the main asyncio  entry point
    res = asyncio.run(main(inventory, commands))

    pprint(res)
```


## Use tests from ANTA

All the test classes inherit from the same abstract Base Class AntaTest. The Class definition indicates which commands are required for the test and the user should focus only on writing the `test` function with optional keywords argument. The instance of the class upon creation instantiates a TestResult object that can be accessed later on to check the status of the test ([unset, skipped, success, failure, error]).

### Test structure

All tests are built on a class named `AntaTest` which provides a complete toolset for a test:

- Object creation
- Test definition
- TestResult definition
- Abstracted method to collect data

This approach means each time you create a test it will be based on this `AntaTest` class. Besides that, you will have to provide some elements:

- `name`: Name of the test
- `description`: A human readable description of your test
- `categories`: a list of categories to sort test.
- `commands`: a list of command to run. This list _must_ be a list of `AntaCommand` which is described in the next part of this document.

Here is an example of a hardware test related to device temperature:

```python
from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional, cast

from anta.models import AntaTest, AntaCommand


class VerifyTemperature(AntaTest):
    """
    Verifies device temparture is currently OK.
    """

    # The test name
    name = "VerifyTemperature"
    # A small description of the test, usually the first line of the class docstring
    description = "Verifies device temparture is currently OK"
    # The category of the test, usually the module name
    categories = ["hardware"]
    # The command(s) used for the test. Could be a template instead
    commands = [AntaCommand(command="show system environment temperature", ofmt="json")]

    # Decorator
    @AntaTest.anta_test
    # abstract method that must be defined by the child Test class
    def test(self) -> None:
        """Run VerifyTemperature validation"""
        command_output = cast(Dict[str, Dict[Any, Any]], self.instance_commands[0].output)
        temperature_status = command_output["systemStatus"] if "systemStatus" in command_output.keys() else ""
        if temperature_status == "temperatureOk":
            self.result.is_success()
        else:
            self.result.is_failure(f"Device temperature is not OK, systemStatus: {temperature_status }")
```

When you run the test, object will automatically call its `anta.models.AntaTest.collect()` method to get device output for each command if no pre-collected data was given to the test. This method does a loop to call `anta.inventory.models.InventoryDevice.collect()` methods which is in charge of managing device connection and how to get data.

??? info "run test offline"
    You can also pass eos data directly to your test if you want to validate data collected in a different workflow. An example is provided below just for information:

    ```python
    test = VerifyTemperature(mocked_device, eos_data=test_data["eos_data"])
    asyncio.run(test.test())
    ```

The `test` function is always the same and __must__ be defined with the `@AntaTest.anta_test` decorator. This function takes at least one argument which is a `anta.inventory.models.InventoryDevice` object.
In some cases a test would rely on some additional inputs from the user, for instance the number of expected peers or some expected numbers. All parameters __must__ come with a default value and the test function __should__ validate the parameters values (at this stage this is the only place where validation can be done but there are future plans to make this better).

```python
class VerifyTemperature(AntaTest):
    ...
    @AntaTest.anta_test
    def test(self) -> None:
        pass

class VerifyTransceiversManufacturers(AntaTest):
    ...
    @AntaTest.anta_test
    def test(self, manufacturers: Optional[List[str]] = None) -> None:
        # validate the manufactures parameter
        pass
```

The test itself does not return any value, but the result is directly availble from your AntaTest object and exposes a `anta.result_manager.models.TestResult` object with result, name of the test and optional messages:

- `name` (str): Device name where the test has run.
- `test` (str): Test name runs on the device.
- `test_category` (List[str]): List of test categories the test belongs to.
- `test_description` (str): Test description.
- `results` (str): Result of the test. Can be one of ["unset", "success", "failure", "error", "skipped"].
- `messages` (List[str], optional): Messages to report after the test if any.

```python
from anta.tests.hardware import VerifyTemperature

test = VerifyTemperature(mocked_device, eos_data=test_data["eos_data"])
asyncio.run(test.test())
assert test.result.result == "success"
```

### Commands for test

To make it easier to get data, ANTA defines 2 different classes to manage commands to send to device:

#### `anta.models.AntaCommand`

Abstract a command with following information:

- Command to run,
- Ouput format expected
- eAPI version
- Output of the command

Usage example:

```python
from anta.models import AntaCommand

cmd1 = AntaCommand(command="show zerotouch")
cmd2 = AntaCommand(command="show running-config diffs", ofmt="text")
```

!!! tip "Command revision and version"
    * Most of EOS commands return a JSON structure according to a model (some commands may not be modeled hence the necessity to use `text` outformat sometimes.
    * The model can change across time (adding feature, ... ) and when the model is changed in a non backward-compatible way, the __revision__ number is bumped. The initial model starts with __revision__ 1.
    * A __revision__ applies to a particular CLI command whereas a __version__ is global to an eAPI call. The __version__ is internally translated to a specific __revision__ for each CLI command in the RPC call. The currently supported __version__ vaues  are `1` and `latest`.
    * A __revision takes precedence over a version__ (e.g. if a command is run with version="latest" and revision=1, the first revision of the model is returned)
    * By default eAPI returns the first revision of each model to ensure that when upgrading, intergation with existing tools is not broken. This is done by using by default `version=1` in eAPI calls.

    ANTA uses by default `version="latest"` in AntaCommand. For some commands, you may want to run them with a different revision or version. 
  
    For instance the `VerifyRoutingTableSize` test leverages the first revision of `show bfd peers`:

    ```
    # revision 1 as later revision introduce additional nesting for type
    commands = [AntaCommand(command="show bfd peers", revision=1)]
    ```


#### `anta.models.AntaTemplate`

Because some command can require more dynamic than just a command with no parameter provided by user, ANTA supports command template: you define a template in your test class and user provide parameters when creating test object.

!!! warning "Warning on AntaTemplate"
    * In its current versiom, an AntaTest class supports only __ONE__ AntaTemplate.
    * The current interface to pass template parameter to a template is an area of future improvements. Feedbacks are welcome.

```python

class RunArbitraryTemplateCommand(AntaTest):
    """
    Run an EOS command and return result
    Based on AntaTest to build relevant output for pytest
    """

    name = "Run aributrary EOS command"
    description = "To be used only with anta debug commands"
    template = AntaTemplate(template="show interfaces {ifd}")
    categories = ["debug"]

    @AntaTest.anta_test
    def test(self) -> None:
        errdisabled_interfaces = [interface for interface, value in response["interfaceStatuses"].items() if value["linkStatus"] == "errdisabled"]
        ...


params = [{"ifd": "Ethernet2"}, {"ifd": "Ethernet49/1"}]
run_command1 = RunArbitraryTemplateCommand(device_anta, params)
```

In this example, test waits for interfaces to check from user setup and will only check for interfaces in `params`
