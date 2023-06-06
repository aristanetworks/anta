"""
Toolkit for ANTA to play with Pydantic.
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Any, Union

if TYPE_CHECKING:
    from anta.inventory.models import InventoryDevices
    from anta.result_manager.models import ListResult

logger = logging.getLogger(__name__)


def pydantic_to_dict(pydantic_list: Union[InventoryDevices, ListResult]) -> Any:
    """
    Convert Pydantic object into a dict

    Mimic .dict() option from pydantic but overwrite IPv4Address nodes

    Args:
        pydantic_list: Iterable pydantic object

    Returns:
        dict: dictionary object
    """
    result = []
    for device in pydantic_list:
        dev_dict = {k: str(v) if not isinstance(v, list) else v for k, v in device}
        result.append(dev_dict)
    return result
