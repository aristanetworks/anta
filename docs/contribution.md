# How to contribute to ANTA

!!! warning
    Still a work in progress, feel free to reach out to the team.

## Install repository

`python setup.py install` is used to install packages that you're not going to modify yourself.
If you want to install the package and then be able to edit the code without having to re-install the package every time for the changes take effect, you can use `python setup.py develop`

you can also use `pip install -e .`
The `.` refers to the current working directory (the directory where is the setup.py file).
The `-e` flag specifies that we want to install in editable mode, which means that when we edit the files in our package we do not need to re-install the package before the changes come into effect. You will need to reload the package though!

Run these commands to install:

- The package [ANTA](https://github.com/arista-netdevops-community/network-test-automation/blob/master/anta) and its dependencies
- These [scripts](https://github.com/arista-netdevops-community/network-test-automation/blob/master/scripts) and the packages they required

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

### Clone & Install package requirements

Run these commands to install the packages indicated in the [requirements.txt](https://github.com/arista-netdevops-community/network-test-automation/blob/master/requirements.txt) file.

```shell
# Clone repository
git clone https://github.com/arista-netdevops-community/network-test-automation.git

# Enter into the repository
cd network-test-automation

# Install requirements
pip install -r requirements.txt
```

These packages are required by:

- These [scripts](https://github.com/arista-netdevops-community/network-test-automation/blob/master/scripts)
- The package [ANTA](https://github.com/arista-netdevops-community/network-test-automation/blob/master/anta)

But this will **not** install:

- The [ANTA](https://github.com/arista-netdevops-community/network-test-automation/blob/master/anta) package
- These [scripts](https://github.com/arista-netdevops-community/network-test-automation/blob/master/scripts)

Run this command to verify:

```shell
# Check ANTA has been installed in your python path
pip list | grep anta

# Check scripts are in your $PATH
check-devices-reachability.py --help

# Find where the script is located
which check-devices-reachability.py
```

### Install dev requirements

Run the following command to install all required packages for the development process.

```shell
# Install dev requirements
pip install -r requirements-dev.txt

# Install pre-commit hook
pre-commit install
```