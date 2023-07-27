"""
ANTA runner function
"""

import asyncio
import itertools
import logging
from typing import Any, Callable, Dict, List, Optional, Tuple

from anta.inventory import AntaInventory
from anta.models import AntaTest
from anta.result_manager import ResultManager
from anta.result_manager.models import TestResult
from anta.tools.misc import anta_log_exception

logger = logging.getLogger(__name__)

# Keys from the ANTA test catalog file tranferred to kwargs for AntaTest initialization.
TEST_CATALOG_PARAMS = [
    "result_overwrite",
    "template_params",
]


async def main(
    manager: ResultManager,
    inventory: AntaInventory,
    tests: List[Tuple[Callable[..., TestResult], Dict[Any, Any]]],
    tags: Optional[List[str]] = None,
    established_only: bool = True,
) -> None:
    """
    Main coroutine to run ANTA.
    Use this as an entrypoint to the test framwork in your script.

    Args:
        manager (ResultManager): ResultManager object to populate with the test results.
        inventory (AntaInventory): AntaInventory object that includes the device(s).
        tests (List[...]): ANTA test catalog. Output of anta.loader.parse_catalog().
        tags (Optional[List[str]]): List of tags to filter devices from the inventory. Defaults to None.
        established_only (bool): Include only established device(s). Defaults to True.

    Example:
        anta.tests.routing.bgp:
        - VerifyBGPIPv4UnicastCount:
            number: 3
            template_params:
                - vrf: default

        anta.tests.connectivity:
        - VerifyReachability:
            result_overwrite:
              categories:
                - "Overwritten category 1"
              description: "Test with overwritten description"
              custom_field: "Test run by John Doe"
            template_params:
              - src: Loopback0
                dst: 10.1.0.1

    Returns:
        any: ResultManager object gets updated with the test results.
    """
    # Accept 6 arguments here
    # pylint: disable=R0913

    await inventory.connect_inventory()

    # asyncio.gather takes an iterator of the function to run concurrently.
    # we get the cross product of the devices and tests to build that iterator.

    coros = []
    for device, test in itertools.product(inventory.get_inventory(established_only=established_only, tags=tags).values(), tests):
        kwargs = {k: v for k, v in test[1].items() if k in TEST_CATALOG_PARAMS}

        if "result_overwrite" in kwargs:
            result_overwrite = kwargs.pop("result_overwrite")
            result_overwrite = {"result_" + k: v for k, v in result_overwrite.items()}
            kwargs.update(result_overwrite)

        test_params = {k: v for k, v in test[1].items() if k not in TEST_CATALOG_PARAMS}

        try:
            # Instantiate AntaTest object
            test_instance = test[0](device=device, **kwargs)
            coros.append(test_instance.test(eos_data=None, **test_params))
        except Exception as e:  # pylint: disable=broad-exception-caught
            message = "Error when creating ANTA tests"
            anta_log_exception(e, message, logger)

    if AntaTest.progress is not None:
        AntaTest.nrfu_task = AntaTest.progress.add_task("Running NRFU Tests...", total=len(coros))

    logger.info("Running ANTA tests...")
    res = await asyncio.gather(*coros, return_exceptions=True)
    for r in res:
        if isinstance(r, Exception):
            message = "Error in main ANTA Runner"
            anta_log_exception(r, message, logger)
            res.remove(r)
    manager.add_test_results(res)
