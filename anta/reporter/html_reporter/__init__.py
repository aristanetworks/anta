# Copyright (c) 2025 Arista Networks, Inc.
# Use of this source code is governed by the Apache License 2.0
# that can be found in the LICENSE file.
"""HTML report generator for ANTA test results."""

from __future__ import annotations

import datetime
import json
import logging
import pkgutil
from typing import TYPE_CHECKING, Any

from jinja2 import Environment, PackageLoader

from anta.constants import ACRONYM_CATEGORIES
from anta.logger import anta_log_exception
from anta.result_manager.models import AntaTestStatus

if TYPE_CHECKING:
    from pathlib import Path

    from anta.result_manager import ResultManager

logger = logging.getLogger(__name__)


class HTMLReportGenerator:
    """Class responsible for generating an HTML report based on the provided `ResultManager` object."""

    _js_content_cache: str | None = None
    """Static cache for JavaScript content to avoid reading file repeatedly if generate is called multiple times."""

    # TODO: The runner should give metadata about the run to the ResultManager
    # Useful metadata: ANTA version, time started, time finished, duration, target inventory, tags, etc.
    @classmethod
    def generate(cls, results: ResultManager, html_output: Path, report_metadata: dict[str, Any] | None = None) -> None:
        """Generate the HTML report."""
        env = Environment(loader=PackageLoader("anta.reporter.html_reporter"), autoescape=True)

        # Register custom filters
        env.filters["pretty_json"] = cls.pretty_json
        env.filters["status_to_badge"] = cls.status_to_badge
        env.filters["status_to_row_class"] = cls.status_to_row_class
        env.filters["format_category"] = cls.format_category
        env.filters["join_list"] = lambda v, sep=" ": sep.join(map(str, v))

        try:
            # Load the template
            template = env.get_template("report_template.html")

            # Prepare context for Jinja2
            context = {
                "report_title": "ANTA Test Results Report",
                "generation_time": datetime.datetime.now(tz=datetime.timezone.utc).strftime("%Y-%m-%d %H:%M:%S %Z"),
                "summary": cls.calculate_summary(results),
                "overall_status": results.get_status(),
                "results": results.get_results(sort_by=["name", "test"]),
                "device_stats": results.device_stats,
                "category_stats": results.category_stats,
                "statuses": [s.value for s in AntaTestStatus],
                "test_names": list(results.test_stats.keys()),
                "metadata": report_metadata or {},
            }

            # Render the template
            html_content = template.render(context)

        # Catch potential errors rendering HTML content
        except Exception as exc:
            message = f"Failed to load and render 'report_template.html' from package 'anta.reporter.html_reporter': {exc}"
            anta_log_exception(exc, message, logger)
            raise RuntimeError(message) from exc

        # Write HTML file
        try:
            with html_output.open("w", encoding="utf-8") as f:
                f.write(html_content)
        except OSError as exc:
            message = f"Error writing HTML report to '{html_output.resolve()}': {exc}"
            anta_log_exception(exc, message, logger)
            raise

        # Write JavaScript file
        js_output = html_output.parent / "anta_report_filter.js"
        try:
            js_content_to_write = cls._get_js_content()
            with js_output.open("w", encoding="utf-8") as f:
                f.write(js_content_to_write)
        except OSError as exc:
            message = f"Error writing JavaScript file to '{js_output.resolve()}': {exc}"
            anta_log_exception(exc, message, logger)
            raise
        except Exception as exc:  # Catch other potential errors loading JS content
            message = f"Error preparing JavaScript file content: {exc}"
            anta_log_exception(exc, message, logger)
            raise RuntimeError(message) from exc

    @classmethod
    def _get_js_content(cls) -> str:
        """Load JavaScript content from package data, caching it."""
        if cls._js_content_cache is None:
            js_bytes = pkgutil.get_data("anta.reporter.html_reporter", "scripts/report_filter.js")
            if js_bytes is None:
                msg = "'report_filter.js' not found in package 'anta.reporter.html_reporter'."
                raise FileNotFoundError(msg)
            cls._js_content_cache = js_bytes.decode("utf-8")
        return cls._js_content_cache

    @staticmethod
    def calculate_summary(results: ResultManager) -> dict[str, Any]:
        """Calculate summary statistics."""
        total_tests = len(results)
        passed_count = results.get_total_results(status={AntaTestStatus.SUCCESS})
        failed_count = results.get_total_results(status={AntaTestStatus.FAILURE})
        error_count = results.get_total_results(status={AntaTestStatus.ERROR})
        skipped_count = results.get_total_results(status={AntaTestStatus.SKIPPED})
        unset_count = results.get_total_results(status={AntaTestStatus.UNSET})
        pass_percentage = (passed_count / total_tests * 100) if total_tests > 0 else 0

        return {
            "total": total_tests,
            "passed": passed_count,
            "failed": failed_count,
            "error": error_count,
            "skipped": skipped_count,
            "unset": unset_count,
            "pass_percentage": f"{pass_percentage:.2f}%",
        }

    @staticmethod
    def pretty_json(value: dict[str, Any]) -> str:
        """Convert dict to formatted JSON for HTML pre tag."""
        return json.dumps(value, indent=4)

    @staticmethod
    def status_to_badge(status: AntaTestStatus) -> str:
        """Map status string to Bootstrap badge class."""
        mapping = {
            AntaTestStatus.SUCCESS: "badge bg-success",
            AntaTestStatus.FAILURE: "badge bg-danger",
            AntaTestStatus.ERROR: "badge bg-danger",  # Or a different color? Maybe dark red/purple?
            AntaTestStatus.SKIPPED: "badge bg-warning text-dark",
            AntaTestStatus.UNSET: "badge bg-secondary",
        }
        return mapping.get(status, "badge bg-info")

    @staticmethod
    def status_to_row_class(status: AntaTestStatus) -> str:
        """Map status string to Bootstrap table row class for subtle background."""
        mapping = {
            AntaTestStatus.SUCCESS: "table-success",
            AntaTestStatus.FAILURE: "table-danger",
            AntaTestStatus.ERROR: "table-danger",
            AntaTestStatus.SKIPPED: "table-warning",
            AntaTestStatus.UNSET: "table-secondary",
        }
        # Default to no specific background
        return mapping.get(status, "")

    @staticmethod
    def format_category(category_name: str) -> str:
        """Format a single category name for display."""
        # Return as is if not string
        if not isinstance(category_name, str):
            return str(category_name)

        # Handle potential multiple words in a single category concept if needed
        words = category_name.split()
        return " ".join(word.upper() if word.lower() in ACRONYM_CATEGORIES else word.title() for word in words)
