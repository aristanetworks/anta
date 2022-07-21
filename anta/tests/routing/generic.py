"""
Generic routing test functions
"""
from jsonrpclib import jsonrpc

def verify_routing_protocol_model(device, enable_password, model = None):

    """
    Verifies the configured routing protocol model is the one we expect.
    And if there is no mismatch between the configured and operating routing protocol model.

    Args:
        device (jsonrpclib.jsonrpc.ServerProxy): Instance of the class jsonrpclib.jsonrpc.ServerProxy with the uri f'https://{username}:{password}@{ip}/command-api'.
        enable_password (str): Enable password.
        model(str): Expected routing protocol model (multi-agent or ribd).

    Returns:
        bool: `True` if the configured routing protocol model is the one we expect.
        And if there is no mismatch between the configured and operating routing protocol model.
        `False` otherwise.
    """
    if not model:
        return None
    try:
        response = device.runCmds(1, [{'cmd': 'show ip route summary', 'revision': 3}], 'json')
    except jsonrpc.AppError:
        return None
    try:
        if (response[0]['protoModelStatus']['configuredProtoModel'] == response[0]['protoModelStatus']['operatingProtoModel']) \
            and (response[0]['protoModelStatus']['operatingProtoModel'] == model):
            return True
        return False
    except KeyError:
        return None

def verify_routing_table_size(device, enable_password, minimum = None, maximum = None):
    """
    Verifies the size of the IP routing table (default VRF).
    Should be between the two provided thresholds.

    Args:
        device (jsonrpclib.jsonrpc.ServerProxy): Instance of the class jsonrpclib.jsonrpc.ServerProxy with the uri f'https://{username}:{password}@{ip}/command-api'.
        enable_password (str): Enable password.
        minimum(int): Expected minimum routing table (default VRF) size.
        maximum(int): Expected maximum routing table (default VRF) size.

    Returns:
        bool: `True` if the size of the IP routing table (default VRF) is between two thresholds.
        `False` otherwise.
    """
    if not minimum or not maximum:
        return None
    try:
        response = device.runCmds(1, [{'cmd': 'show ip route summary', 'revision': 3}], 'json')
    except jsonrpc.AppError:
        return None
    try:
        if (response[0]['vrfs']['default']['totalRoutes'] >= minimum) \
            and (response[0]['vrfs']['default']['totalRoutes'] <= maximum):
            return True
        return False
    except KeyError:
        return None

def verify_bfd(device, enable_password):
    """
    Verifies there is no BFD peer in down state (all VRF, IPv4 neighbors).

    Args:
        device (jsonrpclib.jsonrpc.ServerProxy): Instance of the class jsonrpclib.jsonrpc.ServerProxy with the uri f'https://{username}:{password}@{ip}/command-api'.
        enable_password (str): Enable password.

    Returns:
        bool: `True` if there is no BFD peer in down state (all VRF, IPv4 neighbors, single-hop).
        `False` otherwise.

    """
    try:
        response = device.runCmds(1, ['show bfd peers'], 'json')
    except jsonrpc.AppError:
        return None
    try:
        for vrf in response[0]['vrfs']:
            for neighbor in response[0]['vrfs'][vrf]['ipv4Neighbors']:
                for interface in response[0]['vrfs'][vrf]['ipv4Neighbors'][neighbor]['peerStats']:
                    if response[0]['vrfs'][vrf]['ipv4Neighbors'][neighbor]['peerStats'][interface]['status'] != 'up':
                        return False
            return True
    except KeyError:
        return None
