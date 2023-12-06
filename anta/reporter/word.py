# Copyright (c) 2023 Arista Networks, Inc.
# Use of this source code is governed by the Apache License 2.0
# that can be found in the LICENSE file.
"""
Word report management
"""
import datetime
import json
from typing import Any, Dict, List

from docx import Document
from docx.oxml import parse_xml
from docx.oxml.ns import nsdecls
from docx.shared import Inches, Pt
from docx.table import Table

from anta.result_manager import ResultManager

WIDTHS = (
    Inches(0.5),
    Inches(1.17),
    Inches(2.50),
    Inches(1.25),
    Inches(0.75),
    Inches(1.50),
)


class ReportWordDocx:

    """
    Class to manage docx reporting.
    """

    SUMMARY_HEADERS = [
        "Device name",
        "Case Name",
        "Pass/Fail",
        "Observation",
    ]
    COLORS = {
        "headers": "AECFE1",
        "success": "A9DFBF",
        "failure": "F5B7B1",
        "error": "#E74C3C",
    }
    TABLE_FORMAT = "Table Grid"
    FONT_DEFAULT = "Arial"

    def __init__(self, filename: str, anta_result_manager: ResultManager, title: str = "Anta Tests Report") -> None:
        """Class constructor."""
        self.filename = filename
        self.document = Document()

        section = self.document.sections[0]
        section.left_margin = Inches(0.5)
        section.right_margin = Inches(0.5)
        self._create(title=title)
        self.generate_report(anta_result_manager=anta_result_manager)

    # -------------------------------------------
    # Internal methods
    # -------------------------------------------

    def _create(self, title: str) -> None:
        """Create a document with a L1 title."""
        self.add_header_l1(title)

    def _set_header_generic(self, level: int, content: str, font_size: int) -> None:
        """Wrapper to insert a title with a custom level and font size."""
        heading = self.document.add_heading(level=level)
        run = heading.add_run(content)
        run.font.size = Pt(font_size)
        # run.font.color.rgb = RGBColor(204, 0, 0)

    def _shade_cell(self, cell_idx: int, table: Table, count: int, shade: str) -> None:
        """Shade a cell in word doc table

        Args:
            cell_idx (int): Column index for cell to shade
            table (obj): Word doc table object
            count (int): Row index for cell to shade
            shade (str): hexadecimal color representation
        """
        cell = table.cell(count, cell_idx)
        color = parse_xml(f'<w:shd {nsdecls("w")} w:fill="{shade}"/>')
        # pylint: disable-next=protected-access
        cell._tc.get_or_add_tcPr().append(color)

    def _create_tests_summary_header(self, table: Table) -> None:
        """Table header management."""
        table.autofit = False
        for count, header in enumerate(self.SUMMARY_HEADERS):
            # self.__set_cell_width(table, 0)
            para = table.rows[0].cells[count].paragraphs[0]
            run = para.add_run(header)
            run.font.name = self.FONT_DEFAULT
            run.font.size = Pt(9)
            run.font.bold = True

            self._shade_cell(count, table, 0, self.COLORS["headers"])

    def _create_tests_summary_content(self, table: Table, test_data: List[Dict[str, Any]]) -> None:
        """Populate table with summary of tests run by ANTA."""
        for count, test_case_entry in enumerate(test_data):
            row_cells = table.add_row().cells
            # Add entries with no formatting
            row_cells[0].text = test_case_entry["name"]
            row_cells[1].text = test_case_entry["test"]
            # row_cells[2].text = test_case_entry["result"]
            row_cells[3].text = test_case_entry["messages"]

            # Add entries using formatting
            run = row_cells[2].paragraphs[0].add_run(test_case_entry["result"])
            if test_case_entry["result"] == "failure":
                # run.font.size = Pt(10)
                self._shade_cell(2, table, count + 1, self.COLORS["failure"])
            elif test_case_entry["result"] == "success":
                # run.font.size = Pt(10)
                self._shade_cell(2, table, count + 1, self.COLORS["success"])
            # else:
            #     run.font.size = Pt(10)
            run.bold = True
            run.font.name = self.FONT_DEFAULT

            # self.__shade_cell(0, table, count, "52BE80")

    # -------------------------------------------
    # Pubic methods
    # -------------------------------------------

    def save(self) -> None:
        """Close and Save document."""
        self.document.save(self.filename)

    def add_header_l1(self, content: str) -> None:
        """Insert a level 1 header."""
        self._set_header_generic(level=1, content=content, font_size=24)
        # run.font.color.rgb = RGBColor(204, 0, 0)

    def add_header_l2(self, content: str) -> None:
        """Insert a level 2 header."""
        self._set_header_generic(level=2, content=content, font_size=18)
        # run.font.color.rgb = RGBColor(204, 0, 0)

    def add_header_l3(self, content: str) -> None:
        """Insert a level 3 header."""
        self._set_header_generic(level=3, content=content, font_size=14)

    def add_text(self, content: str, font_pt: int = 9, font: str = FONT_DEFAULT) -> None:
        """Add paragraph to document."""
        para = self.document.add_paragraph()
        run = para.add_run(content)
        run.font.size = Pt(font_pt)
        run.font.name = font

    def create_tests_summary(self, anta_result: List[Dict[str, Any]]) -> None:
        """Create table with all tests result in anta_result."""
        table = self.document.add_table(rows=1, cols=len(self.SUMMARY_HEADERS), style=self.TABLE_FORMAT)
        self._create_tests_summary_header(table)
        self._create_tests_summary_content(table, anta_result)
        # Force font for all entries
        for row in table.rows:
            for cell in row.cells:
                paragraphs = cell.paragraphs
                for paragraph in paragraphs:
                    for run in paragraph.runs:
                        font = run.font
                        font.size = Pt(9)

    def generate_report(self, anta_result_manager: ResultManager) -> None:
        """Build a report based on content of ResultManager."""

        # Abstract section
        self.add_header_l2("1. Abstract")
        self.add_text(f"This is a test report generated by ANTA on {datetime.datetime.now()}\nTo be continued")

        # Tests summary
        self.add_header_l2("2. Tests summary")

        anta_result_json = json.loads(anta_result_manager.get_json_results())
        for index, device in enumerate({d["name"] for d in anta_result_json}, start=1):
            self.add_header_l3(f"2.{index}. Tests summary for {device}")
            self.add_text(f"Tests summary for device {device} captures with ANTA\n")
            sub_result = [d for d in anta_result_json if d["name"] == device]
            self.create_tests_summary(anta_result=sub_result)
            self.add_text("\n")

        # Test sections
        self.add_header_l2("3. Detailled report")
        self.add_text("This section provides detailed results for every tests run with ANTA")

        self.save()
