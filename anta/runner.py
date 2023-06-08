"""
ANTA runner function
"""

import asyncio
import itertools
import logging
from typing import Any, Callable, Dict, List, Optional, Tuple

from anta.inventory import AntaInventory
from anta.result_manager import ResultManager
from anta.result_manager.models import TestResult

logger = logging.getLogger(__name__)

# Key from YAML file tranfered to AntaTestTemplate of the test.
TEST_TPL_PARAM = "tpl_options"


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
        anta.tests.aaa:
          - VerifyAAAMethods:
              method: login
              tpl_options:
                - stage: authentication
                - stage: authorization

    Returns:
        any: List of results.
    """
    await inventory.connect_inventory()

    # asyncio.gather takes an iterator of the function to run concurrently.
    # we get the cross product of the devices and tests to build that iterator.

    res = await asyncio.gather(
        *(
            test[0](device=device,
                    template_params=test[1].get(TEST_TPL_PARAM, [])
                    ).test(
                eos_data=None,
                **{k: v for k, v in test[1].items() if k != TEST_TPL_PARAM}
            )
            for device, test in itertools.product(
                inventory.get_inventory(established_only=established_only, tags=tags),
                tests
            )
        ),
        return_exceptions=True,
    )
    for r in res:
        if isinstance(r, Exception):
            logger.error(f"Error when running tests: {r.__class__.__name__}: {r}")
    logger.info(f"List of test result is: {res}")
    manager.add_test_results(res)
