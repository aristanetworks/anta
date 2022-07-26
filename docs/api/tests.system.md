<!-- markdownlint-disable -->

<a href="../../anta/tests/system.py#L0"><img align="right" style="float:right;" src="https://img.shields.io/badge/-source-cccccc?style=flat-square"></a>

# <kbd>module</kbd> `tests.system`
Test functions related to system-level features and protocols


---

<a href="../../anta/tests/system.py#L9"><img align="right" style="float:right;" src="https://img.shields.io/badge/-source-cccccc?style=flat-square"></a>

## <kbd>function</kbd> `verify_uptime`

```python
verify_uptime(device: anta.inventory.models.InventoryDevice, minimum=None)
```

Verifies the device uptime is higher than a value.



**Args:**

 - <b>`device`</b> (InventoryDevice):  InventoryDevice instance containing all devices information.
 - <b>`minimum`</b> (int):  Minimum uptime in seconds.



**Returns:**
 TestResult instance with * result = "unset" if test has not been executed * result = "success" if uptime is greater than minimun * result = "failure" otherwise. * result = "error" if any exception is caught


---

<a href="../../anta/tests/system.py#L43"><img align="right" style="float:right;" src="https://img.shields.io/badge/-source-cccccc?style=flat-square"></a>

## <kbd>function</kbd> `verify_reload_cause`

```python
verify_reload_cause(device: anta.inventory.models.InventoryDevice) → TestResult
```

Verifies the last reload of the device was requested by a user.

Test considers the following messages as normal and will return success. Failure is for other messages * Reload requested by the user. * Reload requested after FPGA upgrade



**Args:**

 - <b>`device`</b> (InventoryDevice):  InventoryDevice instance containing all devices information.



**Returns:**
 TestResult instance with * result = "unset" if test has not been executed * result = "success" if reload cause is standard * result = "failure" otherwise. * result = "error" if any exception is caught


---

<a href="../../anta/tests/system.py#L75"><img align="right" style="float:right;" src="https://img.shields.io/badge/-source-cccccc?style=flat-square"></a>

## <kbd>function</kbd> `verify_coredump`

```python
verify_coredump(device: anta.inventory.models.InventoryDevice) → TestResult
```

Verifies there is no core file.



**Args:**

 - <b>`device`</b> (InventoryDevice):  InventoryDevice instance containing all devices information.



**Returns:**
 TestResult instance with * result = "unset" if test has not been executed * result = "success" if device has no core-dump * result = "failure" otherwise. * result = "error" if any exception is caught


---

<a href="../../anta/tests/system.py#L104"><img align="right" style="float:right;" src="https://img.shields.io/badge/-source-cccccc?style=flat-square"></a>

## <kbd>function</kbd> `verify_agent_logs`

```python
verify_agent_logs(device: anta.inventory.models.InventoryDevice) → TestResult
```

Verifies there is no agent crash reported on the device.



**Args:**

 - <b>`device`</b> (InventoryDevice):  InventoryDevice instance containing all devices information.



**Returns:**
 TestResult instance with * result = "unset" if test has not been executed * result = "success" if there is no agent crash * result = "failure" otherwise. * result = "error" if any exception is caught


---

<a href="../../anta/tests/system.py#L132"><img align="right" style="float:right;" src="https://img.shields.io/badge/-source-cccccc?style=flat-square"></a>

## <kbd>function</kbd> `verify_syslog`

```python
verify_syslog(device: anta.inventory.models.InventoryDevice) → TestResult
```

Verifies the device had no syslog message with a severity of warning (or a more severe message) during the last 7 days.



**Args:**

 - <b>`device`</b> (InventoryDevice):  InventoryDevice instance containing all devices information.



**Returns:**
 TestResult instance with * result = "unset" if test has not been executed * result = "success" if syslog has no WARNING message * result = "failure" otherwise. * result = "error" if any exception is caught


---

<a href="../../anta/tests/system.py#L160"><img align="right" style="float:right;" src="https://img.shields.io/badge/-source-cccccc?style=flat-square"></a>

## <kbd>function</kbd> `verify_cpu_utilization`

```python
verify_cpu_utilization(
    device: anta.inventory.models.InventoryDevice
) → TestResult
```

Verifies the CPU utilization is less than 75%.



**Args:**

 - <b>`device`</b> (InventoryDevice):  InventoryDevice instance containing all devices information.



**Returns:**
 TestResult instance with * result = "unset" if test has not been executed * result = "success" if CPU usage is lower than 75% * result = "failure" otherwise. * result = "error" if any exception is caught


---

<a href="../../anta/tests/system.py#L188"><img align="right" style="float:right;" src="https://img.shields.io/badge/-source-cccccc?style=flat-square"></a>

## <kbd>function</kbd> `verify_memory_utilization`

```python
verify_memory_utilization(
    device: anta.inventory.models.InventoryDevice
) → TestResult
```

Verifies the memory utilization is less than 75%.



**Args:**

 - <b>`device`</b> (InventoryDevice):  InventoryDevice instance containing all devices information.



**Returns:**
 TestResult instance with * result = "unset" if test has not been executed * result = "success" if memory usage is lower than 75% * result = "failure" otherwise. * result = "error" if any exception is caught


---

<a href="../../anta/tests/system.py#L216"><img align="right" style="float:right;" src="https://img.shields.io/badge/-source-cccccc?style=flat-square"></a>

## <kbd>function</kbd> `verify_filesystem_utilization`

```python
verify_filesystem_utilization(
    device: anta.inventory.models.InventoryDevice
) → TestResult
```

Verifies each partition on the disk is used less than 75%.



**Args:**

 - <b>`device`</b> (InventoryDevice):  InventoryDevice instance containing all devices information.



**Returns:**
 TestResult instance with * result = "unset" if test has not been executed * result = "success" if disk is used less than 75% * result = "failure" otherwise. * result = "error" if any exception is caught


---

<a href="../../anta/tests/system.py#L245"><img align="right" style="float:right;" src="https://img.shields.io/badge/-source-cccccc?style=flat-square"></a>

## <kbd>function</kbd> `verify_ntp`

```python
verify_ntp(device: anta.inventory.models.InventoryDevice) → TestResult
```

Verifies NTP is synchronised.



**Args:**

 - <b>`device`</b> (InventoryDevice):  InventoryDevice instance containing all devices information.



**Returns:**
 TestResult instance with * result = "unset" if test has not been executed * result = "success" if synchronized with NTP server * result = "failure" otherwise. * result = "error" if any exception is caught




---

_This file was automatically generated via [lazydocs](https://github.com/ml-tooling/lazydocs)._
