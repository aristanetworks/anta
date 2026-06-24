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
from anta.bugdb.version import EOSVersion, is_version_affected
from anta.cli.console import console
from anta.cli.utils import ExitCode

if TYPE_CHECKING:
    import pathlib

    from anta.bugdb.models import BugMatch, DeviceBugReport

logger = logging.getLogger(__name__)

SEVERITY_STYLES = {
    "sev1": "bold red",
    "sev2": "dark_orange",
    "sev3": "yellow",
    "sev4": "dim",
}


def _format_fixed_in(version_fixed: list[str], max_entries: int = 3) -> str:
    """Format the version_fixed list for display, filtering nofixyet entries."""
    versions = [v for v in version_fixed if not v.endswith(".nofixyet")]
    if not versions:
        return "-"
    display = ", ".join(versions[:max_entries])
    if len(versions) > max_entries:
        display += f" (+{len(versions) - max_entries})"
    return display


def _split_bugs_by_target(matches: list[BugMatch], target: EOSVersion) -> tuple[list[BugMatch], list[BugMatch]]:
    """Split matching bugs into (fixed_by_upgrade, still_present) for a target version."""
    fixed: list[BugMatch] = []
    still_present: list[BugMatch] = []
    for m in matches:
        if is_version_affected(target, m.bug.version_introduced, m.bug.version_fixed):
            still_present.append(m)
        else:
            fixed.append(m)
    return fixed, still_present


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
    target_version_str = ctx.obj.get("target_version")

    inventory = ctx.obj["inventory"]

    # Parse target version early so invalid input fails fast
    if target_version_str:
        try:
            ctx.obj["parsed_target_version"] = EOSVersion(target_version_str)
        except ValueError:
            logger.critical("Invalid target version: %s", target_version_str)
            ctx.exit(ExitCode.USAGE_ERROR)

    if not token and not bug_database_path:
        logger.error("Either --token or --bug-database must be provided.")
        ctx.exit(ExitCode.USAGE_ERROR)

    if not bug_database_path and not token:
        msg = "Either --token or --bug-database must be provided."
        raise click.UsageError(msg)

    # Load or download the bug database
    try:
        db = load_bug_database(bug_database_path) if bug_database_path else asyncio.run(download_bug_database(token))  # type: ignore[arg-type]
    except Exception as exc:  # noqa: BLE001
        hint = " Try using --bug-database with a local AlertBase-CVP.json file instead." if token else ""
        logger.critical("Failed to load bug database: %s.%s", exc, hint)
        ctx.exit(ExitCode.USAGE_ERROR)

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


def print_bug_table(reports: list[DeviceBugReport], target_version: EOSVersion | None = None, *, wide: bool = False) -> None:
    """Print bug analysis results as a Rich table."""
    _print_summary_table(reports, target_version=target_version)
    if not any(r.matching_bugs for r in reports):
        return
    if target_version is None:
        _print_detail_table(reports, wide=wide)
        return
    # Split each report's bugs and render two tables
    fixed_reports = []
    present_reports = []
    for report in reports:
        fixed, still_present = _split_bugs_by_target(report.matching_bugs, target_version)
        if fixed:
            fixed_reports.append((report, fixed))
        if still_present:
            present_reports.append((report, still_present))
    if fixed_reports:
        _print_detail_table_from_pairs(fixed_reports, title=f"Bugs Fixed by Upgrading to {target_version}", wide=wide)
    if present_reports:
        _print_detail_table_from_pairs(present_reports, title=f"Bugs Still Present in {target_version}", wide=wide)


def _print_summary_table(reports: list[DeviceBugReport], *, target_version: EOSVersion | None = None) -> None:
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
    if target_version:
        summary.add_column("Fixed by Upgrade", style="green", justify="center")
        summary.add_column("Still Present", style="bold red", justify="center")

    for report in reports:
        sev = _count_severities(report)
        row: list[str] = [
            report.device_name,
            report.hw_model,
            report.eos_version,
            _sev_display(sev["sev1"]),
            _sev_display(sev["sev2"]),
            _sev_display(sev["sev3"]),
            _sev_display(sev["sev4"]),
            str(len(report.matching_bugs)),
        ]
        if target_version:
            fixed, still_present = _split_bugs_by_target(report.matching_bugs, target_version)
            row.extend([str(len(fixed)), str(len(still_present))])
        summary.add_row(*row)
    console.print(summary)


def _print_detail_table(reports: list[DeviceBugReport], title: str = "Bug Details", *, wide: bool = False) -> None:
    """Print the detail table with individual bugs."""
    pairs = [(r, r.matching_bugs) for r in reports if r.matching_bugs]
    _print_detail_table_from_pairs(pairs, title=title, wide=wide)


def _print_detail_table_from_pairs(pairs: list[tuple[DeviceBugReport, list[BugMatch]]], title: str = "Bug Details", *, wide: bool = False) -> None:
    """Print a detail table from (report, bugs) pairs."""
    detail = Table(title=title, show_lines=True)
    detail.add_column("Device", style="cyan", no_wrap=True)
    detail.add_column("Bug ID", style="bold", no_wrap=True)
    detail.add_column("Severity", no_wrap=True)
    detail.add_column("CVE", style="dim", no_wrap=True)
    detail.add_column("Bites", justify="center")
    detail.add_column("Fixed In", style="dim", no_wrap=True, max_width=40)
    if wide:
        detail.add_column("Summary")
    else:
        detail.add_column("Summary", max_width=80)

    for report, bugs in pairs:
        for match in bugs:
            b = match.bug
            sev_style = SEVERITY_STYLES.get(b.severity, "")
            summary = b.alert_summary if wide else b.alert_summary[:80] + ("..." if len(b.alert_summary) > 80 else "")  # noqa: PLR2004
            detail.add_row(
                report.device_name,
                str(b.bug_id),
                f"[{sev_style}]{b.severity}[/]",
                b.cve or "-",
                str(b.bites),
                _format_fixed_in(b.version_fixed),
                summary,
            )
    console.print(detail)


def _bug_to_json(m: BugMatch) -> dict[str, object]:
    """Convert a BugMatch to a JSON-serializable dict."""
    return {
        "bug_id": m.bug.bug_id,
        "severity": m.bug.severity,
        "cve": m.bug.cve or None,
        "alert_summary": m.bug.alert_summary,
        "version_fixed": m.bug.version_fixed,
        "bites": m.bug.bites,
        "matched_by": m.matched_by,
    }


def print_bug_json(reports: list[DeviceBugReport], output: pathlib.Path | None = None, target_version: EOSVersion | None = None) -> None:
    """Print bug analysis results as JSON."""
    data = []
    for report in reports:
        entry: dict[str, object] = {
            "device": report.device_name,
            "hw_model": report.hw_model,
            "eos_version": report.eos_version,
            "resolved_tags": sorted(report.resolved_tags),
        }
        if target_version:
            fixed, still_present = _split_bugs_by_target(report.matching_bugs, target_version)
            entry["target_version"] = str(target_version)
            entry["fixed_by_upgrade"] = [_bug_to_json(m) for m in fixed]
            entry["still_present"] = [_bug_to_json(m) for m in still_present]
        else:
            entry["bugs"] = [_bug_to_json(m) for m in report.matching_bugs]
        data.append(entry)

    json_str = json.dumps(data, indent=2)

    if output:
        output.write_text(json_str, encoding="utf-8")
        console.print(f"Bug report saved to {output}")
    else:
        console.print_json(json_str)


def save_bug_csv(reports: list[DeviceBugReport], csv_file: pathlib.Path, target_version: EOSVersion | None = None) -> None:
    """Save bug analysis results as CSV."""
    headers = ["Device", "Model", "EOS Version", "Bug ID", "Severity", "CVE", "Bites", "Summary", "Fixed In", "Matched By"]
    if target_version:
        headers.append("Upgrade Impact")

    with csv_file.open("w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(headers)
        for report in reports:
            if target_version:
                fixed, still_present = _split_bugs_by_target(report.matching_bugs, target_version)
                for match in fixed:
                    _write_csv_bug_row(writer, report, match, f"Fixed in {target_version}")
                for match in still_present:
                    _write_csv_bug_row(writer, report, match, f"Still present in {target_version}")
            else:
                for match in report.matching_bugs:
                    _write_csv_bug_row(writer, report, match)

    console.print(f"Bug report saved to {csv_file}")


def _write_csv_bug_row(writer: csv.writer, report: DeviceBugReport, match: BugMatch, upgrade_impact: str | None = None) -> None:  # type: ignore[type-arg]
    """Write a single bug row to CSV."""
    b = match.bug
    row = [
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
    if upgrade_impact is not None:
        row.append(upgrade_impact)
    writer.writerow(row)


def save_bug_markdown(reports: list[DeviceBugReport], md_file: pathlib.Path, target_version: EOSVersion | None = None) -> None:
    """Save bug analysis results as a Markdown file."""
    lines = ["# ANTA Bug Compliance Report", ""]
    if target_version:
        lines.append(f"**Target Version:** {target_version}")
        lines.append("")
    _md_summary_table(lines, reports, target_version=target_version)
    if target_version:
        for report in reports:
            if report.matching_bugs:
                fixed, still_present = _split_bugs_by_target(report.matching_bugs, target_version)
                if fixed:
                    _md_device_detail_with_bugs(lines, report, fixed, subtitle=f"Fixed by Upgrading to {target_version}")
                if still_present:
                    _md_device_detail_with_bugs(lines, report, still_present, subtitle=f"Still Present in {target_version}")
    else:
        for report in reports:
            if report.matching_bugs:
                _md_device_detail(lines, report)
    md_file.write_text("\n".join(lines), encoding="utf-8")
    console.print(f"Bug report saved to {md_file}")


def _md_summary_table(lines: list[str], reports: list[DeviceBugReport], target_version: EOSVersion | None = None) -> None:
    """Append the markdown summary table to lines."""
    lines.append("## Summary")
    lines.append("")
    header = "| Device | Model | EOS Version | Sev1 | Sev2 | Sev3 | Sev4 | Total |"
    separator = "|--------|-------|-------------|------|------|------|------|-------|"
    if target_version:
        header += " Fixed by Upgrade | Still Present |"
        separator += "-----------------|---------------|"
    lines.append(header)
    lines.append(separator)
    for report in reports:
        sev = _count_severities(report)
        sev_cells = " | ".join(_sev_display(sev[s]) for s in ("sev1", "sev2", "sev3", "sev4"))
        row = f"| {report.device_name} | {report.hw_model} | {report.eos_version} | {sev_cells} | {len(report.matching_bugs)} |"
        if target_version:
            fixed, still_present = _split_bugs_by_target(report.matching_bugs, target_version)
            row += f" {len(fixed)} | {len(still_present)} |"
        lines.append(row)
    lines.append("")


def _md_device_detail(lines: list[str], report: DeviceBugReport) -> None:
    """Append the markdown detail section for one device."""
    _md_device_detail_with_bugs(lines, report, report.matching_bugs)


def _md_device_detail_with_bugs(lines: list[str], report: DeviceBugReport, bugs: list[BugMatch], subtitle: str = "") -> None:
    """Append the markdown detail section for one device with a specific list of bugs."""
    title = report.device_name
    if subtitle:
        title += f" — {subtitle}"
    lines.append(f"## {title}")
    lines.append("")
    lines.append(f"- **Model**: {report.hw_model}")
    lines.append(f"- **EOS Version**: {report.eos_version}")
    lines.append(f"- **Resolved Tags**: {', '.join(sorted(report.resolved_tags))}")
    lines.append("")
    lines.append("| Bug ID | Severity | CVE | Bites | Summary | Fixed In | Matched By |")
    lines.append("|--------|----------|-----|-------|---------|----------|------------|")
    for match in bugs:
        b = match.bug
        cve = b.cve or "-"
        fixed = _format_fixed_in(b.version_fixed)
        summary = b.alert_summary[:100].replace("|", "\\|")
        lines.append(f"| {b.bug_id} | {b.severity} | {cve} | {b.bites} | {summary} | {fixed} | {match.matched_by} |")
    lines.append("")
