<!-- markdownlint-disable -->

<a href="../../anta/tests/routing/generic.py#L0"><img align="right" style="float:right;" src="https://img.shields.io/badge/-source-cccccc?style=flat-square"></a>

# <kbd>module</kbd> `tests.routing.generic`
Generic routing test functions


---

<a href="../../anta/tests/routing/generic.py#L8"><img align="right" style="float:right;" src="https://img.shields.io/badge/-source-cccccc?style=flat-square"></a>

## <kbd>function</kbd> `verify_routing_protocol_model`

```python
verify_routing_protocol_model(
    device: anta.inventory.models.InventoryDevice,
    model: str = 'multi-agent'
) → TestResult
```

Verifies the configured routing protocol model is the one we expect. And if there is no mismatch between the configured and operating routing protocol model.



**Args:**

 - <b>`device`</b> (InventoryDevice):  InventoryDevice instance containing all devices information.
 - <b>`model`</b> (str):  Expected routing protocol model (multi-agent or ribd). Default is multi-agent



**Returns:**
 TestResult instance with * result = "unset" if test has not been executed * result = "success" if routing model is well configured * result = "failure" otherwise. * result = "error" if any exception is caught


---

<a href="../../anta/tests/routing/generic.py#L46"><img align="right" style="float:right;" src="https://img.shields.io/badge/-source-cccccc?style=flat-square"></a>

## <kbd>function</kbd> `verify_routing_table_size`

```python
verify_routing_table_size(
    device: anta.inventory.models.InventoryDevice,
    minimum: int,
    maximum: int
) → TestResult
```

Verifies the size of the IP routing table (default VRF). Should be between the two provided thresholds.



**Args:**

 - <b>`device`</b> (InventoryDevice):  InventoryDevice instance containing all devices information.
 - <b>`minimum`</b> (int):  Expected minimum routing table (default VRF) size.
 - <b>`maximum`</b> (int):  Expected maximum routing table (default VRF) size.



**Returns:**
 TestResult instance with * result = "unset" if test has not been executed * result = "success" if routing-table size is correct * result = "failure" otherwise. * result = "error" if any exception is caught


---

<a href="../../anta/tests/routing/generic.py#L83"><img align="right" style="float:right;" src="https://img.shields.io/badge/-source-cccccc?style=flat-square"></a>

## <kbd>function</kbd> `verify_bfd`

```python
verify_bfd(device: anta.inventory.models.InventoryDevice) → TestResult
```

Verifies there is no BFD peer in down state (all VRF, IPv4 neighbors).



**Args:**

 - <b>`device`</b> (InventoryDevice):  InventoryDevice instance containing all devices information.



**Returns:**
 TestResult instance with * result = "unset" if test has not been executed * result = "success" if routing-table size is OK * result = "failure" otherwise. * result = "error" if any exception is caught




---

_This file was automatically generated via [lazydocs](https://github.com/ml-tooling/lazydocs)._
