# Copyright (c) 2026 Arista Networks, Inc.
# Use of this source code is governed by the Apache License 2.0
# that can be found in the LICENSE file.
"""Regenerate security advisory reporter fixtures from published advisory metadata."""

from pathlib import Path

import anta
from anta._advisory.reporter.reporting import (
    SecurityAdvisoryReport,
    generate_security_advisory_csv_report,
    generate_security_advisory_md_report,
)
from tests.units._advisory.conftest import (
    ADVISORY_ANTA_VERSION,
    build_fleet_security_advisory_run_context,
)
from tests.units._advisory.reporting_data import build_security_advisory_md_result_manager

REPORT_DATA_DIR = Path(__file__).parents[2] / "data"


def main() -> None:
    """Regenerate the checked-in CSV and Markdown reporter fixtures."""
    anta.__version__ = ADVISORY_ANTA_VERSION

    report = SecurityAdvisoryReport.from_result_manager(build_security_advisory_md_result_manager())
    generate_security_advisory_csv_report(report, REPORT_DATA_DIR / "test_security_advisory_csv_report.csv")
    generate_security_advisory_md_report(
        report,
        REPORT_DATA_DIR / "test_security_advisory_md_report.md",
        build_fleet_security_advisory_run_context(report),
    )


if __name__ == "__main__":
    main()
