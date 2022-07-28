<!-- markdownlint-disable -->

<a href="../../anta/result_manager/report.py#L0"><img align="right" style="float:right;" src="https://img.shields.io/badge/-source-cccccc?style=flat-square"></a>

# <kbd>module</kbd> `result_manager.report`
Report management for ANTA.



---

<a href="../../anta/result_manager/report.py#L17"><img align="right" style="float:right;" src="https://img.shields.io/badge/-source-cccccc?style=flat-square"></a>

## <kbd>class</kbd> `Colors`
Manage colors for output.





---

<a href="../../anta/result_manager/report.py#L30"><img align="right" style="float:right;" src="https://img.shields.io/badge/-source-cccccc?style=flat-square"></a>

## <kbd>class</kbd> `TableReport`
TableReport Generate a Table based on tabulate and TestResult.

<a href="../../anta/result_manager/report.py#L36"><img align="right" style="float:right;" src="https://img.shields.io/badge/-source-cccccc?style=flat-square"></a>

### <kbd>method</kbd> `TableReport.__init__`

```python
__init__(headers=None, colors: bool = True) → None
```

__init__ Class constructor



**Args:**

 - <b>`headers`</b> (list[str], optional):  List of headers. Defaults to None.




---

<a href="../../anta/result_manager/report.py#L147"><img align="right" style="float:right;" src="https://img.shields.io/badge/-source-cccccc?style=flat-square"></a>

### <kbd>method</kbd> `TableReport.add_content`

```python
add_content(results: List[result_manager.models.TestResult])
```

add_content Add content to manage in the report.



**Args:**

 - <b>`results`</b> (list[TestResult]):  A list of tests.

---

<a href="../../anta/result_manager/report.py#L157"><img align="right" style="float:right;" src="https://img.shields.io/badge/-source-cccccc?style=flat-square"></a>

### <kbd>method</kbd> `TableReport.build_content`

```python
build_content()
```

build_content Build output for the report.



**Returns:**

 - <b>`list`</b>:  A list of tests.

---

<a href="../../anta/result_manager/report.py#L97"><img align="right" style="float:right;" src="https://img.shields.io/badge/-source-cccccc?style=flat-square"></a>

### <kbd>method</kbd> `TableReport.content_sorted_by`

```python
content_sorted_by(key_index: int, reverse: bool = False) → list
```

content_sorted_by Sort content by using a user's defined key ID

Key ID indicates which column in the inner list to use for sorting



**Args:**

 - <b>`key_index`</b> (int):  innerkey to use to filter.
 - <b>`reverse`</b> (bool, optional):  Do reverse sorting. Defaults to False.



**Returns:**

 - <b>`List`</b>:  List of result to print

---

<a href="../../anta/result_manager/report.py#L52"><img align="right" style="float:right;" src="https://img.shields.io/badge/-source-cccccc?style=flat-square"></a>

### <kbd>method</kbd> `TableReport.content_sorted_by_host`

```python
content_sorted_by_host(reverse: bool = False)
```

content_sorted_by_host Sort content by using host field

Only valid for line using this structure: ``` [entry.host, entry.test, entry.result, entry.message]```



**Args:**


 - <b>`    reverse (bool, optional)`</b>:  Do reverse sorting. Defaults to False.



**Returns:**


 - <b>`    List`</b>:  List of result to print


---

<a href="../../anta/result_manager/report.py#L82"><img align="right" style="float:right;" src="https://img.shields.io/badge/-source-cccccc?style=flat-square"></a>

### <kbd>method</kbd> `TableReport.content_sorted_by_result`

```python
content_sorted_by_result(reverse: bool = False)
```

content_sorted_by_result Sort content by using result field

Only valid for line using this structure: ``` [entry.host, entry.test, entry.result, entry.message]```



**Args:**


 - <b>`    reverse (bool, optional)`</b>:  Do reverse sorting. Defaults to False.



**Returns:**


 - <b>`    List`</b>:  List of result to print


---

<a href="../../anta/result_manager/report.py#L67"><img align="right" style="float:right;" src="https://img.shields.io/badge/-source-cccccc?style=flat-square"></a>

### <kbd>method</kbd> `TableReport.content_sorted_by_test`

```python
content_sorted_by_test(reverse: bool = False)
```

content_sorted_by_test Sort content by using test field

Only valid for line using this structure: ``` [entry.host, entry.test, entry.result, entry.message]```



**Args:**


 - <b>`    reverse (bool, optional)`</b>:  Do reverse sorting. Defaults to False.



**Returns:**


 - <b>`    List`</b>:  List of result to print


---

<a href="../../anta/result_manager/report.py#L112"><img align="right" style="float:right;" src="https://img.shields.io/badge/-source-cccccc?style=flat-square"></a>

### <kbd>method</kbd> `TableReport.get`

```python
get(
    table_format: str = 'pretty',
    sort_by: str = 'host',
    reverse: bool = False,
    enable_colors: bool = True
)
```

get Expose report.

Expose report with multiple rendering options:
- Table style (from tabulate style support)
- Column sorting
- Reverse sorting



**Args:**

 - <b>`table_format`</b> (str, optional):  Table format to use based on tabulate style. Defaults to 'pretty'.
 - <b>`sort_by`</b> (str, optional):  Column to sort tests. Defaults to 'host'.
 - <b>`reverse`</b> (bool, optional):  Revert sort. Defaults to False.
 - <b>`enable_colors`</b> (bool, optional):  Add color to report. Defaults to True.



**Returns:**

 - <b>`tabulate`</b>:  A tabulate instance




---

_This file was automatically generated via [lazydocs](https://github.com/ml-tooling/lazydocs)._
