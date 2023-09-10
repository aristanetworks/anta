# Copyright (c) 2023 Arista Networks, Inc.
# Use of this source code is governed by the Apache License 2.0
# that can be found in the LICENSE file.
"""decorators for tests."""
from __future__ import annotations

from functools import wraps
from typing import TYPE_CHECKING, Any, Callable, Optional, TypeVar, cast

from anta.models import AntaCommand, AntaTest, logger
from anta.tools.misc import exc_to_str

if TYPE_CHECKING:
    from anta.result_manager.models import TestResult

# TODO - should probably use mypy Awaitable in some places rather than this everywhere - @gmuloc
F = TypeVar("F", bound=Callable[..., Any])


def deprecated_test(new_tests: Optional[list[str]] = None) -> Callable[[F], F]:
    """
    Return a decorator to log a message of WARNING severity when a test is deprecated.

    Args:
        new_tests (Optional[list[str]]): A list of new test classes that should replace the deprecated test.

    Returns:
        Callable[[F], F]: A decorator that can be used to wrap test functions.
    """

    def decorator(function: F) -> F:
        """
        Actual decorator that logs the message.

        Args:
            function (F): The test function to be decorated.

        Returns:
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


def skip_on_platforms(platforms: list[str]) -> Callable[[F], F]:
    """
    Return a decorator to skip a test based on the device's hardware model.

    This decorator factory generates a decorator that will check the hardware model of the device
    the test is run on. If the model is in the list of platforms specified, the test will be skipped.

    Args:
        platforms (list[str]): List of hardware models on which the test should be skipped.

    Returns:
        Callable[[F], F]: A decorator that can be used to wrap test functions.
    """

    def decorator(function: F) -> F:
        """
        Actual decorator that either runs the test or skips it based on the device's hardware model.

        Args:
            function (F): The test function to be decorated.

        Returns:
            F: The decorated function.
        """

        @wraps(function)
        async def wrapper(*args: Any, **kwargs: Any) -> TestResult:
            """
            Check the device's hardware model and conditionally run or skip the test.

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


def check_bgp_family_enable(family: str) -> Callable[[F], F]:
    """
    Return a decorator to conditionally skip a test based on BGP address family availability.

    This is a decorator factory that generates a decorator that will skip the test
    if there's no BGP configuration or peer for the given address family.

    !!! warning
        This decorator is deprecated and will eventually be removed in a future major release of ANTA.
        New BGP tests have been created to address this. For more details, please refer to the BGP tests documentation.

    Args:
        family (str): BGP address family to check. Accepted values are 'ipv4', 'ipv6', 'evpn', 'rtc'.

    Returns:
        Callable[[F], F]: A decorator that can be used to wrap test functions.
    """

    def decorator(function: F) -> F:
        """
        Actual decorator that either runs the test or skips it based on BGP address family state.

        Args:
            function (F): The test function to be decorated.

        Returns:
            F: The decorated function.
        """

        @wraps(function)
        async def wrapper(*args: Any, **kwargs: Any) -> TestResult:  # pylint: disable=too-many-branches
            """
            Check BGP address family and conditionally run or skip the test.

            This wrapper checks the BGP address family state on the device.
            If the required BGP configuration or peer is not found, the test is either skipped.
            """
            anta_test = args[0]

            if anta_test.result.result != "unset":
                AntaTest.update_progress()
                return anta_test.result

            if family == "ipv4":
                command = AntaCommand(command="show bgp ipv4 unicast summary vrf all")
            elif family == "ipv6":
                command = AntaCommand(command="show bgp ipv6 unicast summary vrf all")
            elif family == "evpn":
                command = AntaCommand(command="show bgp evpn summary")
            elif family == "rtc":
                command = AntaCommand(command="show bgp rt-membership summary")
            else:
                anta_test.result.is_error(message=f"Wrong address family for BGP decorator: {family}")
                return anta_test.result

            await anta_test.device.collect(command=command)

            if not command.collected and command.failed is not None:
                anta_test.result.is_error(message=f"{command.command}: {exc_to_str(command.failed)}")
                return anta_test.result
            if "vrfs" not in command.json_output:
                anta_test.result.is_skipped(f"No BGP configuration for address family {family} on this device")
                AntaTest.update_progress()
                return anta_test.result
            if len(bgp_vrfs := command.json_output["vrfs"]) == 0 or len(bgp_vrfs["default"]["peers"]) == 0:
                # No VRF
                anta_test.result.is_skipped(f"No BGP peer for address family {family} on this device")
                AntaTest.update_progress()
                return anta_test.result

            return await function(*args, **kwargs)

        return cast(F, wrapper)

    return decorator
