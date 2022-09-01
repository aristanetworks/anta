<!-- markdownlint-disable -->

<a href="../../anta/result_manager/__init__.py#L0"><img align="right" style="float:right;" src="https://img.shields.io/badge/-source-cccccc?style=flat-square"></a>

# <kbd>module</kbd> `result_manager`
Result Manager Module for ANTA. 



---

<a href="../../anta/result_manager/__init__.py#L17"><img align="right" style="float:right;" src="https://img.shields.io/badge/-source-cccccc?style=flat-square"></a>

## <kbd>class</kbd> `ResultManager`
Helper to manage Test Results and generate reports. 



**Examples:**
 

 Create Inventory: 

 inventory_anta = AntaInventory(  inventory_file='examples/inventory.yml',  username='ansible',  password='ansible',  timeout=0.5,  auto_connect=True  ) 

 Create Result Manager: 

 manager = ResultManager() 

 Run tests for all connected devices: 

 for device in inventory_anta.get_inventory():  manager.add_test_result(  verify_eos_version(  device=device, versions=['4.28.0F']  )  )  manager.add_test_result(  verify_uptime(  device=device, minimum=1  )  ) 

 Print result in native format: 

 manager.get_results()  [  TestResult(  host=IPv4Address('192.168.0.10'),  test='verify_eos_version',  result='failure',  message="device is running version 4.27.3F-26379303.4273F (engineering build) and test expect ['4.28.0F']"  ),  TestResult(  host=IPv4Address('192.168.0.10'),  test='verify_eos_version',  result='success',  message=None  ),  ] 

<a href="../../anta/result_manager/__init__.py#L70"><img align="right" style="float:right;" src="https://img.shields.io/badge/-source-cccccc?style=flat-square"></a>

### <kbd>method</kbd> `ResultManager.__init__`

```python
__init__() → None
```

Class constructor. 




---

<a href="../../anta/result_manager/__init__.py#L81"><img align="right" style="float:right;" src="https://img.shields.io/badge/-source-cccccc?style=flat-square"></a>

### <kbd>method</kbd> `ResultManager.add_test_result`

```python
add_test_result(entry: anta.result_manager.models.TestResult) → None
```

Add a result to the list 



**Args:**
 
 - <b>`entry`</b> (TestResult):  TestResult data to add to the report 

---

<a href="../../anta/result_manager/__init__.py#L180"><img align="right" style="float:right;" src="https://img.shields.io/badge/-source-cccccc?style=flat-square"></a>

### <kbd>method</kbd> `ResultManager.get_hosts`

```python
get_hosts() → List[str]
```

Get list of IP addresses in current manager. 



**Returns:**
 
 - <b>`List[str]`</b>:  List of IP addresses. 

---

<a href="../../anta/result_manager/__init__.py#L141"><img align="right" style="float:right;" src="https://img.shields.io/badge/-source-cccccc?style=flat-square"></a>

### <kbd>method</kbd> `ResultManager.get_result_by_host`

```python
get_result_by_host(host_ip: str, output_format: str = 'native') → Any
```

Get list of test result for a given host. 



**Args:**
 
 - <b>`host_ip`</b> (str):  IP Address of the host to use to filter results. 
 - <b>`output_format`</b> (str, optional):  format selector. Can be either native/list. Defaults to 'native'. 



**Returns:**
 
 - <b>`Any`</b>:  List of results related to the host. 

---

<a href="../../anta/result_manager/__init__.py#L115"><img align="right" style="float:right;" src="https://img.shields.io/badge/-source-cccccc?style=flat-square"></a>

### <kbd>method</kbd> `ResultManager.get_result_by_test`

```python
get_result_by_test(test_name: str, output_format: str = 'native') → Any
```

Get list of test result for a given test. 



**Args:**
 
 - <b>`test_name`</b> (str):  Test name to use to filter results 
 - <b>`output_format`</b> (str, optional):  format selector. Can be either native/list. Defaults to 'native'. 



**Returns:**
 
 - <b>`list[TestResult]`</b>:  List of results related to the test. 

---

<a href="../../anta/result_manager/__init__.py#L90"><img align="right" style="float:right;" src="https://img.shields.io/badge/-source-cccccc?style=flat-square"></a>

### <kbd>method</kbd> `ResultManager.get_results`

```python
get_results(output_format: str = 'native') → Any
```

Expose list of all test results in different format 

Support multiple format: 
- native: ListResults format 
- list: a list of TestResult 
- json: a native JSON format 



**Args:**
 
 - <b>`output_format`</b> (str, optional):  format selector. Can be either native/list/json. Defaults to 'native'. 



**Returns:**
 
 - <b>`any`</b>:  List of results. 

---

<a href="../../anta/result_manager/__init__.py#L165"><img align="right" style="float:right;" src="https://img.shields.io/badge/-source-cccccc?style=flat-square"></a>

### <kbd>method</kbd> `ResultManager.get_testcases`

```python
get_testcases() → List[str]
```

Get list of name of all test cases in current manager. 



**Returns:**
 
 - <b>`List[str]`</b>:  List of names for all tests. 




---

_This file was automatically generated via [lazydocs](https://github.com/ml-tooling/lazydocs)._
