# Copyright (c) 2023-2024 Arista Networks, Inc.
# Use of this source code is governed by the Apache License 2.0
# that can be found in the LICENSE file.
"""decorators for tests."""

from __future__ import annotations

from functools import wraps
from typing import TYPE_CHECKING, Any, Callable, TypeVar, cast

from anta.models import AntaTest, logger

if TYPE_CHECKING:
    from anta.result_manager.models import TestResult

# TODO: should probably use mypy Awaitable in some places rather than this everywhere - @gmuloc
F = TypeVar("F", bound=Callable[..., Any])


def deprecated_test(new_tests: list[str] | None = None) -> Callable[[F], F]:
    """Return a decorator to log a message of WARNING severity when a test is deprecated.

    Parameters
    ----------
    new_tests
        A list of new test classes that should replace the deprecated test.

    Returns
    -------
    Callable[[F], F]
        A decorator that can be used to wrap test functions.

    """

    def decorator(function: F) -> F:
        """Actual decorator that logs the message.

        Parameters
        ----------
        function
            The test function to be decorated.

        Returns
        -------
        F
            The decorated function.

        """

        @wraps(function)
        async def wrapper(*args: Any, **kwargs: Any) -> Any:
            anta_test = args[0]
            if new_tests:
                new_test_names = ", ".join(new_tests)
                logger.warning("%s test is deprecated. Consider using the following new tests: %s.", anta_test.name, new_test_names)
            else:
                logger.warning("%s test is deprecated.", anta_test.name)
            return await function(*args, **kwargs)

        return cast(F, wrapper)

    return decorator


def skip_on_platforms(platforms: list[str]) -> Callable[[F], F]:
    """Return a decorator to skip a test based on the device's hardware model.

    This decorator factory generates a decorator that will check the hardware model of the device
    the test is run on. If the model is in the list of platforms specified, the test will be skipped.

    Parameters
    ----------
    platforms
        List of hardware models on which the test should be skipped.

    Returns
    -------
    Callable[[F], F]
        A decorator that can be used to wrap test functions.

    """

    def decorator(function: F) -> F:
        """Actual decorator that either runs the test or skips it based on the device's hardware model.

        Parameters
        ----------
        function
            The test function to be decorated.

        Returns
        -------
        F
            The decorated function.

        """

        @wraps(function)
        async def wrapper(*args: Any, **kwargs: Any) -> TestResult:
            """Check the device's hardware model and conditionally run or skip the test.

            This wrapper inspects the hardware model of the device the test is run on.
            If the model is in the list of specified platforms, the test is either skipped.
            """
            anta_test = args[0]

            if anta_test.result.result != "unset":
                AntaTest.update_progress()
                return anta_test.result

            if anta_test.device.hw_model in platforms:
                anta_test.result.is_skipped(f"{anta_test.__class__.__name__} test is not supported on {anta_test.device.hw_model}.")
                AntaTest.update_progress()
                return anta_test.result

            return await function(*args, **kwargs)

        return cast(F, wrapper)

    return decorator
