#!/usr/bin/python
# coding: utf-8 -*-


# INVENTORY_MODEL_HOST = {
#     "validIPv4": { 'input': "1.1.1.1", 'result': 'valid' },
#     "validIPv6":  { 'input': "fe80::cc62:a9ff:feef:932a", 'result': 'valid' },
# }

INVENTORY_MODEL_HOST = [
    {
        'name': 'validIPv4',
        'input': '1.1.1.1',
        'expected_result': 'valid'
    },
    {
        'name': 'validIPv6',
        'input': 'fe80::cc62:a9ff:feef:932a',
        'expected_result': 'valid'
    },
    {
        'name': 'invalidIPv4_with_netmask',
        'input': '1.1.1.1/32',
        'expected_result': 'invalid'
    },
    {
        'name': 'invalidIPv6_wit_netmask',
        'input': 'fe80::cc62:a9ff:feef:932a/128',
        'expected_result': 'invalid'
    },
    {
        'name': 'invalidIPv4_format',
        'input': '1.1.1.1.1',
        'expected_result': 'invalid'
    },
    {
        'name': 'invalidIPv6_format',
        'input': 'fe80::cc62:a9ff:feef:',
        'expected_result': 'invalid'
    },
]


INVENTORY_MODEL_NETWORK = [
    {
        'name': 'ValidIPv4_Subnet',
        'input': '1.1.1.0/24',
        'expected_result': 'valid'
    },
    {
        'name': 'ValidIPv4_Subnet',
        'input': '1.1.1.0/17',
        'expected_result': 'invalid'
    },
    {
        'name': 'ValidIPv6_Subnet',
        'input': '2001:db8::/32',
        'expected_result': 'valid'
    },
    {
        'name': 'InvalidIPv6_Subnet',
        'input': '2001:db8::/16',
        'expected_result': 'invalid'
    },
]

INVENTORY_MODEL_RANGE = [
    {
        'name': 'ValidIPv4_Range',
        'input': {'start':'10.1.0.1', 'end':'10.1.0.10'},
        'expected_result': 'valid'
    },
]

INVENTORY_MODEL = [
    {
        "name": "Valid_Host_Only",
        "input": {
            "hosts": [
                {
                    "host": "192.168.0.17"
                },
                {
                    "host": "192.168.0.2"
                }
            ]
        },
        "expected_result": "valid"
    },
    {
        "name": "Valid_Networks_Only",
        "input": {
            "networks": [
                {
                    "network": "192.168.0.0/16"
                },
                {
                    "network": "192.168.1.0/24"
                }
            ]
        },
        "expected_result": "valid"
    },
    {
        "name": "Host_with_Invalid_entry",
        "input": {
            "hosts": [
                {
                    "host": "192.168.0.17"
                },
                {
                    "host": "192.168.0.2/32"
                }
            ]
        },
        "expected_result": "invalid"
    }
]