"""
Test functions related to VXLAN
"""
from jsonrpclib import jsonrpc

def verify_vxlan(device, enable_password):
    """
    Verifies the interface vxlan 1 status is up/up.

    Args:
        device (jsonrpclib.jsonrpc.ServerProxy): Instance of the class jsonrpclib.jsonrpc.ServerProxy with the uri f'https://{username}:{password}@{ip}/command-api'.
        enable_password (str): Enable password.

    Returns:
        bool: `True` if the interface vxlan 1 status is up/up.
        `False` otherwise.

    """
    try:
        response = device.runCmds(1, ['show interfaces description | include Vx1'], 'text')
    except jsonrpc.AppError:
        return None
    try:
        if response[0]['output'].count('up') == 2:
            return True
        return False
    except KeyError:
        return None

def verify_vxlan_config_sanity(device, enable_password):
    """
    Verifies there is no VXLAN config-sanity warnings.

    Args:
        device (jsonrpclib.jsonrpc.ServerProxy): Instance of the class jsonrpclib.jsonrpc.ServerProxy with the uri f'https://{username}:{password}@{ip}/command-api'.
        enable_password (str): Enable password.

    Returns:
        bool: `True` if there is no VXLAN config-sanity warnings.
        `False` otherwise.
    """
    try:
        response = device.runCmds(1, ['show vxlan config-sanity'], 'json')
    except jsonrpc.AppError:
        return None
    try:
        if len(response[0]['categories']) == 0:
            return None
        for category in response[0]['categories']:
            if category in ['localVtep', 'mlag']:
                if response[0]['categories'][category]['allCheckPass'] is not True:
                    return False
        return True
    except KeyError:
        return None
