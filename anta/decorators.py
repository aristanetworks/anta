"""
decorators for tests
"""
import socket
from functools import wraps
from typing import Any, Callable, Dict, List

from jsonrpclib import jsonrpc

from anta.result_manager.models import TestResult


def skip_on_platforms(platforms: List[str]) -> Callable[..., Callable[..., TestResult]]:
    """
    Decorator factory to skip a test on a list of platforms

    Args:
    * platforms (List[str]): the list of platforms on which the decorated test should be skipped.

    """

    def decorator(function: Callable[..., TestResult]) -> Callable[..., TestResult]:
        """
        Decorator to skip a test ona list of platform
        * func (Callable): the test to be decorated
        """

        @wraps(function)
        def wrapper(*args: List[Any], **kwargs: Dict[str, Any]) -> TestResult:
            """
            wrapper for func
            """
            device = args[0]
            if device.hw_model in platforms:  # type:ignore
                result = TestResult(name=device.name, test=function.__name__)  # type: ignore
                result.is_skipped(
                    f"{wrapper.__name__} test is not supported on {device.hw_model}."  # type: ignore
                )
                return result

            return function(*args, **kwargs)

        return wrapper

    return decorator


def check_bgp_family_enable(family: str) -> Callable[..., Callable[..., TestResult]]:
    """
    Decorator factory to skip a test if BGP is enabled

    Args:
    * family (str): BGP family to check. Can be ipv4 / ipv6 / evpn / rtc

    """

    def decorator(function: Callable[..., TestResult]) -> Callable[..., TestResult]:
        """
        Decorator to skip a test ona list of platform
        * func (Callable): the test to be decorated
        """

        @wraps(function)
        def wrapper(*args: List[Any], **kwargs: Dict[str, Any]) -> TestResult:
            """
            wrapper for func
            """
            device = args[0]
            eapi_command = "show bgp ipv4 unicast summary vrf all"
            eapi_command = (
                "show bgp ipv6 unicast summary vrf all"
                if family == "ipv6"
                else eapi_command
            )
            eapi_command = "show bgp evpn summary" if family == "evpn" else eapi_command
            eapi_command = (
                "show bgp rt-membership summary" if family == "rtc" else eapi_command
            )

            result = TestResult(name=str(device.name), test=function.__name__)  # type: ignore
            try:
                response = device.session.runCmds(  # type: ignore
                    1, [eapi_command], "json"
                )  # type: ignore

                if "vrfs" not in response[0].keys():
                    result.is_skipped(
                        # type: ignore
                        f"no BGP configuration for {family} on this device"
                    )
                    return result
                bgp_vrfs = response[0]["vrfs"]
                if (
                    len(bgp_vrfs) == 0
                    or len(response[0]["vrfs"]["default"]["peers"]) == 0
                ):
                    # No VRF
                    result.is_skipped(
                        # type: ignore
                        f"no {family} peer on this device"
                    )
                    return result
            except (jsonrpc.AppError, KeyError, socket.timeout) as e:
                result.is_error(str(e))
                return result

            return function(*args, **kwargs)

        return wrapper

    return decorator
