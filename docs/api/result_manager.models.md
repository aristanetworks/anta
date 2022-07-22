<!-- markdownlint-disable -->

<a href="../../anta/result_manager/models.py#L0"><img align="right" style="float:right;" src="https://img.shields.io/badge/-source-cccccc?style=flat-square"></a>

# <kbd>module</kbd> `result_manager.models`
Models related to anta.result_manager module. 

**Global Variables**
---------------
- **RESULT_OPTIONS**


---

<a href="../../anta/result_manager/models.py#L12"><img align="right" style="float:right;" src="https://img.shields.io/badge/-source-cccccc?style=flat-square"></a>

## <kbd>class</kbd> `TestResult`
Describe result of a test from a single device. 



**Attributes:**
 
 - <b>`host`</b> (IPvAnyAddress):  IPv4 or IPv6 address of the device where the test has run. 
 - <b>`test`</b> (str):  Test name runs on the device. 
 - <b>`results`</b> (str):  Result of the test. Can be one of unset / failure / success. 
 - <b>`message`</b> (str, optional):  Message to report after the test. 




---

<a href="../../anta/result_manager/models.py#L27"><img align="right" style="float:right;" src="https://img.shields.io/badge/-source-cccccc?style=flat-square"></a>

### <kbd>classmethod</kbd> `TestResult.name_must_be_in`

```python
name_must_be_in(v)
```






---

<a href="../../anta/result_manager/models.py#L34"><img align="right" style="float:right;" src="https://img.shields.io/badge/-source-cccccc?style=flat-square"></a>

## <kbd>class</kbd> `ListResult`
List result for all tests on all devices. 



**Attributes:**
 
 - <b>`__root__`</b> (List[TestResult]):  A list of TestResult objects. 




---

<a href="../../anta/result_manager/models.py#L43"><img align="right" style="float:right;" src="https://img.shields.io/badge/-source-cccccc?style=flat-square"></a>

### <kbd>method</kbd> `ListResult.append`

```python
append(value) → None
```

Add support for append method. 




---

_This file was automatically generated via [lazydocs](https://github.com/ml-tooling/lazydocs)._
