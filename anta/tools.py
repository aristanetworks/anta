# Copyright (c) 2023-2025 Arista Networks, Inc.
# Use of this source code is governed by the Apache License 2.0
# that can be found in the LICENSE file.
"""Common functions used in ANTA tests."""

from __future__ import annotations

import cProfile
import os
import pstats
import re
from functools import wraps
from time import perf_counter
from typing import TYPE_CHECKING, Any, Callable, TypeVar, cast

from anta.constants import ACRONYM_CATEGORIES
from anta.custom_types import REGEXP_PATH_MARKERS
from anta.logger import format_td

if TYPE_CHECKING:
    import sys
    from logging import Logger
    from types import TracebackType

    if sys.version_info >= (3, 11):
        from typing import Self
    else:
        from typing_extensions import Self

F = TypeVar("F", bound=Callable[..., Any])


def get_failed_logs(expected_output: dict[Any, Any], actual_output: dict[Any, Any]) -> str:
    """Get the failed log for a test.

    Returns the failed log or an empty string if there is no difference between the expected and actual output.

    Parameters
    ----------
    expected_output
        Expected output of a test.
    actual_output
        Actual output of a test

    Returns
    -------
    str
        Failed log of a test.

    """
    failed_logs = []

    for element, expected_data in expected_output.items():
        actual_data = actual_output.get(element)

        if actual_data == expected_data:
            continue
        if actual_data is None:
            failed_logs.append(f"\nExpected `{expected_data}` as the {element}, but it was not found in the actual output.")
            continue
        # actual_data != expected_data: and actual_data is not None
        failed_logs.append(f"\nExpected `{expected_data}` as the {element}, but found `{actual_data}` instead.")

    return "".join(failed_logs)


def custom_division(numerator: float, denominator: float) -> int | float:
    """Get the custom division of numbers.

    Custom division that returns an integer if the result is an integer, otherwise a float.

    Parameters
    ----------
    numerator
        The numerator.
    denominator
        The denominator.

    Returns
    -------
    Union[int, float]
        The result of the division.
    """
    result = numerator / denominator
    return int(result) if result.is_integer() else result


def get_dict_superset(
    list_of_dicts: list[dict[Any, Any]],
    input_dict: dict[Any, Any],
    default: Any | None = None,
    var_name: str | None = None,
    custom_error_msg: str | None = None,
    *,
    required: bool = False,
) -> Any:
    """Get the first dictionary from a list of dictionaries that is a superset of the input dict.

    Returns the supplied default value or None if there is no match and "required" is False.

    Will return the first matching item if there are multiple matching items.

    Parameters
    ----------
    list_of_dicts: list(dict)
        List of Dictionaries to get list items from
    input_dict : dict
        Dictionary to check subset with a list of dict
    default: any
        Default value returned if the key and value are not found
    required: bool
        Fail if there is no match
    var_name : str
        String used for raising an exception with the full variable name
    custom_error_msg : str
        Custom error message to raise when required is True and the value is not found

    Returns
    -------
    any
        Dict or default value

    Raises
    ------
    ValueError
        If the keys and values are not found and "required" == True

    """
    if not isinstance(list_of_dicts, list) or not list_of_dicts or not isinstance(input_dict, dict) or not input_dict:
        if required:
            error_msg = custom_error_msg or f"{var_name} not found in the provided list."
            raise ValueError(error_msg)
        return default

    for list_item in list_of_dicts:
        if isinstance(list_item, dict) and input_dict.items() <= list_item.items():
            return list_item

    if required:
        error_msg = custom_error_msg or f"{var_name} not found in the provided list."
        raise ValueError(error_msg)

    return default


def get_value(
    dictionary: dict[Any, Any],
    key: str,
    default: Any | None = None,
    org_key: str | None = None,
    separator: str = ".",
    *,
    required: bool = False,
) -> Any:
    """Get a value from a dictionary or nested dictionaries.

    Key supports dot-notation like "foo.bar" to do deeper lookups.

    Returns the supplied default value or None if the key is not found and required is False.

    Parameters
    ----------
    dictionary : dict
        Dictionary to get key from
    key : str
        Dictionary Key - supporting dot-notation for nested dictionaries
    default : any
        Default value returned if the key is not found
    required : bool
        Fail if the key is not found
    org_key : str
        Internal variable used for raising exception with the full key name even when called recursively
    separator: str
        String to use as the separator parameter in the split function. Useful in cases when the key
        can contain variables with "." inside (e.g. hostnames)

    Returns
    -------
    any
        Value or default value

    Raises
    ------
    ValueError
        If the key is not found and required == True.

    """
    if org_key is None:
        org_key = key
    keys = key.split(separator)
    value = dictionary.get(keys[0])
    if value is None:
        if required:
            raise ValueError(org_key)
        return default

    if len(keys) > 1:
        return get_value(value, separator.join(keys[1:]), default=default, required=required, org_key=org_key, separator=separator)
    return value


def get_item(
    list_of_dicts: list[dict[Any, Any]],
    key: Any,
    value: Any,
    default: Any | None = None,
    var_name: str | None = None,
    custom_error_msg: str | None = None,
    *,
    required: bool = False,
    case_sensitive: bool = False,
) -> Any:
    """Get one dictionary from a list of dictionaries by matching the given key and value.

    Returns the supplied default value or None if there is no match and "required" is False.

    Will return the first matching item if there are multiple matching items.

    Parameters
    ----------
    list_of_dicts : list(dict)
        List of Dictionaries to get list item from
    key : any
        Dictionary Key to match on
    value : any
        Value that must match
    default : any
        Default value returned if the key and value is not found
    required : bool
        Fail if there is no match
    case_sensitive : bool
        If the search value is a string, the comparison will ignore case by default
    var_name : str
        String used for raising exception with the full variable name
    custom_error_msg : str
        Custom error message to raise when required is True and the value is not found

    Returns
    -------
    any
        Dict or default value

    Raises
    ------
    ValueError
        If the key and value is not found and "required" == True

    """
    if var_name is None:
        var_name = key

    if (not isinstance(list_of_dicts, list)) or list_of_dicts == [] or value is None or key is None:
        if required is True:
            raise ValueError(custom_error_msg or var_name)
        return default

    for list_item in list_of_dicts:
        if not isinstance(list_item, dict):
            # List item is not a dict as required. Skip this item
            continue

        item_value = list_item.get(key)

        # Perform case-insensitive comparison if value and item_value are strings and case_sensitive is False
        if not case_sensitive and isinstance(value, str) and isinstance(item_value, str):
            if item_value.casefold() == value.casefold():
                return list_item
        elif item_value == value:
            # Match. Return this item
            return list_item

    # No Match
    if required is True:
        raise ValueError(custom_error_msg or var_name)
    return default


class Catchtime:
    """A class working as a context to capture time differences."""

    start: float
    raw_time: float
    time: str

    def __init__(self, logger: Logger | None = None, message: str | None = None) -> None:
        self.logger = logger
        self.message = message

    def __enter__(self) -> Self:
        """__enter__ method."""
        self.start = perf_counter()
        if self.logger and self.message:
            self.logger.debug("%s ...", self.message)
        return self

    def __exit__(self, exc_type: type[BaseException] | None, exc_val: BaseException | None, exc_tb: TracebackType | None) -> None:
        """__exit__ method."""
        self.raw_time = perf_counter() - self.start
        self.time = format_td(self.raw_time, 3)
        if self.logger and self.message:
            self.logger.debug("%s completed in: %s.", self.message, self.time)


def cprofile(sort_by: str = "cumtime") -> Callable[[F], F]:
    """Profile a function with cProfile.

    profile is conditionally enabled based on the presence of ANTA_CPROFILE environment variable.
    Expect to decorate an async function.

    Parameters
    ----------
    sort_by
        The criterion to sort the profiling results. Default is 'cumtime'.

    Returns
    -------
    Callable
        The decorated function with conditional profiling.
    """

    def decorator(func: F) -> F:
        @wraps(func)
        async def wrapper(*args: Any, **kwargs: Any) -> Any:
            """Enable cProfile or not.

            If `ANTA_CPROFILE` is set, cProfile is enabled and dumps the stats to the file.

            Parameters
            ----------
            *args
                Arbitrary positional arguments.
            **kwargs
                Arbitrary keyword arguments.

            Returns
            -------
            Any
                The result of the function call.
            """
            cprofile_file = os.environ.get("ANTA_CPROFILE")

            if cprofile_file is not None:
                profiler = cProfile.Profile()
                profiler.enable()

            try:
                result = await func(*args, **kwargs)
            finally:
                if cprofile_file is not None:
                    profiler.disable()
                    stats = pstats.Stats(profiler).sort_stats(sort_by)
                    stats.dump_stats(cprofile_file)

            return result

        return cast("F", wrapper)

    return decorator


def safe_command(command: str) -> str:
    """Return a sanitized command.

    Parameters
    ----------
    command
        The command to sanitize.

    Returns
    -------
    str
        The sanitized command.
    """
    return re.sub(rf"{REGEXP_PATH_MARKERS}", "_", command)


def convert_categories(categories: list[str]) -> list[str]:
    """Convert categories for reports.

    If the category is part of the defined acronym, transform it to upper case
    otherwise capitalize the first letter.

    Parameters
    ----------
    categories
        A list of categories

    Returns
    -------
    list[str]
        The list of converted categories
    """
    if isinstance(categories, list):
        return [" ".join(word.upper() if word.lower() in ACRONYM_CATEGORIES else word.title() for word in category.split()) for category in categories]
    msg = f"Wrong input type '{type(categories)}' for convert_categories."
    raise TypeError(msg)


def format_data(data: dict[str, bool]) -> str:
    """Format a data dictionary for logging purposes.

    Parameters
    ----------
    data
        A dictionary containing the data to format.

    Returns
    -------
    str
        The formatted data.

    Example
    -------
    >>> format_data({"advertised": True, "received": True, "enabled": True})
    "Advertised: True, Received: True, Enabled: True"
    """
    return ", ".join(f"{k.capitalize()}: {v}" for k, v in data.items())


def is_interface_ignored(interface: str, ignored_interfaces: list[str] | None = None) -> bool | None:
    """Verify if an interface is present in the ignored interfaces list.

    Parameters
    ----------
    interface
        This is a string containing the interface name.
    ignored_interfaces
        A list containing the interfaces or interface types to ignore.

    Returns
    -------
    bool
        True if the interface is in the list of ignored interfaces, false otherwise.
    Example
    -------
    ```python
    >>> _is_interface_ignored(interface="Ethernet1", ignored_interfaces=["Ethernet", "Port-Channel1"])
    True
    >>> _is_interface_ignored(interface="Ethernet2", ignored_interfaces=["Ethernet1", "Port-Channel"])
    False
    >>> _is_interface_ignored(interface="Port-Channel1", ignored_interfaces=["Ethernet1", "Port-Channel"])
    True
     >>> _is_interface_ignored(interface="Ethernet1/1", ignored_interfaces: ["Ethernet1/1", "Port-Channel"])
    True
    >>> _is_interface_ignored(interface="Ethernet1/1", ignored_interfaces: ["Ethernet1", "Port-Channel"])
    False
    >>> _is_interface_ignored(interface="Ethernet1.100", ignored_interfaces: ["Ethernet1.100", "Port-Channel"])
    True
    ```
    """
    interface_prefix = re.findall(r"^[a-zA-Z-]+", interface, re.IGNORECASE)[0]
    interface_exact_match = False
    if ignored_interfaces:
        for ignored_interface in ignored_interfaces:
            if interface == ignored_interface:
                interface_exact_match = True
                break
        return bool(any([interface_exact_match, interface_prefix in ignored_interfaces]))
    return None


def lookup_by_range_key(value: str, dictionary: dict[Any, Any]) -> dict[Any, Any] | None:
    """Look up a value (e.g., 'DP1') in a dictionary where keys represent ranges using the format '<prefix><start>-<end>' (e.g., 'DP0-4').

    Parameters
    ----------
    value : str
        The value to look up (e.g., 'DP1').
    dictionary : dict
        A dictionary with keys as either:
            - exact strings (e.g., 'DP1')
            - range strings in format '<prefix><start>-<end>' (e.g., 'DP2-5')

    Returns
    -------
    object or None
        The value from the dictionary if a matching range is found, otherwise None.

    Examples
    --------
    >>> dictionary = {
        "DP0": {"group": "Exact"},
        "DP1-5": {"group": "A"},
        "DP10-15": {"group": "B"},
    }
    >>> lookup_in_range_dict("DP0", lookup_dict)
    {'group': 'EXACT'}  # exact match takes priority

    >>> lookup_in_range_dict("DP3", dictionary)
    {'group': 'A'}

    >>> lookup_in_range_dict("DP12", dictionary)
    {'group': 'B'}

    >>> lookup_in_range_dict("DP6", dictionary)
    None

    >>> lookup_in_range_dict("other1", dictionary)
    None
    """
    # Exact match
    if value in dictionary:
        return dictionary[value]

    # Range match
    match = re.match(r"([a-zA-Z]+)(\d+)", value)
    if not match:
        return None

    prefix, number = match.group(1), int(match.group(2))

    for key, detail in dictionary.items():
        key_match = re.match(rf"({prefix})(\d+)-(\d+)", key)
        if key_match:
            start = int(key_match.group(2))
            end = int(key_match.group(3))
            if start <= number <= end:
                return detail

    return None
