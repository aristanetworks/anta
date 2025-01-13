---
anta_title: Executing Commands on Devices
---
<!--
  ~ Copyright (c) 2023-2025 Arista Networks, Inc.
  ~ Use of this source code is governed by the Apache License 2.0
  ~ that can be found in the LICENSE file.
  -->

ANTA CLI provides a set of entrypoints to facilitate remote command execution on EOS devices.

## EXEC command overview

```bash
anta exec --help
Usage: anta exec [OPTIONS] COMMAND [ARGS]...

  Execute commands to inventory devices

Options:
  --help  Show this message and exit.

Commands:
  clear-counters        Clear counter statistics on EOS devices
  collect-tech-support  Collect scheduled tech-support from EOS devices
  snapshot              Collect commands output from devices in inventory
```

## Clear interfaces counters

This command clears interface counters on EOS devices specified in your inventory.

### Command overview

```bash
Usage: anta exec clear-counters [OPTIONS]

  Clear counter statistics on EOS devices.

Options:
  -u, --username TEXT     Username to connect to EOS  [env var: ANTA_USERNAME;
                          required]
  -p, --password TEXT     Password to connect to EOS that must be provided. It
                          can be prompted using '--prompt' option.  [env var:
                          ANTA_PASSWORD]
  --enable-password TEXT  Password to access EOS Privileged EXEC mode. It can
                          be prompted using '--prompt' option. Requires '--
                          enable' option.  [env var: ANTA_ENABLE_PASSWORD]
  --enable                Some commands may require EOS Privileged EXEC mode.
                          This option tries to access this mode before sending
                          a command to the device.  [env var: ANTA_ENABLE]
  -P, --prompt            Prompt for passwords if they are not provided.  [env
                          var: ANTA_PROMPT]
  --timeout FLOAT         Global API timeout. This value will be used for all
                          devices.  [env var: ANTA_TIMEOUT; default: 30.0]
  --insecure              Disable SSH Host Key validation.  [env var:
                          ANTA_INSECURE]
  --disable-cache         Disable cache globally.  [env var:
                          ANTA_DISABLE_CACHE]
  -i, --inventory FILE    Path to the inventory YAML file.  [env var:
                          ANTA_INVENTORY; required]
  --tags TEXT             List of tags using comma as separator:
                          tag1,tag2,tag3.  [env var: ANTA_TAGS]
  --help                  Show this message and exit.
```

> [!TIP]
> `username`, `password`, `enable-password`, `enable`, `timeout` and `insecure` values are the same for all devices

### Example

```bash
anta exec clear-counters --tags SPINE
[20:19:13] INFO     Connecting to devices...                                                                                                                         utils.py:43
           INFO     Clearing counters on remote devices...                                                                                                           utils.py:46
           INFO     Cleared counters on DC1-SPINE2 (cEOSLab)                                                                                                         utils.py:41
           INFO     Cleared counters on DC2-SPINE1 (cEOSLab)                                                                                                         utils.py:41
           INFO     Cleared counters on DC1-SPINE1 (cEOSLab)                                                                                                         utils.py:41
           INFO     Cleared counters on DC2-SPINE2 (cEOSLab)
```

## Collect a set of commands

This command collects all the commands specified in a commands-list file, which can be in either `json` or `text` format.

### Command overview

```bash
Usage: anta exec snapshot [OPTIONS]

  Collect commands output from devices in inventory.

Options:
  -u, --username TEXT       Username to connect to EOS  [env var:
                            ANTA_USERNAME; required]
  -p, --password TEXT       Password to connect to EOS that must be provided.
                            It can be prompted using '--prompt' option.  [env
                            var: ANTA_PASSWORD]
  --enable-password TEXT    Password to access EOS Privileged EXEC mode. It
                            can be prompted using '--prompt' option. Requires
                            '--enable' option.  [env var:
                            ANTA_ENABLE_PASSWORD]
  --enable                  Some commands may require EOS Privileged EXEC
                            mode. This option tries to access this mode before
                            sending a command to the device.  [env var:
                            ANTA_ENABLE]
  -P, --prompt              Prompt for passwords if they are not provided.
                            [env var: ANTA_PROMPT]
  --timeout FLOAT           Global API timeout. This value will be used for
                            all devices.  [env var: ANTA_TIMEOUT; default:
                            30.0]
  --insecure                Disable SSH Host Key validation.  [env var:
                            ANTA_INSECURE]
  --disable-cache           Disable cache globally.  [env var:
                            ANTA_DISABLE_CACHE]
  -i, --inventory FILE      Path to the inventory YAML file.  [env var:
                            ANTA_INVENTORY; required]
  --tags TEXT               List of tags using comma as separator:
                            tag1,tag2,tag3.  [env var: ANTA_TAGS]
  -c, --commands-list FILE  File with list of commands to collect  [env var:
                            ANTA_EXEC_SNAPSHOT_COMMANDS_LIST; required]
  -o, --output DIRECTORY    Directory to save commands output.  [env var:
                            ANTA_EXEC_SNAPSHOT_OUTPUT; default:
                            anta_snapshot_2024-04-09_15_56_19]
  --help                    Show this message and exit.
```

> `username`, `password`, `enable-password`, `enable`, `timeout` and `insecure` values are the same for all devices

The commands-list file should follow this structure:

```yaml
---
json_format:
  - show version
text_format:
  - show bfd peers
```

### Example

```bash
anta exec snapshot --tags SPINE --commands-list ./commands.yaml --output ./
[20:25:15] INFO     Connecting to devices...                                                                                                                         utils.py:78
           INFO     Collecting commands from remote devices                                                                                                          utils.py:81
           INFO     Collected command 'show version' from device DC2-SPINE1 (cEOSLab)                                                                                utils.py:76
           INFO     Collected command 'show version' from device DC2-SPINE2 (cEOSLab)                                                                                utils.py:76
           INFO     Collected command 'show version' from device DC1-SPINE1 (cEOSLab)                                                                                utils.py:76
           INFO     Collected command 'show version' from device DC1-SPINE2 (cEOSLab)                                                                                utils.py:76
[20:25:16] INFO     Collected command 'show bfd peers' from device DC2-SPINE2 (cEOSLab)                                                                              utils.py:76
           INFO     Collected command 'show bfd peers' from device DC2-SPINE1 (cEOSLab)                                                                              utils.py:76
           INFO     Collected command 'show bfd peers' from device DC1-SPINE1 (cEOSLab)                                                                              utils.py:76
           INFO     Collected command 'show bfd peers' from device DC1-SPINE2 (cEOSLab)
```

The results of the executed commands will be stored in the output directory specified during command execution:

```bash
tree _2023-07-14_20_25_15
_2023-07-14_20_25_15
├── DC1-SPINE1
│   ├── json
│   │   └── show version.json
│   └── text
│       └── show bfd peers.log
├── DC1-SPINE2
│   ├── json
│   │   └── show version.json
│   └── text
│       └── show bfd peers.log
├── DC2-SPINE1
│   ├── json
│   │   └── show version.json
│   └── text
│       └── show bfd peers.log
└── DC2-SPINE2
    ├── json
    │   └── show version.json
    └── text
        └── show bfd peers.log

12 directories, 8 files
```

## Get Scheduled tech-support

EOS offers a feature that automatically creates a tech-support archive every hour by default. These archives are stored under `/mnt/flash/schedule/tech-support`.

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
leaf1_tech-support_2023-03-09.1337.log.gz  leaf1_tech-support_2023-03-10.0837.log.gz  leaf1_tech-support_2023-03-11.0337.log.gz
```

For Network Readiness for Use (NRFU) tests and to keep a comprehensive report of the system state before going live, ANTA provides a command-line interface that efficiently retrieves these files.

### Command overview

```bash
Usage: anta exec collect-tech-support [OPTIONS]

  Collect scheduled tech-support from EOS devices.

Options:
  -u, --username TEXT     Username to connect to EOS  [env var: ANTA_USERNAME;
                          required]
  -p, --password TEXT     Password to connect to EOS that must be provided. It
                          can be prompted using '--prompt' option.  [env var:
                          ANTA_PASSWORD]
  --enable-password TEXT  Password to access EOS Privileged EXEC mode. It can
                          be prompted using '--prompt' option. Requires '--
                          enable' option.  [env var: ANTA_ENABLE_PASSWORD]
  --enable                Some commands may require EOS Privileged EXEC mode.
                          This option tries to access this mode before sending
                          a command to the device.  [env var: ANTA_ENABLE]
  -P, --prompt            Prompt for passwords if they are not provided.  [env
                          var: ANTA_PROMPT]
  --timeout FLOAT         Global API timeout. This value will be used for all
                          devices.  [env var: ANTA_TIMEOUT; default: 30.0]
  --insecure              Disable SSH Host Key validation.  [env var:
                          ANTA_INSECURE]
  --disable-cache         Disable cache globally.  [env var:
                          ANTA_DISABLE_CACHE]
  -i, --inventory FILE    Path to the inventory YAML file.  [env var:
                          ANTA_INVENTORY; required]
  --tags TEXT             List of tags using comma as separator:
                          tag1,tag2,tag3.  [env var: ANTA_TAGS]
  -o, --output PATH       Path for test catalog  [default: ./tech-support]
  --latest INTEGER        Number of scheduled show-tech to retrieve
  --configure             [DEPRECATED] Ensure devices have 'aaa authorization
                          exec default local' configured (required for SCP on
                          EOS). THIS WILL CHANGE THE CONFIGURATION OF YOUR
                          NETWORK.
  --help                  Show this message and exit.
```

> [!TIP]
> `username`, `password`, `enable-password`, `enable`, `timeout` and `insecure` values are the same for all devices

When executed, this command fetches tech-support files and downloads them locally into a device-specific subfolder within the designated folder. You can specify the output folder with the `--output` option.

ANTA uses SCP to download files from devices and will not trust unknown SSH hosts by default. Add the SSH public keys of your devices to your `known_hosts` file or use the `anta --insecure` option to ignore SSH host keys validation.

The configuration `aaa authorization exec default` must be present on devices to be able to use SCP.

> [!CAUTION]
> **Deprecation**
>
> ANTA can automatically configure `aaa authorization exec default local` using the `anta exec collect-tech-support --configure` option but this option is deprecated and will be removed in ANTA 2.0.0.

If you require specific AAA configuration for `aaa authorization exec default`, like `aaa authorization exec default none` or `aaa authorization exec default group tacacs+`, you will need to configure it manually.

The `--latest` option allows retrieval of a specific number of the most recent tech-support files.

> [!WARNING]
> By default **all** the tech-support files present on the devices are retrieved.

### Example

```bash
anta --insecure exec collect-tech-support
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

The output folder structure is as follows:

```bash
tree tech-support/
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

Each device has its own subdirectory containing the collected tech-support files.
