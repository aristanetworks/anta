from jsonrpclib import jsonrpc

def verify_bgp_ipv4_unicast_state(device, enable_password):
    """
    Verifies all IPv4 unicast BGP sessions are established (for all VRF)
    and all BGP messages queues for these sessions are empty (for all VRF).

    Args:
        device (jsonrpclib.jsonrpc.ServerProxy): Instance of the class jsonrpclib.jsonrpc.ServerProxy with the uri f'https://{username}:{password}@{ip}/command-api'.
        enable_password (str): Enable password.

    Returns:
        bool: `True` if all IPv4 unicast BGP sessions are established (for all VRF)
        and all BGP messages queues for these sessions are empty (for all VRF).
        `False` otherwise.

    """
    try:
        response = device.runCmds(1, ['show bgp ipv4 unicast summary vrf all'], 'json')
    except jsonrpc.AppError:
        return None
    try:
        if len(response[0]['vrfs']) == 0:
            return None
        for vrf in response[0]['vrfs']:
            for peer in response[0]['vrfs'][vrf]['peers']:
                if (response[0]['vrfs'][vrf]['peers'][peer]['peerState'] != 'Established') \
                    or (response[0]['vrfs'][vrf]['peers'][peer]["inMsgQueue"] != 0) \
                        or (response[0]['vrfs'][vrf]['peers'][peer]["outMsgQueue"] != 0):
                    return False
        return True
    except KeyError:
        return None

def verify_bgp_ipv4_unicast_count(device, enable_password, number, vrf = 'default'):
    """
    Verifies all IPv4 unicast BGP sessions are established
    and all BGP messages queues for these sessions are empty
    and the actual number of BGP IPv4 unicast neighbors is the one we expect.

    Args:
        device (jsonrpclib.jsonrpc.ServerProxy): Instance of the class jsonrpclib.jsonrpc.ServerProxy with the uri f'https://{username}:{password}@{ip}/command-api'.
        enable_password (str): Enable password.
        number (int): Expected number of BGP IPv4 unicast neighbors
        vrf(str): VRF to verify.

    Returns:
        bool: `True` if all IPv4 unicast BGP sessions are established
        and if all BGP messages queues for these sessions are empty
        and if the actual number of BGP IPv4 unicast neighbors is the one we expect.
        `False` otherwise.

    """
    if not number:
        return None
    if not vrf:
        return None
    count = 0
    command = 'show bgp ipv4 unicast summary vrf ' + vrf
    try:
        response = device.runCmds(1, [command], 'json')
    except jsonrpc.AppError:
        return None
    try:
        for peer in response[0]['vrfs'][vrf]['peers']:
            if (response[0]['vrfs'][vrf]['peers'][peer]['peerState'] != 'Established') \
                or (response[0]['vrfs'][vrf]['peers'][peer]["inMsgQueue"] != 0) \
                    or (response[0]['vrfs'][vrf]['peers'][peer]["outMsgQueue"] != 0):
                return False
            count = count + 1
        if count == number:
            return True
        return False
    except KeyError:
        return None

def verify_bgp_ipv6_unicast_state(device, enable_password):
    """
    Verifies all IPv6 unicast BGP sessions are established (for all VRF)
    and all BGP messages queues for these sessions are empty (for all VRF).

    Args:
        device (jsonrpclib.jsonrpc.ServerProxy): Instance of the class jsonrpclib.jsonrpc.ServerProxy with the uri f'https://{username}:{password}@{ip}/command-api'.
        enable_password (str): Enable password.

    Returns:
        bool: `True` if all IPv6 unicast BGP sessions are established (for all VRF)
        and all BGP messages queues for these sessions are empty (for all VRF).
        `False` otherwise.

    """
    try:
        response = device.runCmds(1, ['show bgp ipv6 unicast summary vrf all'], 'json')
    except jsonrpc.AppError:
        return None
    try:
        if len(response[0]['vrfs']) == 0:
            return None
        for vrf in response[0]['vrfs']:
            for peer in response[0]['vrfs'][vrf]['peers']:
                if (response[0]['vrfs'][vrf]['peers'][peer]['peerState'] != 'Established') \
                    or (response[0]['vrfs'][vrf]['peers'][peer]["inMsgQueue"] != 0) or \
                        (response[0]['vrfs'][vrf]['peers'][peer]["outMsgQueue"] != 0):
                    return False
        return True
    except KeyError:
        return None

def verify_bgp_evpn_state(device, enable_password):

    """
    Verifies all EVPN BGP sessions are established (default VRF).

    Args:
        device (jsonrpclib.jsonrpc.ServerProxy): Instance of the class jsonrpclib.jsonrpc.ServerProxy with the uri f'https://{username}:{password}@{ip}/command-api'.
        enable_password (str): Enable password.

    Returns:
        bool: `True` if all EVPN BGP sessions are established.
        `False` otherwise.

    """
    try:
        response = device.runCmds(1, ['show bgp evpn summary'], 'json')
    except jsonrpc.AppError:
        return None
    try:
        if len(response[0]['vrfs']['default']['peers']) == 0:
            return None
        for peer in response[0]['vrfs']['default']['peers']:
            if response[0]['vrfs']['default']['peers'][peer]['peerState'] != 'Established':
                return False
        return True
    except KeyError:
        return None

def verify_bgp_evpn_count(device, enable_password, number):
    """
    Verifies all EVPN BGP sessions are established (default VRF)
    and the actual number of BGP EVPN neighbors is the one we expect (default VRF).

    Args:
        device (jsonrpclib.jsonrpc.ServerProxy): Instance of the class jsonrpclib.jsonrpc.ServerProxy with the uri f'https://{username}:{password}@{ip}/command-api'.
        enable_password (str): Enable password.
        number (int): The expected number of BGP EVPN neighbors in the default VRF.

    Returns:
        bool: `True` if all EVPN BGP sessions are established
        and if the actual number of BGP EVPN neighbors is the one we expect.
        `False` otherwise.

    """
    if not number:
        return None
    try:
        response = device.runCmds(1, ['show bgp evpn summary'], 'json')
    except jsonrpc.AppError:
        return None
    count = 0
    try:
        for peer in response[0]['vrfs']['default']['peers']:
            if response[0]['vrfs']['default']['peers'][peer]['peerState'] != 'Established':
                return False
            count = count + 1
        if count == number:
            return True
        return False
    except KeyError:
        return None

def verify_bgp_rtc_state(device, enable_password):

    """
    Verifies all RTC BGP sessions are established (default VRF).

    Args:
        device (jsonrpclib.jsonrpc.ServerProxy): Instance of the class jsonrpclib.jsonrpc.ServerProxy with the uri f'https://{username}:{password}@{ip}/command-api'.
        enable_password (str): Enable password.

    Returns:
        bool: `True` if all RTC BGP sessions are established.
        `False` otherwise.

    """
    try:
        response = device.runCmds(1, ['show bgp rt-membership summary'], 'json')
    except jsonrpc.AppError:
        return None
    try:
        if len(response[0]['vrfs']['default']['peers']) == 0:
            return None
        for peer in response[0]['vrfs']['default']['peers']:
            if response[0]['vrfs']['default']['peers'][peer]['peerState'] != 'Established':
                return False
        return True
    except KeyError:
        return None

def verify_bgp_rtc_count(device, enable_password, number):
    """
    Verifies all RTC BGP sessions are established (default VRF)
    and the actual number of BGP RTC neighbors is the one we expect (default VRF).

    Args:
        device (jsonrpclib.jsonrpc.ServerProxy): Instance of the class jsonrpclib.jsonrpc.ServerProxy with the uri f'https://{username}:{password}@{ip}/command-api'.
        enable_password (str): Enable password.
        number (int): The expected number of BGP RTC neighbors (default VRF).

    Returns:
        bool: `True` if all RTC BGP sessions are established
        and if the actual number of BGP RTC neighbors is the one we expect.
        `False` otherwise.

    """
    if not number:
        return None
    try:
        response = device.runCmds(1, ['show bgp rt-membership summary'], 'json')
    except jsonrpc.AppError:
        return None
    count = 0
    try:
        for peer in response[0]['vrfs']['default']['peers']:
            if response[0]['vrfs']['default']['peers'][peer]['peerState'] != 'Established':
                return False
            count = count + 1
        if count == number:
            return True
        return False
    except KeyError:
        return None
