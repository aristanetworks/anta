---
anta_title: Overview of ANTA's Command-Line Interface (CLI)
---
<!--
  ~ Copyright (c) 2023-2025 Arista Networks, Inc.
  ~ Use of this source code is governed by the Apache License 2.0
  ~ that can be found in the LICENSE file.
  -->

ANTA provides a powerful Command-Line Interface (CLI) to perform a wide range of operations. This document provides a comprehensive overview of ANTA CLI usage and its commands.

ANTA can also be used as a Python library, allowing you to build your own tools based on it. Visit this [page](../advanced_usages/as-python-lib.md) for more details.

To start using the ANTA CLI, open your terminal and type `anta`.

## Invoking ANTA CLI

```bash
$ anta --help
--8<-- "anta_help.txt"
```

## ANTA environment variables

Certain parameters are required and can be either passed to the ANTA CLI or set as an environment variable (ENV VAR).

To pass the parameters via the CLI:

```bash
anta nrfu -u admin -p arista123 -i inventory.yaml -c tests.yaml
```

To set them as environment variables:

```bash
export ANTA_USERNAME=admin
export ANTA_PASSWORD=arista123
export ANTA_INVENTORY=inventory.yml
export ANTA_CATALOG=tests.yml
```

Then, run the CLI without options:

```bash
anta nrfu
```

> [!NOTE]
> All environment variables may not be needed for every commands.
>
> Refer to `<command> --help` for the comprehensive environment variables names.

Below are the environment variables usable with the `anta nrfu` command:

| Variable Name | Purpose | Required |
| ------------- | ------- |----------|
| ANTA_USERNAME | The username to use in the inventory to connect to devices. |  Yes  |
| ANTA_PASSWORD | The password to use in the inventory to connect to devices. |  Yes  |
| ANTA_INVENTORY | The path to the inventory file. |  Yes  |
| ANTA_CATALOG | The path to the catalog file. |  Yes  |
| ANTA_PROMPT | The value to pass to the prompt for password is password is not provided |  No  |
| ANTA_INSECURE | Whether or not using insecure mode when connecting to the EOS devices HTTP API. |  No  |
| ANTA_DISABLE_CACHE | A variable to disable caching for all ANTA tests (enabled by default). |  No  |
| ANTA_ENABLE | Whether it is necessary to go to enable mode on devices. |  No  |
| ANTA_ENABLE_PASSWORD | The optional enable password, when this variable is set, ANTA_ENABLE or `--enable` is required. |  No  |

> [!NOTE]
> Caching can be disabled with the global parameter `--disable-cache`. For more details about how caching is implemented in ANTA, please refer to [Caching in ANTA](../advanced_usages/caching.md).

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
