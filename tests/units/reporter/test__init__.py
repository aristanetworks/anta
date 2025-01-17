# Copyright (c) 2023-2025 Arista Networks, Inc.
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
from tests.units.conftest import DEVICE_NAME
from tests.units.result_manager.conftest import FAKE_TEST

if TYPE_CHECKING:
    from anta.result_manager import ResultManager


class TestReportTable:
    """Test ReportTable class."""

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
        ("title", "columns"),
        [
            pytest.param("", [], id="empty list"),
            pytest.param("My title", ["elem1"], id="one elem list"),
            pytest.param("Other title", ["elem1", "elem2"], id="two elemst"),
        ],
    )
    def test__build_table(self, title: str, columns: list[str]) -> None:
        """Test _build_table."""
        report = ReportTable()
        table = report._build_table(title, columns)
        assert len(table.columns) == len(columns)
        if len(table.columns) > 0:
            assert table.columns[0].style == RICH_COLOR_PALETTE.HEADER
        assert table.title == title

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
        """Test _color_result."""
        report = ReportTable()
        assert report._color_result(status) == expected_status

    @pytest.mark.parametrize(
        ("results_size"),
        [
            pytest.param(5, id="5 results"),
            pytest.param(0, id="no results"),
        ],
    )
    def test_generate(
        self,
        result_manager_factory: Callable[..., ResultManager],
        results_size: int,
    ) -> None:
        """Test report table."""
        manager = result_manager_factory(size=results_size)

        report = ReportTable()
        res = report.generate(manager)

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
    def test_generate_expanded(
        self,
        result_manager_factory: Callable[..., ResultManager],
        results_size: int,
        atomic_results_size: int,
    ) -> None:
        """Test report table."""
        manager = result_manager_factory(size=results_size, nb_atomic_results=atomic_results_size)

        report = ReportTable()
        res = report.generate_expanded(manager)

        assert isinstance(res, Table)
        assert res.row_count == results_size + results_size * atomic_results_size

    @pytest.mark.parametrize(
        ("results_size", "expected_length", "distinct", "tests_filter"),
        [
            pytest.param(5, 1, False, None, id="5 results, same test"),
            pytest.param(5, 5, True, None, id="5 results, different tests"),
            pytest.param(5, 0, True, {"BadTest"}, id="5 results, different tests, bad filter"),
            pytest.param(5, 1, True, {FAKE_TEST.__name__ + "0"}, id="5 results, different tests, good filter"),
            pytest.param(5, 2, True, {FAKE_TEST.__name__ + "0", FAKE_TEST.__name__ + "2"}, id="5 results, different tests, good filter 2"),
            pytest.param(0, 0, False, None, id="no results"),
        ],
    )
    def test_generate_summary_tests(
        self, result_manager_factory: Callable[..., ResultManager], results_size: int, expected_length: int, distinct: bool, tests_filter: set[str] | None
    ) -> None:
        """Test generate_summary_tests."""
        manager = result_manager_factory(size=results_size, distinct_tests=distinct)

        report = ReportTable()
        res = report.generate_summary_tests(manager, tests=tests_filter)

        assert isinstance(res, Table)
        assert res.row_count == expected_length

    @pytest.mark.parametrize(
        ("results_size", "expected_length", "distinct", "devices_filter"),
        [
            pytest.param(5, 1, False, None, id="5 results, same device"),
            pytest.param(5, 5, True, None, id="5 results, different tests"),
            pytest.param(5, 0, True, {"BadDevice"}, id="5 results, different tests, bad filter"),
            pytest.param(5, 1, True, {DEVICE_NAME + "0"}, id="5 results, different tests, good filter"),
            pytest.param(5, 2, True, {DEVICE_NAME + "0", DEVICE_NAME + "2"}, id="5 results, different tests, good filter 2"),
            pytest.param(0, 0, False, None, id="no results"),
        ],
    )
    def test_generate_summary_devices(
        self, result_manager_factory: Callable[..., ResultManager], results_size: int, expected_length: int, distinct: bool, devices_filter: set[str] | None
    ) -> None:
        """Test generate_summary_tests."""
        manager = result_manager_factory(size=results_size, distinct_devices=distinct)

        report = ReportTable()
        res = report.generate_summary_devices(manager, devices=devices_filter)

        assert isinstance(res, Table)
        assert res.row_count == expected_length

    @pytest.mark.parametrize(
        ("field", "function"),
        [
            pytest.param("all", "generate", id="generate()"),
            pytest.param("all", "generate_expanded", id="generate_expanded()"),
        ],
    )
    @pytest.mark.parametrize(
        "title",
        [
            pytest.param(None, id="default"),
            pytest.param("", id="empty string"),
            pytest.param("My title", id="string"),
        ],
    )
    def test_titles(
        self,
        result_manager_factory: Callable[..., ResultManager],
        field: str,
        function: str,
        title: str,
    ) -> None:
        """Test ReportTable title changes."""
        manager = result_manager_factory(size=1)

        report = ReportTable()
        if title is not None:
            setattr(report.title, field, title)
        default = getattr(ReportTable.Title, field)
        res = getattr(report, function)(manager)

        assert isinstance(res, Table)
        assert res.title == (title if title is not None else default)


class TestReportJinja:
    """Tests for ReportJinja class."""

    # pylint: disable=too-few-public-methods

    def test_fail__init__file_not_found(self) -> None:
        """Test __init__ failure if file is not found."""
        with pytest.raises(FileNotFoundError, match=r"template file is not found: [/|\\]gnu[/|\\]terry[/|\\]pratchett"):
            ReportJinja(Path("/gnu/terry/pratchett"))
