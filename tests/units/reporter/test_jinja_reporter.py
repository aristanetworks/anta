# Copyright (c) 2023-2026 Arista Networks, Inc.
# Use of this source code is governed by the Apache License 2.0
# that can be found in the LICENSE file.
"""Test anta.reporter.jinja_reporter."""

from pathlib import Path

import pytest

from anta.reporter.jinja_reporter import ReportJinja


class TestReportJinja:
    """Tests for ReportJinja class."""

    # pylint: disable=too-few-public-methods

    def test_fail__init__file_not_found(self) -> None:
        """Test __init__ failure if the template file is not found."""
        with pytest.raises(FileNotFoundError, match=r"template file is not found: [/|\\]gnu[/|\\]terry[/|\\]pratchett"):
            ReportJinja(Path("/gnu/terry/pratchett"))
