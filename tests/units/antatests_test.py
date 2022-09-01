#!/usr/bin/python
# coding: utf-8 -*-
# legacy code
# type: ignore


"""
This script is used to test the functions defined in the directory test_eos without using actual EOS devices.
It requires the installation of the package pytest that is indicated in the file requirements-dev.txt
"""

import ast
from unittest.mock import Mock
import pytest
import anta


def id_func(param):
    """
    Return ids for parametrized tests based on params
    """
    return str(param)


def runCmds(version, commands, cmd_format):
    """
    Mocked runCmds
    """
    if version == 1 and commands == ["show version"] and cmd_format == "json":
        with open(
            "mock_data/show_version_json_4.27.1.1F.out", encoding="utf8"
        ) as data_string:
            data_string = data_string.read()
            data_list = ast.literal_eval(data_string)
    elif version == 1 and commands == ["show uptime"] and cmd_format == "json":
        with open(
            "mock_data/show_uptime_json_1000000.out", encoding="utf8"
        ) as data_string:
            data_string = data_string.read()
            data_list = ast.literal_eval(data_string)
    elif version == 1 and commands == ["show ntp status"] and cmd_format == "text":
        with open(
            "mock_data/show_ntp_status_text_synchronised.out", encoding="utf8"
        ) as data_string:
            data_string = data_string.read()
            data_list = ast.literal_eval(data_string)
    return data_list


@pytest.fixture(name="mock_device")
def fixture_mock_device():
    """
    Mocked device fixture
    """
    mock_device = Mock(spec_set=["runCmds"])
    mock_device.runCmds.side_effect = runCmds
    return mock_device


@pytest.mark.skip("Legacy syntax")
@pytest.mark.parametrize(
    "versions,expected",
    [
        (["4.27.1.1F"], True),
        (["4.24.0F", "4.27.1.1F"], True),
        (["4.24.0F"], False),
        (["4.24.0F", "4.27.0F"], False),
        (None, None),
    ],
    ids=id_func,
)
def test_verify_eos_version(mock_device, versions, expected):
    """
    Legacy tests verify_eos_version
    """
    check = anta.tests.software.verify_eos_version(
        device=mock_device, versions=versions
    )
    assert check == expected


@pytest.mark.skip("Legacy syntax")
@pytest.mark.parametrize(
    "uptime,expected", [(100, True), (10000000, False), (None, None)]
)
def test_verify_uptime(mock_device, uptime, expected):
    """
    Legacy tests verify_uptime
    """
    check = anta.tests.system.verify_uptime(device=mock_device, minimum=uptime)
    assert check == expected


@pytest.mark.skip("Legacy syntax")
def test_verify_ntp(mock_device):
    """
    Legacy tests verify_ntp
    """
    check = anta.tests.system.verify_ntp(device=mock_device)
    assert check is True
