# Copyright (c) 2023-2024 Arista Networks, Inc.
# Use of this source code is governed by the Apache License 2.0
# that can be found in the LICENSE file.

"""Get one dictionary from a list of dictionaries by matching the given key and value."""
from __future__ import annotations

from typing import Any, Optional


# pylint: disable=too-many-arguments
def get_item(
    list_of_dicts: list[dict[Any, Any]],
    key: Any,
    value: Any,
    default: Optional[Any] = None,
    required: bool = False,
    case_sensitive: bool = False,
    var_name: Optional[str] = None,
    custom_error_msg: Optional[str] = None,
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
