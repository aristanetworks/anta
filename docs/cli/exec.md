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

## Get Scheduled tech-support

EOS comes with a feature that generates tech-support archive every 1 hour by default and save this archive under `/mnt/flash/schedule/tech-support`

```eos
leaf1#show schedule summary
Maximum concurrent jobs  1
Prepend host name to logfile: Yes
Name                 At Time       Last        Interval       Timeout        Max        Max     Logfile Location                  Status
                                   Time         (mins)        (mins)         Log        Logs
                                                                            Files       Size
----------------- ------------- ----------- -------------- ------------- ----------- ---------- --------------------------------- ------
tech-support           now         08:37          60            30           100         -      flash:schedule/tech-support/      Success


leaf1#bash ls /mnt/flash/schedule/tech-support
leaf1_tech-support_2023-03-09.1337.log.gz  leaf1_tech-support_2023-03-10.0837.log.gz  leaf1_tech-support_2023-03-11.0337.log.gz  ...
```

As it can be useful for an NRFU to save a very complete state report before a go live, ANTA has implemented a CLI that retrieves these files very easily:

```bash
❯ anta exec collect-tech-support --help

Usage: anta exec collect-tech-support [OPTIONS]

  Collect scheduled tech-support from eos devices.

Options:
  -o, --output PATH               Path for tests catalog  [default: ./tech-
                                  support]
  -ssh, --ssh-port INTEGER        SSH port to use for connection  [default:
                                  22]
  --insecure / --secure           Disable SSH Host Key validation  [default:
                                  secure]
  --latest INTEGER                Number of scheduled show-tech to retrieve
  --configure / --not-configure   Ensure device has 'aaa authorization exec
                                  default local' configured (required for SCP)
                                  [default: not-configure]
  -t, --tags TEXT                 List of tags using coma as separator:
                                  tag1,tag2,tag3
  --log-level, --log [debug|info|warning|critical]
                                  Logging level of the command  [default:
                                  info]
  --help                          Show this message and exit.
```

When you run this command, it will retrieve tech-support files and download it locally in a folder and a subfolder per device.
You can change the default output folder with the `--output` option.
ANTA download files from the devices using SCP, all SSH Host Key devices must be trusted prior to run the command, otherwise use the `--insecure` option.
In order to use SCP with EOS, the configuration `aaa authorization exec default local` must be present on the devices.
By default, ANTA will not configure this automatically, unless `--configure` is specified.
It is possible to retrieve only the latest tech-support files using the `--latest` option.

```bash
❯ anta exec collect-tech-support --insecure
[15:27:19] INFO     Connecting to devices...
INFO     Copying '/mnt/flash/schedule/tech-support/spine1_tech-support_2023-06-09.1315.log.gz' from device spine1 to 'tech-support/spine1' locally
INFO     Copying '/mnt/flash/schedule/tech-support/leaf3_tech-support_2023-06-09.1315.log.gz' from device leaf3 to 'tech-support/leaf3' locally
INFO     Copying '/mnt/flash/schedule/tech-support/leaf1_tech-support_2023-06-09.1315.log.gz' from device leaf1 to 'tech-support/leaf1' locally
INFO     Copying '/mnt/flash/schedule/tech-support/leaf2_tech-support_2023-06-09.1315.log.gz' from device leaf2 to 'tech-support/leaf2' locally
INFO     Copying '/mnt/flash/schedule/tech-support/spine2_tech-support_2023-06-09.1315.log.gz' from device spine2 to 'tech-support/spine2' locally
INFO     Copying '/mnt/flash/schedule/tech-support/leaf4_tech-support_2023-06-09.1315.log.gz' from device leaf4 to 'tech-support/leaf4' locally
INFO     Collected 1 scheduled tech-support from leaf2
INFO     Collected 1 scheduled tech-support from spine2
INFO     Collected 1 scheduled tech-support from leaf3
INFO     Collected 1 scheduled tech-support from spine1
INFO     Collected 1 scheduled tech-support from leaf1
INFO     Collected 1 scheduled tech-support from leaf4
```

The output folder will look like this:

```bash
❯ tree tech-support/
tech-support/
├── leaf1
│   └── leaf1_tech-support_2023-06-09.1315.log.gz
├── leaf2
│   └── leaf2_tech-support_2023-06-09.1315.log.gz
├── leaf3
│   └── leaf3_tech-support_2023-06-09.1315.log.gz
├── leaf4
│   └── leaf4_tech-support_2023-06-09.1315.log.gz
├── spine1
│   └── spine1_tech-support_2023-06-09.1315.log.gz
└── spine2
    └── spine2_tech-support_2023-06-09.1315.log.gz

6 directories, 6 files
```
