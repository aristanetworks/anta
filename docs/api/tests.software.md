<!-- markdownlint-disable -->

<a href="../../anta/tests/software.py#L0"><img align="right" style="float:right;" src="https://img.shields.io/badge/-source-cccccc?style=flat-square"></a>

# <kbd>module</kbd> `tests.software`
Test functions related to the EOS software


---

<a href="../../anta/tests/software.py#L11"><img align="right" style="float:right;" src="https://img.shields.io/badge/-source-cccccc?style=flat-square"></a>

## <kbd>function</kbd> `verify_eos_version`

```python
verify_eos_version(
    device: anta.inventory.models.InventoryDevice,
    versions: List[str] = None
) → TestResult
```

Verifies the device is running one of the allowed EOS version.



**Args:**

 - <b>`device`</b> (InventoryDevice):  InventoryDevice instance containing all devices information.
 - <b>`versions`</b> (list):  List of allowed EOS versions.



**Returns:**
 TestResult instance with * result = "unset" if test has not been executed * result = "success" if EOS version is valid against versions * result = "failure" otherwise. * result = "error" if any exception is caught


---

<a href="../../anta/tests/software.py#L47"><img align="right" style="float:right;" src="https://img.shields.io/badge/-source-cccccc?style=flat-square"></a>

## <kbd>function</kbd> `verify_terminattr_version`

```python
verify_terminattr_version(
    device: anta.inventory.models.InventoryDevice,
    versions=None
) → TestResult
```

Verifies the device is running one of the allowed TerminAttr version.



**Args:**

 - <b>`device`</b> (InventoryDevice):  InventoryDevice instance containing all devices information.
 - <b>`versions`</b> (list):  List of allowed TerminAttr versions.



**Returns:**
 TestResult instance with * result = "unset" if test has not been executed * result = "success" if TerminAttr version is valid against versions * result = "failure" otherwise. * result = "error" if any exception is caught


---

<a href="../../anta/tests/software.py#L81"><img align="right" style="float:right;" src="https://img.shields.io/badge/-source-cccccc?style=flat-square"></a>

## <kbd>function</kbd> `verify_eos_extensions`

```python
verify_eos_extensions(
    device: anta.inventory.models.InventoryDevice
) → TestResult
```

Verifies all EOS extensions installed on the device are enabled for boot persistence.



**Args:**

 - <b>`device`</b> (jsonrpclib.jsonrpc.ServerProxy):  Instance of the class jsonrpclib.jsonrpc.ServerProxy with the uri f'https://{username}:{password}@{ip}/command-api'.
 - <b>`enable_password`</b> (str):  Enable password.



**Returns:**

 - <b>`bool`</b>:  `True` if the device has all installed its EOS extensions enabled for boot persistence. `False` otherwise.


---

<a href="../../anta/tests/software.py#L119"><img align="right" style="float:right;" src="https://img.shields.io/badge/-source-cccccc?style=flat-square"></a>

## <kbd>function</kbd> `verify_field_notice_44_resolution`

```python
verify_field_notice_44_resolution(
    device: anta.inventory.models.InventoryDevice
) → TestResult
```

Verifies the device is using an Aboot version that fix the bug discussed in the field notice 44 (Aboot manages system settings prior to EOS initialization).



**Args:**

 - <b>`device`</b> (InventoryDevice):  InventoryDevice instance containing all devices information.



**Returns:**
 TestResult instance with * result = "unset" if test has not been executed * result = "success" if aboot is running valid version * result = "failure" otherwise. * result = "error" if any exception is caught




---

_This file was automatically generated via [lazydocs](https://github.com/ml-tooling/lazydocs)._
