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

## ANTA Parameters as environement variables

Certain parameters are required and can be either passed to the ANTA CLI or set as an environment variable (ENV VAR).

To pass the parameters via the CLI:

```bash
anta nrfu --username tom --password arista123 --inventory inventory.yml <anta cli>
```

To set them as ENV VAR:

```bash
export ANTA_USERNAME=tom
export ANTA_PASSWORD=arista123
export ANTA_INVENTORY=inventory.yml
```

Then, run the CLI:

```bash
anta nrfu <anta cli>
```
!!! info
    Caching can be disabled with the global parameter `--disable-cache`. For more details about how caching is implemented in ANTA, please refer to [Caching in ANTA](../advanced_usages/caching.md).

### List of available environment variables

!!! note
    All environement variables may not be needed for every commands.

| Variable Name | Purpose |
| ------------- | ------- |
| ANTA_USERNAME | The username to use in the inventory to connect to devices. |
| ANTA_PASSWORD | The password to use in the inventory to connect to devices. |
| ANTA_INVENTORY | The path to the inventory file. |
| ANTA_CATALOG | The path to the catalog file. |
| ANTA_PROMPT | The value to pass to the prompt for password is password is not provided |
| ANTA_INSECURE | Whether or not using insecure mode when connecting to the EOS devices HTTP API. |
| ANTA_DISABLE_CACHE | A variable to disable caching for all ANTA tests (enabled by default). |
| ANTA_ENABLE | Whether it is necessary to go to enable mode on devices. |
| ANTA_ENABLE_PASSWORD | The optional enable password, when this variable is set, ANTA_ENABLE or `--enable` is required. |

## ANTA Exit Codes

ANTA CLI utilizes the following exit codes:

- `Exit code 0` - All tests passed successfully.
- `Exit code 1` - An internal error occurred while executing ANTA.
- `Exit code 2` - A usage error was raised.
- `Exit code 3` - Tests were run, but at least one test returned an error.
- `Exit code 4` - Tests were run, but at least one test returned a failure.

To ignore the test status, use `anta nrfu --ignore-status`, and the exit code will always be 0.

To ignore errors, use `anta nrfu --ignore-error`, and the exit code will be 0 if all tests succeeded or 1 if any test failed.

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
