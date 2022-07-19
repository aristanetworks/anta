"""
Test functions related to ASIC profiles
"""
from jsonrpclib import jsonrpc

def verify_unified_forwarding_table_mode(device, enable_password, mode = None):

    """
    Verifies the device is using the expected Unified Forwarding Table mode.

    Args:
        device (jsonrpclib.jsonrpc.ServerProxy): Instance of the class jsonrpclib.jsonrpc.ServerProxy with the uri f'https://{username}:{password}@{ip}/command-api'.
        enable_password (str): Enable password.
        mode (int): The expected Unified Forwarding Table mode.

    Returns:
        bool: `True` if the device is using the expected Unified Forwarding Table mode.
        `False` otherwise.

    """
    if not mode:
        return None
    try:
        response = device.runCmds(1, ['show platform trident forwarding-table partition'], 'json')
    except jsonrpc.AppError:
        return None
    try:
        if response[0]['uftMode'] == str(mode):
            return True
        return False
    except KeyError:
        return None

def verify_tcam_profile(device, enable_password, profile):

    """
    Verifies the configured TCAM profile is the expected one.

    Args:
        device (jsonrpclib.jsonrpc.ServerProxy): Instance of the class jsonrpclib.jsonrpc.ServerProxy with the uri f'https://{username}:{password}@{ip}/command-api'.
        enable_password (str): Enable password.
        profile (str): The expected TCAM profile.

    Returns:
        bool: `True` if the device is configured with the expected TCAM profile.
        `False` otherwise.

    """
    try:
        response = device.runCmds(1, ['show hardware tcam profile'], 'json')
    except jsonrpc.AppError:
        return None
    try:
        if (response[0]['pmfProfiles']['FixedSystem']['status'] == response[0]['pmfProfiles']['FixedSystem']['config'])\
            and (response[0]['pmfProfiles']['FixedSystem']['status'] == profile):
            return True
        return False
    except KeyError:
        return None
