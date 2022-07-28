<!-- markdownlint-disable -->

<a href="../../anta/tests/hardware.py#L0"><img align="right" style="float:right;" src="https://img.shields.io/badge/-source-cccccc?style=flat-square"></a>

# <kbd>module</kbd> `tests.hardware`
Test functions related to the hardware or environement


---

<a href="../../anta/tests/hardware.py#L9"><img align="right" style="float:right;" src="https://img.shields.io/badge/-source-cccccc?style=flat-square"></a>

## <kbd>function</kbd> `verify_transceivers_manufacturers`

```python
verify_transceivers_manufacturers(
    device: anta.inventory.models.InventoryDevice,
    manufacturers=None
) → TestResult
```

Verifies the device is only using transceivers from supported manufacturers.



**Args:**

 - <b>`device`</b> (InventoryDevice):  InventoryDevice instance containing all devices information.
 - <b>`manufacturers`</b> (list):  List of allowed transceivers manufacturers.



**Returns:**
 TestResult instance with * result = "unset" if no manufacturers were given * result = "success" if the device is only using transceivers from supported manufacturers. * result = "failure" otherwise. * result = "error" if any exception is caught


---

<a href="../../anta/tests/hardware.py#L56"><img align="right" style="float:right;" src="https://img.shields.io/badge/-source-cccccc?style=flat-square"></a>

## <kbd>function</kbd> `verify_system_temperature`

```python
verify_system_temperature(
    device: anta.inventory.models.InventoryDevice
) → TestResult
```

Verifies the device temperature is currently OK and the device did not report any temperature alarm in the past.



**Args:**

 - <b>`device`</b> (InventoryDevice):  InventoryDevice instance containing all devices information.



**Returns:**
 TestResult instance with * result = "success" if the device temperature is OK. * result = "failure" otherwise. * result = "error" if any exception is caught


---

<a href="../../anta/tests/hardware.py#L90"><img align="right" style="float:right;" src="https://img.shields.io/badge/-source-cccccc?style=flat-square"></a>

## <kbd>function</kbd> `verify_transceiver_temperature`

```python
verify_transceiver_temperature(
    device: anta.inventory.models.InventoryDevice
) → TestResult
```

Verifies the transceivers temperature is currently OK and the device did not report any alarm in the past for its transceivers temperature.



**Args:**

 - <b>`device`</b> (InventoryDevice):  InventoryDevice instance containing all devices information.



**Returns:**
 TestResult instance with * result = "success" if the device transceivers temperature of the device is currently OK  AND the device did not report any alarm in the past for its transceivers temperature. * result = "failure" otherwise, * result = "error" if any exception is caught


---

<a href="../../anta/tests/hardware.py#L138"><img align="right" style="float:right;" src="https://img.shields.io/badge/-source-cccccc?style=flat-square"></a>

## <kbd>function</kbd> `verify_environment_cooling`

```python
verify_environment_cooling(
    device: anta.inventory.models.InventoryDevice
) → TestResult
```

Verifies the fans status is OK.



**Args:**

 - <b>`device`</b> (InventoryDevice):  InventoryDevice instance containing all devices information.



**Returns:**
 TestResult instance with * result = "success" if the fans status is OK. * result = "failure" otherwise. * result = "error" if any exception is caught


---

<a href="../../anta/tests/hardware.py#L171"><img align="right" style="float:right;" src="https://img.shields.io/badge/-source-cccccc?style=flat-square"></a>

## <kbd>function</kbd> `verify_environment_power`

```python
verify_environment_power(
    device: anta.inventory.models.InventoryDevice
) → TestResult
```

Verifies the power supplies status is OK.



**Args:**

 - <b>`device`</b> (InventoryDevice):  InventoryDevice instance containing all devices information.



**Returns:**
 TestResult instance with * result = "success" if the power supplies status is OK. * result = "failure" otherwise. * result = "error" if any exception is caught


---

<a href="../../anta/tests/hardware.py#L208"><img align="right" style="float:right;" src="https://img.shields.io/badge/-source-cccccc?style=flat-square"></a>

## <kbd>function</kbd> `verify_adverse_drops`

```python
verify_adverse_drops(device: anta.inventory.models.InventoryDevice) → TestResult
```

Verifies there is no adverse drops on DCS-7280E and DCS-7500E switches.



**Args:**

 - <b>`device`</b> (InventoryDevice):  InventoryDevice instance containing all devices information.



**Returns:**
 TestResult instance with * result = "success" if the device (DCS-7280E and DCS-7500E) doesnt reports adverse drops. * result = "failure" if the device (DCS-7280E and DCS-7500E) report adverse drops. * result = "error" if any exception is caught




---

_This file was automatically generated via [lazydocs](https://github.com/ml-tooling/lazydocs)._
