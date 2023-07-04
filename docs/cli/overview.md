# CLI overview

ANTA comes with a CLI to execute all the supported actions. If you want to build your own tool, you should visit [this page](../advanced_usages/as-python-lib.md) where we describe how to use ANTA as a python library

To invoke anta, open a shell window and then enter `anta`

```bash
Usage: anta [OPTIONS] COMMAND [ARGS]...

  Arista Network Test CLI

Options:
  --version                       Show the version and exit.
  --username TEXT                 Username to connect to EOS  [env var:
                                  ANTA_USERNAME; required]
  --password TEXT                 Password to connect to EOS  [env var:
                                  ANTA_PASSWORD; required]
  --timeout INTEGER               Global connection timeout  [env var:
                                  ANTA_TIMEOUT; default: 5]
  --insecure / --secure           Disable SSH Host Key validation  [env var:
                                  ANTA_INSECURE; default: secure]
  --enable-password TEXT          Enable password if required to connect  [env
                                  var: ANTA_ENABLE_PASSWORD]
  -i, --inventory FILE            Path to the inventory YAML file  [env var:
                                  ANTA_INVENTORY; required]
  --log-level, --log [CRITICAL|ERROR|WARNING|INFO|DEBUG]
                                  ANTA logging level  [env var:
                                  ANTA_LOG_LEVEL; default: INFO]
  --ignore-status                 Always exit with success  [env var:
                                  ANTA_IGNORE_STATUS]
  --ignore-error                  Only report failures and not errors  [env
                                  var: ANTA_IGNORE_ERROR]
  --help                          Show this message and exit.

Commands:
  debug  Debug commands for building ANTA
  exec   Execute commands to inventory devices
  get    Get data from/to ANTA
  nrfu   Run NRFU against inventory devices
```

## ANTA parameters

Some parameters are globally required and can be passed to anta via cli or via ENV VAR:

```bash
$ anta --username tom --password arista123 --inventory inventory.yml <anta cli>
```

Or if you prefer to set ENV VAR:

```bash
# Save information for anta cli
$ export ANTA_USERNAME=tom
$ export ANTA_PASSWORD=arista123
$ export ANTA_INVENTORY=inventory.yml

# Run cli
$ anta <anta cli>
```

## ANTA ExitCodes

For all subcommands except nrfu, `anta` wil return with the exit code 0.

For the nrfu commands, `anta` is using the following exit codes:

* Exit code 0 - All tests passed successfully.
* Exit code 1 - Tests were run but at least one test returned a failure.
* Exit code 2 - Tests were run but at least one test returned an error.
* Exit code 3 - Internal error happened while executing tests (not used today).

It is possible to ignore the status when running the nrfu command by using `anta --ignore-status nrfu` and in that case the exit code will always be 0.

It is possible to ignore errors when running the nrfu command by using `anta --ignore-error nrfu` and in that case the exit code will either be 0 if all tests succeeded or 1 if any test failed.

## Shell Completion

You can enable shell completion for the anta cli:

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
