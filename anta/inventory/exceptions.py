"""Manage Exception in Inventory module."""


class InventoryRootKeyErrors(Exception):
    """Error raised when inventory root key is not found."""


class InventoryIncorrectSchema(Exception):
    """Error when user data does not follow ANTA schema."""
