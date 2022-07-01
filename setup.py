#!/usr/bin/python
# coding: utf-8 -*-

from setuptools import setup
from pathlib import Path
import anta

this_directory = Path(__file__).parent
long_description = (this_directory / "README.md").read_text()

with open('requirements.txt') as f:
    required = f.read().splitlines()

setup(
    name="anta",
    version="{}".format(anta.__version__),
    python_requires=">=3.8",
    packages=['anta'],
    scripts=[
        "scripts/check_devices_reachability.py", 
        "scripts/check_devices.py", 
        "scripts/collect_eos_commands.py"
    ],
    install_requires=required,
    include_package_data=True,
    url="https://github.com/to-be-set-after",
    license="APACHE",
    author="{}".format(anta.__author__),
    author_email="{}".format(anta.__email__),
    long_description=long_description,
    long_description_content_type='text/markdown',
    classifiers=[
        'Development Status :: 4 - Beta',
        'Intended Audience :: Developers',
        'Intended Audience :: System Administrators',
        'Intended Audience :: Information Technology',
        'Topic :: System :: Software Distribution',
        'Topic :: Terminals',
        'Topic :: Utilities',
        'License :: OSI Approved :: Apache Software License',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.8',
        'Programming Language :: Python :: 3.9',
        'Programming Language :: Python :: 3.10',
        'Programming Language :: Python :: 3 :: Only',
        'Programming Language :: Python :: Implementation :: PyPy',
    ]
)
