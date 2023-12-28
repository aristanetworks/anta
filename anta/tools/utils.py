# Copyright (c) 2023 Arista Networks, Inc.
# Use of this source code is governed by the Apache License 2.0
# that can be found in the LICENSE file.
"""
Toolkit for ANTA.
"""
from __future__ import annotations

from collections import defaultdict
from typing import Any, Dict, List


def create_index(list_of_dicts: List[Dict[str, Any]], key: str) -> Dict[str, List[Dict[str, Any]]]:
    """
    Creates an index for a list of dictionaries based on a specified key.

    Parameters:
    list_of_dicts (List[Dict[str, Any]]): A list of dictionaries.
    key (str): The key to be indexed.

    Returns:
    Dict[str, List[Dict[str, Any]]]: A dictionary where each key is a unique value from the list_of_dicts[key]
    and each value is a list of dictionaries that have that value for the key.
    """

    # Initialize a default dictionary
    index = defaultdict(list)

    # Iterate over each dictionary in the list
    for dict_item in list_of_dicts:
        # Check if the key exists in the dictionary
        if key in dict_item:
            # Add the dictionary to the list of its key's value
            index[dict_item[key]].append(dict_item)

    return index
