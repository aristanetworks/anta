# Create your own custom tests

ANTA is not only a CLI with a collection of built-in tests, it is also a framework you can extend by building your own tests library.

For that, you need to create your own Python package as described in this [hitchhiker's guide](https://the-hitchhikers-guide-to-packaging.readthedocs.io/en/latest/) to package Python code. We assume it is well known and we won't focus on this aspect.

## Generic approach

To make it easier for everyone, it is recommended to apply always same structure to all code:

```python

# Optional for easy coding
from typing import Optional
import logging

# Import ANTA components
from anta.inventory.models import InventoryDevice
from anta.result_manager.models import TestResult
from anta.tests import anta_test

# Instantiate logger
logger = logging.getLogger(__name__)

# define a function with at least one decorator to mark as a test
@anta.test
async def verify_dynamic_vlan(device: InventoryDevice,
    result: TestResult, minimum: Optional[int] = None) -> TestResult:

    # Create docstring
    # [...]

    # Create your own logic

    # Check if test option is correct
    if not minimum:
        result.is_skipped("verify_dynamic_vlan was run without minimum value set")
        return result

    # Send command to device
    response = await device.session.cli(command="show vlan", ofmt="json")

    # Optionaly log response for futur debug
    logger.debug(f"query result is: {response}")

    # Do your test: In this example we count number of vlans with field dynamic set to true
    num_dyn_vlan = len([ vlan for vlan,data in response['vlans'].items() if data['dynamic'] is True])
    if num_dyn_vlan >= minimum:
        result.is_success()
    else:
        result.is_failure(f"Device has {num_dyn_vlan} configured, we expect at least {minimum}")

    return result
```

## Python imports

### Mandatory imports

You should import at least following elements:

- [`InventoryDevice`](../api/inventory.models.md): Where the eAPI session lives. It is used to send commands over HTTP/HTTPS define in your test.
- [`TestResult`](../api/result_manager_models.md): Structure used to facilitate test result. It provides helpers like `is_success`, `is_failure`, `is_skipped` and also runs execption managment for you.
- `anta_test`: A python decorator to mark function as a test and inject all the base requirements to run test and capture Exceptions.

```python
from anta.inventory.models import InventoryDevice
from anta.result_manager.models import TestResult
from anta.tests import anta_test


@anta.test
async def verify_dynamic_vlan(...)
```

### Optional ANTA imports

Besides these 3 main imports, anta provides some additional and optional decorators:

- `anta.test.skip_on_platforms`: To skip a test for a function not available for some platform
- `anta.tests.check_bgp_family_enable`: To run tests only if specific BGP family is active.


```python
from anta.decorators import skip_on_platforms


@skip_on_platforms(["cEOSLab", "VEOS-LAB"])
@anta_test
async def verify_unified_forwarding_table_mode(...)
```

### Optional python imports

And finally, you are free to import any other python library you may want to use in your package.

!!! info "logging function"
    It is strongly recommended to import `logging` to help development process and being able to log some outputs usefull for test development.

## Code for a test

### Function definition

The code here can be very simple as well as very complex and will depend of what you expect to do. But in all situation, the same baseline can be leverage:

- Function parameters:
  - `async` in front of the function the function signature defines it as a coroutine and enable parallel execution.
  - `device: InventoryDevice`: Device information (mandatory)
  - `result: TestResult`: A result structure to save test (mandatory)
  - Any option your test may require. In our example, we use `minimum: Optional[int]`

```python
async def verify_dynamic_vlan(
    device: InventoryDevice,
    result: TestResult,
    minimum: Optional[int] = None
) -> TestResult:
```

### Function documentation

Then, a docstring to document your test. We recommend to use the following syntax rendering for documentation is working pretty well:

!!! info "docstring is optional"
    Of course this section is optional, but we stringly believe in documentation to make the code easier to maintain over the time.

```python
"""
< Short description >

< Optional long description >

< A list of inputs >
Args:
    device (InventoryDevice): InventoryDevice instance containing all devices information.
    minimum (int): Minimum number of dynamic vlans expected.

< Description of returned values in TestResult object >
Returns:
    TestResult instance with
    * result = "unset" if the test has not been executed
    * result = "skipped" if the `minimum` parameter is  missing
    * result = "success" if device has more than minimum dynamic vlans
    * result = "failure" otherwise.
    * result = "error" if any exception is caught
"""
```

You can see output using [mkdocstring-python](https://mkdocstrings.github.io/python/) here: [tests.software.md](../api/tests.software.md)

### Check inputs

If your test has some user's inputs, first you have to validate values are valid. If it is not valid, we expect `TestResult` to return `skipped` with a custom message

```python
# Check if test option is correct
if not minimum:
    result.is_skipped("verify_dynamic_vlan was run without minimum value set")
    return result
```

### Implement your logic

Here you implement your own logic. In general, the first action is to send command to devices and capture its response.

In the example below, we request list of vlans configured on device and then count all the vlans marked as dynamic

```python
# Send command to device
response = await device.session.cli(command="show vlan", ofmt="json")

# Do your test: In this example we count number of vlans with field dynamic set to true
num_dyn_vlan = len([ vlan for vlan,data in response['vlans'].items() if data['dynamic'] is True])
if num_dyn_vlan >= minimum:
    result.is_success()
else:
    result.is_failure(f"Device has {num_dyn_vlan} configured, we expect at least {minimum}")

return result
```

As you can see there is no error management to do in your code. Everything is packaged in `anta_tests` and below is a simple example of error captured with an incorrect JSON key in the code above:

```bash
ERROR    Exception raised for test verify_dynamic_vlan (on device 192.168.0.10) - KeyError ('vlans')
```

!!! info "Get stack trace for debugging"
    If you want to access to the full exception stack, you can run your test with logging level set to `DEBUG`. With ANTA cli, it is available with following option:
    ```bash
    $ anta nrfu text --catalog test_custom.yml --log-level debug
    ```

## Create your catalog

It is very similar to what is documented in [catalog section](../usage-inventory-catalog.md) but you have to use your own package name.

Let say my custom catalog is `anta_titom73` and my test is configured in `anta_titom73.dc_project`, my test catalog should be:

```yaml
anta_titom73.dc_project:
  - verify_dynamic_vlan:
      minimum: 1
```
And now you can run your NRFU tests with the CLI:

```bash
anta nrfu text --catalog test_custom.yml
spine01 :: verify_dynamic_vlan :: FAILURE (Device has 0 configured, we expect at least 1)
spine02 :: verify_dynamic_vlan :: FAILURE (Device has 0 configured, we expect at least 1)
leaf01 :: verify_dynamic_vlan :: SUCCESS
leaf02 :: verify_dynamic_vlan :: SUCCESS
leaf03 :: verify_dynamic_vlan :: SUCCESS
leaf04 :: verify_dynamic_vlan :: SUCCESS
```

!!! warning "Install your python package"
    Anta uses Python path to access to your test. So it is critical to have your tests library installed correctly.