#!/usr/bin/python
# coding: utf-8 -*-


from logging import exception

"""Manage Exception in Inventory module."""

class InventoryRootKeyErrors(Exception):
    """Error raised when inventory root key is not found."""
    pass

class InventoryIncorrectSchema(Exception):
    """Error when user data does not follow ANTA schema."""
    pass

class InventoryUnknownFormat(Exception):
    """Error when inventory format output is not a supported one."""
    pass