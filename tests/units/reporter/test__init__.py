# Copyright (c) 2023-2024 Arista Networks, Inc.
# Use of this source code is governed by the Apache License 2.0
# that can be found in the LICENSE file.
"""Test anta.report.__init__.py."""

from __future__ import annotations

from typing import TYPE_CHECKING, Callable

import pytest
from rich.table import Table

from anta import RICH_COLOR_PALETTE
from anta.reporter import ReportTable

if TYPE_CHECKING:
    from anta.custom_types import TestStatus
    from anta.result_manager import ResultManager


class TestReportTable:
    """Test ReportTable class."""

    # not testing __init__ as nothing is going on there

    @pytest.mark.parametrize(
        ("usr_list", "delimiter", "expected_output"),
        [
            pytest.param([], None, "", id="empty list no delimiter"),
            pytest.param([], "*", "", id="empty list with delimiter"),
            pytest.param(["elem1"], None, "elem1", id="one elem list no delimiter"),
            pytest.param(["elem1"], "*", "* elem1", id="one elem list with delimiter"),
            pytest.param(["elem1", "elem2"], None, "elem1\nelem2", id="two elems list no delimiter"),
            pytest.param(["elem1", "elem2"], "&", "& elem1\n& elem2", id="two elems list with delimiter"),
        ],
    )
    def test__split_list_to_txt_list(self, usr_list: list[str], delimiter: str | None, expected_output: str) -> None:
        """Test _split_list_to_txt_list."""
        # pylint: disable=protected-access
        report = ReportTable()
        assert report._split_list_to_txt_list(usr_list, delimiter) == expected_output

    @pytest.mark.parametrize(
        "headers",
        [
            pytest.param([], id="empty list"),
            pytest.param(["elem1"], id="one elem list"),
            pytest.param(["elem1", "elem2"], id="two elemst"),
        ],
    )
    def test__build_headers(self, headers: list[str]) -> None:
        """Test _build_headers."""
        # pylint: disable=protected-access
        report = ReportTable()
        table = Table()
        table_column_before = len(table.columns)
        report._build_headers(headers, table)
        assert len(table.columns) == table_column_before + len(headers)
        if len(table.columns) > 0:
            assert table.columns[table_column_before].style == RICH_COLOR_PALETTE.HEADER

    @pytest.mark.parametrize(
        ("status", "expected_status"),
        [
            pytest.param("unknown", "unknown", id="unknown status"),
            pytest.param("unset", "[grey74]unset", id="unset status"),
            pytest.param("skipped", "[bold orange4]skipped", id="skipped status"),
            pytest.param("failure", "[bold red]failure", id="failure status"),
            pytest.param("error", "[indian_red]error", id="error status"),
            pytest.param("success", "[green4]success", id="success status"),
        ],
    )
    def test__color_result(self, status: TestStatus, expected_status: str) -> None:
        """Test _build_headers."""
        # pylint: disable=protected-access
        report = ReportTable()
        assert report._color_result(status) == expected_status

    @pytest.mark.parametrize(
        ("host", "testcase", "title", "number_of_tests", "expected_length"),
        [
            pytest.param(None, None, None, 5, 5, id="all results"),
            pytest.param("host1", None, None, 5, 0, id="result for host1 when no host1 test"),
            pytest.param(None, "VerifyTest3", None, 5, 1, id="result for test VerifyTest3"),
            pytest.param(None, None, "Custom title", 5, 5, id="Change table title"),
        ],
    )
    def test_report_all(
        self,
        result_manager_factory: Callable[[int], ResultManager],
        host: str | None,
        testcase: str | None,
        title: str | None,
        number_of_tests: int,
        expected_length: int,
    ) -> None:
        """Test report_all."""
        # pylint: disable=too-many-arguments
        rm = result_manager_factory(number_of_tests)

        report = ReportTable()
        kwargs = {"host": host, "testcase": testcase, "title": title}
        kwargs = {k: v for k, v in kwargs.items() if v is not None}
        res = report.report_all(rm, **kwargs)  # type: ignore[arg-type]

        assert isinstance(res, Table)
        assert res.title == (title or "All tests results")
        assert res.row_count == expected_length

    @pytest.mark.parametrize(
        ("testcase", "title", "number_of_tests", "expected_length"),
        [
            pytest.param(None, None, 5, 5, id="all results"),
            pytest.param("VerifyTest3", None, 5, 1, id="result for test VerifyTest3"),
            pytest.param(None, "Custom title", 5, 5, id="Change table title"),
        ],
    )
    def test_report_summary_tests(
        self,
        result_manager_factory: Callable[[int], ResultManager],
        testcase: str | None,
        title: str | None,
        number_of_tests: int,
        expected_length: int,
    ) -> None:
        """Test report_summary_tests."""
        # pylint: disable=too-many-arguments
        # TODO: refactor this later... this is injecting double test results by modyfing the device name
        # should be a fixture
        rm = result_manager_factory(number_of_tests)
        new_results = [result.model_copy() for result in rm.get_results()]
        for result in new_results:
            result.name = "test_device"
            result.result = "failure"
        rm.add_test_results(new_results)

        report = ReportTable()
        kwargs = {"testcase": testcase, "title": title}
        kwargs = {k: v for k, v in kwargs.items() if v is not None}
        res = report.report_summary_tests(rm, **kwargs)  # type: ignore[arg-type]

        assert isinstance(res, Table)
        assert res.title == (title or "Summary per test case")
        assert res.row_count == expected_length

    @pytest.mark.parametrize(
        ("host", "title", "number_of_tests", "expected_length"),
        [
            pytest.param(None, None, 5, 2, id="all results"),
            pytest.param("host1", None, 5, 1, id="result for host host1"),
            pytest.param(None, "Custom title", 5, 2, id="Change table title"),
        ],
    )
    def test_report_summary_hosts(
        self,
        result_manager_factory: Callable[[int], ResultManager],
        host: str | None,
        title: str | None,
        number_of_tests: int,
        expected_length: int,
    ) -> None:
        """Test report_summary_hosts."""
        # pylint: disable=too-many-arguments
        # TODO: refactor this later... this is injecting double test results by modyfing the device name
        # should be a fixture
        rm = result_manager_factory(number_of_tests)
        new_results = [result.model_copy() for result in rm.get_results()]
        for result in new_results:
            result.name = host or "test_device"
            result.result = "failure"
        rm.add_test_results(new_results)

        report = ReportTable()
        kwargs = {"host": host, "title": title}
        kwargs = {k: v for k, v in kwargs.items() if v is not None}
        res = report.report_summary_hosts(rm, **kwargs)  # type: ignore[arg-type]

        assert isinstance(res, Table)
        assert res.title == (title or "Summary per host")
        assert res.row_count == expected_length
