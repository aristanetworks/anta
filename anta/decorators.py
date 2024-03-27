# Copyright (c) 2023-2024 Arista Networks, Inc.
# Use of this source code is governed by the Apache License 2.0
# that can be found in the LICENSE file.
"""decorators for tests."""

from __future__ import annotations

from functools import wraps
from typing import TYPE_CHECKING, Any, Callable, Literal, TypeVar, cast

from anta.models import AntaTest, logger
from anta.platform_utils import find_series_by_platform

if TYPE_CHECKING:
    from anta.result_manager.models import TestResult

# TODO: should probably use mypy Awaitable in some places rather than this everywhere - @gmuloc
F = TypeVar("F", bound=Callable[..., Any])


def deprecated_test(new_tests: list[str] | None = None) -> Callable[[F], F]:
    """Return a decorator to log a message of WARNING severity when a test is deprecated.

    Args:
    ----
        new_tests (Optional[list[str]]): A list of new test classes that should replace the deprecated test.

    Returns
    -------
        Callable[[F], F]: A decorator that can be used to wrap test functions.

    """

    def decorator(function: F) -> F:
        """Actual decorator that logs the message.

        Args:
        ----
            function (F): The test function to be decorated.

        Returns
        -------
            F: The decorated function.

        """

        @wraps(function)
        async def wrapper(*args: Any, **kwargs: Any) -> Any:
            anta_test = args[0]
            if new_tests:
                new_test_names = ", ".join(new_tests)
                logger.warning(f"{anta_test.name} test is deprecated. Consider using the following new tests: {new_test_names}.")
            else:
                logger.warning(f"{anta_test.name} test is deprecated.")
            return await function(*args, **kwargs)

        return cast(F, wrapper)

    return decorator


def platform_series_filter(series: list[str], action: Literal["run", "skip"]) -> Callable[[F], F]:
    """Return a decorator to run a test based on the device's hardware model.

    This decorator factory generates a decorator that will check the hardware model of the device
    the test is run on. If the model is part of the provided platform series, the test will be run.

    Args:
    ----
        series (list[str]): List of platform series on which the test should be run.

    Returns
    -------
        Callable[[F], F]: A decorator that can be used to wrap test functions.

    Examples
    --------
    The following test will only run if the device's hardware model is part of the 7800R3, 7500R3, 7500R, or 7280R3 series, e.g. DCS-7280SR3-48YC8.

    ```python
    @run_on_platform_series([["7800R3", "7500R3", "7500R", "7280R3"])
    @AntaTest.anta_test
    def test(self) -> None:
        pass
    """
    if action not in ["run", "skip"]:
        msg = f"Improper way of using the platform series filter decorator function. Action must be 'run' or 'skip', not '{action}'."
        raise ValueError(msg)

    def decorator(function: F) -> F:
        """Actual decorator that either runs the test or skips it based on the device's hardware model.

        Args:
        ----
            function (F): The test function to be decorated.

        Returns
        -------
            F: The decorated function.

        """

        @wraps(function)
        async def wrapper(*args: Any, **kwargs: Any) -> Any:
            """Check the device's hardware model and conditionally run or skip the test.

            This wrapper inspects the hardware model of the device the test is run on.
            If the model is NOT in the list of specified platform series, the test is skipped.
            """
            anta_test = args[0]

            if anta_test.result.result != "unset":
                AntaTest.update_progress()
                return anta_test.result

            platform_series = find_series_by_platform(anta_test.device.hw_model)

            if (action == "run" and platform_series not in series) or (action == "skip" and platform_series in series):
                anta_test.result.is_skipped(f"{anta_test.__class__.__name__} test is not supported on {anta_test.device.hw_model}.")
                AntaTest.update_progress()
                return anta_test.result

            return await function(*args, **kwargs)

        return cast(F, wrapper)

    return decorator


def platform_filter(platforms: list[str], action: Literal["run", "skip"]) -> Callable[[F], F]:
    """Return a decorator to skip a test based on the device's hardware model.

    This decorator factory generates a decorator that will check the hardware model of the device
    the test is run on. If the model is in the list of platforms specified, the test will be skipped.

    Args:
    ----
        platforms (list[str]): List of hardware models on which the test should be skipped.

    Returns
    -------
        Callable[[F], F]: A decorator that can be used to wrap test functions.

    """
    if action not in ["run", "skip"]:
        msg = f"Improper way of using the platform filter decorator function. Action must be 'run' or 'skip', not '{action}'."
        raise ValueError(msg)

    def decorator(function: F) -> F:
        """Actual decorator that either runs the test or skips it based on the device's hardware model.

        Args:
        ----
            function (F): The test function to be decorated.

        Returns
        -------
            F: The decorated function.

        """

        @wraps(function)
        async def wrapper(*args: Any, **kwargs: Any) -> TestResult:
            """Check the device's hardware model and conditionally run or skip the test.

            This wrapper inspects the hardware model of the device the test is run on.
            If the model is in the list of specified platforms, the test is skipped.
            """
            anta_test = args[0]

            if anta_test.result.result != "unset":
                AntaTest.update_progress()
                return anta_test.result

            platform = anta_test.device.hw_model

            if (action == "run" and platform not in platforms) or (action == "skip" and platform in platforms):
                anta_test.result.is_skipped(f"{anta_test.__class__.__name__} test is not supported on {anta_test.device.hw_model}.")
                AntaTest.update_progress()
                return anta_test.result

            return await function(*args, **kwargs)

        return cast(F, wrapper)

    return decorator
