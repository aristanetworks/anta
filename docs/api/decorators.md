<!-- markdownlint-disable -->

<a href="../../anta/decorators.py#L0"><img align="right" style="float:right;" src="https://img.shields.io/badge/-source-cccccc?style=flat-square"></a>

# <kbd>module</kbd> `decorators`
decorators for tests 


---

<a href="../../anta/decorators.py#L13"><img align="right" style="float:right;" src="https://img.shields.io/badge/-source-cccccc?style=flat-square"></a>

## <kbd>function</kbd> `skip_on_platforms`

```python
skip_on_platforms(
    platforms: List[str]
) → Callable[..., Callable[..., anta.result_manager.models.TestResult]]
```

Decorator factory to skip a test on a list of platforms 



**Args:**
 * platforms (List[str]): the list of platforms on which the decorated test should be skipped. 


---

<a href="../../anta/decorators.py#L48"><img align="right" style="float:right;" src="https://img.shields.io/badge/-source-cccccc?style=flat-square"></a>

## <kbd>function</kbd> `check_bgp_family_enable`

```python
check_bgp_family_enable(
    family: str
) → Callable[..., Callable[..., anta.result_manager.models.TestResult]]
```

Decorator factory to skip a test if BGP is enabled 



**Args:**
 * family (str): BGP family to check. Can be ipv4 / ipv6 / evpn / rtc 




---

_This file was automatically generated via [lazydocs](https://github.com/ml-tooling/lazydocs)._
