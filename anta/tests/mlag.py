from jsonrpclib import jsonrpc

def verify_mlag_status(device, enable_password):

    """
    Verifies the MLAG status:
    state is active, negotiation status is connected, local int is up, peer link is up.

    Args:
        device (jsonrpclib.jsonrpc.ServerProxy): Instance of the class jsonrpclib.jsonrpc.ServerProxy with the uri f'https://{username}:{password}@{ip}/command-api'.
        enable_password (str): Enable password.

    Returns:
        bool: `True` if the MLAG status is OK.
        `False` otherwise.

    """
    try:
        response = device.runCmds(1, ['show mlag'], 'json')
    except jsonrpc.AppError:
        return None
    try:
        if response[0]['state'] == 'disabled':
            return None
        if response[0]['state'] != 'active':
            return False
        if response[0]['negStatus'] != 'connected':
            return False
        if response[0]['localIntfStatus'] != 'up':
            return False
        if response[0]['peerLinkStatus'] != 'up':
            return False
        return True
    except KeyError:
        return None

def verify_mlag_interfaces(device, enable_password):
    """
    Verifies there is no inactive or active-partial MLAG interfaces.

    Args:
        device (jsonrpclib.jsonrpc.ServerProxy): Instance of the class jsonrpclib.jsonrpc.ServerProxy with the uri f'https://{username}:{password}@{ip}/command-api'.
        enable_password (str): Enable password.

    Returns:
        bool: `True` if there is no inactive or active-partial MLAG interfaces.
        `False` otherwise.

    """
    try:
        response = device.runCmds(1, ['show mlag'], 'json')
    except jsonrpc.AppError:
        return None
    try:
        if response[0]['state'] == 'disabled':
            return None
        if response[0]['mlagPorts']['Inactive'] != 0:
            return False
        if response[0]['mlagPorts']['Active-partial'] != 0:
            return False
        return True
    except KeyError:
        return None

def verify_mlag_config_sanity(device, enable_password):
    """
    Verifies there is no MLAG config-sanity warnings.

    Args:
        device (jsonrpclib.jsonrpc.ServerProxy): Instance of the class jsonrpclib.jsonrpc.ServerProxy with the uri f'https://{username}:{password}@{ip}/command-api'.
        enable_password (str): Enable password.

    Returns:
        bool: `True` if there is no MLAG config-sanity warnings.
        `False` otherwise.
    """
    try:
        response = device.runCmds(1, ['show mlag config-sanity'],'json')
    except jsonrpc.AppError:
        return None
    try:
        if response[0]['response']['mlagActive'] is False:
            # MLAG isn't running
            return None
        if len(response[0]['response']['globalConfiguration']) > 0 or \
            len(response[0]['response']['interfaceConfiguration']) > 0:
            return False
        return True
    except KeyError:
        return None
