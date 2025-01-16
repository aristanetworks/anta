<!--
  ~ Copyright (c) 2023-2025 Arista Networks, Inc.
  ~ Use of this source code is governed by the Apache License 2.0
  ~ that can be found in the LICENSE file.
  -->

ANTA is a Python library that can be used in user applications. This section describes how you can leverage ANTA Python modules to help you create your own NRFU solution.

> [!TIP]
> If you are unfamiliar with asyncio, refer to the Python documentation relevant to your Python version - https://docs.python.org/3/library/asyncio.html

## [AntaDevice](../api/device.md#anta.device.AntaDevice) Abstract Class

A device is represented in ANTA as a instance of a subclass of the [AntaDevice](../api/device.md#anta.device.AntaDevice) abstract class.
There are few abstract methods that needs to be implemented by child classes:

- The [collect()](../api/device.md#anta.device.AntaDevice.collect) coroutine is in charge of collecting outputs of [AntaCommand](../api/commands.md#anta.models.AntaCommand) instances.
- The [refresh()](../api/device.md#anta.device.AntaDevice.refresh) coroutine is in charge of updating attributes of the [AntaDevice](../api/device.md#anta.device.AntaDevice) instance. These attributes are used by [AntaInventory](../api/inventory.md#anta.inventory.AntaInventory) to filter out unreachable devices or by [AntaTest](../api/tests/anta_test.md#anta.models.AntaTest) to skip devices based on their hardware models.

The [copy()](../api/device.md#anta.device.AntaDevice.copy) coroutine is used to copy files to and from the device. It does not need to be implemented if tests are not using it.

### [AsyncEOSDevice](../api/device.md#anta.device.AsyncEOSDevice) Class

The [AsyncEOSDevice](../api/device.md#anta.device.AsyncEOSDevice) class is an implementation of [AntaDevice](../api/device.md#anta.device.AntaDevice) for Arista EOS.
It uses the [aio-eapi](https://github.com/jeremyschulman/aio-eapi) eAPI client and the [AsyncSSH](https://github.com/ronf/asyncssh) library.

- The [_collect()](../api/device.md#anta.device.AsyncEOSDevice._collect) coroutine collects [AntaCommand](../api/commands.md#anta.models.AntaCommand) outputs using eAPI.
- The [refresh()](../api/device.md#anta.device.AsyncEOSDevice.refresh) coroutine tries to open a TCP connection on the eAPI port and update the `is_online` attribute accordingly. If the TCP connection succeeds, it sends a `show version` command to gather the hardware model of the device and updates the `established` and `hw_model` attributes.
- The [copy()](../api/device.md#anta.device.AsyncEOSDevice.copy) coroutine copies files to and from the device using the SCP protocol.

## [AntaInventory](../api/inventory.md#anta.inventory.AntaInventory) Class

The [AntaInventory](../api/inventory.md#anta.inventory.AntaInventory) class is a subclass of the standard Python type [dict](https://docs.python.org/3/library/stdtypes.html#dict). The keys of this dictionary are the device names, the values are [AntaDevice](../api/device.md#anta.device.AntaDevice) instances.

[AntaInventory](../api/inventory.md#anta.inventory.AntaInventory) provides methods to interact with the ANTA inventory:

- The [add_device()](../api/inventory.md#anta.inventory.AntaInventory.add_device) method adds an [AntaDevice](../api/device.md#anta.device.AntaDevice) instance to the inventory. Adding an entry to [AntaInventory](../api/inventory.md#anta.inventory.AntaInventory) with a key different from the device name is not allowed.
- The [get_inventory()](../api/inventory.md#anta.inventory.AntaInventory.get_inventory) returns a new [AntaInventory](../api/inventory.md#anta.inventory.AntaInventory) instance with filtered out devices based on the method inputs.
- The [connect_inventory()](../api/inventory.md#anta.inventory.AntaInventory.connect_inventory) coroutine will execute the [refresh()](../api/device.md#anta.device.AntaDevice.refresh) coroutines of all the devices in the inventory.
- The [parse()](../api/inventory.md#anta.inventory.AntaInventory.parse) static method creates an [AntaInventory](../api/inventory.md#anta.inventory.AntaInventory) instance from a YAML file and returns it. The devices are [AsyncEOSDevice](../api/device.md#anta.device.AsyncEOSDevice) instances.

## Examples

### Parse an ANTA inventory file

```python
--8<-- "parse_anta_inventory_file.py"
```

> [!NOTE]
> **How to create your inventory file**
>
> Please visit this [dedicated section](../usage-inventory-catalog.md) for how to use inventory and catalog files.

### Run EOS commands

```python
--8<-- "run_eos_commands.py"
```
