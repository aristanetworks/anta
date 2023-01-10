"""
parametrize.py - Retrieves the mock data from the json_data file
"""
from typing import Any, Dict, List


def generate_list_from_dict(data: Dict[str, Any]) -> List[Any]:
    """
    generate_flat_data Generate a flat list of dict

    Example
    -------
    >>> CUSTOMER_CVP_CONTAINER_TOPOLOGY = {"Tenant":{"name":"Tenant","key":"root","parentContainerId":"None"},
                                           "Undefined":{"name":"Undefined","key":"undefined_container","parentContainerId":"root"}}

    >>> result = generate_flat_data(CUSTOMER_CVP_CONTAINER_TOPOLOGY)

    >>> print(result)
    [{"name":"Tenant","key":"root","parentContainerId":"None"},{"name":"Undefined","key":"undefined_container","parentContainerId":"root"}]

    Parameters
    ----------
    data : dict
        Data to transform

    Returns
    -------
    list
        List extracted from the dict
    """
    return [dict(data[d].items()) for d in data]
