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

!!! warning "Report correctness is still under development"
    Repeated invocations of a test can receive identical JUnit testcase identities, even when their inputs and outcomes differ. CI consumers such as GitLab can silently ignore duplicate entries. Testcase identities are also not guaranteed to remain stable across runs. Compare the artifact with ANTA's JSON results when evaluating this feature; do not use it as the sole source of truth for CI test results.

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

## Current limitations

- The duplicate-name hash uses result metadata rather than the original test inputs. Identical metadata can produce identical names, and changes to the surrounding results can change testcase names between runs.
- An `UNSET` result is currently emitted without a failure, error or skipped element and excluded from the root test total. Consumers can display it as passing, and suite and root totals can disagree.
- The CLI's `--hide` option removes matching results from the XML artifact.
- Per-test timing is unavailable and reported as zero. Suite timestamps reflect report generation time.

These limitations remain under review while the feature is experimental.

## Python API

::: anta.experimental.reporter.junit_reporter.JUnitReporter
