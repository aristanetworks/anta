<!-- markdownlint-disable -->

<a href="../../anta/tests/multicast.py#L0"><img align="right" style="float:right;" src="https://img.shields.io/badge/-source-cccccc?style=flat-square"></a>

# <kbd>module</kbd> `tests.multicast`
Test functions related to multicast


---

<a href="../../anta/tests/multicast.py#L10"><img align="right" style="float:right;" src="https://img.shields.io/badge/-source-cccccc?style=flat-square"></a>

## <kbd>function</kbd> `verify_igmp_snooping_vlans`

```python
verify_igmp_snooping_vlans(
    device: anta.inventory.models.InventoryDevice,
    vlans: List[str],
    configuration: str
)
```

Verifies the IGMP snooping configuration for some VLANs.



**Args:**

 - <b>`device`</b> (InventoryDevice):  InventoryDevice instance containing all devices information.
 - <b>`vlans`</b> (List[str]):  A list of VLANs
 - <b>`configuration`</b> (str):  Expected IGMP snooping configuration (enabled or disabled) for these VLANs.



**Returns:**
 TestResult instance with * result = "unset" if test has not been executed * result = "success" if IGMP snooping is configured on these vlans * result = "failure" otherwise. * result = "error" if any exception is caught


---

<a href="../../anta/tests/multicast.py#L50"><img align="right" style="float:right;" src="https://img.shields.io/badge/-source-cccccc?style=flat-square"></a>

## <kbd>function</kbd> `verify_igmp_snooping_global`

```python
verify_igmp_snooping_global(
    device: anta.inventory.models.InventoryDevice,
    configuration: str
)
```

Verifies the IGMP snooping global configuration.



**Args:**

 - <b>`device`</b> (InventoryDevice):  InventoryDevice instance containing all devices information.
 - <b>`configuration`</b> (str):  Expected global IGMP snooping configuration (enabled or disabled).



**Returns:**
 TestResult instance with * result = "unset" if test has not been executed * result = "success" if IGMP snooping is globally configured * result = "failure" otherwise. * result = "error" if any exception is caught




---

_This file was automatically generated via [lazydocs](https://github.com/ml-tooling/lazydocs)._
