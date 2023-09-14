# Copyright (c) 2023 Arista Networks, Inc.
# Use of this source code is governed by the Apache License 2.0
# that can be found in the LICENSE file.
"""
Toolkit for ANTA to play with Pydantic.
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Any, Sequence

if TYPE_CHECKING:
    from anta.result_manager.models import ListResult

logger = logging.getLogger(__name__)


def pydantic_to_dict(pydantic_list: ListResult) -> list[dict[str, Sequence[Any]]]:
    """
    Convert Pydantic object into a list of dict

    Mimic .dict() option from pydantic but overwrite IPv4Address nodes

    Args:
        pydantic_list: Iterable pydantic object

    Returns:
        list[dict[str, str]]: The list of dict
    """
    result = []
    for device in pydantic_list:
        dev_dict = {k: v if isinstance(v, list) else str(v) for k, v in device}
        result.append(dev_dict)
    return result
