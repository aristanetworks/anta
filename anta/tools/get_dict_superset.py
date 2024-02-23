# Copyright (c) 2023-2024 Arista Networks, Inc.
# Use of this source code is governed by the Apache License 2.0
# that can be found in the LICENSE file.

"""Get one dictionary from a list of dictionaries by matching the given key and values."""
from __future__ import annotations

from typing import Any, Optional


def get_dict_superset(
    list_of_dicts: list[dict[Any, Any]],
    input_dict: dict[Any, Any],
    default: Optional[Any] = None,
    required: bool = False,
    var_name: Optional[str] = None,
    custom_error_msg: Optional[str] = None,
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
