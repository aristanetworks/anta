"""
Tests for anta.tests.configuration.py
"""
from unittest.mock import patch
from jsonrpclib.jsonrpc import AppError
import pytest
from anta.tests import verify_zerotouch, verify_running_config_diffs


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

    assert result.result == expected_result
    assert result.messages == expected_messages
