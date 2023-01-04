#!/usr/bin/python
# coding: utf-8 -*-
# pylint: skip-file

"""
Tests for anta.tests.configuration.py
"""
import asyncio
from typing import Any, Dict, List
from unittest.mock import MagicMock

import pytest
from jsonrpclib.jsonrpc import AppError

from anta.tests.configuration import (verify_running_config_diffs,
                                      verify_zerotouch)


@pytest.mark.parametrize(
    "return_value, side_effect, expected_result, expected_messages",
    [
        pytest.param({"mode": "disabled"}, None, "success", [], id="success"),
        pytest.param(
            {"mode": "enabled"},
            None,
            "failure",
            ["ZTP is NOT disabled"],
            id="failure",
        ),
        # Hmmmm both errors do not return the same string ...
        pytest.param(
            None, AppError("dummy"), "error", ["AppError: dummy"], id="JSON RPC error"
        ),
        pytest.param(
            None, KeyError("dummy"), "error", ["KeyError: 'dummy'"], id="Key error"
        ),
    ],
)
def test_verify_zerotouch(
    mocked_device: MagicMock,
    return_value: List[Dict[str, str]],
    side_effect: Any,
    expected_result: str,
    expected_messages: List[str],
) -> None:
    mocked_device.session.cli.return_value = return_value
    mocked_device.session.cli.side_effect = side_effect
    result = asyncio.run(verify_zerotouch(mocked_device))

    assert result.test == "verify_zerotouch"
    assert str(result.name) == "42.42.42.42"
    assert result.result == expected_result
    assert result.messages == expected_messages


@pytest.mark.parametrize(
    "return_value, side_effect, remove_enable_password, expected_result, expected_messages",
    [
        pytest.param(
            [None, []],
            None,
            False,
            "success",
            [],
            id="success",
        ),
        pytest.param(
            [None, "blah\nblah"],
            None,
            False,
            "failure",
            ["blah", "blah"],
            id="failure",
        ),
        # Hmmmm both errors do not return the same string ...
        pytest.param(
            None,
            AppError("dummy"),
            False,
            "error",
            ["AppError: dummy"],
            id="JSON RPC error",
        ),
        pytest.param(
            None,
            KeyError("dummy"),
            False,
            "error",
            ["KeyError: 'dummy'"],
            id="Key error",
        ),
        pytest.param(
            None,
            None,
            True,
            "error",
            [
                "ValueError: verify_running_config_diffs requires `enable_password` to be set"
            ],
            id="Missing enable password",
        ),
    ],
)
def test_verify_running_config_diffs(
    mocked_device: MagicMock,
    return_value: List[Any],
    side_effect: Any,
    remove_enable_password: str,
    expected_result: str,
    expected_messages: List[str],
) -> None:
    if remove_enable_password:
        mocked_device.enable_password = None
    mocked_device.session.cli.return_value = return_value
    mocked_device.session.cli.side_effect = side_effect
    result = asyncio.run(verify_running_config_diffs(mocked_device))

    assert result.test == "verify_running_config_diffs"
    assert str(result.name) == "42.42.42.42"
    assert result.result == expected_result
    assert result.messages == expected_messages
