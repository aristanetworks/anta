"""
ANTA runner function
"""

import asyncio
import itertools
import logging
from typing import Any, Callable, Dict, List, Optional, Tuple

from anta import __DEBUG__
from anta.inventory import AntaInventory
from anta.models import AntaTest
from anta.result_manager import ResultManager
from anta.result_manager.models import TestResult
from anta.tools.misc import exc_to_str

logger = logging.getLogger(__name__)

# Key from YAML file tranfered to AntaTemplate of the test.
TEST_TPL_PARAMS = "template_params"


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
        inventory (AntaInventory): Device inventory object.
        tests (List[...]): Test catalog. Output of anta.loader.parse_catalog().

    Example:
        anta.tests.routing.bgp:
        - VerifyBGPIPv4UnicastCount:
            number: 3
            template_params:
                - vrf: default

    Returns:
        any: List of results.
    """
    # Accept 6 arguments here
    # pylint: disable=R0913

    await inventory.connect_inventory()

    # asyncio.gather takes an iterator of the function to run concurrently.
    # we get the cross product of the devices and tests to build that iterator.

    coros = []
    for device, test in itertools.product(inventory.get_inventory(established_only=established_only, tags=tags).values(), tests):
        test_params = {k: v for k, v in test[1].items() if k != TEST_TPL_PARAMS}
        template_params = test[1].get(TEST_TPL_PARAMS)
        try:
            # Instantiate AntaTest object
            test_instance = test[0](device=device, template_params=template_params)
            coros.append(test_instance.test(eos_data=None, **test_params))
        except Exception as e:  # pylint: disable=broad-exception-caught
            message = "Error when creating ANTA tests"
            if __DEBUG__:
                logger.exception(message)
            else:
                logger.error(f"{message}: {exc_to_str(e)}")

    if AntaTest.progress is not None:
        AntaTest.nrfu_task = AntaTest.progress.add_task("Running NRFU Tests...", total=len(coros))

    logger.info("Running ANTA tests...")
    res = await asyncio.gather(*coros, return_exceptions=True)
    for r in res:
        if isinstance(r, Exception):
            message = "Error in main ANTA Runner"
            if __DEBUG__:
                logger.exception(message, exc_info=r)
            else:
                logger.error(f"{message}: {exc_to_str(r)}")
            res.remove(r)
    manager.add_test_results(res)
