#!/usr/bin/python
# coding: utf-8 -*-
# pylint: disable=logging-format-interpolation
# pylint: disable=dangerous-default-value
# pylint:disable=duplicate-code
# flake8: noqa: W503
# flake8: noqa: W1202
# flake8: noqa: R0801

"""
parametrize.py - Retrieves the mock data from the json_data file
"""
from typing import Dict, List, Any


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
