from jsonrpclib import jsonrpc

def verify_transceivers_manufacturers(device, enable_password, manufacturers = None):

    """
    Verifies the device is only using transceivers from supported manufacturers.

    Args:
        device (jsonrpclib.jsonrpc.ServerProxy): Instance of the class jsonrpclib.jsonrpc.ServerProxy with the uri f'https://{username}:{password}@{ip}/command-api'.
        enable_password (str): Enable password.
        manufacturers (list): List of allowed transceivers manufacturers.

    Returns:
        bool: `True` if the device is only using transceivers from supported manufacturers.
        `False` otherwise.

    """
    if not manufacturers:
        return None
    try:
        response = device.runCmds(1, ['show inventory'], 'json')
    except jsonrpc.AppError:
        return None
    try:
        for interface in response[0]['xcvrSlots']:
            if response[0]['xcvrSlots'][interface]['mfgName'] not in manufacturers:
                return False
        return True
    except KeyError:
        return None

def verify_system_temperature(device, enable_password):

    """
    Verifies the device temperature is currently OK
    and the device did not report any temperature alarm in the past.

    Args:
        device (jsonrpclib.jsonrpc.ServerProxy): Instance of the class jsonrpclib.jsonrpc.ServerProxy with the uri f'https://{username}:{password}@{ip}/command-api'.
        enable_password (str): Enable password.

    Returns:
        bool: `True` if the device temperature is OK.
        `False` otherwise.

    """
    try:
        response = device.runCmds(1, ['show system environment temperature'], 'json')
    except jsonrpc.AppError:
        return None
    try:
        if response[0]['systemStatus'] != 'temperatureOk':
            return False
        return True
    except KeyError:
        return None

def verify_transceiver_temperature(device, enable_password):

    """
    Verifies the transceivers temperature is currently OK
    and the device did not report any alarm in the past for its transceivers temperature.

    Args:
        device (jsonrpclib.jsonrpc.ServerProxy): Instance of the class jsonrpclib.jsonrpc.ServerProxy with the uri f'https://{username}:{password}@{ip}/command-api'.
        enable_password (str): Enable password.

    Returns:
        bool: `True` if the transceivers temperature of the device is currently OK
        and if the device did not report any alarm in the past for its transceivers temperature.
        `False` otherwise.

    """
    try:
        response = device.runCmds(1, ['show system environment temperature transceiver'], 'json')
    except jsonrpc.AppError:
        return None
    try:
        for sensor in response[0]['tempSensors']:
            if sensor['hwStatus'] != 'ok' or sensor['alertCount'] != 0:
                return False
        return True
    except KeyError:
        return None

def verify_environment_cooling(device, enable_password):

    """
    Verifies the fans status is OK.

    Args:
        device (jsonrpclib.jsonrpc.ServerProxy): Instance of the class jsonrpclib.jsonrpc.ServerProxy with the uri f'https://{username}:{password}@{ip}/command-api'.
        enable_password (str): Enable password.

    Returns:
        bool: `True` if the if the fans status is OK.
        `False` otherwise.

    """
    try:
        response = device.runCmds(1, ['show system environment cooling'], 'json')
    except jsonrpc.AppError:
        return None
    try:
        if response[0]['systemStatus'] != 'coolingOk':
            return False
        return True
    except KeyError:
        return None

def verify_environment_power(device, enable_password):

    """
    Verifies the power supplies status is OK.

    Args:
        device (jsonrpclib.jsonrpc.ServerProxy): Instance of the class jsonrpclib.jsonrpc.ServerProxy with the uri f'https://{username}:{password}@{ip}/command-api'.
        enable_password (str): Enable password.

    Returns:
        bool: `True` if the power supplies is OK.
        `False` otherwise.

    """
    try:
        response = device.runCmds(1, ['show system environment power'], 'json')
    except jsonrpc.AppError:
        return None
    try:
        for powersupply in response[0]['powerSupplies']:
            if response[0]['powerSupplies'][powersupply]['state'] != 'ok':
                return False
        return True
    except KeyError:
        return None

def verify_adverse_drops(device, enable_password):

    """
    Verifies there is no adverse drops on DCS-7280E and DCS-7500E switches.

    Args:
        device (jsonrpclib.jsonrpc.ServerProxy): Instance of the class jsonrpclib.jsonrpc.ServerProxy with the uri f'https://{username}:{password}@{ip}/command-api'.
        enable_password (str): Enable password.

    Returns:
        bool: `True` if the device (DCS-7280E and DCS-7500E) doesnt reports adverse drops.
        `False` if the device (DCS-7280E and DCS-7500E) report adverse drops.

    """
    try:
        response = device.runCmds(1, ['show hardware counter drop'], 'json')
    except jsonrpc.AppError:
        return None
    try:
        if response[0]['totalAdverseDrops'] == 0:
            return True
        return False
    except KeyError:
        return None
