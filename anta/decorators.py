# Copyright (c) 2023 Arista Networks, Inc.
# Use of this source code is governed by the Apache License 2.0
# that can be found in the LICENSE file.
"""decorators for tests."""
from __future__ import annotations

from functools import wraps
from typing import TYPE_CHECKING, Any, Callable, TypeVar, cast

from anta.models import AntaCommand, AntaTest
from anta.tools.misc import exc_to_str

if TYPE_CHECKING:
    from anta.result_manager.models import TestResult

# TODO - should probably use mypy Awaitable in some places rather than this everywhere - @gmuloc
F = TypeVar("F", bound=Callable[..., Any])


def skip_on_platforms(platforms: list[str]) -> Callable[[F], F]:
    """
    Return a decorator to conditionally skip or fail a test based on the device's hardware model.

    This decorator factory generates a decorator that will check the hardware model of the device
    the test is run on. If the model is in the list of platforms specified, the test will be skipped or failed.

    If `strict` is set to True in the test's input definition, the test status will be set to "failure"
    instead of "skipped" when the device's hardware model is in the list.

    Args:
        platforms (list[str]): List of hardware models on which the test should be skipped or failed.

    Returns:
        Callable[[F], F]: A decorator that can be used to wrap test functions.
    """

    def decorator(function: F) -> F:
        """
        Actual decorator that either runs the test or skips/fails it based on the device's hardware model.

        Args:
            function (F): The test function to be decorated.

        Returns:
            F: The decorated function.
        """

        @wraps(function)
        async def wrapper(*args: Any, **kwargs: Any) -> TestResult:
            """
            Check the device's hardware model and conditionally run or skip/fail the test.

            This wrapper inspects the hardware model of the device the test is run on.
            If the model is in the list of specified platforms, the test is either skipped or failed.
            """
            anta_test = args[0]

            # Set the strict variable
            strict = anta_test.inputs.strict if hasattr(anta_test, "inputs") and hasattr(anta_test.inputs, "strict") else False

            if anta_test.result.result != "unset":
                AntaTest.update_progress()
                return anta_test.result

            if anta_test.device.hw_model in platforms:
                if strict:
                    anta_test.result.is_failure(f"{anta_test.__class__.__name__} test is not supported on {anta_test.device.hw_model}.")
                else:
                    anta_test.result.is_skipped(f"{anta_test.__class__.__name__} test is not supported on {anta_test.device.hw_model}.")
                AntaTest.update_progress()
                return anta_test.result

            return await function(*args, **kwargs)

        return cast(F, wrapper)

    return decorator


def check_bgp_family_enable(family: str) -> Callable[[F], F]:
    """
    Return a decorator to conditionally skip or fail a test based on BGP address family availability.

    This is a decorator factory that generates a decorator that will skip or fail the test
    if there's no BGP configuration or peer for the given address family.

    If `strict` is set to True in the catalog test input definition,
    the test status will be set to "failure" instead of "skipped" when conditions are not met.

    Args:
        family (str): BGP address family to check. Accepted values are 'ipv4', 'ipv6', 'evpn', 'rtc'.

    Returns:
        Callable[[F], F]: A decorator that can be used to wrap test functions.
    """

    def decorator(function: F) -> F:
        """
        Actual decorator that either runs the test or skips/fails it based on BGP address family state.

        Args:
            function (F): The test function to be decorated.

        Returns:
            F: The decorated function.
        """

        @wraps(function)
        async def wrapper(*args: Any, **kwargs: Any) -> TestResult:  # pylint: disable=too-many-branches
            """
            Check BGP address family and conditionally run or skip/fail the test.

            This wrapper checks the BGP address family state on the device.
            If the required BGP configuration or peer is not found, the test is either skipped or failed.
            """
            anta_test = args[0]

            # Set the strict variable
            strict = anta_test.inputs.strict if hasattr(anta_test, "inputs") and hasattr(anta_test.inputs, "strict") else False

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
                if strict:
                    anta_test.result.is_failure(f"No BGP configuration for address family {family} on this device")
                else:
                    anta_test.result.is_skipped(f"No BGP configuration for address family {family} on this device")
                AntaTest.update_progress()
                return anta_test.result
            if len(bgp_vrfs := command.json_output["vrfs"]) == 0 or len(bgp_vrfs["default"]["peers"]) == 0:
                # No VRF
                if strict:
                    anta_test.result.is_failure(f"No BGP peer for address family {family} on this device")
                else:
                    anta_test.result.is_skipped(f"No BGP peer for address family {family} on this device")
                AntaTest.update_progress()
                return anta_test.result

            return await function(*args, **kwargs)

        return cast(F, wrapper)

    return decorator
