# Copyright (c) 2023-2026 Arista Networks, Inc.
# Use of this source code is governed by the Apache License 2.0
# that can be found in the LICENSE file.
"""Utility functions for the ``anta bug`` CLI command."""

from __future__ import annotations

import asyncio
import csv
import json
import logging
from typing import TYPE_CHECKING

import click
from rich.table import Table

from anta import RICH_COLOR_PALETTE
from anta.bugdb import BugDatabase
from anta.bugdb.download import download_bug_database, load_bug_database
from anta.cli.console import console
from anta.cli.utils import ExitCode

if TYPE_CHECKING:
    import pathlib

    from anta.bugdb.models import DeviceBugReport

logger = logging.getLogger(__name__)

SEVERITY_STYLES = {
    "sev1": "bold red",
    "sev2": "dark_orange",
    "sev3": "yellow",
    "sev4": "dim",
}


def run_bug_analysis(ctx: click.Context) -> list[DeviceBugReport]:
    """Load the bug database and run analysis on the inventory.

    Parameters
    ----------
    ctx
        Click context with ``token``, ``bug_database``, ``inventory``, etc.

    Returns
    -------
    list[DeviceBugReport]
        Analysis results for all devices.
    """
    if ctx.parent is None:
        ctx.exit()

    bug_ctx_params = ctx.parent.params
    token = bug_ctx_params.get("token")
    bug_database_path = bug_ctx_params.get("bug_database")
    severity = bug_ctx_params.get("severity")
    device = bug_ctx_params.get("device") or None

    inventory = ctx.obj["inventory"]

    if not token and not bug_database_path:
        logger.error("Either --token or --bug-database must be provided.")
        ctx.exit(ExitCode.USAGE_ERROR)

    # Load or download the bug database
    if bug_database_path:
        db = load_bug_database(bug_database_path)
    elif token:
        db = asyncio.run(download_bug_database(token))
    else:
        msg = "Either --token or --bug-database must be provided."
        raise click.UsageError(msg)

    bug_db = BugDatabase(db)

    console.print(
        f"[{RICH_COLOR_PALETTE.HEADER}]Bug database loaded: {bug_db.bug_count} EOS bugs, {len(bug_db.compiled_rules)} AQL rules[/]",
    )

    return asyncio.run(
        bug_db.analyze_inventory(
            inventory,
            tags=ctx.obj.get("tags"),
            devices=device,
            min_severity=severity,
        ),
    )


def _count_severities(report: DeviceBugReport) -> dict[str, int]:
    """Count bugs by severity for a device report."""
    counts: dict[str, int] = {"sev1": 0, "sev2": 0, "sev3": 0, "sev4": 0}
    for match in report.matching_bugs:
        if match.bug.severity in counts:
            counts[match.bug.severity] += 1
    return counts


def _sev_display(count: int) -> str:
    """Format a severity count for display."""
    return str(count) if count else "-"


def print_bug_table(reports: list[DeviceBugReport]) -> None:
    """Print bug analysis results as a Rich table."""
    _print_summary_table(reports)
    if any(r.matching_bugs for r in reports):
        _print_detail_table(reports)


def _print_summary_table(reports: list[DeviceBugReport]) -> None:
    """Print the summary table with bug counts per device."""
    summary = Table(title="Bug Compliance Summary", show_lines=True)
    summary.add_column("Device", style="cyan", no_wrap=True)
    summary.add_column("Model", style="dim")
    summary.add_column("EOS Version", style="dim")
    summary.add_column("Sev1", style="bold red", justify="center")
    summary.add_column("Sev2", style="dark_orange", justify="center")
    summary.add_column("Sev3", style="yellow", justify="center")
    summary.add_column("Sev4", style="dim", justify="center")
    summary.add_column("Total", style="bold", justify="center")

    for report in reports:
        sev = _count_severities(report)
        summary.add_row(
            report.device_name,
            report.hw_model,
            report.eos_version,
            _sev_display(sev["sev1"]),
            _sev_display(sev["sev2"]),
            _sev_display(sev["sev3"]),
            _sev_display(sev["sev4"]),
            str(len(report.matching_bugs)),
        )
    console.print(summary)


def _print_detail_table(reports: list[DeviceBugReport]) -> None:
    """Print the detail table with individual bugs."""
    detail = Table(title="Bug Details", show_lines=True)
    detail.add_column("Device", style="cyan", no_wrap=True)
    detail.add_column("Bug ID", style="bold", no_wrap=True)
    detail.add_column("Severity", no_wrap=True)
    detail.add_column("CVE", style="dim", no_wrap=True)
    detail.add_column("Bites", justify="center")
    detail.add_column("Summary", max_width=80)

    for report in reports:
        for match in report.matching_bugs:
            b = match.bug
            sev_style = SEVERITY_STYLES.get(b.severity, "")
            detail.add_row(
                report.device_name,
                str(b.bug_id),
                f"[{sev_style}]{b.severity}[/]",
                b.cve or "-",
                str(b.bites),
                b.alert_summary[:80] + ("..." if len(b.alert_summary) > 80 else ""),  # noqa: PLR2004
            )
    console.print(detail)


def print_bug_json(reports: list[DeviceBugReport], output: pathlib.Path | None = None) -> None:
    """Print bug analysis results as JSON."""
    data = []
    for report in reports:
        entry = {
            "device": report.device_name,
            "hw_model": report.hw_model,
            "eos_version": report.eos_version,
            "resolved_tags": sorted(report.resolved_tags),
            "bugs": [
                {
                    "bug_id": m.bug.bug_id,
                    "severity": m.bug.severity,
                    "cve": m.bug.cve or None,
                    "alert_summary": m.bug.alert_summary,
                    "version_fixed": m.bug.version_fixed,
                    "bites": m.bug.bites,
                    "matched_by": m.matched_by,
                }
                for m in report.matching_bugs
            ],
        }
        data.append(entry)

    json_str = json.dumps(data, indent=2)

    if output:
        output.write_text(json_str, encoding="utf-8")
        console.print(f"Bug report saved to {output}")
    else:
        console.print_json(json_str)


def save_bug_csv(reports: list[DeviceBugReport], csv_file: pathlib.Path) -> None:
    """Save bug analysis results as CSV."""
    headers = ["Device", "Model", "EOS Version", "Bug ID", "Severity", "CVE", "Bites", "Summary", "Fixed In", "Matched By"]

    with csv_file.open("w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(headers)
        for report in reports:
            for match in report.matching_bugs:
                b = match.bug
                writer.writerow(
                    [
                        report.device_name,
                        report.hw_model,
                        report.eos_version,
                        b.bug_id,
                        b.severity,
                        b.cve or "",
                        b.bites,
                        b.alert_summary,
                        ", ".join(b.version_fixed),
                        match.matched_by,
                    ]
                )

    console.print(f"Bug report saved to {csv_file}")


def save_bug_markdown(reports: list[DeviceBugReport], md_file: pathlib.Path) -> None:
    """Save bug analysis results as a Markdown file."""
    lines = ["# ANTA Bug Compliance Report", ""]
    _md_summary_table(lines, reports)
    for report in reports:
        if report.matching_bugs:
            _md_device_detail(lines, report)
    md_file.write_text("\n".join(lines), encoding="utf-8")
    console.print(f"Bug report saved to {md_file}")


def _md_summary_table(lines: list[str], reports: list[DeviceBugReport]) -> None:
    """Append the markdown summary table to lines."""
    lines.append("## Summary")
    lines.append("")
    lines.append("| Device | Model | EOS Version | Sev1 | Sev2 | Sev3 | Sev4 | Total |")
    lines.append("|--------|-------|-------------|------|------|------|------|-------|")
    for report in reports:
        sev = _count_severities(report)
        sev_cells = " | ".join(_sev_display(sev[s]) for s in ("sev1", "sev2", "sev3", "sev4"))
        lines.append(f"| {report.device_name} | {report.hw_model} | {report.eos_version} | {sev_cells} | {len(report.matching_bugs)} |")
    lines.append("")


def _md_device_detail(lines: list[str], report: DeviceBugReport) -> None:
    """Append the markdown detail section for one device."""
    lines.append(f"## {report.device_name}")
    lines.append("")
    lines.append(f"- **Model**: {report.hw_model}")
    lines.append(f"- **EOS Version**: {report.eos_version}")
    lines.append(f"- **Resolved Tags**: {', '.join(sorted(report.resolved_tags))}")
    lines.append("")
    lines.append("| Bug ID | Severity | CVE | Bites | Summary | Fixed In | Matched By |")
    lines.append("|--------|----------|-----|-------|---------|----------|------------|")
    for match in report.matching_bugs:
        b = match.bug
        cve = b.cve or "-"
        fixed = ", ".join(b.version_fixed[:3])
        if len(b.version_fixed) > 3:  # noqa: PLR2004
            fixed += f" (+{len(b.version_fixed) - 3})"
        summary = b.alert_summary[:100].replace("|", "\\|")
        lines.append(f"| {b.bug_id} | {b.severity} | {cve} | {b.bites} | {summary} | {fixed} | {match.matched_by} |")
    lines.append("")
