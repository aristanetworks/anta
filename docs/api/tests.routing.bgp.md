<!-- markdownlint-disable -->

<a href="../../anta/tests/routing/bgp.py#L0"><img align="right" style="float:right;" src="https://img.shields.io/badge/-source-cccccc?style=flat-square"></a>

# <kbd>module</kbd> `tests.routing.bgp`
BGP test functions


---

<a href="../../anta/tests/routing/bgp.py#L9"><img align="right" style="float:right;" src="https://img.shields.io/badge/-source-cccccc?style=flat-square"></a>

## <kbd>function</kbd> `verify_bgp_ipv4_unicast_state`

```python
verify_bgp_ipv4_unicast_state(
    device: anta.inventory.models.InventoryDevice
) → TestResult
```

Verifies all IPv4 unicast BGP sessions are established (for all VRF) and all BGP messages queues for these sessions are empty (for all VRF).



**Args:**

 - <b>`device`</b> (InventoryDevice):  InventoryDevice instance containing all devices information.



**Returns:**
 TestResult instance with * result = "unset" if test has not been executed * result = "success" if all IPv4 unicast BGP sessions are established (for all VRF)  and all BGP messages queues for these sessions are empty (for all VRF). * result = "failure" otherwise. * result = "error" if any exception is caught


---

<a href="../../anta/tests/routing/bgp.py#L77"><img align="right" style="float:right;" src="https://img.shields.io/badge/-source-cccccc?style=flat-square"></a>

## <kbd>function</kbd> `verify_bgp_ipv4_unicast_count`

```python
verify_bgp_ipv4_unicast_count(
    device: anta.inventory.models.InventoryDevice,
    number: int,
    vrf: str = 'default'
) → TestResult
```

Verifies all IPv4 unicast BGP sessions are established and all BGP messages queues for these sessions are empty and the actual number of BGP IPv4 unicast neighbors is the one we expect.



**Args:**

 - <b>`device`</b> (InventoryDevice):  InventoryDevice instance containing all devices information.
 - <b>`number`</b> (int):  Expected number of BGP IPv4 unicast neighbors
 - <b>`vrf`</b> (str):  VRF to verify. default is "default".



**Returns:**
 TestResult instance with * result = "unset" if test has not been executed * result = "success" if all IPv4 unicast BGP sessions are established  and if all BGP messages queues for these sessions are empty  and if the actual number of BGP IPv4 unicast neighbors is equal to `number. * result = "failure" otherwise. * result = "error" if any exception is caught


---

<a href="../../anta/tests/routing/bgp.py#L148"><img align="right" style="float:right;" src="https://img.shields.io/badge/-source-cccccc?style=flat-square"></a>

## <kbd>function</kbd> `verify_bgp_ipv6_unicast_state`

```python
verify_bgp_ipv6_unicast_state(
    device: anta.inventory.models.InventoryDevice
) → TestResult
```

Verifies all IPv6 unicast BGP sessions are established (for all VRF) and all BGP messages queues for these sessions are empty (for all VRF).



**Args:**

 - <b>`device`</b> (InventoryDevice):  InventoryDevice instance containing all devices information.



**Returns:**
 TestResult instance with * result = "unset" if test has not been executed * result = "success" if all IPv6 unicast BGP sessions are established (for all VRF)  and all BGP messages queues for these sessions are empty (for all VRF). * result = "failure" otherwise. * result = "error" if any exception is caught


---

<a href="../../anta/tests/routing/bgp.py#L217"><img align="right" style="float:right;" src="https://img.shields.io/badge/-source-cccccc?style=flat-square"></a>

## <kbd>function</kbd> `verify_bgp_evpn_state`

```python
verify_bgp_evpn_state(
    device: anta.inventory.models.InventoryDevice
) → TestResult
```

Verifies all EVPN BGP sessions are established (default VRF).



**Args:**

 - <b>`device`</b> (InventoryDevice):  InventoryDevice instance containing all devices information.



**Returns:**
 TestResult instance with * result = "unset" if test has not been executed * result = "success" if all EVPN BGP sessions are established. * result = "failure" otherwise. * result = "error" if any exception is caught


---

<a href="../../anta/tests/routing/bgp.py#L262"><img align="right" style="float:right;" src="https://img.shields.io/badge/-source-cccccc?style=flat-square"></a>

## <kbd>function</kbd> `verify_bgp_evpn_count`

```python
verify_bgp_evpn_count(
    device: anta.inventory.models.InventoryDevice,
    number: int
) → TestResult
```

Verifies all EVPN BGP sessions are established (default VRF) and the actual number of BGP EVPN neighbors is the one we expect (default VRF).



**Args:**

 - <b>`device`</b> (InventoryDevice):  InventoryDevice instance containing all devices information.
 - <b>`number`</b> (int):  The expected number of BGP EVPN neighbors in the default VRF.



**Returns:**
 TestResult instance with * result = "unset" if test has not been executed * result = "success" if all EVPN BGP sessions are Established and if the actual  number of BGP EVPN neighbors is the one we expect. * result = "failure" otherwise. * result = "error" if any exception is caught


---

<a href="../../anta/tests/routing/bgp.py#L315"><img align="right" style="float:right;" src="https://img.shields.io/badge/-source-cccccc?style=flat-square"></a>

## <kbd>function</kbd> `verify_bgp_rtc_state`

```python
verify_bgp_rtc_state(device: anta.inventory.models.InventoryDevice) → TestResult
```

Verifies all RTC BGP sessions are established (default VRF).



**Args:**

 - <b>`device`</b> (InventoryDevice):  InventoryDevice instance containing all devices information.



**Returns:**
 TestResult instance with * result = "unset" if test has not been executed * result = "success" if all RTC BGP sessions are Established. * result = "failure" otherwise. * result = "error" if any exception is caught


---

<a href="../../anta/tests/routing/bgp.py#L358"><img align="right" style="float:right;" src="https://img.shields.io/badge/-source-cccccc?style=flat-square"></a>

## <kbd>function</kbd> `verify_bgp_rtc_count`

```python
verify_bgp_rtc_count(
    device: anta.inventory.models.InventoryDevice,
    number: int
) → TestResult
```

Verifies all RTC BGP sessions are established (default VRF) and the actual number of BGP RTC neighbors is the one we expect (default VRF).



**Args:**

 - <b>`device`</b> (InventoryDevice):  InventoryDevice instance containing all devices information.
 - <b>`number`</b> (int):  The expected number of BGP RTC neighbors (default VRF).



**Returns:**
 TestResult instance with * result = "unset" if test has not been executed * result = "success" if all RTC BGP sessions are established  and if the actual number of BGP RTC neighbors is the one we expect. * result = "failure" otherwise. * result = "error" if any exception is caught




---

_This file was automatically generated via [lazydocs](https://github.com/ml-tooling/lazydocs)._
