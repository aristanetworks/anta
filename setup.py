#!/usr/bin/python
# coding: utf-8 -*-

from setuptools import setup
import eos_testing

with open("README.md", "r") as fh:
    long_description = fh.read()

with open('requirements.txt') as f:
    required = f.read().splitlines()

setup(
    name="eos_testing",
    version="{}".format(eos_testing.__version__),
    python_requires=">=3.8",
    packages=['eos_testing'],
    scripts=["bin/check-devices-reachability.py", "bin/check-devices.py", "bin/clear_counters.py", "bin/collect-eos-commands.py"],
    install_requires=required,
    include_package_data=True,
    url="https://github.com/arista-netdevops-community/network_tests_automation",
    license="APACHE",
    author="{}".format(eos_testing.__author__),
    author_email="{}".format(eos_testing.__email__),
    description=long_description,
)