<!--
  ~ Copyright (c) 2023 Arista Networks, Inc.
  ~ Use of this source code is governed by the Apache License 2.0
  ~ that can be found in the LICENSE file.
  -->

# Overview of ANTA's Command-Line Interface (CLI)

ANTA provides a powerful Command-Line Interface (CLI) to perform a wide range of operations. This document provides a comprehensive overview of ANTA CLI usage and its commands.

ANTA can also be used as a Python library, allowing you to build your own tools based on it. Visit this [page](../advanced_usages/as-python-lib.md) for more details.

To start using the ANTA CLI, open your terminal and type `anta`.

## Invoking ANTA CLI

```bash
$ anta --help
--8<-- "anta_help.txt"
```

## ANTA Global Parameters

Certain parameters are globally required and can be either passed to the ANTA CLI or set as an environment variable (ENV VAR).

To pass the parameters via the CLI:

```bash
anta --username tom --password arista123 --inventory inventory.yml <anta cli>
```

To set them as ENV VAR:

```bash
export ANTA_USERNAME=tom
export ANTA_PASSWORD=arista123
export ANTA_INVENTORY=inventory.yml
```

Then, run the CLI:

```bash
anta <anta cli>
```

## ANTA Exit Codes

ANTA utilizes different exit codes to indicate the status of the test runs.

For all subcommands, ANTA will return the exit code 0, indicating a successful operation, except for the nrfu command.

For the nrfu command, ANTA uses the following exit codes:

- `Exit code 0` - All tests passed successfully.
- `Exit code 1` - Tests were run, but at least one test returned a failure.
- `Exit code 2` - Tests were run, but at least one test returned an error.
- `Exit code 3` - An internal error occurred while executing tests.

To ignore the test status, use `anta --ignore-status nrfu`, and the exit code will always be 0.

To ignore errors, use `anta --ignore-error nrfu`, and the exit code will be 0 if all tests succeeded or 1 if any test failed.

## Shell Completion

You can enable shell completion for the ANTA CLI:

=== "ZSH"

    If you use ZSH shell, add the following line in your `~/.zshrc`:

    ```bash
    eval "$(_ANTA_COMPLETE=zsh_source anta)" > /dev/null
    ```

=== "BASH"

    With bash, add the following line in your `~/.bashrc`:

    ```bash
    eval "$(_ANTA_COMPLETE=bash_source anta)" > /dev/null
    ```
