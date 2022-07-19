from jsonrpclib import jsonrpc

def verify_zerotouch(device, enable_password):

    """
    Verifies ZeroTouch is disabled.

    Args:
        device (jsonrpclib.jsonrpc.ServerProxy): Instance of the class jsonrpclib.jsonrpc.ServerProxy with the uri f'https://{username}:{password}@{ip}/command-api'.
        enable_password (str): Enable password.

    Returns:
        bool: `True` if ZeroTouch is disabled.
        `False` otherwise.

    """
    try:
        response = device.runCmds(1, ['show zerotouch'], 'json')
    except jsonrpc.AppError:
        return None
    try:
        if response[0]['mode'] == 'disabled':
            return True
        return False
    except KeyError:
        return None

def verify_running_config_diffs(device, enable_password):

    """
    Verifies there is no difference between the running-config and the startup-config.

    Args:
        device (jsonrpclib.jsonrpc.ServerProxy): Instance of the class jsonrpclib.jsonrpc.ServerProxy with the uri f'https://{username}:{password}@{ip}/command-api'.
        enable_password (str): Enable password.

    Returns:
        bool: `True` if there is no difference between the running-config and the startup-config.
        `False` otherwise.

    """
    try:
        response = device.runCmds(1, \
            [{"cmd": "enable", "input": enable_password},'show running-config diffs'], 'text')
    except jsonrpc.AppError:
        return None
    try:
        if len(response[1]['output']) == 0:
            return True
        return False
    except KeyError:
        return None
