#!/usr/bin/env python3

"""
anta installation script
"""
from pathlib import Path

from setuptools import find_packages, setup

import anta

this_directory = Path(__file__).parent
long_description = (this_directory / "README.md").read_text()

with open('requirements.txt', encoding='utf8') as f:
    required = f.read().splitlines()

setup(
    name="anta",
    version=f"{anta.__version__}",
    python_requires=">=3.7",
    packages=find_packages(exclude=["tests", "tests.*", "scripts", "scripts.*"]),
    scripts=[
        "scripts/check-devices.py",
        "scripts/collect-eos-commands.py",
        "scripts/clear-counters.py",
        "scripts/collect-scheduled-show-tech.py",
        "scripts/evpn-blacklist-recovery.py",
        "scripts/create-devices-inventory-from-cvp.py"
    ],
    entry_points={
        'console_scripts': ['anta=anta.cli.cli:cli']
    },
    install_requires=required,
    include_package_data=True,
    url="https://github.com/arista-netdevops-community/network-test-automation",
    license=f"{anta.__license__.upper()}",
    author=f"{anta.__author__}",
    author_email=f"{anta.__email__}",
    long_description=long_description,
    long_description_content_type='text/markdown',
    classifiers=[
        'Development Status :: 4 - Beta',
        'Intended Audience :: Developers',
        'Intended Audience :: System Administrators',
        'Intended Audience :: Information Technology',
        'Topic :: System :: Networking',
        'License :: OSI Approved :: Apache Software License',
        'Programming Language :: Python',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.7',
        'Programming Language :: Python :: 3.8',
        'Programming Language :: Python :: 3.9',
        'Programming Language :: Python :: 3.10',
        'Programming Language :: Python :: 3 :: Only'
    ]
)
