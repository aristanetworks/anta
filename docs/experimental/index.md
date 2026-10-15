---
title: Experimental Features
hide:
  - tags
tags:
  - Experimental
---

<!--
  ~ Copyright (c) 2026 Arista Networks, Inc.
  ~ Use of this source code is governed by the Apache License 2.0
  ~ that can be found in the LICENSE file.
  -->

Experimental features let users try new ANTA functionality and provide feedback before it becomes stable.

!!! warning "Experimental compatibility"
    Experimental Python APIs, CLI options, behavior and output formats may change or be removed between releases, including minor and patch releases. They are outside ANTA's stable API compatibility guarantees. Review the feature's documented limitations before using its output in automation.

## Python modules

Experimental Python features live under `anta.experimental`. Import classes from their implementation modules, for example:

```python
from anta.experimental.reporter.junit_reporter import JUnitReporter
```

The experimental reporter modules can be used without installing the CLI extra.

## CLI commands

Experimental CLI implementations live under `anta.experimental.cli`. Commands are exposed in the relevant ANTA command group and marked `[Experimental]` in their help text.

Executing an experimental command prints a warning before running the feature. The warning also appears for dry runs. Requesting `--help` displays the experimental label without running the command.

## Available features

- [JUnit reporting](junit.md): generate a JUnit XML artifact from NRFU test results.
