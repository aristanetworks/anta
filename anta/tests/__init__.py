#!/usr/bin/python
# coding: utf-8 -*-
"""
Test decorator from which tests can derive
"""

import logging
from functools import wraps
from typing import Any, Callable, List, Dict

from anta.inventory.models import InventoryDevice
from anta.result_manager.models import TestResult

logger = logging.getLogger(__name__)


def anta_test(function: Callable[..., TestResult]) -> Callable[..., TestResult]:
    """
    Decorator to generate the structure for a test
    * func (Callable): the test to be decorated
    """

    @wraps(function)
    def wrapper(
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
        result = TestResult(host=str(device.host), test=function.__name__)  # type: ignore
        logger.debug(f"Start {function.__name__} test for host {device.host}")

        try:
            return function(device, result, *args, **kwargs)

        # In this case we want to catch all exceptions
        except Exception as e:  # pylint: disable=broad-except
            logger.error(
                f"exception raised for {function.__name__} -  {device.host}: {str(e)}"
            )
            result.is_error(str(e))
            return result

    return wrapper
