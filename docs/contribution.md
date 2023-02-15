# How to contribute to ANTA

!!! note "Work in Progress"
    Still a work in progress, feel free to reach out to the team.

## Install repository

Run these commands to install:

- The package [ANTA](https://github.com/arista-netdevops-community/network-test-automation/blob/master/anta) and its dependencies
- ANTA cli executable.

```shell
# Clone repository
git clone https://github.com/arista-netdevops-community/network-test-automation.git
cd network-test-automation

# Install module in editable mode
pip install -e .
```

Run these commands to verify:

```bash
# Check python installation
$ pip list

# Check version using cli
$ anta --version
anta, version 0.4.0
```

### Install development requirements

Run pip to install anta and its developement tools.

```
pip install 'anta[dev]'
```

> This command has to be done after you install repository with commands provided in previous section.
