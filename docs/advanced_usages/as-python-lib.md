# How to use ANTA as a Python Library

ANTA has been built to allow user to embeded its tools in your own application. This section describes how you can leverage ANTA modules to help you create your own NRFU solution.

## Inventory Manager

AntaInventory class is in charge of creating a list of hosts with their information and an eAPI session ready to be consummed. To do that, it connects to all devices to check reachability and ensure eAPI is running.

```python
from anta.inventory import AntaInventory

inventory = AntaInventory.parse(
    inventory_file="inventory.yml",
    username="username",
    password="password",
    enable_password="enable",
    timeout=1,
    insecure=False,
)
```

Then it is easy to get all devices or only active devices with the following method:

```python
"""
Example
"""
# This is needed to run the script for python < 3.10 for typing annotations
from __future__ import annotations

import asyncio

from anta.inventory import AntaInventory


async def main_loop(inv: AntaInventory) -> None:
    """
    Take an inventory and a list of commands and:
    1. try to connect to every device in the inventory
    2. print a message for every device where connection could not be established
    """
    await inv.connect_inventory()

    # Print a list of devices that could not be connected to
    for device in inv.get_inventory(established_only=False).values():
        if device.established is False:
            print(f"Could not connect to device {device.name}")

if __name__ == "__main__":
    # Create the inventory
    inventory = AntaInventory.parse(
        inventory_file="inv.yml",
        username="arista",
        password="@rista123",
        timeout=15,
    )

    # Run the main asyncio  entry point
    res = asyncio.run(main_loop(inventory, commands))
```


To run an EOS commands list on the reachable devices from the inventory
```python
"""
Example
"""
# This is needed to run the script for python < 3.10 for typing annotations
from __future__ import annotations

import asyncio
from copy import deepcopy
from pprint import pprint

from anta.inventory import AntaInventory
from anta.models import AntaCommand


async def main_loop(inv: AntaInventory, commands: list[str]) -> dict[str, list[AntaCommand]]:                                                                                                                                                                             
    """
    Take an inventory and a list of commands and:
    1. try to connect to every device in the inventory
    2. collect the results of the commands towards each device

    Returns:
      a dictionary where key is the device name and the value is the list of AntaCommand ran towards the device
    """
    await inv.connect_inventory()

    # Make a list of coroutine to run commands towards each connected device
    coros = []
    # dict to keep track of the commands per device
    result_dict = {}
    print("DONE")
    for name, device in inv.get_inventory(established_only=True).items():
        anta_commands = [AntaCommand(command=command, ofmt="json") for command in commands]
        result_dict[name] = anta_commands
        coros.append(device.collect_commands(anta_commands))

    # Run the coroutines
    await asyncio.gather(*coros)

    return result_dict


if __name__ == "__main__":
    # Create the inventory
    inventory = AntaInventory.parse(
        inventory_file="inv.yml",
        username="arista",
        password="@rista123",
        timeout=15,
    )

    # Create a list of commands with json output
    commands = ["show version", "show ip bgp summary"]

    # Run the main asyncio  entry point
    res = asyncio.run(main_loop(inventory, commands))

    pprint(res)
```

!!! tip
    If you are unfamiliar with asyncio, refer to the Python documentation relevant to your Python version - https://docs.python.org/3/library/asyncio.html

You can find the ANTA Inventory module [here](../api/inventory.md).

??? note "How to create your inventory file"
    Please visit this [dedicated section](../usage-inventory-catalog.md) for how to use inventory and catalog files.


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
