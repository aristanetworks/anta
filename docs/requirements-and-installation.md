# ANTA Requirements


## Python version

Python 3 (`>=3.8` and `=<3.10`) is required:

```shell
python --version
Python 3.9.9
```

## Install ANTA package

This installation will deploy tests collection, scripts and all their Python requirements.

The ANTA package and the scripts require some packages that are not part of the Python standard library. They are indicated in the [requirements.txt](https://github.com/arista-netdevops-community/network-test-automation/blob/master/requirements.txt) file

There are several ways to installt the [ANTA](https://github.com/arista-netdevops-community/network-test-automation/blob/master/anta) and the [scripts](https://github.com/arista-netdevops-community/network-test-automation/blob/master/scripts) and the [requirements](https://github.com/arista-netdevops-community/network-test-automation/blob/master/requirements.txt). This is described below.

Run this command to install:

- The package [ANTA](https://github.com/arista-netdevops-community/network-test-automation/blob/master/anta) and its dependencies
- These [scripts](https://github.com/arista-netdevops-community/network-test-automation/blob/master/scripts) and packages they required

```shell
pip install git+https://github.com/arista-netdevops-community/network-test-automation.git
```

You can even specify the commit you would like to install.

Run these commands to verify:

```shell
# Check ANTA has been installed in your python path
pip list | grep anta

# Check scripts are in your $PATH
check-devices-reachability.py --help

# Find where the script is located
which check-devices-reachability.py
```

To update, simply run pip with `-U` option:

```shell
pip install -U git+https://github.com/arista-netdevops-community/network-test-automation.git
```

## EOS Requirements

```eos
configure
!
vrf instance MGMT
!
interface Management1
   description oob_management
   vrf MGMT
   ip address 10.73.1.105/24
!
end
```

Enable eAPI on the MGMT vrf:

```eos
configure
!
management api http-commands
   protocol https port 443
   no shutdown
   vrf MGMT
      no shutdown
!
end
```

Now the swicth accepts on port 443 in the MGMT VRF HTTPS requests containing a list of CLI commands.

Run these EOS commands to verify:

```eos
show management http-server
show management api http-commands
```
