#!/usr/bin/python
# -*- coding: utf-8 -*-
# pylint: skip-file

"""Models related to anta.result_manager module."""

from typing import Optional
from pydantic import BaseModel, IPvAnyAddress, validator

RESULT_OPTIONS = ['unset', 'success', 'failure']


class TestResult(BaseModel):
    """Describe result of a test from a single device."""
    host: IPvAnyAddress
    test: str
    result: str = 'unset'
    message: Optional[str]

    @validator('result')
    def name_must_contain_space(cls, v):
        if v not in RESULT_OPTIONS:
            raise ValueError(f'must be one of {RESULT_OPTIONS}')
        return v


class ListResult(BaseModel):
    """List result for all tests on all devices."""
    __root__ = []

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
