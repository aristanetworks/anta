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
    """Return a decorator factory to skip a test on a list of platforms.

    Args:
    ----
      platforms (List[str]): the list of platforms on which the decorated test should be skipped.

    """

    def decorator(function: F) -> F:
        """Implement the decorator to skip a test ona list of platform.

        Args:
        ----
            function (F): the test to be decorated.
        """

        @wraps(function)
        async def wrapper(*args: Any, **kwargs: Any) -> TestResult:
            """Implement the wrapper for func."""
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
    """Return a decorator factory to skip a test if BGP is enabled.

    Args:
    ----
        family (str): BGP family to check. Can be ipv4 / ipv6 / evpn / rtc

    """

    def decorator(function: F) -> F:
        """Implement the decorator to skip a test if an address family is not configured.

        Args:
        ----
            function (F): the test to be decorated.
        """

        @wraps(function)
        async def wrapper(*args: Any, **kwargs: Any) -> TestResult:
            """Implement the wrapper for func."""
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
                anta_test.result.is_error(f"Wrong address family for bgp decorator: {family}")
                return anta_test.result

            await anta_test.device.collect(command=command)

            if not command.collected and command.failed is not None:
                anta_test.result.is_error(f"{command.command}: {exc_to_str(command.failed)}")
                return anta_test.result
            if "vrfs" not in command.json_output:
                anta_test.result.is_skipped(f"no BGP configuration for {family} on this device")
                AntaTest.update_progress()
                return anta_test.result
            if len(bgp_vrfs := command.json_output["vrfs"]) == 0 or len(bgp_vrfs["default"]["peers"]) == 0:
                # No VRF
                anta_test.result.is_skipped(f"no {family} peer on this device")
                AntaTest.update_progress()
                return anta_test.result

            return await function(*args, **kwargs)

        return cast(F, wrapper)

    return decorator
