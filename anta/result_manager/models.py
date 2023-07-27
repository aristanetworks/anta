"""Models related to anta.result_manager module."""

from typing import Iterator, List, Optional

from pydantic import BaseModel, RootModel, field_validator

RESULT_OPTIONS = ["unset", "success", "failure", "error", "skipped"]


class TestResult(BaseModel):
    """
    Describe the result of a test from a single device.

    Attributes:
        name (str): Device name where the test has run.
        test (str): Test name runs on the device.
        categories (List[str]): List of categories the TestResult belongs to, by default the AntaTest categories.
        description (str): TestResult description, by default the AntaTest description.
        results (str): Result of the test. Can be one of ["unset", "success", "failure", "error", "skipped"].
        message (str, optional): Message to report after the test if any.
        custom_field (str, optional): Custom field to store a string for flexibility in integrating with ANTA
    """

    name: str
    test: str
    categories: List[str]
    description: str
    result: str = "unset"
    messages: List[str] = []
    custom_field: Optional[str] = None

    @classmethod
    @field_validator("result")
    def name_must_be_in(cls, v: str) -> str:
        """
        Status validator

        Validate status is a supported one

        Args:
            v (str): User defined status

        Raises:
            ValueError: If status is unsupported

        Returns:
            str: status value
        """
        if v not in RESULT_OPTIONS:
            raise ValueError(f"must be one of {RESULT_OPTIONS}")
        return v

    def is_success(self, message: str = "") -> bool:
        """
        Helper to set status to success

        Args:
            message (str): Optional message related to the test

        Returns:
            bool: Always true
        """
        return self._set_status("success", message)

    def is_failure(self, message: str = "") -> bool:
        """
        Helper to set status to failure

        Args:
            message (str): Optional message related to the test

        Returns:
            bool: Always true
        """
        return self._set_status("failure", message)

    def is_skipped(self, message: str = "") -> bool:
        """
        Helper to set status to skipped

        Args:
            message (str): Optional message related to the test

        Returns:
            bool: Always true
        """
        return self._set_status("skipped", message)

    def is_error(self, message: str = "") -> bool:
        """
        Helper to set status to error

        Args:
            message (str): Optional message related to the test

        Returns:
            bool: Always true
        """
        return self._set_status("error", message)

    def _set_status(self, status: str, message: str = "") -> bool:
        """
        Set status and insert optional message

        Args:
            status (str): status of the test
            message (str): optional message

        Returns:
            bool: Always true
        """
        self.result = status
        if message != "":
            self.messages.append(message)
        return True

    def __str__(self) -> str:
        """
        Returns a human readable string of this TestResult
        """
        return f"Test {self.test} on device {self.name} has result {self.result}"


class ListResult(RootModel[List[TestResult]]):
    """
    List result for all tests on all devices.

    Attributes:
        __root__ (List[TestResult]): A list of TestResult objects.
    """

    root: List[TestResult] = []

    def extend(self, values: List[TestResult]) -> None:
        """Add support for extend method."""
        self.root.extend(values)

    def append(self, value: TestResult) -> None:
        """Add support for append method."""
        self.root.append(value)

    def __iter__(self) -> Iterator[TestResult]:  # type: ignore
        """Use custom iter method."""
        # TODO - mypy is not happy because we overwrite BaseModel.__iter__
        # return type and are breaking Liskov Substitution Principle.
        return iter(self.root)

    def __getitem__(self, item: int) -> TestResult:
        """Use custom getitem method."""
        return self.root[item]

    def __len__(self) -> int:
        """Support for length of __root__"""
        return len(self.root)
