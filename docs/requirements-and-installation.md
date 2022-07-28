**Table of Contents**

- [Requirements on your laptop](#requirements-on-your-laptop)
  - [Install the package ANTA and the scripts and the requirements](#install-the-package-anta-and-the-scripts-and-the-requirements)
    - [Use the `pip install` command with the Git URL](#use-the-pip-install-command-with-the-git-url)
    - [Clone the repository and install the package](#clone-the-repository-and-install-the-package)
      - [Using the `pip install .` command](#using-the-pip-install--command)
      - [Using `python setup.py` commands](#using-python-setuppy-commands)
    - [Clone the repository and install the package in editable mode](#clone-the-repository-and-install-the-package-in-editable-mode)
    - [Clone the repository and use the `pip install -r requirements.txt` command](#clone-the-repository-and-use-the-pip-install--r-requirementstxt-command)
  - [Update your PATH environment variable if it is required](#update-your-path-environment-variable-if-it-is-required)
- [Requirements on the switches](#requirements-on-the-switches)
- [Quick checks](#quick-checks)

# Requirements on your laptop

Python 3 (at least 3.3) is required:

```shell
python -V
```
## Install the package ANTA and the scripts and the requirements

[ANTA](../anta) and these [scripts](../scripts) require some packages that are not part of the Python standard library. They are indicated in the [requirements.txt](../requirements.txt) file

There are several ways to installt the [ANTA](../anta) and the [scripts](../scripts) and the [requirements](../requirements.txt). This is described below.

### Use the `pip install` command with the Git URL

Run this command to install:

- The package [ANTA](../anta) and its dependencies
- These [scripts](../scripts) and the packages they required

```shell
pip install git+https://github.com/arista-netdevops-community/network-test-automation.git
```

You can even specify the commit you would like to install.

Run these commands to verify:

```bash
pip list
check-devices-reachability.py --help
which check-devices-reachability.py
```

To update, run this command:

```shell
pip install -U git+https://github.com/arista-netdevops-community/network-test-automation.git
```

### Clone the repository and install the package

Run these commands to clone the repository and to move to the new folder:

```shell
git clone https://github.com/arista-netdevops-community/network-test-automation.git
cd network-test-automation
```

#### Using the `pip install .` command

Run this command to install:

- The package [ANTA](../anta) and its dependencies
- These [scripts](../scripts) and the packages they required

```shell
pip install .
```

Run these commands to verify:

```bash
pip list
check-devices-reachability.py --help
which check-devices-reachability.py
```

#### Using `python setup.py` commands

Run this command to build the package [ANTA](../anta):

```shell
python setup.py build
```

Run this command to install:

- The package [ANTA](../anta) and its dependencies
- These [scripts](../scripts) and the packages they required

```shell
python setup.py install
```

Run these commands to verify:

```bash
pip list
check-devices-reachability.py --help
which check-devices-reachability.py
```

### Clone the repository and install the package in editable mode

`python setup.py install` is used to install packages that you're not going to modify yourself.
If you want to install the package and then be able to edit the code without having to re-install the package every time for the changes take effect, you can use `python setup.py develop`

you can also use `pip install -e .`
The `.` refers to the current working directory (the directory where is the setup.py file).
The `-e` flag specifies that we want to install in editable mode, which means that when we edit the files in our package we do not need to re-install the package before the changes come into effect. You will need to reload the package though!

Run these commands to install:

- The package [ANTA](../anta) and its dependencies
- These [scripts](../scripts) and the packages they required

```shell
git clone https://github.com/arista-netdevops-community/network-test-automation.git
cd network-test-automation
```

```shell
python setup.py develop
```

or

```shell
pip install -e .
```

Run these commands to verify:

```bash
pip list
check-devices-reachability.py --help
which check-devices-reachability.py
```

### Clone the repository and use the `pip install -r requirements.txt` command

Run these commands to install the packages indicated in the [requirements.txt](../requirements.txt) file.

```shell
git clone https://github.com/arista-netdevops-community/network-test-automation.git
cd network-test-automation
pip install -r requirements.txt
```

These packages are required by:

- These [scripts](../scripts)
- The package [ANTA](../anta)

But this will **not** install:

- The [ANTA](../anta) package
- These [scripts](../scripts)

Run this command to verify:

```bash
pip list
```

## Update your PATH environment variable if it is required

If the path where the scripts are installed is not yet include in your PATH environment variable, please update it.

Here's an example if the scripts are installed here:

```bash
ls -l /home/arista/.local/bin/
```

Run this command to update path  to update your PATH environment variable:

```bash
echo $HOME
echo $PATH
export PATH="$HOME/.local/bin:$PATH"
echo $PATH
```

# Requirements on the switches

```eos
configure
interface Management1
   description oob_management
   vrf MGMT
   ip address 10.73.1.105/24
end
```

Enable eAPI on the MGMT vrf:

```eos
configure
management api http-commands
   protocol https port 443
   no shutdown
   vrf MGMT
      no shutdown
end
```

Now the swicth accepts on port 443 in the MGMT VRF HTTPS requests containing a list of CLI commands.

Run these EOS commands to verify:

```eos
switch1#show management http-server
```

```eos
switch1#show management api http-commands
```

# Quick checks

Execute this python script to validate:

- You can import the jsonrpclib library
- The device reachability using eAPI
Use your device credentials and IP address.

```python
import ssl
from jsonrpclib import Server
ssl._create_default_https_context = ssl._create_unverified_context
USERNAME = "arista"
PASSWORD = "aristatwfn"
ENABLE_PASSWORD = "aristatwfn"
IP = "192.168.0.12"
URL=f'https://{USERNAME}:{PASSWORD}@{IP}/command-api'
switch = Server(URL)
result=switch.runCmds(1,['show version'], 'json')
print(result[0]['uptime'])
```

Run these python commands to validate you can import and use the [ANTA](anta) package

```python
from anta.tests import *
dir()
help(verify_bgp_ipv4_unicast_state)
verify_bgp_ipv4_unicast_state(switch, ENABLE_PASSWORD)
exit()
```
