"""
Test anta.report.__init__.py
"""

from __future__ import annotations

from typing import List, Optional

import pytest
from rich.table import Table
from rich.text import Text

from anta import RICH_COLOR_PALETTE
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
    def test__split_list_to_txt_list(self, usr_list: List[str], delimiter: Optional[str], expected_output: str) -> None:
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
    def test__build_headers(self, headers: List[str]) -> None:
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
        "status, output_type, expected_status",
        [
            pytest.param("unknown", None, None, id="unknown status"),
            pytest.param("unset", None, None, id="unset status"),
            pytest.param("skipped", None, "[bold orange4]skipped", id="skipped status"),
            pytest.param("failure", None, "[bold red]failure", id="failure status"),
            pytest.param("error", None, "[indian_red]error", id="error status"),
            pytest.param("success", None, "[green4]success", id="success status"),
            pytest.param("success", "Text", "to_be_replaced", id="Text"),
            pytest.param("success", "DUMMY", "[green4]success", id="DUMMY"),
        ],
    )
    def test__color_result(self, status: str, output_type: str, expected_status: str | Text) -> None:
        """
        test _build_headers
        """
        # pylint: disable=protected-access
        report = ReportTable()
        if output_type == "Text":
            expected_status = report.colors[0].style_rich()
        assert report._color_result(status, output_type) == expected_status
