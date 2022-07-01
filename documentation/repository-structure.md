**Table of Contents**
- [devices.txt file](#devicestxt-file)
- [eos-commands.yaml file](#eos-commandsyaml-file)
- [tests.yaml file](#testsyaml-file)
- [anta directory](#anta-directory)
- [generate_functions_documentation.py file](#generate_functions_documentationpy-file)
- [documentation directory](#documentation-directory)
- [check_devices_reachability.py file](#check_devices_reachabilitypy-file)
- [clear_counters.py file](#clear_counterspy-file)
- [collect_eos_commands.py file](#collect_eos_commandspy-file)
- [check_devices.py file](#check_devicespy-file)
- [evpn_blacklist_recovery.py file](#evpn_blacklist_recoverypy-file)
- [collect_sheduled_show_tech.py file](#collect_sheduled_show_techpy-file)
- [demo directory](#demo-directory)
- [unit_test.py file](#unit_testpy-file)
- [mock_data directory](#mock_data-directory)
# [devices.txt](devices.txt) file

The file [devices.txt](../examples/devices.txt) is the devices inventory.

The devices inventory is a text file with the devices IP address or hostnames (if resolvable with DNS or your hosts file). This file has one device per ligne.

# [eos-commands.yaml](../examples/eos-commands.yaml) file

The file [eos-commands.yaml](../examples/eos-commands.yaml) is a YAML file used to indicated the list of commands output we would like to collect from devices in text or json format.

# [tests.yaml](../examples/tests.yaml) file

The file [tests.yaml](../examples/tests.yaml) is a YAML file used to indicated the tests we would like to run. It is also used to indicated the parameters used by the tests.
Each test has an identifier which is then used in the tests report.
The tests are defined in the directory [anta](../anta/).

# [anta](../anta/) directory

The directory [anta](../anta/) is a python package.

The python functions to test EOS devices are defined the python module [tests.py](../anta/tests.py) in the python package [anta](../anta/).

# [generate_functions_documentation.py](../documentation/generate-functions-documentation.py) file

The script [generate_functions_documentation.py](../documentation/generate-functions-documentation.py) file is used to generate the functions documentation in markdown format.
It requires the installation of the package `lazydocs` that is indicated in the file [requirements-dev.txt](../requirements-dev.txt)

The functions to test EOS devices are coded in the python module [tests.py](nta/tests.py) in the python package [nta](nta).
These functions have docstrings.
The docstrings are used by the script [generate_functions_documentation.py](generate_functions_documentation.py) to generate the functions documentation in markdown format in the directory [documentation](documentation).

Please refer to the [contribution guide](CONTRIBUTING.md) to get instructions.

# [documentation](documentation) directory

The [documentation](documentation) directory has the tests documentation in markdown format:
* [overview.md](documentation/overview.md) file
* [nta.tests.md](documentation/nta.tests.md) file

# [check_devices_reachability.py](check_devices_reachability.py) file

The python script [check_devices_reachability.py](check_devices_reachability.py) is used to test devices reachability with eAPI.

The python script [check_devices_reachability.py](check_devices_reachability.py) takes as input a text file with the devices IP address or hostnames (when resolvable), and tests devices reachability with eAPI and prints the unreachable devices on the console.

# [clear_counters.py](clear_counters.py) file

The python script [clear_counters.py](clear_counters.py) is used to clear counters on EOS devices.

It takes as input a text file with the devices IP address or hostnames (when resolvable) and clears counters on these devices.

# [collect_eos_commands.py](collect_eos_commands.py) file

The python script [collect_eos_commands.py](collect_eos_commands.py) is used to collect commands output from EOS devices.

The python script [collect_eos_commands.py](collect_eos_commands.py):
* Takes as input:
  * A text file with the devices IP address or hostnames (when resolvable).
  * A YAML file with the list of EOS commands we would like to collect in text or JSON format.
* Collects the EOS commands from the devices, and saves the result in files.

# [check_devices.py](check_devices.py) file

The python script [check_devices.py](check_devices.py) is used to run tests on devices.

The python script [check_devices.py](check_devices.py):
* Imports the python functions defined in the directory [nta](nta).
  * These functions defined the tests.
* Takes as input:
  * A text file with the devices IP address or hostnames (when resolvable).
  * A YAML file with the list of the tests we would like to use and their parameters.
* Runs the tests, and prints the result on the console and saves the result in a file.

# [evpn_blacklist_recovery.py](evpn_blacklist_recovery.py) file

The python script [evpn_blacklist_recovery.py](evpn_blacklist_recovery.py) is used to clear on EOS devices the list of MAC addresses which are blacklisted in EVPN.

The python script [evpn_blacklist_recovery.py](evpn_blacklist_recovery.py) takes as input a text file with the devices IP address or hostnames (when resolvable) and run the command `clear bgp evpn host-flap` on the EOS devices.

# [collect_sheduled_show_tech.py](collect_sheduled_show_tech.py) file

The python script [collect_sheduled_show_tech.py](collect_sheduled_show_tech.py) is used to collect the scheduled show tech-support files from EOS devices.

It takes as input a text file with the devices IP address or hostname and collects the show tech-support files from these devices and save the files locally.
# [demo](demo) directory

The [demo](demo) directory shows a demo of this repository with an ATD (Arista Test Drive) instance.
# [unit_test.py](unit_test.py) file

The python script [unit_test.py](unit_test.py) is used to test the functions defined in the directory [test_eos](test_eos) without using actual EOS devices.
It requires the installation of the package `pytest` that is indicated in the file [requirements-dev.txt](requirements-dev.txt)

# [mock_data](mock_data) directory

The [mock_data](mock_data) directory has data used by the python script [unit_test.py](unit_test.py) to test the functions defined in the directory [test_eos](test_eos) without using actual EOS devices.
