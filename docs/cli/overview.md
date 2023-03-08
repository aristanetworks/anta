# CLI overview

ANTA comes with a CLI to execute all the supported actions. If you want to build your own tool, you should visit [this page](../usage-as-python-lib/) where we describe how to use ANTA as a python library

To invoke anta, open a shell window and then enter `anta`

```bash
$ anta
Usage: anta [OPTIONS] COMMAND [ARGS]...

  Arista Network Test CLI

Options:
  --username TEXT         Username to connect to EOS  [env var: ANTA_USERNAME]
  --password TEXT         Password to connect to EOS  [env var: ANTA_PASSWORD]
  --timeout INTEGER       Connection timeout (default 5)  [env var: ANTA_TIMEOUT]
  --enable-password TEXT  Enable password if required to connect  [env var: ANTA_ENABLE_PASSWORD]
  -i, --inventory PATH    Path to your inventory file  [env var: ANTA_INVENTORY]
  --timeout INTEGER       Connection timeout (default 5)  [env var: ANTA_TIMEOUT]
  --help                  Show this message and exit.

Commands:
  exec  Execute commands to inventory devices
  get   Get data from/to ANTA
  nrfu  Run NRFU against inventory devices
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
    eval "$(_ANTA_COMPLETE=bash_source anta)"
    ```
