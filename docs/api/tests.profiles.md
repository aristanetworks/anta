<!-- markdownlint-disable -->

<a href="../../anta/tests/profiles.py#L0"><img align="right" style="float:right;" src="https://img.shields.io/badge/-source-cccccc?style=flat-square"></a>

# <kbd>module</kbd> `tests.profiles`
Test functions related to ASIC profiles


---

<a href="../../anta/tests/profiles.py#L9"><img align="right" style="float:right;" src="https://img.shields.io/badge/-source-cccccc?style=flat-square"></a>

## <kbd>function</kbd> `verify_unified_forwarding_table_mode`

```python
verify_unified_forwarding_table_mode(
    device: anta.inventory.models.InventoryDevice,
    mode: str
) → TestResult
```

Verifies the device is using the expected Unified Forwarding Table mode.



**Args:**

 - <b>`device`</b> (InventoryDevice):  InventoryDevice instance containing all devices information.
 - <b>`mode`</b> (str):  The expected Unified Forwarding Table mode.



**Returns:**
 TestResult instance with * result = "unset" if test has not been executed * result = "success" if UFT mode is correct * result = "failure" otherwise. * result = "error" if any exception is caught


---

<a href="../../anta/tests/profiles.py#L45"><img align="right" style="float:right;" src="https://img.shields.io/badge/-source-cccccc?style=flat-square"></a>

## <kbd>function</kbd> `verify_tcam_profile`

```python
verify_tcam_profile(
    device: anta.inventory.models.InventoryDevice,
    profile: str
) → TestResult
```

Verifies the configured TCAM profile is the expected one.



**Args:**

 - <b>`device`</b> (InventoryDevice):  InventoryDevice instance containing all devices information.
 - <b>`profile`</b> (str):  The expected TCAM profile.0



**Returns:**
 TestResult instance with * result = "unset" if test has not been executed * result = "success" if TCAM profile is correct * result = "failure" otherwise. * result = "error" if any exception is caught




---

_This file was automatically generated via [lazydocs](https://github.com/ml-tooling/lazydocs)._
