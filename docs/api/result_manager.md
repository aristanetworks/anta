<!-- markdownlint-disable -->

<a href="../../anta/result_manager/__init__.py#L0"><img align="right" style="float:right;" src="https://img.shields.io/badge/-source-cccccc?style=flat-square"></a>

# <kbd>module</kbd> `result_manager`
Result Manager Module for ANTA.

**Global Variables**
---------------
- **models**: # -*- coding: utf-8 -*-
# pylint: skip-file

- **report**: # coding: utf-8 -*-



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

<a href="../../anta/result_manager/__init__.py#L74"><img align="right" style="float:right;" src="https://img.shields.io/badge/-source-cccccc?style=flat-square"></a>

### <kbd>method</kbd> `ResultManager.add_test_result`

```python
add_test_result(entry: result_manager.models.TestResult) → None
```

Add a result to the list



**Args:**

 - <b>`entry`</b> (TestResult):  TestResult data to add to the report

---

<a href="../../anta/result_manager/__init__.py#L127"><img align="right" style="float:right;" src="https://img.shields.io/badge/-source-cccccc?style=flat-square"></a>

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

<a href="../../anta/result_manager/__init__.py#L106"><img align="right" style="float:right;" src="https://img.shields.io/badge/-source-cccccc?style=flat-square"></a>

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

<a href="../../anta/result_manager/__init__.py#L82"><img align="right" style="float:right;" src="https://img.shields.io/badge/-source-cccccc?style=flat-square"></a>

### <kbd>method</kbd> `ResultManager.get_results`

```python
get_results(output_format: str = 'native') → <built-in function any>
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

<a href="../../anta/result_manager/__init__.py#L147"><img align="right" style="float:right;" src="https://img.shields.io/badge/-source-cccccc?style=flat-square"></a>

### <kbd>method</kbd> `ResultManager.table_report`

```python
table_report(
    sort_by: str = 'host',
    reverse: bool = False,
    colors: bool = True
) → <function tabulate at 0x7fc131b2b160>
```

Build a table report of all tests



**Args:**

 - <b>`sort_by`</b> (str, optional):  Key to use to filter result. Can be either host/test/result. Defaults to 'host'.
 - <b>`reverse`</b> (bool, optional):  Enable reverse sorting. Defaults to False.
 - <b>`colors`</b> (bool, optional):  Select if tests results are colored or not. Defaults to True.



**Returns:**

 - <b>`tabulate`</b>:  A Tabulate str that can be printed.




---

_This file was automatically generated via [lazydocs](https://github.com/ml-tooling/lazydocs)._
