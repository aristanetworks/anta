<!-- markdownlint-disable -->

<a href="../../anta/inventory/__init__.py#L0"><img align="right" style="float:right;" src="https://img.shields.io/badge/-source-cccccc?style=flat-square"></a>

# <kbd>module</kbd> `inventory`
Inventory Module for ANTA.

**Global Variables**
---------------
- **exceptions**: # coding: utf-8 -*-

- **models**: # -*- coding: utf-8 -*-
# pylint: skip-file



---

<a href="../../anta/inventory/__init__.py#L34"><img align="right" style="float:right;" src="https://img.shields.io/badge/-source-cccccc?style=flat-square"></a>

## <kbd>class</kbd> `AntaInventory`
Inventory Abstraction for ANTA framework.



**Attributes:**

 - <b>`timeout`</b> (float):  Connection to device timeout.
 - <b>`INVENTORY_ROOT_KEY`</b> (str, Optional):  head of the YAML inventory. Default is anta_inventory
 - <b>`EAPI_SESSION_TPL`</b> (str, Optional):  Template for eAPI URL builder
 - <b>`INVENTORY_OUTPUT_FORMAT`</b> (List[str],Optional):  List of supported output format. Default ['native', 'json']
 - <b>`HW_MODEL_KEY`</b> (str,Optional):  Name of the key in Arista eAPI JSON provided by device.



**Examples:**


Inventory file input

 print(inventory.yml)  anta_inventory:  hosts:
            - hosts: 1.1.1.1
            - host: 2.2.2.2  networks:
            - network: 10.0.0.0/8
            - network: 192.168.0.0/16  ranges:
            - start: 10.0.0.1  end: 10.0.0.11

Inventory result:

 test = AntaInventory(  ... inventory_file='examples/inventory.yml',  ... username='ansible',  ... password='ansible',  ... auto_connect=True)  test.get_inventory()  [  "InventoryDevice(host=IPv4Address('192.168.0.17')",  "username='ansible'",  "password='ansible'",  "session=<ServerProxy for ansible:ansible@192.168.0.17/command-api>",  "url='https://ansible:ansible@192.168.0.17/command-api'",  "established=True",  "is_online=True",  "hw_model=cEOS-LAB",  ...  "InventoryDevice(host=IPv4Address('192.168.0.2')",  "username='ansible'",  "password='ansible'",  "session=None",  "url='https://ansible:ansible@192.168.0.2/command-api'",  "established=False"  "is_online=False",  "hw_model=unset",  ]



**Raises:**

 - <b>`InventoryRootKeyErrors`</b>:  Root key of inventory is missing.
 - <b>`InventoryIncorrectSchema`</b>:  Inventory file is not following AntaInventory Schema.
 - <b>`InventoryUnknownFormat`</b>:  Output format is not supported.

<a href="../../anta/inventory/__init__.py#L106"><img align="right" style="float:right;" src="https://img.shields.io/badge/-source-cccccc?style=flat-square"></a>

### <kbd>method</kbd> `AntaInventory.__init__`

```python
__init__(
    inventory_file: str,
    username: str,
    password: str,
    enable_password: str = None,
    auto_connect: bool = True,
    timeout: float = 5
) → None
```

Class constructor.



**Args:**

 - <b>`inventory_file`</b> (str):  Path to inventory YAML file where user has described his inputs
 - <b>`username`</b> (str):  Username to use to connect to devices
 - <b>`password`</b> (str):  Password to use to connect to devices
 - <b>`auto_connect`</b> (bool, optional):  Automatically build eAPI context for every devices. Defaults to True.
 - <b>`timeout`</b> (float, optional):  Timeout in second to wait before marking device down. Defaults to 5sec.




---

<a href="../../anta/inventory/__init__.py#L486"><img align="right" style="float:right;" src="https://img.shields.io/badge/-source-cccccc?style=flat-square"></a>

### <kbd>method</kbd> `AntaInventory.connect_inventory`

```python
connect_inventory()
```

connect_inventory Helper to prepare inventory with network data.

---

<a href="../../anta/inventory/__init__.py#L439"><img align="right" style="float:right;" src="https://img.shields.io/badge/-source-cccccc?style=flat-square"></a>

### <kbd>method</kbd> `AntaInventory.create_all_sessions`

```python
create_all_sessions(refresh_online_first: bool = False) → None
```

Helper to build RPC sessions to all devices.



**Args:**

 - <b>`refresh_online_first`</b> (bool):  Run  a refresh of is_online flag for all devices.

---

<a href="../../anta/inventory/__init__.py#L452"><img align="right" style="float:right;" src="https://img.shields.io/badge/-source-cccccc?style=flat-square"></a>

### <kbd>method</kbd> `AntaInventory.create_device_session`

```python
create_device_session(host_ip: str) → bool
```

Get session of a device.

If device has already a session, function only returns active session, if not, try to build a new session



**Args:**

 - <b>`host_ip`</b> (str):  IP address of the device



**Returns:**

 - <b>`bool`</b>:  True if update succeed, False if not

---

<a href="../../anta/inventory/__init__.py#L407"><img align="right" style="float:right;" src="https://img.shields.io/badge/-source-cccccc?style=flat-square"></a>

### <kbd>method</kbd> `AntaInventory.get_device`

```python
get_device(host_ip) → InventoryDevice
```

Get device information from a given IP.



**Args:**

 - <b>`host_ip`</b> (str):  IP address of the device



**Returns:**

 - <b>`InventoryDevice`</b>:  Device information

---

<a href="../../anta/inventory/__init__.py#L420"><img align="right" style="float:right;" src="https://img.shields.io/badge/-source-cccccc?style=flat-square"></a>

### <kbd>method</kbd> `AntaInventory.get_device_session`

```python
get_device_session(host_ip: str) → ServerProxy
```

Expose RPC session of a given host from our inventory.

Provide RPC session if the session exists, if not, it returns None



**Args:**

 - <b>`host_ip`</b> (str):  IP address of the host to match



**Returns:**

 - <b>`jsonrpclib.Server`</b>:  Instance to the device. None if session does not exist

---

<a href="../../anta/inventory/__init__.py#L380"><img align="right" style="float:right;" src="https://img.shields.io/badge/-source-cccccc?style=flat-square"></a>

### <kbd>method</kbd> `AntaInventory.get_inventory`

```python
get_inventory(
    format_out: str = 'native',
    established_only: bool = True
) → InventoryDevices
```

get_inventory Expose device inventory.

Provides inventory has a list of InventoryDevice objects. If requried, it can be exposed in JSON format. Also, by default expose only active devices.



**Args:**

 - <b>`format`</b> (str, optional):  Format output, can be native, list or JSON. Defaults to 'native'.
 - <b>`established_only`</b> (bool, optional):  Allow to expose also unreachable devices. Defaults to True.



**Returns:**

 - <b>`InventoryDevices`</b>:  List of InventoryDevice

---

<a href="../../anta/inventory/__init__.py#L495"><img align="right" style="float:right;" src="https://img.shields.io/badge/-source-cccccc?style=flat-square"></a>

### <kbd>method</kbd> `AntaInventory.refresh_device_facts`

```python
refresh_device_facts() → None
```

refresh_online_flag_inventory Update is_online flag for all devices.

Execute in parallel a call to _refresh_online_flag_device to test device connectivity.

---

<a href="../../anta/inventory/__init__.py#L481"><img align="right" style="float:right;" src="https://img.shields.io/badge/-source-cccccc?style=flat-square"></a>

### <kbd>method</kbd> `AntaInventory.set_credentials`

```python
set_credentials(
    username: str = None,
    password: str = None,
    enable_password: str = None
)
```








---

_This file was automatically generated via [lazydocs](https://github.com/ml-tooling/lazydocs)._
