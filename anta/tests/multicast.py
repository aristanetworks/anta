"""
Test functions related to multicast
"""
from jsonrpclib import jsonrpc

def verify_igmp_snooping_vlans(device, enable_password, vlans, configuration):
    """
    Verifies the IGMP snooping configuration for some VLANs.

    Args:
        device (jsonrpclib.jsonrpc.ServerProxy): Instance of the class jsonrpclib.jsonrpc.ServerProxy with the uri f'https://{username}:{password}@{ip}/command-api'.
        enable_password (str): Enable password.
        vlans (list): A list of VLANs
        configuration (str): Expected IGMP snooping configuration (enabled or disabled) for these VLANs.

    Returns:
        bool: `True` if the IGMP snooping configuration for the VLANs is the one we expect.
        `False` otherwise.

    """
    if not vlans or not configuration:
        return None
    try:
        response = device.runCmds(1, ['show ip igmp snooping'],'json')
    except jsonrpc.AppError:
        return None
    try:
        for vlan in vlans:
            if response[0]['vlans'][str(vlan)]['igmpSnoopingState'] != configuration:
                return False
        return True
    except KeyError:
        return None

def verify_igmp_snooping_global(device, enable_password,  configuration):
    """
    Verifies the IGMP snooping global configuration.

    Args:
        device (jsonrpclib.jsonrpc.ServerProxy): Instance of the class jsonrpclib.jsonrpc.ServerProxy with the uri f'https://{username}:{password}@{ip}/command-api'.
        enable_password (str): Enable password.
        configuration (str): Expected global IGMP snooping configuration (enabled or disabled) for these VLANs.

    Returns:
        bool: `True` if the IGMP snooping global configuration is the one we expect.
        `False` otherwise.

    """
    if not configuration:
        return None
    try:
        response = device.runCmds(1, ['show ip igmp snooping'],'json')
    except jsonrpc.AppError:
        return None
    try:
        if response[0]['igmpSnoopingState'] == configuration:
            return True
        return False
    except KeyError:
        return None
