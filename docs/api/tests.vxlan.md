<!-- markdownlint-disable -->

<a href="../../anta/tests/vxlan.py#L0"><img align="right" style="float:right;" src="https://img.shields.io/badge/-source-cccccc?style=flat-square"></a>

# <kbd>module</kbd> `tests.vxlan`
Test functions related to VXLAN


---

<a href="../../anta/tests/vxlan.py#L9"><img align="right" style="float:right;" src="https://img.shields.io/badge/-source-cccccc?style=flat-square"></a>

## <kbd>function</kbd> `verify_vxlan`

```python
verify_vxlan(device: anta.inventory.models.InventoryDevice) → TestResult
```

Verifies the interface vxlan 1 status is up/up.



**Args:**

 - <b>`device`</b> (InventoryDevice):  InventoryDevice instance containing all devices information.



**Returns:**
 TestResult instance with * result = "unset" if test has not been executed * result = "success" if vxlan1 interface is UP UP * result = "failure" otherwise. * result = "error" if any exception is caught


---

<a href="../../anta/tests/vxlan.py#L41"><img align="right" style="float:right;" src="https://img.shields.io/badge/-source-cccccc?style=flat-square"></a>

## <kbd>function</kbd> `verify_vxlan_config_sanity`

```python
verify_vxlan_config_sanity(
    device: anta.inventory.models.InventoryDevice
) → TestResult
```

Verifies there is no VXLAN config-sanity warnings.



**Args:**

 - <b>`device`</b> (InventoryDevice):  InventoryDevice instance containing all devices information.



**Returns:**
 TestResult instance with * result = "unset" if test has not been executed * result = "success" if VXLAN config sanity is OK * result = "failure" otherwise. * result = "error" if any exception is caught




---

_This file was automatically generated via [lazydocs](https://github.com/ml-tooling/lazydocs)._
