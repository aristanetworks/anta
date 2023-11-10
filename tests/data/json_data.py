# Copyright (c) 2023 Arista Networks, Inc.
# Use of this source code is governed by the Apache License 2.0
# that can be found in the LICENSE file.
# pylint: skip-file

INVENTORY_MODEL_HOST_VALID = [
    {"name": "validIPv4", "input": "1.1.1.1", "expected_result": "valid"},
    {
        "name": "validIPv6",
        "input": "fe80::cc62:a9ff:feef:932a",
    },
]

INVENTORY_MODEL_HOST_INVALID = [
    {
        "name": "invalidIPv4_with_netmask",
        "input": "1.1.1.1/32",
    },
    {
        "name": "invalidIPv6_with_netmask",
        "input": "fe80::cc62:a9ff:feef:932a/128",
    },
    {"name": "invalidHost_format", "input": "@", "expected_result": "invalid"},
    {
        "name": "invalidIPv6_format",
        "input": "fe80::cc62:a9ff:feef:",
    },
]

INVENTORY_MODEL_HOST_CACHE = [
    {"name": "Host cache default", "input": {"host": "1.1.1.1"}, "expected_result": False},
    {"name": "Host cache enabled", "input": {"host": "1.1.1.1", "disable_cache": False}, "expected_result": False},
    {"name": "Host cache disabled", "input": {"host": "1.1.1.1", "disable_cache": True}, "expected_result": True},
]

INVENTORY_MODEL_NETWORK_VALID = [
    {"name": "ValidIPv4_Subnet", "input": "1.1.1.0/24", "expected_result": "valid"},
    {"name": "ValidIPv6_Subnet", "input": "2001:db8::/32", "expected_result": "valid"},
]

INVENTORY_MODEL_NETWORK_INVALID = [
    {"name": "ValidIPv4_Subnet", "input": "1.1.1.0/17", "expected_result": "invalid"},
    {
        "name": "InvalidIPv6_Subnet",
        "input": "2001:db8::/16",
        "expected_result": "invalid",
    },
]

INVENTORY_MODEL_NETWORK_CACHE = [
    {"name": "Network cache default", "input": {"network": "1.1.1.0/24"}, "expected_result": False},
    {"name": "Network cache enabled", "input": {"network": "1.1.1.0/24", "disable_cache": False}, "expected_result": False},
    {"name": "Network cache disabled", "input": {"network": "1.1.1.0/24", "disable_cache": True}, "expected_result": True},
]

INVENTORY_MODEL_RANGE_VALID = [
    {
        "name": "ValidIPv4_Range",
        "input": {"start": "10.1.0.1", "end": "10.1.0.10"},
        "expected_result": "valid",
    },
]

INVENTORY_MODEL_RANGE_INVALID = [
    {
        "name": "InvalidIPv4_Range_name",
        "input": {"start": "toto", "end": "10.1.0.1"},
        "expected_result": "invalid",
    },
]

INVENTORY_MODEL_RANGE_CACHE = [
    {"name": "Range cache default", "input": {"start": "1.1.1.1", "end": "1.1.1.10"}, "expected_result": False},
    {"name": "Range cache enabled", "input": {"start": "1.1.1.1", "end": "1.1.1.10", "disable_cache": False}, "expected_result": False},
    {"name": "Range cache disabled", "input": {"start": "1.1.1.1", "end": "1.1.1.10", "disable_cache": True}, "expected_result": True},
]

INVENTORY_MODEL_VALID = [
    {
        "name": "Valid_Host_Only",
        "input": {"hosts": [{"host": "192.168.0.17"}, {"host": "192.168.0.2"}]},
        "expected_result": "valid",
    },
    {
        "name": "Valid_Networks_Only",
        "input": {"networks": [{"network": "192.168.0.0/16"}, {"network": "192.168.1.0/24"}]},
        "expected_result": "valid",
    },
    {
        "name": "Valid_Ranges_Only",
        "input": {
            "ranges": [
                {"start": "10.1.0.1", "end": "10.1.0.10"},
                {"start": "10.2.0.1", "end": "10.2.1.10"},
            ]
        },
        "expected_result": "valid",
    },
]

INVENTORY_MODEL_INVALID = [
    {
        "name": "Host_with_Invalid_entry",
        "input": {"hosts": [{"host": "192.168.0.17"}, {"host": "192.168.0.2/32"}]},
        "expected_result": "invalid",
    },
]

INVENTORY_DEVICE_MODEL_VALID = [
    {
        "name": "Valid_Inventory",
        "input": [{"host": "1.1.1.1", "username": "arista", "password": "arista123!"}, {"host": "1.1.1.2", "username": "arista", "password": "arista123!"}],
        "expected_result": "valid",
    },
]

INVENTORY_DEVICE_MODEL_INVALID = [
    {
        "name": "Invalid_Inventory",
        "input": [{"host": "1.1.1.1", "password": "arista123!"}, {"host": "1.1.1.1", "username": "arista"}],
        "expected_result": "invalid",
    },
]

ANTA_INVENTORY_TESTS_VALID = [
    {
        "name": "ValidInventory_with_host_only",
        "input": {"anta_inventory": {"hosts": [{"host": "192.168.0.17"}, {"host": "192.168.0.2"}, {"host": "my.awesome.host.com"}]}},
        "expected_result": "valid",
        "parameters": {
            "ipaddress_in_scope": "192.168.0.17",
            "ipaddress_out_of_scope": "192.168.1.1",
            "nb_hosts": 2,
        },
    },
    {
        "name": "ValidInventory_with_networks_only",
        "input": {"anta_inventory": {"networks": [{"network": "192.168.0.0/24"}]}},
        "expected_result": "valid",
        "parameters": {
            "ipaddress_in_scope": "192.168.0.1",
            "ipaddress_out_of_scope": "192.168.1.1",
            "nb_hosts": 256,
        },
    },
    {
        "name": "ValidInventory_with_ranges_only",
        "input": {
            "anta_inventory": {
                "ranges": [
                    {"start": "10.0.0.1", "end": "10.0.0.11"},
                    {"start": "10.0.0.101", "end": "10.0.0.111"},
                ]
            }
        },
        "expected_result": "valid",
        "parameters": {
            "ipaddress_in_scope": "10.0.0.10",
            "ipaddress_out_of_scope": "192.168.1.1",
            "nb_hosts": 22,
        },
    },
    {
        "name": "ValidInventory_with_host_port",
        "input": {"anta_inventory": {"hosts": [{"host": "192.168.0.17", "port": 443}, {"host": "192.168.0.2", "port": 80}]}},
        "expected_result": "valid",
        "parameters": {
            "ipaddress_in_scope": "192.168.0.17",
            "ipaddress_out_of_scope": "192.168.1.1",
            "nb_hosts": 2,
        },
    },
    {
        "name": "ValidInventory_with_host_tags",
        "input": {"anta_inventory": {"hosts": [{"host": "192.168.0.17", "tags": ["leaf"]}, {"host": "192.168.0.2", "tags": ["spine"]}]}},
        "expected_result": "valid",
        "parameters": {
            "ipaddress_in_scope": "192.168.0.17",
            "ipaddress_out_of_scope": "192.168.1.1",
            "nb_hosts": 2,
        },
    },
    {
        "name": "ValidInventory_with_networks_tags",
        "input": {"anta_inventory": {"networks": [{"network": "192.168.0.0/24", "tags": ["leaf"]}]}},
        "expected_result": "valid",
        "parameters": {
            "ipaddress_in_scope": "192.168.0.1",
            "ipaddress_out_of_scope": "192.168.1.1",
            "nb_hosts": 256,
        },
    },
    {
        "name": "ValidInventory_with_ranges_tags",
        "input": {
            "anta_inventory": {
                "ranges": [
                    {"start": "10.0.0.1", "end": "10.0.0.11", "tags": ["leaf"]},
                    {"start": "10.0.0.101", "end": "10.0.0.111", "tags": ["spine"]},
                ]
            }
        },
        "expected_result": "valid",
        "parameters": {
            "ipaddress_in_scope": "10.0.0.10",
            "ipaddress_out_of_scope": "192.168.1.1",
            "nb_hosts": 22,
        },
    },
]

ANTA_INVENTORY_TESTS_INVALID = [
    {
        "name": "InvalidInventory_with_host_only",
        "input": {"anta_inventory": {"hosts": [{"host": "192.168.0.17/32"}, {"host": "192.168.0.2"}]}},
        "expected_result": "invalid",
    },
    {
        "name": "InvalidInventory_wrong_network_bits",
        "input": {"anta_inventory": {"networks": [{"network": "192.168.42.0/8"}]}},
        "expected_result": "invalid",
    },
    {
        "name": "InvalidInventory_wrong_network",
        "input": {"anta_inventory": {"networks": [{"network": "toto"}]}},
        "expected_result": "invalid",
    },
    {
        "name": "InvalidInventory_wrong_range",
        "input": {"anta_inventory": {"ranges": [{"start": "toto", "end": "192.168.42.42"}]}},
        "expected_result": "invalid",
    },
    {
        "name": "InvalidInventory_wrong_range_type_mismatch",
        "input": {"anta_inventory": {"ranges": [{"start": "fe80::cafe", "end": "192.168.42.42"}]}},
        "expected_result": "invalid",
    },
    {
        "name": "Invalid_Root_Key",
        "input": {
            "inventory": {
                "ranges": [
                    {"start": "10.0.0.1", "end": "10.0.0.11"},
                    {"start": "10.0.0.100", "end": "10.0.0.111"},
                ]
            }
        },
        "expected_result": "invalid",
    },
]

TEST_RESULT_SET_STATUS = [
    {"name": "set_success", "target": "success", "message": "success"},
    {"name": "set_error", "target": "error", "message": "error"},
    {"name": "set_failure", "target": "failure", "message": "failure"},
    {"name": "set_skipped", "target": "skipped", "message": "skipped"},
    {"name": "set_unset", "target": "unset", "message": "unset"},
]
