# Copyright (c) 2026 Arista Networks, Inc.
# Use of this source code is governed by the Apache License 2.0
# that can be found in the LICENSE file.
"""Run the built-in ANTA security advisory catalog."""

from __future__ import annotations

import pathlib
from typing import TYPE_CHECKING

import click

from anta._advisory.reporter.reporting import (
    SecurityAdvisoryReport,
    generate_security_advisory_csv_report,
    generate_security_advisory_md_report,
)
from anta.cli.console import console
from anta.cli.nrfu import IgnoreRequiredWithHelp
from anta.cli.nrfu import commands as nrfu_commands
from anta.cli.nrfu.utils import _get_result_manager, run_tests
from anta.cli.utils import ExitCode, exit_with_code, inventory_options, result_options
from anta.result_manager import ResultManager
from anta.tests.advisories import get_catalog

if TYPE_CHECKING:
    from anta.catalog import AntaCatalog
    from anta.inventory import AntaInventory


def _load_default_catalog() -> AntaCatalog:
    """Load the complete built-in advisory catalog at invocation time."""
    return get_catalog()


def _build_advisory_report(ctx: click.Context, *, allow_empty: bool = False) -> SecurityAdvisoryReport:
    """Build a security advisory report from the visible test results."""
    return SecurityAdvisoryReport.from_result_manager(_get_result_manager(ctx), allow_empty=allow_empty)


@click.command(name="csv")
@click.pass_context
@click.option(
    "--csv-output",
    type=click.Path(file_okay=True, dir_okay=False, exists=False, writable=True, path_type=pathlib.Path),
    show_envvar=True,
    required=True,
    help="Path to save the security advisory report as a CSV file",
)
def _csv(ctx: click.Context, csv_output: pathlib.Path) -> None:
    """Generate a detailed security advisory CSV report."""
    _ = run_tests(ctx)
    try:
        generate_security_advisory_csv_report(_build_advisory_report(ctx), csv_output)
    except (OSError, ValueError) as error:
        console.print(f"Failed to save security advisory CSV report to {csv_output}: {error} ❌", style="cyan")
        ctx.exit(ExitCode.USAGE_ERROR)

    console.print(f"Security advisory CSV report saved to {csv_output} ✅", style="cyan")
    exit_with_code(ctx)


@click.command(name="md-report")
@click.pass_context
@click.option(
    "--md-output",
    type=click.Path(file_okay=True, dir_okay=False, exists=False, writable=True, path_type=pathlib.Path),
    show_envvar=True,
    required=True,
    help="Path to save the security advisory report as a Markdown file",
)
def _md_report(ctx: click.Context, md_output: pathlib.Path) -> None:
    """Generate a detailed security advisory Markdown report."""
    run_context = run_tests(ctx)
    try:
        report = _build_advisory_report(ctx, allow_empty=True)
        generate_security_advisory_md_report(report, md_output, run_context)
    except (OSError, ValueError) as error:
        console.print(f"Failed to save security advisory Markdown report to {md_output}: {error} ❌", style="cyan")
        ctx.exit(ExitCode.USAGE_ERROR)

    console.print(f"Security advisory Markdown report saved to {md_output} ✅", style="cyan")
    exit_with_code(ctx)


@click.group(
    name="psirt",
    help=(
        "[PREVIEW] Run ANTA tests for Arista security advisories. This command is a preview feature; its interface and behavior may change at any time without a "
        "deprecation notice. JSON, text, and table reports are not currently implemented."
    ),
    no_args_is_help=True,
    cls=IgnoreRequiredWithHelp,
)
@inventory_options
@click.option(
    "--device",
    "-d",
    help="Run tests on a specific device. Can be provided multiple times.",
    type=str,
    multiple=True,
    required=False,
)
@click.option(
    "--test",
    "-t",
    help="Run only a specific security advisory test. Can be provided multiple times.",
    type=str,
    multiple=True,
    required=False,
)
@result_options
@click.option(
    "--dry-run",
    help="Run anta psirt command but stop before starting to execute the tests. Considers all devices as connected.",
    type=bool,
    show_envvar=True,
    is_flag=True,
    default=False,
)
@click.pass_context
def psirt(
    ctx: click.Context,
    inventory: AntaInventory,
    tags: set[str] | None,
    device: tuple[str, ...],
    test: tuple[str, ...],
    hide: tuple[str, ...],
    *,
    ignore_status: bool,
    ignore_error: bool,
    dry_run: bool,
) -> None:
    """Run the built-in ANTA security advisory tests."""
    if ctx.obj.get("_anta_help"):
        return

    catalog = _load_default_catalog()
    if catalog is None:
        msg = "Missing catalog for anta psirt"
        raise RuntimeError(msg)

    available_tests = {test_definition.test.name for test_definition in catalog.tests}
    unknown_tests = sorted(set(test).difference(available_tests))
    if unknown_tests:
        names = ", ".join(unknown_tests)
        msg = f"Unknown security advisory test(s): {names}"
        raise click.BadParameter(msg, param_hint="'--test'")

    _: dict[str, object] = ctx.ensure_object(dict)
    ctx.obj["result_manager"] = ResultManager()
    ctx.obj["ignore_status"] = ignore_status
    ctx.obj["ignore_error"] = ignore_error
    ctx.obj["hide"] = set(hide) if hide else None
    ctx.obj["catalog"] = catalog
    ctx.obj["catalog_format"] = "yaml"
    ctx.obj["inventory"] = inventory
    ctx.obj["tags"] = tags
    ctx.obj["device"] = device
    ctx.obj["test"] = test
    ctx.obj["dry_run"] = dry_run
    ctx.obj["disconnect"] = True


psirt.add_command(nrfu_commands.tpl_report)
psirt.add_command(_csv)
psirt.add_command(_md_report)


__all__ = ["psirt"]
