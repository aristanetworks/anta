# Copyright (c) 2023-2026 Arista Networks, Inc.
# Use of this source code is governed by the Apache License 2.0
# that can be found in the LICENSE file.
"""Repeat native measurements in fresh processes while preserving raw evidence."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import platform
import shlex
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Any

from tests.benchmark.memory_profile import summarize_profile

BENCHMARK = "tests/benchmark/test_anta.py"
TARGET = f"{BENCHMARK}::test_anta[2-devices]"
VARIANTS = ("isolated", "suite")
RESET_VARIANTS = ("isolated", "isolated-reset", "suite", "suite-reset")


def command_output(*command: str) -> str:
    """Capture an environment diagnostic, including errors rather than dropping them."""
    result = subprocess.run(command, check=False, text=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)  # noqa: S603
    return result.stdout


def native_binaries() -> dict[str, str]:
    """Fingerprint the actual interpreter and instruments, not just their versions."""
    paths = [sys.executable, shutil.which("codspeed"), shutil.which("codspeed-memtrack")]
    fingerprints = {}
    for path in paths:
        if path:
            digest = hashlib.sha256()
            with Path(path).open("rb") as binary:
                while chunk := binary.read(1024 * 1024):
                    digest.update(chunk)
            fingerprints[str(Path(path).resolve())] = digest.hexdigest()
    return fingerprints


def validate_session(directory: Path, variant: str) -> dict[str, Any]:
    """Reject missing evidence, a changed selection, or incomplete two-device results."""
    evidence = json.loads((directory / "metadata/session.json").read_text(encoding="utf-8"))
    expected = (
        [TARGET]
        if variant.removesuffix("-reset") == "isolated"
        else [f"{BENCHMARK}::{test}[{count}]" for test in ("test_anta_dry_run", "test_anta") for count in ("1-device", "2-devices", "5-devices")]
    )
    if evidence["collected_order"] != expected or evidence["runner_mode"] != "memory" or evidence["exitstatus"] != 0:
        msg = "Unexpected pytest selection, missing native memory mode, or failing session"
        raise ValueError(msg)
    case = evidence["cases"]["2-devices"]
    if case["count"] != 2 * evidence["catalog_count"] or case["statuses"].get("error", 0) or case["statuses"].get("unset", 0):
        msg = "Incomplete two-device results or unexpected error/unset statuses"
        raise ValueError(msg)
    if not list((directory / "profile").rglob("*ExecutionTimestamps*")) or not list((directory / "profile").rglob("*Memtrack*")):
        msg = "Native timestamp or allocation artifacts are missing"
        raise ValueError(msg)
    reset = variant.endswith("-reset")
    resets = evidence["task_registry_resets"]
    expected_resets = [nodeid for nodeid in expected for _ in range(2)] if reset else []
    if evidence["task_registry_reset"] != reset or [entry["nodeid"] for entry in resets] != expected_resets:
        msg = "Registry reset did not run exactly before warm-up and measurement, or baseline was altered"
        raise ValueError(msg)
    if reset and any(entry["table_bytes_after"] != resets[0]["table_bytes_after"] or entry["tasks_after"] != 0 for entry in resets):
        msg = "Registry reset evidence is inconsistent"
        raise ValueError(msg)
    profile = summarize_profile(directory, TARGET, additional_targets=expected)
    return {
        "catalog_sha256": evidence["catalog_sha256"],
        "raw_catalog_sha256": evidence["raw_catalog_sha256"],
        "normalized_one_day_ago_timestamps": evidence["normalized_one_day_ago_timestamps"],
        "catalog_count": evidence["catalog_count"],
        "result_count": case["count"],
        "statuses": case["statuses"],
        "order_sha256": case["order_sha256"],
        "task_registry_resets": resets,
        "allocation_profiles": profile.pop("cases"),
        "allocation_profile": profile,
    }


def case_summary(runs: list[dict[str, Any]], variants: tuple[str, ...]) -> str:
    """Show repeated peaks for every suite sample, including dry-run and one/five devices."""
    summary = "\nAll suite cases, peak requested bytes from allocations originating in each sample:\n\n"
    cases = sorted({nodeid for run in runs for nodeid in run.get("allocation_profiles", {})})
    for nodeid in cases:
        for variant in variants:
            if not variant.startswith("suite"):
                continue
            peaks = [
                run["allocation_profiles"][nodeid]["peak_sample_allocations_bytes"]
                for run in runs
                if run["variant"] == variant and nodeid in run.get("allocation_profiles", {})
            ]
            summary += f"- {variant} {nodeid}: {peaks}\n"
    return summary


def main() -> int:  # pylint: disable=too-many-locals
    """Repeat isolated/suite processes, optionally comparing a supported registry reset."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repetitions", type=int, default=10, choices=range(1, 21))
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--include-registry-reset", action="store_true", help="Include reset variants only on interpreters exposing the compatible WeakSet")
    args = parser.parse_args()
    variants = RESET_VARIANTS if args.include_registry_reset else VARIANTS
    output = args.output.resolve()
    output.mkdir(parents=True, exist_ok=True)
    before = native_binaries()
    manifest = {
        "commit": command_output("git", "rev-parse", "HEAD").strip(),
        "git_status": command_output("git", "status", "--porcelain"),
        "python": sys.version,
        "python_implementation": platform.python_implementation(),
        "platform": platform.platform(),
        "page_size": os.sysconf("SC_PAGE_SIZE"),
        "hash_seed": os.environ.get("PYTHONHASHSEED"),
        "dont_write_bytecode": sys.dont_write_bytecode,
        "runner_image": {key: os.environ.get(key) for key in ("ImageOS", "ImageVersion", "RUNNER_ARCH", "GITHUB_RUN_ID", "GITHUB_RUN_ATTEMPT")},
        "native_binaries": before,
        "codspeed": command_output("codspeed", "--version"),
        "memtrack": command_output("codspeed-memtrack", "--version"),
        "packages": command_output(sys.executable, "-m", "pip", "freeze", "--all"),
        "libc": command_output("ldd", "--version"),
        "python_libraries": command_output("ldd", sys.executable),
        "repetitions": args.repetitions,
        "variants": variants,
        "target": TARGET,
        "memory_track_physical": True,
        "memory_capture_stack": True,
    }
    (output / "environment.json").write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    runs = []
    for repetition in range(1, args.repetitions + 1):
        # Rotate host-level order; each member starts its own runner, tracker and pytest.
        offset = (repetition - 1) % len(variants)
        for variant in variants[offset:] + variants[:offset]:
            directory = output / f"{repetition:02d}-{variant}"
            directory.mkdir()
            selection = TARGET if variant.removesuffix("-reset") == "isolated" else BENCHMARK
            pytest_command = shlex.join(
                [
                    sys.executable,
                    "-m",
                    "pytest",
                    "--codspeed",
                    "--no-cov",
                    "--log-cli-level",
                    "INFO",
                    "-p",
                    "tests.benchmark.memory_diagnostics",
                    *(["--anta-reset-task-registry"] if variant.endswith("-reset") else []),
                    f"--junitxml={directory}/junit.xml",
                    selection,
                ]
            )
            command = [
                "codspeed",
                "run",
                "--mode",
                "memory",
                "--skip-setup",
                "--skip-upload",
                "--show-full-output",
                "--profile-folder",
                str(directory / "profile"),
                "--",
                pytest_command,
            ]
            environment = {**os.environ, "ANTA_MEMORY_EVIDENCE_DIR": str(directory / "metadata")}
            print(f"Running {repetition:02d}-{variant}", flush=True)  # noqa: T201
            with (directory / "run.log").open("w", encoding="utf-8") as log:
                result = subprocess.run(command, env=environment, stdout=log, stderr=subprocess.STDOUT, check=False)  # noqa: S603
            record: dict[str, Any] = {"repetition": repetition, "variant": variant, "exit_code": result.returncode, "command": command}
            try:
                record.update(validate_session(directory, variant))
            except (OSError, ValueError, KeyError) as error:
                record["validation_error"] = str(error)
            runs.append(record)
            (output / "runs.json").write_text(json.dumps(runs, indent=2) + "\n", encoding="utf-8")
            print(json.dumps(record), flush=True)  # noqa: T201
    unchanged = before == native_binaries() and manifest["packages"] == command_output(sys.executable, "-m", "pip", "freeze", "--all")
    catalogs = {(run.get("catalog_sha256"), run.get("catalog_count"), run.get("normalized_one_day_ago_timestamps")) for run in runs}
    statuses = {json.dumps(run.get("statuses"), sort_keys=True) for run in runs}
    valid = unchanged and len(catalogs) == 1 and len(statuses) == 1 and all(run["exit_code"] == 0 and "validation_error" not in run for run in runs)
    summary = (
        f"Native memory repeatability: {'evidence complete' if valid else 'FAILED — inspect runs.json and run.log'}\n\n"
        f"Commit: {manifest['commit']}\n\n"
        f"Python: {manifest['python']}\n\n"
        f"Attempted {len(runs)} processes ({args.repetitions} repetitions of {', '.join(variants)}). Environment unchanged: {unchanged}.\n\n"
        "Raw native profiles are in each process's profile/ directory. No CodSpeed upload was performed. "
        "This summary validates evidence completeness; it does not declare memory stable or calculate a CodSpeed dashboard metric.\n"
    )
    summary += "\nPeak live requested bytes from allocations originating in the two-device sample (independent reconstruction, not RSS):\n\n"
    for variant in variants:
        peaks = [run["allocation_profile"]["peak_sample_allocations_bytes"] for run in runs if run["variant"] == variant and "allocation_profile" in run]
        summary += f"- {variant}: {peaks}\n"
    summary += case_summary(runs, variants)
    (output / "summary.md").write_text(summary, encoding="utf-8")
    if path := os.environ.get("GITHUB_STEP_SUMMARY"):
        with Path(path).open("a", encoding="utf-8") as step_summary:
            step_summary.write(summary)
    print(summary, flush=True)  # noqa: T201
    return 0 if valid else 1


if __name__ == "__main__":
    raise SystemExit(main())
