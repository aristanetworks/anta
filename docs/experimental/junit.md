---
title: Experimental JUnit Reporting
hide:
  - tags
tags:
  - Experimental
  - Reports
  - NRFU
  - Python
---

<!--
  ~ Copyright (c) 2026 Arista Networks, Inc.
  ~ Use of this source code is governed by the Apache License 2.0
  ~ that can be found in the LICENSE file.
  -->

The experimental JUnit reporter writes NRFU results to an XML file, grouping testcases by device. The CLI command and the Python reporter follow the [experimental compatibility policy](index.md).

!!! warning "Testcase identity is still experimental"
    If repeated invocations produce identical JUnit testcase identities, export fails rather than writing a report that consumers could silently collapse. Give repeated invocations distinct `result_overwrite.description` values to distinguish them. Testcase identities are not guaranteed to remain stable across runs; stable invocation identity is deferred to a follow-up change. Compare the artifact with ANTA's JSON results when evaluating this feature.

## CLI usage

Install ANTA with its [CLI extra](../requirements-and-installation.md), then run:

```bash
anta nrfu --inventory inventory.yaml --catalog tests.yaml junit --junit-output reports/anta-junit.xml
```

Provide authentication through the usual [NRFU options or environment variables](../cli/overview.md#anta-environment-variables). The command prints an experimental-feature warning before running the tests, saves the XML report, and uses the usual [ANTA exit codes](../cli/overview.md#anta-exit-codes). The output path is required; missing parent directories are created.

```text
--8<-- "anta_nrfu_junit_help.txt"
```

Common NRFU device, test and tag filters also apply to this command. `--dry-run` prints the experimental warning and performs the normal NRFU dry run without writing a report.

The shared NRFU `--hide` option is ignored for JUnit reporting, and a warning is printed when it is supplied. The XML includes all results from the selected run so that failures and errors cannot be hidden from report consumers. Other report formats retain their usual `--hide` behavior.

## Python usage

Pass a populated `ResultManager` to `JUnitReporter.generate()`:

```python
from pathlib import Path

from anta.experimental.reporter.junit_reporter import JUnitReporter
from anta.result_manager import ResultManager
from anta.result_manager.models import AntaTestStatus, TestResult

results = ResultManager()
results.add(
    TestResult(
        name="leaf1",
        test="VerifyUptime",
        categories=["system"],
        description="Verifies the device uptime.",
        result=AntaTestStatus.SUCCESS,
    )
)

JUnitReporter.generate(results=results, output_path=Path("reports/anta-junit.xml"))
```

Python imports and direct reporter calls do not print the CLI warning.

## XML text handling

Characters that XML 1.0 cannot represent are written as visible escape sequences, such as `\x00` for a null character and `\ud800` for an unpaired surrogate. This applies to result text, device and testcase names, descriptions, and catalog filenames. Valid Unicode characters are preserved, and XML markup characters are escaped by the XML serializer. The original results are unchanged.

## Unfinished results

JUnit has no separate `UNSET` outcome. The reporter emits an ANTA `UNSET` result as an `<error type="UnsetResult">` with the message "ANTA result is UNSET: no final status was recorded", preserving any result messages as error details. It counts toward both the test and error totals at suite and report level. This avoids presenting an unfinished result as passing or implying that it was deliberately skipped. The original ANTA status and the usual CLI exit-code behavior are unchanged.

## Current limitations

- The duplicate-name hash uses result metadata rather than the original test inputs. Identical metadata can produce identical names, and changes to the surrounding results can change testcase names between runs. The reporter checks the final XML classname/name pairs and raises `ValueError` on duplicates before writing the file. The CLI prints the reason and exits with a usage error; any existing output file is left unchanged.
- Per-test durations are intentionally not measured: command caching and reuse prevent meaningful attribution of command collection time to individual tests, while timing the test function alone provides little useful information. Testcase, suite and report durations are reported as zero for JUnit compatibility; these are placeholders, not measured durations. Suite timestamps reflect report generation time.

These limitations remain under review while the feature is experimental.

## Python API

::: anta.experimental.reporter.junit_reporter.JUnitReporter
