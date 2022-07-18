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

<a href="../../anta/result_manager/__init__.py#L16"><img align="right" style="float:right;" src="https://img.shields.io/badge/-source-cccccc?style=flat-square"></a>

## <kbd>class</kbd> `ResultManager`
ResultManager Helper to manage Test Results and generate reports. 

<a href="../../anta/result_manager/__init__.py#L19"><img align="right" style="float:right;" src="https://img.shields.io/badge/-source-cccccc?style=flat-square"></a>

### <kbd>method</kbd> `ResultManager.__init__`

```python
__init__() → None
```

__init__ Class constructor. 




---

<a href="../../anta/result_manager/__init__.py#L23"><img align="right" style="float:right;" src="https://img.shields.io/badge/-source-cccccc?style=flat-square"></a>

### <kbd>method</kbd> `ResultManager.add_test_result`

```python
add_test_result(entry: result_manager.models.TestResult) → None
```

add_test_result Add a result to the list 



**Args:**
 
 - <b>`entry`</b> (TestResult):  TestResult data to add to the report 

---

<a href="../../anta/result_manager/__init__.py#L68"><img align="right" style="float:right;" src="https://img.shields.io/badge/-source-cccccc?style=flat-square"></a>

### <kbd>method</kbd> `ResultManager.get_result_by_host`

```python
get_result_by_host(host_ip: str)
```

get_result_by_test Get list of test result for a given host. 



**Args:**
 
 - <b>`host_ip`</b> (str):  IP Address of the host to use to filter results. 



**Returns:**
 
 - <b>`list[TestResult]`</b>:  List of results related to the host. 

---

<a href="../../anta/result_manager/__init__.py#L56"><img align="right" style="float:right;" src="https://img.shields.io/badge/-source-cccccc?style=flat-square"></a>

### <kbd>method</kbd> `ResultManager.get_result_by_test`

```python
get_result_by_test(test_name: str)
```

get_result_by_test Get list of test result for a given test. 



**Args:**
 
 - <b>`test_name`</b> (str):  Test name to use to filter results 



**Returns:**
 
 - <b>`list[TestResult]`</b>:  List of results related to the test. 

---

<a href="../../anta/result_manager/__init__.py#L32"><img align="right" style="float:right;" src="https://img.shields.io/badge/-source-cccccc?style=flat-square"></a>

### <kbd>method</kbd> `ResultManager.get_results`

```python
get_results(output_format: str = 'native') → <built-in function any>
```

get_results Expose list of all test results in different format 

Support multiple format: 
- native: ListResults format 
- list: a list of TestResult 
- json: a native JSON format 



**Args:**
 
 - <b>`output_format`</b> (str, optional):  format selector. Can be either native/list/json. Defaults to 'native'. 



**Returns:**
 
 - <b>`any`</b>:  List of results. 

---

<a href="../../anta/result_manager/__init__.py#L80"><img align="right" style="float:right;" src="https://img.shields.io/badge/-source-cccccc?style=flat-square"></a>

### <kbd>method</kbd> `ResultManager.table_report`

```python
table_report(
    sort_by: str = 'host',
    reverse: bool = False,
    colors: bool = True
) → <function tabulate at 0x7fa05bc62dc0>
```

table_report Build a table report of all tests 



**Args:**
 
 - <b>`sort_by`</b> (str, optional):  Key to use to filter result. Can be either host/test/result. Defaults to 'host'. 
 - <b>`reverse`</b> (bool, optional):  Enable reverse sorting. Defaults to False. 
 - <b>`colors`</b> (bool, optional):  Select if tests results are colored or not. Defaults to True. 



**Returns:**
 
 - <b>`tabulate`</b>:  A Tabulate str that can be printed. 




---

_This file was automatically generated via [lazydocs](https://github.com/ml-tooling/lazydocs)._
