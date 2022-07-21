"""
OSPF test functions
"""
from jsonrpclib import jsonrpc

def verify_ospf_state(device, enable_password):
    """
    Verifies all OSPF neighbors are in FULL state.

    Args:
        device (jsonrpclib.jsonrpc.ServerProxy): Instance of the class jsonrpclib.jsonrpc.ServerProxy with the uri f'https://{username}:{password}@{ip}/command-api'.
        enable_password (str): Enable password.

    Returns:
        bool: `True` if all OSPF neighbors are in FULL state.
        `False` otherwise.

    """
    try:
        response = device.runCmds(1, ['show ip ospf neighbor | exclude FULL|Address'], 'text')
    except jsonrpc.AppError:
        return None
    try:
        if response[0]['output'].count('\n') == 0:
            return True
        return False
    except KeyError:
        return None

def verify_ospf_count(device, enable_password, number = None):
    """
    Verifies the number of OSPF neighbors in FULL state is the one we expect.

    Args:
        device (jsonrpclib.jsonrpc.ServerProxy): Instance of the class jsonrpclib.jsonrpc.ServerProxy with the uri f'https://{username}:{password}@{ip}/command-api'.
        enable_password (str): Enable password.
        number (int): The expected number of OSPF neighbors in FULL state.

    Returns:
        bool: `True` if the number of OSPF neighbors in FULL state is the one we expect.
        `False` otherwise.

    """
    if not number:
        return None
    try:
        response = device.runCmds(1, ['show ip ospf neighbor | exclude  Address'], 'text')
    except jsonrpc.AppError:
        return None
    try:
        if response[0]['output'].count('FULL') == number:
            return True
        return False
    except KeyError:
        return None
