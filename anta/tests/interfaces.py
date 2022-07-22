"""
Test functions related to the device interfaces
"""
from jsonrpclib import jsonrpc

def verify_interface_utilization(device, enable_password):

    """
    Verifies interfaces utilization is below 75%.

    Args:
        device (jsonrpclib.jsonrpc.ServerProxy): Instance of the class jsonrpclib.jsonrpc.ServerProxy with the uri f'https://{username}:{password}@{ip}/command-api'.
        enable_password (str): Enable password.

    Returns:
        bool: `True` if interfaces utilization is below 75%. `False` otherwise.

    """
    try:
        response = device.runCmds(1, ['show interfaces counters rates'], 'text')
    except jsonrpc.AppError:
        return None
    try:
        for line in response[0]['output'].split('\n')[1:]:
            if len(line) > 0:
                if line.split()[-5] == '-' or line.split()[-2] == '-':
                    pass
                elif float(line.split()[-5].replace('%', '')) > 75.0:
                    return False
                elif float(line.split()[-2].replace('%', '')) > 75.0:
                    return False
        return True
    except KeyError:
        return None

def verify_interface_errors(device, enable_password):

    """
    Verifies interfaces error counters are equal to zero.

    Args:
        device (jsonrpclib.jsonrpc.ServerProxy): Instance of the class jsonrpclib.jsonrpc.ServerProxy with the uri f'https://{username}:{password}@{ip}/command-api'.
        enable_password (str): Enable password.

    Returns:
        bool: `True` if the interfaces error counters are equal to zero.
        `False` otherwise.

    """
    try:
        response = device.runCmds(1, ['show interfaces counters errors'], 'json')
    except jsonrpc.AppError:
        return None
    try:
        for interface in response[0]['interfaceErrorCounters']:
            for counter in response[0]['interfaceErrorCounters'][interface]:
                if response[0]['interfaceErrorCounters'][interface][counter] != 0:
                    return False
        return True
    except KeyError:
        return None

def verify_interface_discards(device, enable_password):

    """
    Verifies interfaces packet discard counters are equal to zero.

    Args:
        device (jsonrpclib.jsonrpc.ServerProxy): Instance of the class jsonrpclib.jsonrpc.ServerProxy with the uri f'https://{username}:{password}@{ip}/command-api'.
        enable_password (str): Enable password.

    Returns:
        bool: `True` if the interfaces packet discard counters are equal to zero.
        `False` otherwise.

    """
    try:
        response = device.runCmds(1, ['show interfaces counters discards'], 'json')
    except jsonrpc.AppError:
        return None
    try:
        for interface in response[0]['interfaces']:
            for counter in response[0]['interfaces'][interface]:
                if response[0]['interfaces'][interface][counter] != 0:
                    return False
        return True
    except KeyError:
        return None

def verify_interface_errdisabled(device, enable_password):

    """
    Verifies there is no interface in error disable state.

    Args:
        device (jsonrpclib.jsonrpc.ServerProxy): Instance of the class jsonrpclib.jsonrpc.ServerProxy with the uri f'https://{username}:{password}@{ip}/command-api'.
        enable_password (str): Enable password.

    Returns:
        bool: `True` if there is no interface in error disable state..
        `False` otherwise.

    """

    try:
        response = device.runCmds(1, ['show interfaces status'], 'json')
    except jsonrpc.AppError:
        return None
    try:
        for interface in response[0]['interfaceStatuses']:
            if response[0]['interfaceStatuses'][interface]['linkStatus'] == 'errdisabled':
                return False
        return True
    except KeyError:
        return None

def verify_interfaces_status(device, enable_password, minimum = None):
    """
    Verifies the number of Ethernet interfaces up/up on the device is higher or equal than a value.

    Args:
        device (jsonrpclib.jsonrpc.ServerProxy): Instance of the class jsonrpclib.jsonrpc.ServerProxy with the uri f'https://{username}:{password}@{ip}/command-api'.
        enable_password (str): Enable password.
        minimum (int): Expected minimum number of Ethernet interfaces up/up

    Returns:
        bool: `True` if the number of Ethernet interfaces up/up on the device is higher or equal
        than the provided value.
        `False` otherwise.

    """
    if not minimum:
        return None
    try:
        response = device.runCmds(1, ['show interfaces description'], 'json')
    except jsonrpc.AppError:
        return None
    nbr = 0
    try:
        for item in response[0]['interfaceDescriptions']:
            if ('Ethernet' in item) \
                and (response[0]['interfaceDescriptions'][item]['lineProtocolStatus'] == 'up')\
                and (response[0]['interfaceDescriptions'][item]['interfaceStatus'] == 'up'):
                nbr = nbr + 1
        if nbr >= minimum:
            return True
        return False
    except KeyError:
        return None

def verify_storm_control_drops(device, enable_password):
    """
    Verifies the device did not drop packets due its to storm-control configuration.

    Args:
        device (jsonrpclib.jsonrpc.ServerProxy): Instance of the class jsonrpclib.jsonrpc.ServerProxy with the uri f'https://{username}:{password}@{ip}/command-api'.
        enable_password (str): Enable password.

    Returns:
        bool: `True` if the device did not drop packet due to its storm-control configuration.
        `False` otherwise.

    """
    try:
        response = device.runCmds(1, ['show storm-control'], 'json')
    except jsonrpc.AppError:
        return None
    try:
        for interface in response[0]['interfaces']:
            for traffic_type in ['all', 'unknown-unicast', 'multicast', 'broadcast']:
                if traffic_type in response[0]['interfaces'][interface]["trafficTypes"]:
                    if 'drop' in response[0]['interfaces'][interface]["trafficTypes"][traffic_type] \
                        and response[0]['interfaces'][interface]["trafficTypes"][traffic_type]['drop'] != 0:
                        return False
        return True
    except KeyError:
        return None

def verify_portchannels(device, enable_password):

    """
    Verifies there is no inactive port in port channels.

    Args:
        device (jsonrpclib.jsonrpc.ServerProxy): Instance of the class jsonrpclib.jsonrpc.ServerProxy with the uri f'https://{username}:{password}@{ip}/command-api'.
        enable_password (str): Enable password.

    Returns:
        bool: `True` if there is no inactive port in port channels.
        `False` otherwise.

    """
    try:
        response = device.runCmds(1, ['show port-channel'], 'json')
    except jsonrpc.AppError:
        return None
    try:
        if len(response[0]['portChannels']) == 0:
            return None
        for portchannel in response[0]['portChannels']:
            if len(response[0]['portChannels'][portchannel]['inactivePorts']) != 0:
                return False
        return True
    except KeyError:
        return None

def verify_illegal_lacp(device, enable_password):

    """
    Verifies there is no illegal LACP packets received.

    Args:
        device (jsonrpclib.jsonrpc.ServerProxy): Instance of the class jsonrpclib.jsonrpc.ServerProxy with the uri f'https://{username}:{password}@{ip}/command-api'.
        enable_password (str): Enable password.

    Returns:
        bool: `True` if there is no illegal LACP packets received.
        `False` otherwise.

    """

    try:
        response = device.runCmds(1, ['show lacp counters all-ports'], 'json')
    except jsonrpc.AppError:
        return None
    try:
        if len(response[0]['portChannels']) == 0:
            return None
        for portchannel in response[0]['portChannels']:
            for interface in response[0]['portChannels'][portchannel]['interfaces']:
                if response[0]['portChannels'][portchannel]['interfaces'][interface]['illegalRxCount'] != 0:
                    return False
        return True
    except KeyError:
        return None

def verify_loopback_count(device, enable_password, number = None):
    """
    Verifies the number of loopback interfaces on the device is the one we expect.
    And if none of the loopback is down.

    Args:
        device (jsonrpclib.jsonrpc.ServerProxy): Instance of the class jsonrpclib.jsonrpc.ServerProxy with the uri f'https://{username}:{password}@{ip}/command-api'.
        enable_password (str): Enable password.
        number (int): Expected number of loopback interfaces.

    Returns:
        bool: `True` if the device is running an allowed EOS version.
        `False` otherwise.

    """
    if not number:
        return None
    try:
        response = device.runCmds(1, ['show ip interface brief  | include Loopback'], 'text')
    except jsonrpc.AppError:
        return None
    try:
        if (response[0]['output'].count('\n') == number) and (response[0]['output'].count('down') == 0) :
            return True
        return False
    except KeyError:
        return None

def verify_svi(device, enable_password):
    """
    Verifies there is no interface vlan down.

    Args:
        device (jsonrpclib.jsonrpc.ServerProxy): Instance of the class jsonrpclib.jsonrpc.ServerProxy with the uri f'https://{username}:{password}@{ip}/command-api'.
        enable_password (str): Enable password.

    Returns:
        bool: `True` if there is no interface vlan down. `False` otherwise.
    """
    try:
        response = device.runCmds(1, ['show ip interface brief | include Vl'], 'text')
    except jsonrpc.AppError:
        return None
    try:
        if response[0]['output'].count('down') == 0:
            return True
        return False
    except KeyError:
        return None

def verify_spanning_tree_blocked_ports(device, enable_password):

    """
    Verifies there is no spanning-tree blocked ports.

    Args:
        device (jsonrpclib.jsonrpc.ServerProxy): Instance of the class jsonrpclib.jsonrpc.ServerProxy with the uri f'https://{username}:{password}@{ip}/command-api'.
        enable_password (str): Enable password.

    Returns:
        bool: `True` there is no spanning-tree blocked ports.
        `False` otherwise.
    """
    try:
        response = device.runCmds(1, ['show spanning-tree blockedports'], 'json')
    except jsonrpc.AppError:
        return None
    try:
        if len(response[0]['spanningTreeInstances']) == 0:
            return True
        return False
    except KeyError:
        return None
