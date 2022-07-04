#!/usr/bin/python
# coding: utf-8 -*-

from typing import List, Optional, Any
from pydantic import BaseModel, IPvAnyAddress, IPvAnyNetwork


# Pydantic models for input validation

class AntaInventoryHost(BaseModel):
    host: IPvAnyAddress

class AntaInventoryNetwork(BaseModel):
    network: IPvAnyNetwork

class AntaInventoryInput(BaseModel):
    networks: Optional[List[AntaInventoryNetwork]]
    hosts: Optional[List[AntaInventoryHost]]

# Pydantic models for inventory output structures

class InventoryDevice(BaseModel):
    host: IPvAnyAddress
    username: str
    password: str
    session: Any
    established = False
    url: str
