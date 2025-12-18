# Copyright (c) 2023-2025 Arista Networks, Inc.
# Use of this source code is governed by the Apache License 2.0
# that can be found in the LICENSE file.
"""Common functions used in ANTA tests."""

from __future__ import annotations

import cProfile
import os
import pstats
import re
from collections.abc import Callable, Coroutine, Sequence
from datetime import datetime, timezone
from functools import cache, wraps
from time import perf_counter
from typing import TYPE_CHECKING, Any, ParamSpec, TypeVar

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

P = ParamSpec("P")
T = TypeVar("T")
AsyncFunc = Callable[P, Coroutine[Any, Any, T]]
AsyncDecorator = Callable[[AsyncFunc], AsyncFunc]


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


def cprofile(sort_by: str = "cumtime") -> AsyncDecorator:
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

    def _enable_profiler(cprofile_file: str | None) -> tuple[cProfile.Profile, str] | None:
        if cprofile_file is not None:
            profiler = cProfile.Profile()
            profiler.enable()
            return profiler, cprofile_file
        return None

    def decorator(func: AsyncFunc) -> AsyncFunc:
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
            profiler_info = _enable_profiler(os.environ.get("ANTA_CPROFILE"))

            try:
                result = await func(*args, **kwargs)
            finally:
                if profiler_info is not None:
                    profiler, cprofile_file = profiler_info
                    profiler.disable()
                    stats = pstats.Stats(profiler).sort_stats(sort_by)
                    stats.dump_stats(cprofile_file)

            return result

        return wrapper

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


def convert_categories(categories: Sequence[str], *, sort: bool = False) -> list[str]:
    """Convert categories for reports using cache.

    Handles input conversion and calls the cached conversion logic.

    Parameters
    ----------
    categories
        A list or tuple of categories.
    sort
        A boolean to indicate if the return should be sorted.

    Returns
    -------
    list[str]
        The list of converted categories, sorted if required.
    """
    if not isinstance(categories, (list, tuple)):
        msg = f"Wrong input type '{type(categories)}' for convert_categories."
        raise TypeError(msg)

    categories_tuple = tuple(categories)
    converted_categories_tuples = convert_categories_cached(categories_tuple)

    return sorted(converted_categories_tuples) if sort else list(converted_categories_tuples)


@cache
def convert_categories_cached(categories: tuple[str, ...]) -> tuple[str, ...]:
    """Convert categories for reports.

    If the category is part of the defined acronym, transform it to upper case
    otherwise capitalize the first letter.

    Parameters
    ----------
    categories
        A tuple of categories.

    Returns
    -------
    tuple[str]
        The tuple of converted categories.
    """
    return tuple(convert_single_category_cached(category) for category in categories)


@cache
def convert_single_category_cached(category: str) -> str:
    """Convert one category for reports.

    Parameters
    ----------
    category
        The category to convert.

    Returns
    -------
    str
        The converted category.
    """
    return " ".join(word.upper() if word.lower() in ACRONYM_CATEGORIES else word.title() for word in category.split())


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


def get_value_by_range_key(dictionary: dict[str, Any], key: str, default: Any = None) -> Any:
    """Get a value from a dictionary where keys represent ranges using the format '<prefix><start>-<end>' (e.g., 'TC0-4').

    Returns the supplied default value or None if the key is not found.

    Parameters
    ----------
    dictionary
        A dictionary with keys as either:
            - exact strings (e.g., 'TC1')
            - range strings in format '<prefix><start>-<end>' (e.g., 'TC2-5')
    key
        The key to look up (e.g., 'TC1').
    default
        Default value returned if the key is not found.

    Returns
    -------
    Any
        Value or default value.

    Examples
    --------
    >>> dictionary = {
        "TC0": {"group": "Exact"},
        "TC1-5": {"group": "A"},
        "TC6-7": {"group": "B"},
    }
    >>> get_value_by_range_key("TC0", lookup_dict)
    {'group': 'EXACT'}  # exact match takes priority

    >>> get_value_by_range_key("TC3", dictionary)
    {'group': 'A'}

    >>> get_value_by_range_key("TC6", dictionary)
    {'group': 'B'}

    >>> get_value_by_range_key("TC9", dictionary)
    None

    >>> get_value_by_range_key("other1", dictionary)
    None
    """
    # Exact match
    if key in dictionary:
        return dictionary[key]

    # Range match
    match = re.match(r"([a-zA-Z]+)(\d+)", key)
    if not match:
        return default

    prefix, number = match.group(1), int(match.group(2))

    for item, detail in dictionary.items():
        key_match = re.match(rf"({prefix})(\d+)-(\d+)", item)
        if key_match and int(key_match.group(2)) <= number <= int(key_match.group(3)):
            return detail

    return default


def time_ago(timestamp: float) -> str:
    """Return a human-readable string representing the time elapsed since a given timestamp.

    Parameters
    ----------
    timestamp
        A POSIX timestamp (a float representing seconds since the epoch).

    Returns
    -------
    str
        A string describing the elapsed time.
    """
    now = datetime.now(timezone.utc)
    then = datetime.fromtimestamp(timestamp, tz=timezone.utc)
    delta = now - then

    if delta.days > 0:
        return f"{delta.days} day{'s' if delta.days > 1 else ''}"

    hours, remainder = divmod(delta.seconds, 3600)
    minutes, _ = divmod(remainder, 60)

    if hours > 0:
        hour_str = f"{hours} hour{'s' if hours > 1 else ''}"
        if minutes > 0:
            minute_str = f"{minutes} minute{'s' if minutes > 1 else ''}"
            return f"{hour_str} and {minute_str}"
        return hour_str

    if minutes > 0:
        return f"{minutes} minute{'s' if minutes > 1 else ''}"

    return "less than a minute"
