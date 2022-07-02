**Table of Contents**

- [Requirements on your laptop](#requirements-on-your-laptop)
  - [Use the `pip install` command with the git url](#use-the-pip-install-command-with-the-git-url)
  - [Clone the repository and use the `pip install .` command](#clone-the-repository-and-use-the-pip-install--command)
  - [Clone the repository and use `setup.py`](#clone-the-repository-and-use-setuppy)
  - [Clone the repository and use the `pip install -r requirements.txt` command](#clone-the-repository-and-use-the-pip-install--r-requirementstxt-command)
- [Requirements on the switches](#requirements-on-the-switches)
- [Quick checks](#quick-checks)

# Requirements on your laptop

Python 3 (at least 3.3) is required:

```shell
python -V
```

The Python package [anta](../anta) and these [scripts](../scripts) require some packages that are not part of the Python standard library:  

- They are indicated in the [requirements.txt](../requirements.txt) file
- There are several ways to install them. They are described below.

## Use the `pip install` command with the git url  

Run this command to install:

- The package [anta](../anta) and its dependencies
- The packages required by these [scripts](../scripts)  
- These [scripts](../scripts) in `/usr/local/bin/`
  
```shell
sudo pip install git+https://github.com/arista-netdevops-community/network-test-automation.git
```

Run these commands to verify:

```bash
pip list
check-devices-reachability.py --help
```

To update, run this command:

```shell
sudo pip install -U git+https://github.com/arista-netdevops-community/network-test-automation.git
```

## Clone the repository and use the `pip install .` command

Run these commands to install:

- The package [anta](../anta) and its dependencies
- The packages required by these [scripts](../scripts)  
- These [scripts](../scripts) in `/usr/local/bin/`

```shell
git clone https://github.com/arista-netdevops-community/network-test-automation.git
cd network-test-automation
sudo pip install .
```

Run these commands to verify:

```bash
pip list
check-devices-reachability.py --help
```

## Clone the repository and use `setup.py`

Run these commands to clone the repository and to move to the new folder:

```shell
git clone https://github.com/arista-netdevops-community/network-test-automation.git
cd network-test-automation
```

Run this command to build the package [anta](../anta):

```shell
python setup.py build
```

Run this command to install:

- The package [anta](../anta) and its dependencies
- The packages required by these [scripts](../scripts)  
- These [scripts](../scripts) in `/usr/local/bin/`

```shell
sudo python setup.py install
```

Run these commands to verify:

```bash
pip list
check-devices-reachability.py --help
```

## Clone the repository and use the `pip install -r requirements.txt` command

Run these commands to install the packages indicated in the [requirements.txt](../requirements.txt) file.  

```shell
git clone https://github.com/arista-netdevops-community/network-test-automation.git
cd network-test-automation
pip install -r requirements.txt
```

These packages are required by:

- These [scripts](../scripts)
- The package [anta](../anta)

But this will **not** install:

- The [anta](../anta) package
- These [scripts](../scripts) in `/usr/local/bin/`

Run this command to verify:

```bash
pip list
```

# Requirements on the switches

```text
switch1#sh run int ma1
interface Management1
   description oob_management
   vrf MGMT
   ip address 10.73.1.105/24
switch1#
```

Enable eAPI on the MGMT vrf:

```text
switch1#configure
switch1(config)#management api http-commands
switch1(config-mgmt-api-http-cmds)#protocol https port 443
switch1(config-mgmt-api-http-cmds)#no shutdown
switch1(config-mgmt-api-http-cmds)#vrf MGMT
switch1(config-mgmt-api-http-cmds-vrf-MGMT)#no shutdown
switch1(config-mgmt-api-http-cmds-vrf-MGMT)#exit
switch1(config-mgmt-api-http-cmds)#exit
switch1(config)#
```

Now the swicth accepts on port 443 in the MGMT VRF HTTPS requests containing a list of CLI commands.

Run these EOS commands to verify:

```text
switch1#sh management http-server
```

```text
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
IP = "192.168.0.12"
URL=f'https://{USERNAME}:{PASSWORD}@{IP}/command-api'
switch = Server(url)
result=switch.runCmds(1,['show version'], 'text')
print(result[0]['output'])
```

Run these python commands to validate you can import and use the [anta](anta) package

```python
>>> from anta.tests import *
>>> dir()
>>> help(verify_eos_version)
>>> import ssl
>>> from jsonrpclib import Server
>>> ssl._create_default_https_context = ssl._create_unverified_context
>>> USERNAME = "arista"
>>> PASSWORD = "aristatwfn"
>>> ENABLE_PASSWORD = "aristatwfn"
>>> IP = "192.168.0.12"
>>> URL=f'https://{USERNAME}:{PASSWORD}@{IP}/command-api'
>>> switch = Server(URL)
>>> verify_eos_version(switch, ENABLE_PASSWORD, ["4.22.1F"])
>>> exit()
```
