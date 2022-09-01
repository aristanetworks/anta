<!-- markdownlint-disable -->

<a href="../../anta/inventory/models.py#L0"><img align="right" style="float:right;" src="https://img.shields.io/badge/-source-cccccc?style=flat-square"></a>

# <kbd>module</kbd> `inventory.models`
Models related to inventory management. 



---

<a href="../../anta/inventory/models.py#L13"><img align="right" style="float:right;" src="https://img.shields.io/badge/-source-cccccc?style=flat-square"></a>

## <kbd>class</kbd> `AntaInventoryHost`
Host definition for user's inventory. 



**Attributes:**
 
 - <b>`host`</b> (IPvAnyAddress):  IPv4 or IPv6 address of the device 





---

<a href="../../anta/inventory/models.py#L24"><img align="right" style="float:right;" src="https://img.shields.io/badge/-source-cccccc?style=flat-square"></a>

## <kbd>class</kbd> `AntaInventoryNetwork`
Network definition for user's inventory. 



**Attributes:**
 
 - <b>`network`</b> (IPvAnyNetwork):  Subnet to use for testing. 





---

<a href="../../anta/inventory/models.py#L35"><img align="right" style="float:right;" src="https://img.shields.io/badge/-source-cccccc?style=flat-square"></a>

## <kbd>class</kbd> `AntaInventoryRange`
IP Range definition for user's inventory. 



**Attributes:**
 
 - <b>`start`</b> (IPvAnyAddress):  IPv4 or IPv6 address for the begining of the range. 
 - <b>`stop`</b> (IPvAnyAddress):  IPv4 or IPv6 address for the end of the range. 





---

<a href="../../anta/inventory/models.py#L48"><img align="right" style="float:right;" src="https://img.shields.io/badge/-source-cccccc?style=flat-square"></a>

## <kbd>class</kbd> `AntaInventoryInput`
User's inventory model. 



**Attributes:**
 
 - <b>`netwrks`</b> (List[AntaInventoryNetwork],Optional):  List of AntaInventoryNetwork objects for networks. 
 - <b>`hosts`</b> (List[AntaInventoryHost],Optional):  List of AntaInventoryHost objects for hosts. 
 - <b>`range`</b> (List[AntaInventoryRange],Optional):  List of AntaInventoryRange objects for ranges. 





---

<a href="../../anta/inventory/models.py#L66"><img align="right" style="float:right;" src="https://img.shields.io/badge/-source-cccccc?style=flat-square"></a>

## <kbd>class</kbd> `InventoryDevice`
Inventory model exposed by Inventory class. 



**Attributes:**
 
 - <b>`host`</b> (IPvAnyAddress):  IPv4 or IPv6 address of the device. 
 - <b>`username`</b> (str):  Username to use for connection. 
 - <b>`password`</b> (password):  Password to use for connection. 
 - <b>`enable_password`</b> (Optional[str]):  enable_password to use on the device, required for some tests 
 - <b>`session`</b> (Any):  JSONRPC session. 
 - <b>`established`</b> (bool):  Flag to mark if connection is established (True) or not (False). Default: False. 
 - <b>`is_online`</b> (bool):  Flag to mark if host is alive (True) or not (False). Default: False. 
 - <b>`hw_model`</b> (str):  HW name gathered during device discovery. 
 - <b>`url`</b> (str):  eAPI URL to use to build session. 




---

<a href="../../anta/inventory/models.py#L92"><img align="right" style="float:right;" src="https://img.shields.io/badge/-source-cccccc?style=flat-square"></a>

### <kbd>method</kbd> `InventoryDevice.assert_enable_password_is_not_none`

```python
assert_enable_password_is_not_none(test_name: Optional[str] = None) → None
```

raise ValueError is enable_password is None 


---

<a href="../../anta/inventory/models.py#L104"><img align="right" style="float:right;" src="https://img.shields.io/badge/-source-cccccc?style=flat-square"></a>

## <kbd>class</kbd> `InventoryDevices`
Inventory model to list all InventoryDevice entries. 



**Attributes:**
 
 - <b>`__root__`</b> (List[InventoryDevice]):  A list of InventoryDevice objects. 




---

<a href="../../anta/inventory/models.py#L115"><img align="right" style="float:right;" src="https://img.shields.io/badge/-source-cccccc?style=flat-square"></a>

### <kbd>method</kbd> `InventoryDevices.append`

```python
append(value: inventory.models.InventoryDevice) → None
```

Add support for append method. 




---

_This file was automatically generated via [lazydocs](https://github.com/ml-tooling/lazydocs)._
