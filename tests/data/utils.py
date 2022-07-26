#!/usr/bin/python
# coding: utf-8 -*-
"""
tests.data.utils
"""
from typing import Dict, Any


def generate_test_ids_dict(val: Dict[str, Any]) -> str:
    """
    generate_test_ids Helper to generate test ID for parametrize

    Only related to SYSTEM_CONFIGLETS_TESTS structure

    Parameters
    ----------
    val : dict
        A configlet test structure

    Returns
    -------
    str
        Name of the configlet
    """
    if "name" in val.keys():
        # note this wouldn't show any hours/minutes/seconds
        return val["name"]
    return "undefined_test"
