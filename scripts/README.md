# [check-devices-reachability.py](check-devices-reachability.py) file

The python script [check-devices-reachability.py](check-devices-reachability.py) is used to test devices reachability with eAPI.

The python script [check-devices-reachability.py](check-devices-reachability.py) takes as input a text file with the devices IP address or hostnames (when resolvable), and tests devices reachability with eAPI and prints the unreachable devices on the console.

# [clear-counters.py](clear-counters.py) file

The python script [clear-counters.py](clear-counters.py) is used to clear counters on EOS devices.

It takes as input a text file with the devices IP address or hostnames (when resolvable) and clears counters on these devices.

# [collect-eos-commands.py](collect-eos-commands.py) file

The python script [collect-eos-commands.py](collect-eos-commands.py) is used to collect commands output from EOS devices.

The python script [collect-eos-commands.py](collect-eos-commands.py):

- Takes as input:
  - A text file with the devices IP address or hostnames (when resolvable).
  - A YAML file with the list of EOS commands we would like to collect in text or JSON format.
- Collects the EOS commands from the devices, and saves the result in files.

# [check-devices.py](check-devices.py) file

The python script [check-devices.py](check-devices.py) is used to run tests on devices.

The python script [check-devices.py](check-devices.py):

- Imports the python functions defined in the directory [anta](anta).
  - These functions defined the tests.
- Takes as input:
  - A text file with the devices IP address or hostnames (when resolvable).
  - A YAML file with the list of the tests we would like to use and their parameters.
- Runs the tests, and prints the result on the console and saves the result in a file.

# [evpn-blacklist-recovery.py](evpn-blacklist-recovery.py) file

The python script [evpn-blacklist-recovery.py](evpn-blacklist-recovery.py) is used to clear on EOS devices the list of MAC addresses which are blacklisted in EVPN.

The python script [evpn-blacklist-recovery.py](evpn-blacklist-recovery.py) takes as input a text file with the devices IP address or hostnames (when resolvable) and run the command `clear bgp evpn host-flap` on the EOS devices.

# [collect-sheduled-show-tech.py](collect-sheduled-show-tech.py) file

The python script [collect-sheduled-show-tech.py](collect-sheduled-show-tech.py) is used to collect the scheduled show tech-support files from EOS devices.

It takes as input a text file with the devices IP address or hostname and collects the show tech-support files from these devices and save the files locally.
