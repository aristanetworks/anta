# Copyright (c) 2023-2025 Arista Networks, Inc.
# Use of this source code is governed by the Apache License 2.0
# that can be found in the LICENSE file.
"""Manage Exception in Inventory module."""


class InventoryRootKeyError(Exception):
    """Error raised when inventory root key is not found."""


class InventoryIncorrectSchemaError(Exception):
    """Error when user data does not follow ANTA schema."""
