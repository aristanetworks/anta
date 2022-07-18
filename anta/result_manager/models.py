#!/usr/bin/python
# -*- coding: utf-8 -*-
# pylint: skip-file

"""Models related to anta.result_manager module."""

from typing import List, Optional, Any
from pydantic import BaseModel, IPvAnyAddress, IPvAnyNetwork, validator


class TestResult(BaseModel):
    host: str
    test: str
    result: Optional[str]
    message: Optional[str]

    @validator('result')
    def result_validator(cls, v):
        if v not in ['unset', 'success', 'failure']:
            raise ValueError('result must be either success or failure')
        return v

class ListResult(BaseModel):
    __root__= []

    def append(self, value) -> None:
        """Add support for append method."""
        self.__root__.append(value)
        super().__init__(__root__=self.__root__)

    def __iter__(self):
        """Use custom iter method."""
        return iter(self.__root__)

    def __getitem__(self, item):
        """Use custom getitem method."""
        return self.__root__[item]
