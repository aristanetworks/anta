#!/usr/bin/python
# -*- coding: utf-8 -*-
# pylint: skip-file

"""Models related to anta.result_manager module."""

from typing import List, Optional, Any
from pydantic import BaseModel, IPvAnyAddress, validator

RESULT_OPTIONS = ['unset', 'success', 'failure']

class TestResult(BaseModel):
    """
    Describe result of a test from a single device.

    Attributes:
        host(IPvAnyAddress): IPv4 or IPv6 address of the device where the test has run.
        test(str): Test name runs on the device.
        results(str): Result of the test. Can be one of unset / failure / success.
        message(str, optional): Message to report after the test.
    """
    host: IPvAnyAddress
    test: str
    result: str = 'unset'
    message: Optional[str]

    @validator('result', allow_reuse=True)
    def name_must_be_in(cls, v):
        if v not in RESULT_OPTIONS:
            raise ValueError(f'must be one of {RESULT_OPTIONS}')
        return v


class ListResult(BaseModel):
    """
    List result for all tests on all devices.

    Attributes:
        __root__(List[TestResult]): A list of TestResult objects.
    """
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

    def __len__(self):
        """Support for length of __root__"""
        return len(self.__root__)
