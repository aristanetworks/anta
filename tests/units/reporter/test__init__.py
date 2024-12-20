# Copyright (c) 2023-2024 Arista Networks, Inc.
# Use of this source code is governed by the Apache License 2.0
# that can be found in the LICENSE file.
"""Test anta.report.__init__.py."""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING, Callable

import pytest
from rich.table import Table

from anta import RICH_COLOR_PALETTE
from anta.reporter import ReportJinja, ReportTable
from anta.result_manager.models import AntaTestStatus

if TYPE_CHECKING:
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
            pytest.param(
                ["elem1", "elem2"],
                None,
                "elem1\nelem2",
                id="two elems list no delimiter",
            ),
            pytest.param(
                ["elem1", "elem2"],
                "&",
                "& elem1\n& elem2",
                id="two elems list with delimiter",
            ),
        ],
    )
    def test__split_list_to_txt_list(self, usr_list: list[str], delimiter: str | None, expected_output: str) -> None:
        """Test _split_list_to_txt_list."""
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
            pytest.param(AntaTestStatus.UNSET, "[grey74]unset", id="unset status"),
            pytest.param(AntaTestStatus.SKIPPED, "[bold orange4]skipped", id="skipped status"),
            pytest.param(AntaTestStatus.FAILURE, "[bold red]failure", id="failure status"),
            pytest.param(AntaTestStatus.ERROR, "[indian_red]error", id="error status"),
            pytest.param(AntaTestStatus.SUCCESS, "[green4]success", id="success status"),
        ],
    )
    def test__color_result(self, status: AntaTestStatus, expected_status: str) -> None:
        """Test _build_headers."""
        report = ReportTable()
        assert report._color_result(status) == expected_status

    @pytest.mark.parametrize(
        ("results_size"),
        [
            pytest.param(5, id="5 results"),
            pytest.param(0, id="no results"),
        ],
    )
    def test_report(
        self,
        result_manager_factory: Callable[..., ResultManager],
        results_size: int,
    ) -> None:
        """Test report table."""
        manager = result_manager_factory(size=results_size)

        report = ReportTable()
        res = report.report(manager)

        assert isinstance(res, Table)
        assert res.row_count == results_size

    @pytest.mark.parametrize(
        ("results_size", "atomic_results_size"),
        [
            pytest.param(5, 0, id="5 results no atomic"),
            pytest.param(0, 0, id="no results"),
            pytest.param(5, 5, id="5 results 5 atomic"),
        ],
    )
    def test_report_expanded(
        self,
        result_manager_factory: Callable[..., ResultManager],
        results_size: int,
        atomic_results_size: int,
    ) -> None:
        """Test report table."""
        manager = result_manager_factory(size=results_size, nb_atomic_results=atomic_results_size)

        report = ReportTable()
        res = report.report_expanded(manager)

        assert isinstance(res, Table)
        assert res.row_count == results_size + results_size * atomic_results_size

    @pytest.mark.parametrize(
        ("results_size", "expected_length", "distinct", "tests_filter"),
        [
            pytest.param(5, 1, False, None, id="5 results, same test"),
            pytest.param(5, 5, True, None, id="5 results, different tests"),
            pytest.param(0, 0, False, None, id="no results"),
        ],
    )
    def test_report_summary_tests(
        self, result_manager_factory: Callable[..., ResultManager], results_size: int, expected_length: int, distinct: bool, tests_filter: list[str] | None
    ) -> None:
        """Test report_summary_tests."""
        manager = result_manager_factory(size=results_size, distinct_tests=distinct)

        report = ReportTable()
        res = report.report_summary_tests(manager, tests=tests_filter)

        assert isinstance(res, Table)
        assert res.row_count == expected_length

    @pytest.mark.parametrize(
        ("dev", "title", "number_of_tests", "expected_length"),
        [
            pytest.param(None, None, 5, 1, id="all results"),
            pytest.param("device1", None, 5, 1, id="result for host host1"),
            pytest.param(None, "Custom title", 5, 1, id="Change table title"),
        ],
    )
    def test_report_summary_devices(
        self,
        result_manager_factory: Callable[[int], ResultManager],
        dev: str | None,
        title: str | None,
        number_of_tests: int,
        expected_length: int,
    ) -> None:
        """Test report_summary_devices."""
        # TODO: refactor this later... this is injecting double test results by modyfing the device name
        # should be a fixture
        manager = result_manager_factory(number_of_tests)
        new_results = [result.model_copy() for result in manager.results]
        for result in new_results:
            result.name = dev or "test_device"
            result.result = AntaTestStatus.FAILURE
        manager.results = new_results

        report = ReportTable()
        kwargs = {"devices": [dev] if dev is not None else None, "title": title}
        kwargs = {k: v for k, v in kwargs.items() if v is not None}
        res = report.report_summary_devices(manager, **kwargs)  # type: ignore[arg-type]

        assert isinstance(res, Table)
        assert res.title == (title or "Summary per device")
        assert res.row_count == expected_length


class TestReportJinja:
    """Tests for ReportJinja class."""

    # pylint: disable=too-few-public-methods

    def test_fail__init__file_not_found(self) -> None:
        """Test __init__ failure if file is not found."""
        with pytest.raises(FileNotFoundError, match=r"template file is not found: [/|\\]gnu[/|\\]terry[/|\\]pratchett"):
            ReportJinja(Path("/gnu/terry/pratchett"))
