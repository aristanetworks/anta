# Copyright (c) 2023-2024 Arista Networks, Inc.
# Use of this source code is governed by the Apache License 2.0
# that can be found in the LICENSE file.
"""Common functions used in ANTA tests."""

from __future__ import annotations

from typing import Any


def get_failed_logs(expected_output: dict[Any, Any], actual_output: dict[Any, Any]) -> str:
    """Get the failed log for a test.

    Returns the failed log or an empty string if there is no difference between the expected and actual output.

    Args:
    ----
    expected_output (dict): Expected output of a test.
    actual_output (dict): Actual output of a test

    Returns
    -------
    str: Failed log of a test.

    """
    failed_logs = []

    for element, expected_data in expected_output.items():
        actual_data = actual_output.get(element)

        if actual_data is None:
            failed_logs.append(f"\nExpected `{expected_data}` as the {element}, but it was not found in the actual output.")
        elif actual_data != expected_data:
            failed_logs.append(f"\nExpected `{expected_data}` as the {element}, but found `{actual_data}` instead.")

    return "".join(failed_logs)


# pylint: disable=too-many-arguments
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


# pylint: disable=too-many-arguments
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


# pylint: disable=too-many-arguments
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
