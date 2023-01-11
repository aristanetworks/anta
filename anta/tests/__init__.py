"""
Test decorator from which tests can derive
"""

import logging
import traceback
from functools import wraps
from typing import Any, Callable, Coroutine, Dict, List

from aioeapi import EapiCommandError
from httpx import ConnectError, HTTPError

from anta.inventory.models import InventoryDevice
from anta.result_manager.models import TestResult

logger = logging.getLogger(__name__)


def anta_test(function: Callable[..., Coroutine[Any, Any, TestResult]]) -> Callable[..., Coroutine[Any, Any, Coroutine[Any, Any, TestResult]]]:
    """
    Decorator to generate the structure for a test
    * func (Callable): the test to be decorated
    """

    @wraps(function)
    async def wrapper(
        device: InventoryDevice, *args: List[Any], **kwargs: Dict[str, Any]
    ) -> TestResult:
        """
        wrapper for func
        Args:
            TODO

        Returns:
            TestResult instance with
            * result = "unset" if the test has not been executed
            * result = "success" if the MLAG status is OK
            * result = "failure" otherwise.
            * result = "error" if any exception is caught
        """
        result = TestResult(name=device.name, test=function.__name__)
        logger.debug(f"Start {function.__name__} check for host {device.host}")

        try:
            return await function(device, result, *args, **kwargs)
        except EapiCommandError as e:
            logger.error(f"Command failed on {device.name}: {e.errmsg}")
            result.is_error(f"{type(e).__name__}{'' if not str(e) else f' ({str(e)})'}")
        except (HTTPError, ConnectError) as e:
            logger.warning(f"Cannot connect to device {device.name}: {type(e).__name__}{'' if not str(e) else f' ({str(e)})'}")
            result.is_error(f"{type(e).__name__}{'' if not str(e) else f' ({str(e)})'}")
        # In this case we want to catch all exceptions
        except Exception as e:  # pylint: disable=broad-except
            logger.error(
                f"Exception raised for test {function.__name__} (on device {device.host}) - {type(e).__name__}{'' if not str(e) else f' ({str(e)})'}"
            )
            logger.debug(traceback.format_exc())
            result.is_error(f"{type(e).__name__}{'' if not str(e) else f' ({str(e)})'}")
        return result

    return wrapper
