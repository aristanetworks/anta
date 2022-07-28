<!-- markdownlint-disable -->

<a href="../../anta/tests/interfaces.py#L0"><img align="right" style="float:right;" src="https://img.shields.io/badge/-source-cccccc?style=flat-square"></a>

# <kbd>module</kbd> `tests.interfaces`
Test functions related to the device interfaces


---

<a href="../../anta/tests/interfaces.py#L11"><img align="right" style="float:right;" src="https://img.shields.io/badge/-source-cccccc?style=flat-square"></a>

## <kbd>function</kbd> `verify_interface_utilization`

```python
verify_interface_utilization(
    device: anta.inventory.models.InventoryDevice
) → TestResult
```

Verifies interfaces utilization is below 75%.



**Args:**

 - <b>`device`</b> (InventoryDevice):  InventoryDevice instance containing all devices information.



**Returns:**
 TestResult instance with * result = "unset" if test has not been executed * result = "success" if interfaces utilization is below 75% * result = "failure" otherwise. * result = "error" if any exception is caught


---

<a href="../../anta/tests/interfaces.py#L55"><img align="right" style="float:right;" src="https://img.shields.io/badge/-source-cccccc?style=flat-square"></a>

## <kbd>function</kbd> `verify_interface_errors`

```python
verify_interface_errors(
    device: anta.inventory.models.InventoryDevice
) → TestResult
```

Verifies interfaces error counters are equal to zero.



**Args:**

 - <b>`device`</b> (InventoryDevice):  InventoryDevice instance containing all devices information.



**Returns:**
 TestResult instance with * result = "unset" if test has not been executed * result = "success" if interfaces error counters are equal to zero. * result = "failure" otherwise. * result = "error" if any exception is caught


---

<a href="../../anta/tests/interfaces.py#L95"><img align="right" style="float:right;" src="https://img.shields.io/badge/-source-cccccc?style=flat-square"></a>

## <kbd>function</kbd> `verify_interface_discards`

```python
verify_interface_discards(
    device: anta.inventory.models.InventoryDevice
) → TestResult
```

Verifies interfaces packet discard counters are equal to zero.



**Args:**

 - <b>`device`</b> (InventoryDevice):  InventoryDevice instance containing all devices information.



**Returns:**
 TestResult instance with * result = "unset" if test has not been executed * result = "success" if interfaces discard counters are equal to zero. * result = "failure" otherwise. * result = "error" if any exception is caught


---

<a href="../../anta/tests/interfaces.py#L135"><img align="right" style="float:right;" src="https://img.shields.io/badge/-source-cccccc?style=flat-square"></a>

## <kbd>function</kbd> `verify_interface_errdisabled`

```python
verify_interface_errdisabled(
    device: anta.inventory.models.InventoryDevice
) → TestResult
```

Verifies there is no interface in error disable state.



**Args:**

 - <b>`device`</b> (InventoryDevice):  InventoryDevice instance containing all devices information.



**Returns:**
 TestResult instance with * result = "unset" if test has not been executed * result = "success" if no interface is in error disable state. * result = "failure" otherwise. * result = "error" if any exception is caught


---

<a href="../../anta/tests/interfaces.py#L175"><img align="right" style="float:right;" src="https://img.shields.io/badge/-source-cccccc?style=flat-square"></a>

## <kbd>function</kbd> `verify_interfaces_status`

```python
verify_interfaces_status(
    device: anta.inventory.models.InventoryDevice,
    minimum: int = None
) → TestResult
```

Verifies the number of Ethernet interfaces up/up on the device is higher or equal than a value.



**Args:**

 - <b>`device`</b> (InventoryDevice):  InventoryDevice instance containing all devices information.
 - <b>`minimum`</b> (int):  Expected minimum number of Ethernet interfaces up/up



**Returns:**
 TestResult instance with * result = "unset" if test has not been executed * result = "success" if the number of Ethernet interface up/up is >= minimum * result = "failure" otherwise. * result = "error" if any exception is caught


---

<a href="../../anta/tests/interfaces.py#L233"><img align="right" style="float:right;" src="https://img.shields.io/badge/-source-cccccc?style=flat-square"></a>

## <kbd>function</kbd> `verify_storm_control_drops`

```python
verify_storm_control_drops(
    device: anta.inventory.models.InventoryDevice
) → TestResult
```

Verifies the device did not drop packets due its to storm-control configuration.



**Args:**

 - <b>`device`</b> (InventoryDevice):  InventoryDevice instance containing all devices information.



**Returns:**
 TestResult instance with * result = "unset" if test has not been executed * result = "success" if the device did not drop packet due to its storm-control configuration. * result = "failure" otherwise. * result = "error" if any exception is caught


---

<a href="../../anta/tests/interfaces.py#L277"><img align="right" style="float:right;" src="https://img.shields.io/badge/-source-cccccc?style=flat-square"></a>

## <kbd>function</kbd> `verify_portchannels`

```python
verify_portchannels(device: anta.inventory.models.InventoryDevice) → TestResult
```

Verifies there is no inactive port in port channels.



**Args:**

 - <b>`device`</b> (InventoryDevice):  InventoryDevice instance containing all devices information.



**Returns:**
 TestResult instance with * result = "unset" if test has not been executed * result = "success" if there is no inactive ports in port-channels  in particular "success" if there is no port-channel * result = "failure" otherwise. * result = "error" if any exception is caught


---

<a href="../../anta/tests/interfaces.py#L318"><img align="right" style="float:right;" src="https://img.shields.io/badge/-source-cccccc?style=flat-square"></a>

## <kbd>function</kbd> `verify_illegal_lacp`

```python
verify_illegal_lacp(device: anta.inventory.models.InventoryDevice) → TestResult
```

Verifies there is no illegal LACP packets received.



**Args:**

 - <b>`device`</b> (InventoryDevice):  InventoryDevice instance containing all devices information.



**Returns:**
 TestResult instance with * result = "unset" if test has not been executed * result = "success" if there is no illegal LACP packets received.  in particular "success" if there is no port-channel * result = "failure" otherwise. * result = "error" if any exception is caught


---

<a href="../../anta/tests/interfaces.py#L363"><img align="right" style="float:right;" src="https://img.shields.io/badge/-source-cccccc?style=flat-square"></a>

## <kbd>function</kbd> `verify_loopback_count`

```python
verify_loopback_count(
    device: anta.inventory.models.InventoryDevice,
    number: int = None
) → TestResult
```

Verifies the number of loopback interfaces on the device is the one we expect. And if none of the loopback is down.



**Args:**

 - <b>`device`</b> (InventoryDevice):  InventoryDevice instance containing all devices information.
 - <b>`number`</b> (int):  Expected number of loopback interfaces.



**Returns:**
 TestResult instance with * result = "unset" if test has not been executed * result = "success" if the number of loopback is equal to `number` and if  none of the loopback is down * result = "failure" otherwise. * result = "error" if any exception is caught


---

<a href="../../anta/tests/interfaces.py#L424"><img align="right" style="float:right;" src="https://img.shields.io/badge/-source-cccccc?style=flat-square"></a>

## <kbd>function</kbd> `verify_svi`

```python
verify_svi(device: anta.inventory.models.InventoryDevice) → TestResult
```

Verifies there is no interface vlan down.



**Args:**

 - <b>`device`</b> (InventoryDevice):  InventoryDevice instance containing all devices information.



**Returns:**
 TestResult instance with * result = "unset" if test has not been executed * result = "success" if no SVI is down * result = "failure" otherwise. * result = "error" if any exception is caught


---

<a href="../../anta/tests/interfaces.py#L466"><img align="right" style="float:right;" src="https://img.shields.io/badge/-source-cccccc?style=flat-square"></a>

## <kbd>function</kbd> `verify_spanning_tree_blocked_ports`

```python
verify_spanning_tree_blocked_ports(
    device: anta.inventory.models.InventoryDevice
) → TestResult
```

Verifies there is no spanning-tree blocked ports.



**Args:**

 - <b>`device`</b> (InventoryDevice):  InventoryDevice instance containing all devices information.



**Returns:**
 TestResult instance with * result = "unset" if test has not been executed * result = "success" if there is no spanning-tree blocked ports * result = "failure" otherwise. * result = "error" if any exception is caught




---

_This file was automatically generated via [lazydocs](https://github.com/ml-tooling/lazydocs)._
