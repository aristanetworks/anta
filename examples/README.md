# ANTA Example files

This section provides some examples about how to use ANTA as listed in [the documentation](https://anta.arista.com).

## Device Inventory

- Filename: [`inventory.yaml`](./inventory.yaml)

The file [inventory.yaml](inventory.yaml) is an example of [device inventory](https://anta.arista.com/stable/usage-inventory-catalog/#create-an-inventory-file).

## Test Catalog

- Filename: [`tests.yaml`](./tests.yaml)

The file [tests.yaml](tests.yaml) is an example of a [test catalog](https://anta.arista.com/stable/usage-inventory-catalog/#test-catalog).
This file should contain all the tests implemented in [anta.tests](../anta/tests) with arbitrary parameters.

## Commands to get from snapshot

- Filename: [`eos-commands.yaml file`](./eos-commands.yaml)

The file [eos-commands.yaml](eos-commands.yaml) is an example of input given with the `--commands-list` option to the [anta exec snapshot](https://anta.arista.com/stable/cli/exec/#collect-a-set-of-commands) command.

## ANTA runner in Python

- Filename: [`anta_runner.py`](./anta_runner.py)

The file is an example demonstrating how to run ANTA using a Python script.

## ANTA template for results rendering

- Filename: [`template.j2`](./template.j2)

This file is a simple Jinja2 file to customize ANTA CLI output as documented in [cli documentation](https://anta.arista.com/stable/cli/nrfu/#performing-nrfu-with-custom-reports).

## Merge multiple catalogs

- Filename: [`merge_catalogs.py`](./merge_catalogs.py)

This file is an example demonstrating how to merge multiple catalogs into a single catalog and save it to a file, as documented in [usage test catalog](https://anta.arista.com/stable/usage-inventory-catalog/#example-script-to-merge-catalogs).

## Run multiple commands

- Filename: [`run_eos_commands.py`](./run_eos_commands.py)

This file is an example demonstrating how to run multiple commands on multiple devices, as documented in [advanced usages](https://anta.arista.com/stable/advanced_usages/as-python-lib/#run-eos-commands).

## Parse ANTA inventory file

- Filename: [`parse_anta_inventory_file.py`](./parse_anta_inventory_file.py)

This file is an example demonstrating how to parse an ANTA inventory file, as documented in [advanced usages](https://anta.arista.com/stable/advanced_usages/as-python-lib/#parse-anta-inventory-file).