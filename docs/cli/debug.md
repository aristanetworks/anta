# ANTA debug commands

ANTA CLI also provides a set of entrypoints to help building ANTA content. We call it debug and it provides different options:

- Run a command on a device from your inventory and expose a result from AntaCommand
- Run a templated command and expose the result

Both are extremly useful to build your test since you have a visual access to the output you have to test. It also helps to extract content to use for unit test as descirbed in our [contribution guide](../contribution.md).

!!! info "Use your inventory"
    Because it is based on ANTA cli, all your commands use an [ANTA inventory](overview.md) and require to get a valid one.

## Get result of an EOS command

To run a command, you can leverage `run-cmd` entrypoint with following options:

```bash
$ anta debug run-cmd --help
Usage: anta debug run-cmd [OPTIONS]

  Run arbitrary command to an EOS device and get result using eAPI

Options:
  -c, --command TEXT             Command to run on EOS using eAPI  [required]
  --ofmt [text|json]             eAPI format to use. can be text or json
  --api-version, --version TEXT  Version of the command through eAPI
  -d, --device TEXT              Device from inventory to use  [required]
  --log-level, --log TEXT        Logging level of the command
  --help                         Show this message and exit.
```

In practice, this command is very simple to use. Here is an example using `show interfaces description` with a `JSON` format:

```bash
anta debug run-cmd -c "show interfaces description" --device ptt015
run command show interfaces description on ptt015
{
    'interfaceDescriptions': {
        'Ethernet8': {'interfaceStatus': 'adminDown', 'description': '', 'lineProtocolStatus': 'down'},
        'Ethernet9': {'interfaceStatus': 'adminDown', 'description': '', 'lineProtocolStatus': 'down'},
        'Ethernet12': {'interfaceStatus': 'adminDown', 'description': '', 'lineProtocolStatus': 'down'},
    ...
}
```

## Get result of an EOS command using templates

This command allows user to provide an [`f-string`](https://realpython.com/python-f-strings/#f-strings-a-new-and-improved-way-to-format-strings-in-python) and a list of dictionary to run a command dynamically. Idea is to help building output for test using such approach.

```bash
$ anta debug run-template --help
Usage: anta debug run-template [OPTIONS]

  Run arbitrary command to an EOS device and get result using eAPI

Options:
  -t, --template TEXT            Command template to run on EOS using eAPI
  -p, --params TEXT              Command parameters to use with template. Must
                                 be a JSON string for a list of dict
                                 [required]
  --ofmt [text|json]             eAPI format to use. can be text or json
  --api-version, --version TEXT  Version of the command through eAPI
  -d, --device TEXT              Device from inventory to use  [required]
  --log-level, --log TEXT        Logging level of the command
  --help                         Show this message and exit.
```

In practice, this command is very simple to use. Here is an example using `show lldp neighbors ` with a `JSON` format for only 2 interfaces: Ethernet1 and Ethernet2

```bash
anta debug run-template \
    --params "[{"ifd": "Ethernet1"}, {"ifd":"Ethernet2"}]" \
    --template "show lldp neighbors {ifd}" \
    --device ptt015

run dynmic command show lldp neighbors {ifd} with [{"ifd": "Ethernet1"}, {"ifd":"Ethernet2"}] on ptt015
run_command = show lldp neighbors Ethernet1 ptt015
{
  "tablesLastChangeTime": 1682498936.0082116,
  "tablesAgeOuts": 0,
  "tablesInserts": 1,
  "lldpNeighbors": [],
  "tablesDeletes": 0,
  "tablesDrops": 0
}
run_command = show lldp neighbors Ethernet2 ptt015
{
  "tablesLastChangeTime": 1682498936.008321,
  "tablesAgeOuts": 0,
  "tablesInserts": 1,
  "lldpNeighbors": [],
  "tablesDeletes": 0,
  "tablesDrops": 0
}
```
