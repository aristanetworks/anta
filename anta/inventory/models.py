#!/usr/bin/python
# -*- coding: utf-8 -*-
# pylint: skip-file

"""Models related to inventory management."""

from typing import List, Optional, Any
from pydantic import BaseModel, IPvAnyAddress, IPvAnyNetwork


# Pydantic models for input validation

class AntaInventoryHost(BaseModel):
    """Host definition for user's inventory."""
    host: IPvAnyAddress

class AntaInventoryNetwork(BaseModel):
    """Network definition for user's inventory."""
    network: IPvAnyNetwork

class AntaInventoryInput(BaseModel):
    """User's inventory model."""
    networks: Optional[List[AntaInventoryNetwork]]
    hosts: Optional[List[AntaInventoryHost]]

# Pydantic models for inventory output structures

class InventoryDevice(BaseModel):
    """Inventory model exposed by Inventory class."""
    host: IPvAnyAddress
    username: str
    password: str
    session: Any
    established = False
    url: str
