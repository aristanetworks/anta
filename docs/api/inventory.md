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

Inventory file example: 
---------------------- ``` print(inventory.yml)```
``` anta_inventory:``` ```   hosts:```
```     - hosts: 1.1.1.1``` ```     - host: 2.2.2.2```
```   networks:``` ```     - network: 10.0.0.0/8```
```     - network: 192.168.0.0/16``` ```   ranges:```
```     - start: 10.0.0.1``` ```       end: 10.0.0.11```

Inventory Output:

------------------
``` test = AntaInventory(inventory_file='examples/inventory.yml',username='ansible', password='ansible', auto_connect=True)``` ``` test.get_inventory()```
``` [``` ```     "InventoryDevice(host=IPv4Address('192.168.0.17')",```
```     "username='ansible'",``` ```     "password='ansible'",```
```     "session=<ServerProxy for ansible:ansible@192.168.0.17/command-api>",``` ```     "url='https://ansible:ansible@192.168.0.17/command-api'",```
```     "established=True",``` 

```     "InventoryDevice(host=IPv4Address('192.168.0.2')",```
```     "username='ansible'",``` ```     "password='ansible'",```
```     "session=None",``` ```     "url='https://ansible:ansible@192.168.0.2/command-api'",```
```     "established=False"``` ``` ]```


<a href="../../anta/inventory/__init__.py#L80"><img align="right" style="float:right;" src="https://img.shields.io/badge/-source-cccccc?style=flat-square"></a>

### <kbd>method</kbd> `AntaInventory.__init__`

```python
__init__(
    inventory_file: str,
    username: str,
    password: str,
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

<a href="../../anta/inventory/__init__.py#L359"><img align="right" style="float:right;" src="https://img.shields.io/badge/-source-cccccc?style=flat-square"></a>

### <kbd>method</kbd> `AntaInventory.create_all_sessions`

```python
create_all_sessions(refresh_online_first: bool = False) → None
```

Helper to build RPC sessions to all devices. 



**Args:**
 
 - <b>`refresh_online_first`</b> (bool):  Run  a refresh of is_online flag for all devices. 

---

<a href="../../anta/inventory/__init__.py#L372"><img align="right" style="float:right;" src="https://img.shields.io/badge/-source-cccccc?style=flat-square"></a>

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

<a href="../../anta/inventory/__init__.py#L327"><img align="right" style="float:right;" src="https://img.shields.io/badge/-source-cccccc?style=flat-square"></a>

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

<a href="../../anta/inventory/__init__.py#L340"><img align="right" style="float:right;" src="https://img.shields.io/badge/-source-cccccc?style=flat-square"></a>

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

<a href="../../anta/inventory/__init__.py#L302"><img align="right" style="float:right;" src="https://img.shields.io/badge/-source-cccccc?style=flat-square"></a>

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
 
 - <b>`format`</b> (str, optional):  Format output, can be native or JSON. Defaults to 'native'. 
 - <b>`established_only`</b> (bool, optional):  Allow to expose also unreachable devices. Defaults to True. 



**Returns:**
 
 - <b>`InventoryDevices`</b>:  List of InventoryDevice 

---

<a href="../../anta/inventory/__init__.py#L401"><img align="right" style="float:right;" src="https://img.shields.io/badge/-source-cccccc?style=flat-square"></a>

### <kbd>method</kbd> `AntaInventory.refresh_online_flag_inventory`

```python
refresh_online_flag_inventory() → None
```

refresh_online_flag_inventory Update is_online flag for all devices. 

Execute in parallel a call to _refresh_online_flag_device to test device connectivity. 




---

_This file was automatically generated via [lazydocs](https://github.com/ml-tooling/lazydocs)._
