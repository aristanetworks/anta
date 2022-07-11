# devices.txt file

The file [devices.txt](devices.txt) is the devices inventory.

The devices inventory is a text file with the devices IP address or hostnames (if resolvable with DNS or your hosts file). This file has one device per ligne.

# eos-commands.yaml file

The file [eos-commands.yaml](eos-commands.yaml) is a YAML file used to indicated the list of commands output we would like to collect from devices in text or json format.

# tests.yaml file

The file [tests.yaml](tests.yaml) is a YAML file used to indicated the tests we would like to run.
It is also used to indicated the parameters used by the tests.
Each test has an identifier which is then used in the tests report.
The tests are defined in the directory [ANTA](../anta/).
