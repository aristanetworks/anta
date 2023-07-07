# ANTA Requirements


## Python version

Python 3 (`>=3.8` and `=<3.10`) is required:

```shell
python --version
Python 3.9.9
```

## Install ANTA package

This installation will deploy tests collection, scripts and all their Python requirements.

The ANTA package and the cli require some packages that are not part of the Python standard library. They are indicated in the [pyproject.toml](https://github.com/arista-netdevops-community/anta/blob/master/pyproject.toml#L20) file


### Install from Pypi server

```shell
pip install anta
```

### Install ANTA from github


```shell
pip install git+https://github.com/arista-netdevops-community/anta.git
```

You can even specify the branch, tag or commit:

- `<anta-repository>@<cool-feature-branch>`
- `<anta-repository>@<cool-tag>`
- `<anta-repository>@<cool-hash>`

### Check installation

Run these commands to verify:

```shell
# Check ANTA has been installed in your python path
pip list | grep anta

# Check scripts are in your $PATH
# Path may differ but it means CLI is in your path
which anta
/home/tom/.pyenv/shims/anta

# Chck ANTA version
anta --version
anta, version 0.6.0
```

## EOS Requirements

To get ANTA working, your Arista EOS devices must have the following configuration (assuming you connect to the device using Management interface in MGMT VRF):

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
