# Copyright (c) 2023 Arista Networks, Inc.
# Use of this source code is governed by the Apache License 2.0
# that can be found in the LICENSE file.
"""
Test anta.report.__init__.py
"""
from __future__ import annotations

import pytest
from rich.table import Table

from anta import RICH_COLOR_PALETTE
from anta.custom_types import TestStatus
from anta.reporter import ReportTable


class Test_ReportTable:
    """
    Test ReportTable class
    """

    # not testing __init__ as nothing is going on there

    @pytest.mark.parametrize(
        "usr_list, delimiter, expected_output",
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
        """
        test _split_list_to_txt_list
        """
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
        """
        test _build_headers
        """
        # pylint: disable=protected-access
        report = ReportTable()
        table = Table()
        table_column_before = len(table.columns)
        report._build_headers(headers, table)
        assert len(table.columns) == table_column_before + len(headers)
        if len(table.columns) > 0:
            assert table.columns[table_column_before].style == RICH_COLOR_PALETTE.HEADER

    @pytest.mark.parametrize(
        "status, expected_status",
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
        """
        test _build_headers
        """
        # pylint: disable=protected-access
        report = ReportTable()
        assert report._color_result(status) == expected_status
