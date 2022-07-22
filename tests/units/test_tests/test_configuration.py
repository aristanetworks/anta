"""
Tests for anta.tests.configuration.py
"""
from unittest.mock import patch
from jsonrpclib.jsonrpc import AppError
import pytest
from anta.tests.configuration import verify_zerotouch, verify_running_config_diffs


@pytest.mark.parametrize(
    "return_value, side_effect, expected_result, expected_messages",
    [
        pytest.param(
            [{"mode": "disabled"}], None, "success", ["ZTP is disabled"], id="success"
        ),
        pytest.param(
            [{"mode": "enabled"}],
            None,
            "failure",
            ["ZTP is NOT disabled"],
            id="failure",
        ),
        # Hmmmm both errors do not return the same string ...
        pytest.param(None, AppError("dummy"), "error", ["dummy"], id="JSON RPC error"),
        pytest.param(None, KeyError("dummy"), "error", ["'dummy'"], id="Key error"),
    ],
)
def test_verify_zerotouch(
    mocked_device, return_value, side_effect, expected_result, expected_messages
):
    mocked_device.session.runCmds.return_value = return_value
    mocked_device.session.runCmds.side_effect = side_effect
    result = verify_zerotouch(mocked_device)

    assert result.test == "verify_zerotouch"
    assert str(result.host) == "42.42.42.42"
    assert result.result == expected_result
    assert result.messages == expected_messages


@pytest.mark.parametrize(
    "return_value, side_effect, remove_enable_password, expected_result, expected_messages",
    [
        pytest.param(
            [42, {"output": []}],
            None,
            False,
            "success",
            [
                "There is no difference between the running-config and the startup-config."
            ],
            id="success",
        ),
        pytest.param(
            [42, {"output": ["blah", "blah"]}],
            None,
            False,
            "failure",
            ["blah", "blah"],
            id="failure",
        ),
        # Hmmmm both errors do not return the same string ...
        pytest.param(
            None, AppError("dummy"), False, "error", ["dummy"], id="JSON RPC error"
        ),
        pytest.param(
            None, KeyError("dummy"), False, "error", ["'dummy'"], id="Key error"
        ),
        pytest.param(
            None,
            None,
            True,
            "error",
            [
                "verify_running_config_diff requires the device tohave the `enable_password` configured"
            ],
            id="Missing enable password",
        ),
    ],
)
def test_verify_running_config_diffs(
    mocked_device,
    return_value,
    side_effect,
    remove_enable_password,
    expected_result,
    expected_messages,
):
    if remove_enable_password:
        mocked_device.enable_password = None
    mocked_device.session.runCmds.return_value = return_value
    mocked_device.session.runCmds.side_effect = side_effect
    result = verify_running_config_diffs(mocked_device)

    assert result.test == "verify_running_config_diffs"
    assert str(result.host) == "42.42.42.42"
    assert result.result == expected_result
    assert result.messages == expected_messages
