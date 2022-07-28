<!-- markdownlint-disable -->

<a href="../../anta/tests/mlag.py#L0"><img align="right" style="float:right;" src="https://img.shields.io/badge/-source-cccccc?style=flat-square"></a>

# <kbd>module</kbd> `tests.mlag`
Test functions related to Multi-Chassis LAG


---

<a href="../../anta/tests/mlag.py#L9"><img align="right" style="float:right;" src="https://img.shields.io/badge/-source-cccccc?style=flat-square"></a>

## <kbd>function</kbd> `verify_mlag_status`

```python
verify_mlag_status(device: anta.inventory.models.InventoryDevice) → TestResult
```

Verifies the MLAG status: state is active, negotiation status is connected, local int is up, peer link is up.



**Args:**

 - <b>`device`</b> (InventoryDevice):  InventoryDevice instance containing all devices information.



**Returns:**
 TestResult instance with * result = "unset" if test has not been executed * result = "success" if the MLAG status is OK * result = "failure" otherwise. * result = "error" if any exception is caught


---

<a href="../../anta/tests/mlag.py#L48"><img align="right" style="float:right;" src="https://img.shields.io/badge/-source-cccccc?style=flat-square"></a>

## <kbd>function</kbd> `verify_mlag_interfaces`

```python
verify_mlag_interfaces(
    device: anta.inventory.models.InventoryDevice
) → TestResult
```

Verifies there is no inactive or active-partial MLAG interfaces.



**Args:**

 - <b>`device`</b> (InventoryDevice):  InventoryDevice instance containing all devices information.



**Returns:**
 TestResult instance with * result = "unset" if test has not been executed * result = "success" if there is no inactive or active-partial MLAG interfaces. * result = "failure" otherwise. * result = "error" if any exception is caught


---

<a href="../../anta/tests/mlag.py#L84"><img align="right" style="float:right;" src="https://img.shields.io/badge/-source-cccccc?style=flat-square"></a>

## <kbd>function</kbd> `verify_mlag_config_sanity`

```python
verify_mlag_config_sanity(
    device: anta.inventory.models.InventoryDevice
) → TestResult
```

Verifies there is no MLAG config-sanity inconsistencies.



**Args:**

 - <b>`device`</b> (InventoryDevice):  InventoryDevice instance containing all devices information.



**Returns:**
 TestResult instance with * result = "unset" if test has not been executed * result = "success" if there is no MLAG config-sanity inconsistencies * result = "failure" otherwise. * result = "error" if any exception is caught




---

_This file was automatically generated via [lazydocs](https://github.com/ml-tooling/lazydocs)._
