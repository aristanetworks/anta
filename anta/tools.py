# Copyright (c) 2023-2024 Arista Networks, Inc.
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
    """
    Get the first dictionary from a list of dictionaries that is a superset of the input dict.

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
            self.logger.info("%s ...", self.message)
        return self

    def __exit__(self, exc_type: type[BaseException] | None, exc_val: BaseException | None, exc_tb: TracebackType | None) -> None:
        """__exit__ method."""
        self.raw_time = perf_counter() - self.start
        self.time = format_td(self.raw_time, 3)
        if self.logger and self.message:
            self.logger.info("%s completed in: %s.", self.message, self.time)


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

        return cast(F, wrapper)

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

    if the category is part of the defined acronym, transform it to upper case
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
