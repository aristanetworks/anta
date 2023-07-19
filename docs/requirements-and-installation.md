# ANTA Requirements

## Python version

Python 3 (`>=3.8`) is required:

```bash
python --version
Python 3.9.9
```

## Install ANTA package

This installation will deploy tests collection, scripts and all their Python requirements.

The ANTA package and the cli require some packages that are not part of the Python standard library. They are indicated in the [pyproject.toml](https://github.com/arista-netdevops-community/anta/blob/main/pyproject.toml) file, under dependencies.


### Install from Pypi server

```bash
pip install anta
```

### Install ANTA from github


```bash
pip install git+https://github.com/arista-netdevops-community/anta.git

# You can even specify the branch, tag or commit:
pip install git+https://github.com/arista-netdevops-community/anta.git@<cool-feature-branch>
pip install git+https://github.com/arista-netdevops-community/anta.git@<cool-tag>
pip install git+https://github.com/arista-netdevops-community/anta.git@<more-or-less-cool-hash>
```


### Check installation

Run these commands to verify:

```bash
# Check ANTA has been installed in your python path
pip list | grep anta

# Check scripts are in your $PATH
# Path may differ but it means CLI is in your path
which anta
/home/tom/.pyenv/shims/anta

# Chck ANTA version
anta --version
anta, version v0.6.0
```

## EOS Requirements

To get ANTA working, the targetted Arista EOS devices must have the following configuration (assuming you connect to the device using Management interface in MGMT VRF):

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
