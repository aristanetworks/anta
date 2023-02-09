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

Some parameters are globally required and can be pass to anta via cli or via ENV VAR:

```bash
$ anta --username tom --password arista123 --inventory inventory.yml <anta cli>
```

Or if you prefer to set ENV VAR:

```bash
export ANTA_USERNAME=tom
export ANTA_PASSWORD=arista123
export ANTA_INVENTORY=inventory.yml

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

# Execute NRFU testing

All the NRFU testing commands are placed under `anta nrfu` and provides different rendering options:

- Table view
- JSON view
- Text view

```bash
anta nrfu
Usage: anta nrfu [OPTIONS] COMMAND [ARGS]...

  Run NRFU against inventory devices

Options:
  --help  Show this message and exit.

Commands:
  json   ANTA command to check network state with JSON result
  table  ANTA command to check network states with table result
  text   ANTA command to check network states with text result
```

All of these commands require the following input:

- A path to a catalog of tests to execute (`--catalog`)
- A list of tags if they are part of your inventory (`--tags`). List is comma separated


## NRFU with text rendering

This rendering is a pure text report for every test run on all devices. It comes with some options:

- Search (`--search`) for a regexp pattern in hostname and test name
- Option to skip (`--skip-error`) tests in error (not failure) because of a connectivity issue or unsupported command

Example output

```bash
$ anta nrfu text --tags pod1 --catalog nrfu/leaf.yml
leaf2 :: verify_mlag_status :: SUCCESS
leaf2 :: verify_mlag_interfaces :: SUCCESS
leaf2 :: verify_mlag_config_sanity :: SUCCESS
leaf2 :: verify_interface_utilization :: SUCCESS
leaf2 :: verify_interface_errors :: SUCCESS
leaf2 :: verify_interface_discards :: SUCCESS
leaf2 :: verify_interface_errdisabled :: SUCCESS
leaf2 :: verify_interfaces_status :: SUCCESS
leaf2 :: verify_storm_control_drops :: SKIPPED (verify_storm_control_drops test is not supported on cEOSLab.)
leaf2 :: verify_portchannels :: SUCCESS
leaf2 :: verify_illegal_lacp :: SUCCESS
leaf2 :: verify_loopback_count :: FAILURE (Found 3 Loopbacks when expecting 2)
leaf2 :: verify_svi :: SUCCESS
[...]
```

## NRFU with table report

This rendering print results in a nice table suppoting grep filtering. It comes with its own set of options:

- Search (`--search`) for a pattern in hostname and test name.
- Option to group (`--group-by`) and summarize results. You can group by `host` or `test`.

```bash
$ anta check table -t pod1 -c nrfu/cudi.yml
```

![anta nrfu table result](imgs/anta-nrfu-table-output.png){ loading=lazy width="800" }

You can also group per host or per test to get a summary view in case of large setup

![anta nrfu table group-by result](imgs/anta-nrfu-table-group-by-test-output.png){ loading=lazy width="800" }

## NRFU with JSON output

This command is helpful to generate a JSON and then pass it to another tool for reporting for instance. Only one option is available to save output to a file (`--output`)

```bash
$ anta check json -t pod1 -c nrfu/leaf.yml
[
  {
    "name": "leaf2",
    "test": "verify_mlag_status",
    "result": "success",
    "messages": "[]"
  },
  {
    "name": "leaf2",
    "test": "verify_mlag_interfaces",
    "result": "success",
    "messages": "[]"
  }
]
```

# Execute commands on devices

ANTA CLI also provides a set of entrypoints to execute commands remotely on EOS devices.

## Clear interfaces counters

This command clear interfaces counters on EOS devices defined in your inventory

```bash
$ anta exec clear-counters --help
Usage: anta exec clear-counters [OPTIONS]

  Clear counter statistics on EOS devices

Options:
  -t, --tags TEXT                 List of tags using comma as separator:
                                  tag1,tag2,tag3
  --log-level, --log [debug|info|warning|critical]
                                  Logging level of the command
  --help                          Show this message and exit.
```

## Collect a set of commands

This command collects all commands you defined in a catalog. It can bei either `json` or `text`.

```bash
anta exec snapshot --help
Usage: anta exec snapshot [OPTIONS]

  Collect commands output from devices in inventory

Options:
  -t, --tags TEXT                 List of tags using comma as separator:
                                  tag1,tag2,tag3
  -c, --commands-list PATH        File with list of commands to grab  [env
                                  var: ANTA_EXEC_SNAPSHOT_COMMANDS_LIST]
  -outut, -o, --output-directory PATH
                                  Path where to save commands output  [env
                                  var: ANTA_EXEC_SNAPSHOT_OUTPUT_DIRECTORY]
  --log-level, --log [debug|info|warning|critical]
                                  Logging level of the command
  --help                          Show this message and exit.
```

And structure of your catalog file should be:

```yaml
json_format:
  - show version
text_format:
  - show agent logs crash
  - show bfd peers
  - show bgp evpn
```

# Create inventory from CloudVision

In large setup, it can be useful to create your inventory based on CloudVision inventory.

```bash
anta get from-cvp
Usage: anta get from-cvp [OPTIONS]

  Build ANTA inventory from Cloudvision

Options:
  -ip, --cvp-ip TEXT              CVP IP Address
  -u, --cvp-username TEXT         CVP Username
  -p, --cvp-password TEXT         CVP Password / token
  -c, --cvp-container TEXT        Container where devices are configured
  -d, --inventory-directory PATH  Path to save inventory file
  --log-level, --log [debug|info|warning|critical]
                                  Logging level of the command
  --help                          Show this message and exit.
```

Output is an inventory with name of the container added as a tag for the host

```yaml
anta_inventory:
  hosts:
  - host: 192.168.0.13
    name: leaf2
    tags:
    - pod1
  - host: 192.168.0.15
    name: leaf4
    tags:
    - pod2
```