<!-- markdownlint-disable -->

<a href="../../anta/tests/routing/ospf.py#L0"><img align="right" style="float:right;" src="https://img.shields.io/badge/-source-cccccc?style=flat-square"></a>

# <kbd>module</kbd> `tests.routing.ospf`
OSPF test functions


---

<a href="../../anta/tests/routing/ospf.py#L9"><img align="right" style="float:right;" src="https://img.shields.io/badge/-source-cccccc?style=flat-square"></a>

## <kbd>function</kbd> `verify_ospf_state`

```python
verify_ospf_state(device: anta.inventory.models.InventoryDevice) → TestResult
```

Verifies all OSPF neighbors are in FULL state.



**Args:**

 - <b>`device`</b> (InventoryDevice):  InventoryDevice instance containing all devices information.



**Returns:**
 TestResult instance with * result = "unset" if test has not been executed * result = "success" if all OSPF neighbors are FULL. * result = "failure" otherwise. * result = "error" if any exception is caught


---

<a href="../../anta/tests/routing/ospf.py#L36"><img align="right" style="float:right;" src="https://img.shields.io/badge/-source-cccccc?style=flat-square"></a>

## <kbd>function</kbd> `verify_ospf_count`

```python
verify_ospf_count(
    device: anta.inventory.models.InventoryDevice,
    number: int
) → TestResult
```

Verifies the number of OSPF neighbors in FULL state is the one we expect.



**Args:**

 - <b>`device`</b> (InventoryDevice):  InventoryDevice instance containing all devices information.
 - <b>`number`</b> (int):  The expected number of OSPF neighbors in FULL state.



**Returns:**
 TestResult instance with * result = "unset" if test has not been executed * result = "success" if device has correct number of devices * result = "failure" otherwise. * result = "error" if any exception is caught




---

_This file was automatically generated via [lazydocs](https://github.com/ml-tooling/lazydocs)._
