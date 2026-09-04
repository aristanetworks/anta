# Copyright (c) 2026 Arista Networks, Inc.
# Use of this source code is governed by the Apache License 2.0
# that can be found in the LICENSE file.
"""Regenerate security advisory reporter fixtures from published advisory metadata."""

from pathlib import Path

import anta
from anta._advisory.reporter.reporting import (
    SecurityAdvisoryReport,
    SecurityAdvisoryReportConfig,
    generate_security_advisory_csv_report,
    generate_security_advisory_md_report,
)
from tests.units._advisory.conftest import (
    ADVISORY_ANTA_VERSION,
    DEFAULT_ADVISORY_REPORT_CONFIG,
    build_fleet_security_advisory_run_context,
)
from tests.units._advisory.reporting_data import build_security_advisory_md_result_manager, build_security_advisory_result_manager

REPORT_DATA_DIR = Path(__file__).parents[2] / "data"


def main() -> None:
    """Regenerate the checked-in CSV and Markdown reporter fixtures."""
    anta.__version__ = ADVISORY_ANTA_VERSION

    csv_report = SecurityAdvisoryReport.from_result_manager(build_security_advisory_result_manager())
    generate_security_advisory_csv_report(csv_report, REPORT_DATA_DIR / "test_security_advisory_csv_report.csv")

    md_report = SecurityAdvisoryReport.from_result_manager(build_security_advisory_md_result_manager())
    run_context = build_fleet_security_advisory_run_context(md_report)
    generate_security_advisory_md_report(
        md_report,
        REPORT_DATA_DIR / "test_security_advisory_md_report.md",
        run_context,
        DEFAULT_ADVISORY_REPORT_CONFIG,
    )
    generate_security_advisory_md_report(
        md_report,
        REPORT_DATA_DIR / "test_security_advisory_md_report_expanded.md",
        run_context,
        SecurityAdvisoryReportConfig(expand_results=True),
    )


if __name__ == "__main__":
    main()
