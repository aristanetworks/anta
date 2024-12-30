<!--
  ~ Copyright (c) 2023-2024 Arista Networks, Inc.
  ~ Use of this source code is governed by the Apache License 2.0
  ~ that can be found in the LICENSE file.
  -->

## Python version

Python 3 (`>=3.9`) is required:

```bash
python --version
Python 3.11.8
```

## Install ANTA package

This installation will deploy tests collection, scripts and all their Python requirements.

The ANTA package and the cli require some packages that are not part of the Python standard library. They are indicated in the [pyproject.toml](https://github.com/aristanetworks/anta/blob/main/pyproject.toml) file, under dependencies.

### Install library from Pypi server

```bash
pip install anta
```

> [!WARNING]
> This command alone **will not** install the ANTA CLI requirements.

### Install ANTA CLI as an application with `pipx`

[`pipx`](https://pipx.pypa.io/stable/) is a tool to install and run python applications in isolated environments. If you plan to use ANTA only as a CLI tool you can use `pipx` to install it. `pipx` installs ANTA in an isolated python environment and makes it available globally.

```bash
pipx install anta[cli]
```

> [!INFO]
> Please take the time to read through the installation instructions of `pipx` before getting started.

### Install CLI from Pypi server

Alternatively, pip install with `cli` extra is enough to install the ANTA CLI.

```bash
pip install anta[cli]
```

### Install ANTA from github

```bash
pip install git+https://github.com/aristanetworks/anta.git
pip install git+https://github.com/aristanetworks/anta.git#egg=anta[cli]

# You can even specify the branch, tag or commit:
pip install git+https://github.com/aristanetworks/anta.git@<cool-feature-branch>
pip install git+https://github.com/aristanetworks/anta.git@<cool-feature-branch>#egg=anta[cli]

pip install git+https://github.com/aristanetworks/anta.git@<cool-tag>
pip install git+https://github.com/aristanetworks/anta.git@<cool-tag>#egg=anta[cli]

pip install git+https://github.com/aristanetworks/anta.git@<more-or-less-cool-hash>
pip install git+https://github.com/aristanetworks/anta.git@<more-or-less-cool-hash>#egg=anta[cli]
```

### Check installation

After installing ANTA, verify the installation with the following commands:

```bash
# Check ANTA has been installed in your python path
pip list | grep anta

# Check scripts are in your $PATH
# Path may differ but it means CLI is in your path
which anta
/home/tom/.pyenv/shims/anta
```

> [!WARNING]
> Before running the `anta --version` command, please be aware that some users have reported issues related to the `urllib3` package. If you encounter an error at this step, please refer to our [FAQ](faq.md) page for guidance on resolving it.

```bash
# Check ANTA version
anta --version
anta, version v1.2.0
```

## EOS Requirements

To get ANTA working, the targeted Arista EOS devices must have eAPI enabled. They need to use the following configuration (assuming you connect to the device using Management interface in MGMT VRF):

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

Now the switch accepts on port 443 in the MGMT VRF HTTPS requests containing a list of CLI commands.

Run these EOS commands to verify:

```eos
show management http-server
show management api http-commands
```
