"""
Toolkit for ANTA to play with Pydantic.
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Any, Dict, List, Sequence

if TYPE_CHECKING:
    from anta.result_manager.models import ListResult

logger = logging.getLogger(__name__)


def pydantic_to_dict(pydantic_list: ListResult) -> List[Dict[str, Sequence[Any]]]:
    """
    Convert Pydantic object into a list of dict

    Mimic .dict() option from pydantic but overwrite IPv4Address nodes

    Args:
        pydantic_list: Iterable pydantic object

    Returns:
        List[Dict[str, str]]: the list of dict
    """
    result = []
    for device in pydantic_list:
        dev_dict = {k: str(v) if not isinstance(v, list) else v for k, v in device}
        result.append(dev_dict)
    return result
