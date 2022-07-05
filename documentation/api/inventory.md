<!-- markdownlint-disable -->

<a href="../../anta/inventory/__init__.py#L0"><img align="right" style="float:right;" src="https://img.shields.io/badge/-source-cccccc?style=flat-square"></a>

# <kbd>module</kbd> `inventory`
Inventory Module for ANTA 

**Global Variables**
---------------
- **models**: # coding: utf-8 -*-
# pylint: skip-file



---

<a href="../../anta/inventory/__init__.py#L24"><img align="right" style="float:right;" src="https://img.shields.io/badge/-source-cccccc?style=flat-square"></a>

## <kbd>class</kbd> `AntaInventory`
Inventory Abstraction for ANTA framework 

Inventory file example: 
---------------------- ``` print(inventory.yml)```
``` anta_inventory:``` ```   hosts:```
```     - hosts: 1.1.1.1``` ```     - host: 2.2.2.2```
```   networks:``` ```     - network: 10.0.0.0/8```
```     - network: 192.168.0.0/16``` 

Inventory Output: 
------------------ ``` test = AntaInventory(inventory_file='examples/inventory.yml',username='ansible', password='ansible', auto_connect=True)```
``` test.inventory_get()``` ``` [```
```     "InventoryDevice(host=IPv4Address('192.168.0.17')",``` ```     "username='ansible'",```
```     "password='ansible'",``` ```     "session=<ServerProxy for ansible:ansible@192.168.0.17/command-api>",```
```     "url='https://ansible:ansible@192.168.0.17/command-api'",``` ```     "established=True",```

```     "InventoryDevice(host=IPv4Address('192.168.0.2')",``` ```     "username='ansible'",```
```     "password='ansible'",``` ```     "session=None",```
```     "url='https://ansible:ansible@192.168.0.2/command-api'",``` ```     "established=False"```
``` ]``` 

<a href="../../anta/inventory/__init__.py#L65"><img align="right" style="float:right;" src="https://img.shields.io/badge/-source-cccccc?style=flat-square"></a>

### <kbd>method</kbd> `AntaInventory.__init__`

```python
__init__(
    inventory_file: str,
    username: str,
    password: str,
    auto_connect: bool = True
)
```

__init__ Class constructor 



**Args:**
 
 - <b>`inventory_file`</b> (str):  Path to inventory YAML file where user has described his inputs 
 - <b>`username`</b> (str):  Username to use to connect to devices 
 - <b>`password`</b> (str):  Password to use to connect to devices 
 - <b>`auto_connect`</b> (bool, optional):  Automatically build eAPI context for every devices. Defaults to False. 




---

<a href="../../anta/inventory/__init__.py#L115"><img align="right" style="float:right;" src="https://img.shields.io/badge/-source-cccccc?style=flat-square"></a>

### <kbd>method</kbd> `AntaInventory.device_get`

```python
device_get(host_ip)
```

device_get Get device information from a given IP 



**Args:**
 
 - <b>`host_ip`</b> (str):  IP address of the device 



**Returns:**
 
 - <b>`InventoryDevice`</b>:  Device information 

---

<a href="../../anta/inventory/__init__.py#L259"><img align="right" style="float:right;" src="https://img.shields.io/badge/-source-cccccc?style=flat-square"></a>

### <kbd>method</kbd> `AntaInventory.inventory_get`

```python
inventory_get(format_out: str = 'native', established_only: bool = True)
```

inventory_get Expose device inventory 

Provides inventory has a list of InventoryDevice objects. If requried, it can be exposed in JSON format. Also, by default expose only active devices. 



**Args:**
 
 - <b>`format`</b> (str, optional):  Format output, can be native or JSON. Defaults to 'native'. 
 - <b>`established_only`</b> (bool, optional):  Allow to expose also unreachable devices. Defaults to True. 



**Returns:**
 
 - <b>`List`</b>:  List of InventoryDevice 

---

<a href="../../anta/inventory/__init__.py#L175"><img align="right" style="float:right;" src="https://img.shields.io/badge/-source-cccccc?style=flat-square"></a>

### <kbd>method</kbd> `AntaInventory.session_create`

```python
session_create(host_ip: str)
```

session_create Get session of a device 

If device has already a session, function only returns active session, if not, try to build a new session 



**Args:**
 
 - <b>`host_ip`</b> (str):  IP address of the device 



**Returns:**
 
 - <b>`bool`</b>:  True if update succeed, False if not 

---

<a href="../../anta/inventory/__init__.py#L196"><img align="right" style="float:right;" src="https://img.shields.io/badge/-source-cccccc?style=flat-square"></a>

### <kbd>method</kbd> `AntaInventory.session_get`

```python
session_get(host_ip: str)
```

session_get Expose RPC session of a given host from our inventory 

Provide RPC session if the session exists, if not, it returns None 



**Args:**
 
 - <b>`host_ip`</b> (str):  IP address of the host to match 



**Returns:**
 
 - <b>`jsonrpclib.Server`</b>:  Instance to the device. None if session does not exist 

---

<a href="../../anta/inventory/__init__.py#L213"><img align="right" style="float:right;" src="https://img.shields.io/badge/-source-cccccc?style=flat-square"></a>

### <kbd>method</kbd> `AntaInventory.sessions_create`

```python
sessions_create()
```

sessions_create Helper to build RPC sessions to all devices 




---

_This file was automatically generated via [lazydocs](https://github.com/ml-tooling/lazydocs)._
