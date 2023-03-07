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

This command collects all commands you defined in a catalog. It can be either `json` or `text`.

```bash
$ anta exec snapshot --help
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