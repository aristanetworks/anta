<!-- markdownlint-disable -->

<a href="../../anta/tests/configuration.py#L0"><img align="right" style="float:right;" src="https://img.shields.io/badge/-source-cccccc?style=flat-square"></a>

# <kbd>module</kbd> `tests.configuration`
Test functions related to the device configuration


---

<a href="../../anta/tests/configuration.py#L9"><img align="right" style="float:right;" src="https://img.shields.io/badge/-source-cccccc?style=flat-square"></a>

## <kbd>function</kbd> `verify_zerotouch`

```python
verify_zerotouch(device: anta.inventory.models.InventoryDevice) → TestResult
```

Verifies ZeroTouch is disabled.



**Args:**

 - <b>`device`</b> (InventoryDevice):  InventoryDevice instance containing all devices information.



**Returns:**
 TestResult instance with * result = "success" if ZTP is disabled * result = "failure" if ZTP is enabled * result = "error" if any exception is caught


---

<a href="../../anta/tests/configuration.py#L41"><img align="right" style="float:right;" src="https://img.shields.io/badge/-source-cccccc?style=flat-square"></a>

## <kbd>function</kbd> `verify_running_config_diffs`

```python
verify_running_config_diffs(
    device: anta.inventory.models.InventoryDevice
) → TestResult
```

Verifies there is no difference between the running-config and the startup-config.



**Args:**

 - <b>`device`</b> (InventoryDevice):  InventoryDevice instance containing all devices information.



**Returns:**
 TestResult instance with * result = "success" if there is no difference between the running-config and the startup-config * result = "failure" if there are differences * result = "error" if any exception is caught




---

_This file was automatically generated via [lazydocs](https://github.com/ml-tooling/lazydocs)._
