# Copyright (c) 2023-2025 Arista Networks, Inc.
# Use of this source code is governed by the Apache License 2.0
# that can be found in the LICENSE file.
"""Tests for `anta.tools`."""

from __future__ import annotations

from contextlib import AbstractContextManager
from contextlib import nullcontext as does_not_raise
from datetime import datetime, timedelta, timezone
from typing import Any

import pytest

from anta.tools import convert_categories, custom_division, format_data, get_dict_superset, get_failed_logs, get_item, get_value, is_interface_ignored, time_ago

TEST_GET_FAILED_LOGS_DATA = [
    {"id": 1, "name": "Alice", "age": 30, "email": "alice@example.com"},
    {"id": 2, "name": "Bob", "age": 35, "email": "bob@example.com"},
    {"id": 3, "name": "Charlie", "age": 40, "email": "charlie@example.com"},
    {"id": 4, "name": "Jon", "age": 25, "email": "Jon@example.com"},
    {"id": 4, "name": "Rob", "age": 25, "email": "Jon@example.com"},
]
TEST_GET_DICT_SUPERSET_DATA = [
    ("id", 0),
    {
        "id": 1,
        "name": "Alice",
        "age": 30,
        "email": "alice@example.com",
    },
    {
        "id": 2,
        "name": "Bob",
        "age": 35,
        "email": "bob@example.com",
    },
    {
        "id": 3,
        "name": "Charlie",
        "age": 40,
        "email": "charlie@example.com",
    },
]
TEST_GET_VALUE_DATA = {"test_value": 42, "nested_test": {"nested_value": 43}}
TEST_GET_ITEM_DATA = [
    ("id", 0),
    {
        "id": 1,
        "name": "Alice",
        "age": 30,
        "email": "alice@example.com",
    },
    {
        "id": 2,
        "name": "Bob",
        "age": 35,
        "email": "bob@example.com",
    },
    {
        "id": 3,
        "name": "Charlie",
        "age": 40,
        "email": "charlie@example.com",
    },
]


@pytest.mark.parametrize(
    ("expected_output", "actual_output", "expected_result"),
    [
        pytest.param(
            TEST_GET_FAILED_LOGS_DATA[0],
            TEST_GET_FAILED_LOGS_DATA[0],
            "",
            id="no difference",
        ),
        pytest.param(
            TEST_GET_FAILED_LOGS_DATA[0],
            TEST_GET_FAILED_LOGS_DATA[1],
            "\nExpected `1` as the id, but found `2` instead.\nExpected `Alice` as the name, but found `Bob` instead.\n"
            "Expected `30` as the age, but found `35` instead.\nExpected `alice@example.com` as the email, but found `bob@example.com` instead.",
            id="different data",
        ),
        pytest.param(
            TEST_GET_FAILED_LOGS_DATA[0],
            {},
            "\nExpected `1` as the id, but it was not found in the actual output.\nExpected `Alice` as the name, but it was not found in the actual output.\n"
            "Expected `30` as the age, but it was not found in the actual output.\nExpected `alice@example.com` as the email, but it was not found in "
            "the actual output.",
            id="empty actual output",
        ),
        pytest.param(
            TEST_GET_FAILED_LOGS_DATA[3],
            TEST_GET_FAILED_LOGS_DATA[4],
            "\nExpected `Jon` as the name, but found `Rob` instead.",
            id="different name",
        ),
    ],
)
def test_get_failed_logs(
    expected_output: dict[Any, Any],
    actual_output: dict[Any, Any],
    expected_result: str,
) -> None:
    """Test get_failed_logs."""
    assert get_failed_logs(expected_output, actual_output) == expected_result


@pytest.mark.parametrize(
    (
        "list_of_dicts",
        "input_dict",
        "default",
        "required",
        "var_name",
        "custom_error_msg",
        "expected_result",
        "expected_raise",
    ),
    [
        pytest.param(
            [],
            {"id": 1, "name": "Alice"},
            None,
            False,
            None,
            None,
            None,
            does_not_raise(),
            id="empty list",
        ),
        pytest.param(
            [],
            {"id": 1, "name": "Alice"},
            None,
            True,
            None,
            None,
            None,
            pytest.raises(ValueError, match="not found in the provided list."),
            id="empty list and required",
        ),
        pytest.param(
            TEST_GET_DICT_SUPERSET_DATA,
            {"id": 10, "name": "Jack"},
            None,
            False,
            None,
            None,
            None,
            does_not_raise(),
            id="missing item",
        ),
        pytest.param(
            TEST_GET_DICT_SUPERSET_DATA,
            {"id": 1, "name": "Alice"},
            None,
            False,
            None,
            None,
            TEST_GET_DICT_SUPERSET_DATA[1],
            does_not_raise(),
            id="found item",
        ),
        pytest.param(
            TEST_GET_DICT_SUPERSET_DATA,
            {"id": 10, "name": "Jack"},
            "default_value",
            False,
            None,
            None,
            "default_value",
            does_not_raise(),
            id="default value",
        ),
        pytest.param(
            TEST_GET_DICT_SUPERSET_DATA,
            {"id": 10, "name": "Jack"},
            None,
            True,
            None,
            None,
            None,
            pytest.raises(ValueError, match="not found in the provided list."),
            id="required",
        ),
        pytest.param(
            TEST_GET_DICT_SUPERSET_DATA,
            {"id": 10, "name": "Jack"},
            None,
            True,
            "custom_var_name",
            None,
            None,
            pytest.raises(ValueError, match="custom_var_name not found in the provided list."),
            id="custom var_name",
        ),
        pytest.param(
            TEST_GET_DICT_SUPERSET_DATA,
            {"id": 1, "name": "Alice"},
            None,
            True,
            "custom_var_name",
            "Custom error message",
            TEST_GET_DICT_SUPERSET_DATA[1],
            does_not_raise(),
            id="custom error message",
        ),
        pytest.param(
            TEST_GET_DICT_SUPERSET_DATA,
            {"id": 10, "name": "Jack"},
            None,
            True,
            "custom_var_name",
            "Custom error message",
            None,
            pytest.raises(ValueError, match="Custom error message"),
            id="custom error message and required",
        ),
        pytest.param(
            TEST_GET_DICT_SUPERSET_DATA,
            {"id": 1, "name": "Jack"},
            None,
            False,
            None,
            None,
            None,
            does_not_raise(),
            id="id ok but name not ok",
        ),
        pytest.param(
            "not a list",
            {"id": 1, "name": "Alice"},
            None,
            True,
            None,
            None,
            None,
            pytest.raises(ValueError, match="not found in the provided list."),
            id="non-list input for list_of_dicts",
        ),
        pytest.param(
            TEST_GET_DICT_SUPERSET_DATA,
            "not a dict",
            None,
            True,
            None,
            None,
            None,
            pytest.raises(ValueError, match="not found in the provided list."),
            id="non-dictionary input",
        ),
        pytest.param(
            TEST_GET_DICT_SUPERSET_DATA,
            {},
            None,
            False,
            None,
            None,
            None,
            does_not_raise(),
            id="empty dictionary input",
        ),
        pytest.param(
            TEST_GET_DICT_SUPERSET_DATA,
            {"id": 1, "name": "Alice", "extra_key": "extra_value"},
            None,
            True,
            None,
            None,
            None,
            pytest.raises(ValueError, match="not found in the provided list."),
            id="input dictionary with extra keys",
        ),
        pytest.param(
            TEST_GET_DICT_SUPERSET_DATA,
            {"id": 1},
            None,
            False,
            None,
            None,
            TEST_GET_DICT_SUPERSET_DATA[1],
            does_not_raise(),
            id="input dictionary is a subset of more than one dictionary in list_of_dicts",
        ),
        pytest.param(
            TEST_GET_DICT_SUPERSET_DATA,
            {
                "id": 1,
                "name": "Alice",
                "age": 30,
                "email": "alice@example.com",
                "extra_key": "extra_value",
            },
            None,
            True,
            None,
            None,
            None,
            pytest.raises(ValueError, match="not found in the provided list."),
            id="input dictionary is a superset of a dictionary in list_of_dicts",
        ),
    ],
)
def test_get_dict_superset(
    list_of_dicts: list[dict[Any, Any]],
    input_dict: dict[Any, Any],
    default: str | None,
    required: bool,
    var_name: str | None,
    custom_error_msg: str | None,
    expected_result: str,
    expected_raise: AbstractContextManager[Exception],
) -> None:
    """Test get_dict_superset."""
    with expected_raise:
        assert get_dict_superset(list_of_dicts, input_dict, default, var_name, custom_error_msg, required=required) == expected_result


@pytest.mark.parametrize(
    (
        "input_dict",
        "key",
        "default",
        "required",
        "org_key",
        "separator",
        "expected_result",
        "expected_raise",
    ),
    [
        pytest.param({}, "test", None, False, None, None, None, does_not_raise(), id="empty dict"),
        pytest.param(
            TEST_GET_VALUE_DATA,
            "test_value",
            None,
            False,
            None,
            None,
            42,
            does_not_raise(),
            id="simple key",
        ),
        pytest.param(
            TEST_GET_VALUE_DATA,
            "nested_test.nested_value",
            None,
            False,
            None,
            None,
            43,
            does_not_raise(),
            id="nested_key",
        ),
        pytest.param(
            TEST_GET_VALUE_DATA,
            "missing_value",
            None,
            False,
            None,
            None,
            None,
            does_not_raise(),
            id="missing_value",
        ),
        pytest.param(
            TEST_GET_VALUE_DATA,
            "missing_value_with_default",
            "default_value",
            False,
            None,
            None,
            "default_value",
            does_not_raise(),
            id="default",
        ),
        pytest.param(
            TEST_GET_VALUE_DATA,
            "missing_required",
            None,
            True,
            None,
            None,
            None,
            pytest.raises(ValueError, match="missing_required"),
            id="required",
        ),
        pytest.param(
            TEST_GET_VALUE_DATA,
            "missing_required",
            None,
            True,
            "custom_org_key",
            None,
            None,
            pytest.raises(ValueError, match="custom_org_key"),
            id="custom org_key",
        ),
        pytest.param(
            TEST_GET_VALUE_DATA,
            "nested_test||nested_value",
            None,
            None,
            None,
            "||",
            43,
            does_not_raise(),
            id="custom separator",
        ),
    ],
)
def test_get_value(
    input_dict: dict[Any, Any],
    key: str,
    default: str | None,
    required: bool,
    org_key: str | None,
    separator: str | None,
    expected_result: int | str | None,
    expected_raise: AbstractContextManager[Exception],
) -> None:
    """Test get_value."""
    kwargs = {
        "default": default,
        "required": required,
        "org_key": org_key,
        "separator": separator,
    }
    kwargs = {k: v for k, v in kwargs.items() if v is not None}
    with expected_raise:
        assert get_value(input_dict, key, **kwargs) == expected_result  # type: ignore[arg-type]


@pytest.mark.parametrize(
    ("list_of_dicts", "key", "value", "default", "required", "case_sensitive", "var_name", "custom_error_msg", "expected_result", "expected_raise"),
    [
        pytest.param([], "name", "Bob", None, False, False, None, None, None, does_not_raise(), id="empty list"),
        pytest.param([], "name", "Bob", None, True, False, None, None, None, pytest.raises(ValueError, match="name"), id="empty list and required"),
        pytest.param(TEST_GET_ITEM_DATA, "name", "Jack", None, False, False, None, None, None, does_not_raise(), id="missing item"),
        pytest.param(TEST_GET_ITEM_DATA, "name", "Alice", None, False, False, None, None, TEST_GET_ITEM_DATA[1], does_not_raise(), id="found item"),
        pytest.param(TEST_GET_ITEM_DATA, "name", "Jack", "default_value", False, False, None, None, "default_value", does_not_raise(), id="default value"),
        pytest.param(TEST_GET_ITEM_DATA, "name", "Jack", None, True, False, None, None, None, pytest.raises(ValueError, match="name"), id="required"),
        pytest.param(TEST_GET_ITEM_DATA, "name", "Bob", None, False, True, None, None, TEST_GET_ITEM_DATA[2], does_not_raise(), id="case sensitive"),
        pytest.param(TEST_GET_ITEM_DATA, "name", "charlie", None, False, False, None, None, TEST_GET_ITEM_DATA[3], does_not_raise(), id="case insensitive"),
        pytest.param(
            TEST_GET_ITEM_DATA,
            "name",
            "Jack",
            None,
            True,
            False,
            "custom_var_name",
            None,
            None,
            pytest.raises(ValueError, match="custom_var_name"),
            id="custom var_name",
        ),
        pytest.param(
            TEST_GET_ITEM_DATA,
            "name",
            "Jack",
            None,
            True,
            False,
            None,
            "custom_error_msg",
            None,
            pytest.raises(ValueError, match="custom_error_msg"),
            id="custom error msg",
        ),
    ],
)
def test_get_item(
    list_of_dicts: list[dict[Any, Any]],
    key: str,
    value: str | None,
    default: str | None,
    required: bool,
    case_sensitive: bool,
    var_name: str | None,
    custom_error_msg: str | None,
    expected_result: str,
    expected_raise: AbstractContextManager[Exception],
) -> None:
    """Test get_item."""
    with expected_raise:
        assert get_item(list_of_dicts, key, value, default, var_name, custom_error_msg, required=required, case_sensitive=case_sensitive) == expected_result


@pytest.mark.parametrize(
    ("numerator", "denominator", "expected_result"),
    [
        pytest.param(4.0, 2.0, 2, id="int return for float input"),
        pytest.param(4, 2, 2, id="int return for int input"),
        pytest.param(5.0, 2.0, 2.5, id="float return for float input"),
        pytest.param(5, 2, 2.5, id="float return for int input"),
    ],
)
def test_custom_division(numerator: float, denominator: float, expected_result: str) -> None:
    """Test custom_division."""
    assert custom_division(numerator, denominator) == expected_result


@pytest.mark.parametrize(
    ("test_input", "expected_raise", "expected_result"),
    [
        pytest.param([], does_not_raise(), [], id="empty list"),
        pytest.param(["bgp", "system", "vlan", "configuration"], does_not_raise(), ["BGP", "System", "VLAN", "Configuration"], id="list with acronyms and titles"),
        pytest.param(42, pytest.raises(TypeError, match="Wrong input type"), None, id="wrong input type"),
    ],
)
def test_convert_categories(test_input: list[str], expected_raise: AbstractContextManager[Exception], expected_result: list[str]) -> None:
    """Test convert_categories."""
    with expected_raise:
        assert convert_categories(test_input) == expected_result


@pytest.mark.parametrize(
    ("input_data", "expected_output"),
    [
        pytest.param({"advertised": True, "received": True, "enabled": True}, "Advertised: True, Received: True, Enabled: True", id="multiple entry, all True"),
        pytest.param({"advertised": False, "received": False}, "Advertised: False, Received: False", id="multiple entry, all False"),
        pytest.param({}, "", id="empty dict"),
        pytest.param({"test": True}, "Test: True", id="single entry"),
    ],
)
def test_format_data(input_data: dict[str, bool], expected_output: str) -> None:
    """Test format_data."""
    assert format_data(input_data) == expected_output


CANONICAL_TYPES = {
    "ethernet": "Ethernet",
    "portchannel": "Port-Channel",
    "vlan": "Vlan",
    "loopback": "Loopback",
    "management": "Management",
    "tunnel": "Tunnel",
    "fabric": "Fabric",
    "vxlan": "Vxlan",
    "dps": "Dps",
    "recircchannel": "Recirc-Channel",
}


@pytest.mark.parametrize(
    ("input_params", "expected_output"),
    [
        # Docstring Examples
        pytest.param({"interface": "Ethernet1", "ignored_interfaces": [CANONICAL_TYPES["ethernet"], "Port-Channel1"]}, True, id="doc_ex1_prefix_match_type"),
        pytest.param({"interface": "Ethernet2", "ignored_interfaces": ["Ethernet1", CANONICAL_TYPES["portchannel"]]}, False, id="doc_ex2_no_match"),
        pytest.param(
            {"interface": "Port-Channel1", "ignored_interfaces": ["Ethernet1", CANONICAL_TYPES["portchannel"]]}, True, id="doc_ex3_prefix_match_type_portchannel"
        ),
        pytest.param({"interface": "Ethernet1/1", "ignored_interfaces": ["Ethernet1/1", CANONICAL_TYPES["portchannel"]]}, True, id="doc_ex4_exact_match_subif"),
        pytest.param(
            {"interface": "Ethernet1/1", "ignored_interfaces": ["Ethernet1", CANONICAL_TYPES["portchannel"]]}, False, id="doc_ex5_no_match_specific_ignored_name"
        ),
        pytest.param(
            {"interface": "Ethernet1.100", "ignored_interfaces": ["Ethernet1.100", CANONICAL_TYPES["portchannel"]]}, True, id="doc_ex6_exact_match_dot_subif"
        ),
        # Cases for None or Empty ignored_interfaces (function returns None)
        pytest.param({"interface": "Loopback0", "ignored_interfaces": None}, None, id="none_ignored_list"),
        pytest.param({"interface": "Management1", "ignored_interfaces": []}, None, id="empty_ignored_list"),
        # Exact Match Cases (full interface names in ignored_interfaces list)
        pytest.param({"interface": "Vlan20", "ignored_interfaces": ["Vlan20", CANONICAL_TYPES["ethernet"]]}, True, id="exact_match_Vlan20"),
        pytest.param(
            {"interface": "Port-Channel200", "ignored_interfaces": ["port-channel200", CANONICAL_TYPES["ethernet"]]}, False, id="exact_match_case_sensitive_fail"
        ),
        pytest.param(
            {"interface": "Port-Channel200", "ignored_interfaces": ["Port-Channel200", CANONICAL_TYPES["ethernet"]]}, True, id="exact_match_case_sensitive_pass"
        ),
        pytest.param({"interface": "Ethernet1/1/1", "ignored_interfaces": ["ethernet1/1/1"]}, False, id="exact_match_subif_case_fail"),
        pytest.param({"interface": "Ethernet1/1/1", "ignored_interfaces": ["Ethernet1/1/1"]}, True, id="exact_match_subif_case_pass"),
        # Prefix Match Cases (interface types in ignored_interfaces list)
        pytest.param(
            {"interface": "Ethernet10/1", "ignored_interfaces": [CANONICAL_TYPES["ethernet"], CANONICAL_TYPES["loopback"]]}, True, id="prefix_match_Ethernet_type"
        ),
        pytest.param(
            {"interface": "Port-Channel123", "ignored_interfaces": [CANONICAL_TYPES["portchannel"], CANONICAL_TYPES["vlan"]]},
            True,
            id="prefix_match_PortChannel_type",
        ),
        pytest.param({"interface": "Tunnel5", "ignored_interfaces": [CANONICAL_TYPES["tunnel"], CANONICAL_TYPES["vxlan"]]}, True, id="prefix_match_Tunnel_type"),
        pytest.param({"interface": "Fabric1/2", "ignored_interfaces": [CANONICAL_TYPES["fabric"]]}, True, id="prefix_match_Fabric_type"),
        pytest.param({"interface": "Dps1", "ignored_interfaces": [CANONICAL_TYPES["dps"]]}, True, id="prefix_match_Dps_type"),
        pytest.param({"interface": "Recirc-Channel2/1", "ignored_interfaces": [CANONICAL_TYPES["recircchannel"]]}, True, id="prefix_match_RecircChannel_type"),
        # Prefix Match: Case sensitivity of items in ignored_interfaces
        pytest.param(
            {"interface": "Ethernet20/1", "ignored_interfaces": ["ethernet", CANONICAL_TYPES["loopback"]]}, False, id="prefix_match_vs_lowercase_type_in_list_fail"
        ),
        pytest.param({"interface": "Vlan30.10", "ignored_interfaces": ["vlan"]}, False, id="prefix_match_vs_lowercase_vlan_in_list_fail"),  # "Vlan" vs "vlan"
        # Mixed: Exact name vs. Type in ignored_interfaces
        pytest.param({"interface": "Ethernet1", "ignored_interfaces": ["Ethernet1"]}, True, id="mixed_exact_name_match_Ethernet1"),
        pytest.param({"interface": "Ethernet1", "ignored_interfaces": [CANONICAL_TYPES["ethernet"]]}, True, id="mixed_type_match_Ethernet"),
        pytest.param({"interface": "Ethernet1/1", "ignored_interfaces": [CANONICAL_TYPES["ethernet"]]}, True, id="mixed_type_match_subif_Ethernet"),
        pytest.param({"interface": "Management1", "ignored_interfaces": ["Management1", CANONICAL_TYPES["management"]]}, True, id="mixed_exact_and_type_present"),
        # No Match Cases
        pytest.param(
            {"interface": "Management1/1", "ignored_interfaces": [CANONICAL_TYPES["ethernet"], "Vlan10"]}, False, id="no_match_completely_different_types_and_names"
        ),
        pytest.param(
            {"interface": "Loopback0", "ignored_interfaces": ["Loopback1", CANONICAL_TYPES["vxlan"]]}, False, id="no_match_specific_names_different_number"
        ),
        pytest.param({"interface": "Ethernet1", "ignored_interfaces": ["Eth", CANONICAL_TYPES["loopback"]]}, False, id="no_match_partial_prefix_in_list"),
        pytest.param({"interface": "Vxlan1", "ignored_interfaces": [CANONICAL_TYPES["vlan"]]}, False, id="no_match_vxlan_vs_vlan_type"),
    ],
)
def test_is_interface_ignored(input_params: dict[str, Any], expected_output: bool | None) -> None:
    """Tests the is_interface_ignored function with various inputs, assuming Pydantic has validated and canonicalized interface names."""
    interface_value = input_params["interface"]
    ignored_interfaces_value = input_params["ignored_interfaces"]
    assert is_interface_ignored(interface_value, ignored_interfaces_value) == expected_output


@pytest.mark.parametrize(
    ("time_delta", "expected_output"),
    [
        pytest.param(timedelta(seconds=30), "less than a minute", id="less_than_a_minute"),
        pytest.param(timedelta(minutes=1), "1 minute", id="one_minute"),
        pytest.param(timedelta(minutes=1, seconds=10), "1 minute", id="one_minute_plus_seconds"),
        pytest.param(timedelta(minutes=15), "15 minutes", id="multiple_minutes"),
        pytest.param(timedelta(hours=1), "1 hour", id="one_hour"),
        pytest.param(timedelta(hours=1, minutes=10), "1 hour and 10 minutes", id="one_hour_and_minutes"),
        pytest.param(timedelta(hours=3), "3 hours", id="multiple_hours"),
        pytest.param(timedelta(hours=2, minutes=45), "2 hours and 45 minutes", id="multiple_hours_and_minutes"),
        pytest.param(timedelta(days=1), "1 day", id="one_day"),
        pytest.param(timedelta(days=1, hours=5), "1 day", id="one_day_plus_hours"),
        pytest.param(timedelta(days=5), "5 days", id="multiple_days"),
        pytest.param(timedelta(seconds=0), "less than a minute", id="exactly_now"),
    ],
)
def test_time_ago(time_delta: timedelta, expected_output: str) -> None:
    """Tests the time_ago function with various time deltas."""
    now = datetime.now(timezone.utc)
    test_timestamp = (now - time_delta).timestamp()

    assert time_ago(test_timestamp) == expected_output
