"""
Test functions related to system-level features and protocols
"""
from jsonrpclib import jsonrpc

def verify_uptime(device, enable_password, minimum = None):
    """
    Verifies the device uptime is higher than a value.

    Args:
        device (jsonrpclib.jsonrpc.ServerProxy): Instance of the class jsonrpclib.jsonrpc.ServerProxy with the uri f'https://{username}:{password}@{ip}/command-api'.
        enable_password (str): Enable password.
        minimum (int): Minimum uptime in seconds.

    Returns:
        bool: `True` if the device uptime is higher than the threshold.
        `False` otherwise.

    """
    if not minimum:
        return None
    try:
        response = device.runCmds(1, ['show uptime'], 'json')
    except jsonrpc.AppError:
        return None
    try:
        if response[0]['upTime'] > minimum:
            return True
        return False
    except KeyError:
        return None

def verify_reload_cause(device, enable_password):
    """
    Verifies the last reload of the device was requested by a user.

    Args:
        device (jsonrpclib.jsonrpc.ServerProxy): Instance of the class jsonrpclib.jsonrpc.ServerProxy with the uri f'https://{username}:{password}@{ip}/command-api'.
        enable_password (str): Enable password.

    Returns:
        bool: `True` if the device last reload was requested by a user.
        `False` otherwise.

    """
    try:
        response = device.runCmds(1, ['show version','show reload cause'], 'json')
    except jsonrpc.AppError:
        return None
    try:
        if response[0]['response']['resetCauses'][0]['description'] == 'Reload requested by the user.' or \
           response[0]['response']['resetCauses'][0]['description'] == 'Reload requested after FPGA upgrade':
            return True
        return False
    except KeyError:
        return None

def verify_coredump(device, enable_password):
    """
    Verifies there is no core file.

    Args:
        device (jsonrpclib.jsonrpc.ServerProxy): Instance of the class jsonrpclib.jsonrpc.ServerProxy with the uri f'https://{username}:{password}@{ip}/command-api'.
        enable_password (str): Enable password.

    Returns:
        bool: `True` if the device has no core file. `False` otherwise.

    """
    try:
        response = device.runCmds(1, \
            [{"cmd": "enable", "input": enable_password},'bash timeout 10 ls /var/core'], 'text')
    except jsonrpc.AppError:
        return None
    try:
        if len(response[1]['output']) == 0:
            return True
        return False
    except KeyError:
        return None

def verify_agent_logs(device, enable_password):
    """
    Verifies there is no agent crash reported on the device.

    Args:
        device (jsonrpclib.jsonrpc.ServerProxy): Instance of the class jsonrpclib.jsonrpc.ServerProxy with the uri f'https://{username}:{password}@{ip}/command-api'.
        enable_password (str): Enable password.

    Returns:
        bool: `True` if the device has no agent crash reported.
        `False` otherwise.

    """
    try:
        response = device.runCmds(1, ['show agent logs crash'], 'text')
    except jsonrpc.AppError:
        return None
    try:
        if len(response[0]['output']) == 0:
            return True
        return False
    except KeyError:
        return None

def verify_syslog(device, enable_password):
    """
    Verifies the device had no syslog message with a severity of warning (or a more severe message)
    during the last 7 days.

    Args:
        device (jsonrpclib.jsonrpc.ServerProxy): Instance of the class jsonrpclib.jsonrpc.ServerProxy with the uri f'https://{username}:{password}@{ip}/command-api'.
        enable_password (str): Enable password.

    Returns:
        bool: `True` if the device had no syslog message with a severity of warning (or a more severe message)
        during the last 7 days.
        `False` otherwise.

    """
    try:
        response = device.runCmds(1, ['show logging last 7 days threshold warnings'], 'text')
    except jsonrpc.AppError:
        return None
    try:
        if len(response[0]['output']) == 0:
            return True
        return False
    except KeyError:
        return None

def verify_cpu_utilization(device, enable_password):
    """
    Verifies the CPU utilization is less than 75%.

    Args:
        device (jsonrpclib.jsonrpc.ServerProxy): Instance of the class jsonrpclib.jsonrpc.ServerProxy with the uri f'https://{username}:{password}@{ip}/command-api'.
        enable_password (str): Enable password.

    Returns:
        bool: `True` if the device CPU utilization is less than 75%.
        `False` otherwise.

    """
    try:
        response = device.runCmds(1, ['show processes top once'], 'json')
    except jsonrpc.AppError:
        return None
    try:
        if response[0]['cpuInfo']['%Cpu(s)']['idle'] > 25:
            return True
        return False
    except KeyError:
        return None

def verify_memory_utilization(device, enable_password):
    """
    Verifies the memory utilization is less than 75%.

    Args:
        device (jsonrpclib.jsonrpc.ServerProxy): Instance of the class jsonrpclib.jsonrpc.ServerProxy with the uri f'https://{username}:{password}@{ip}/command-api'.
        enable_password (str): Enable password.

    Returns:
        bool: `True` if the device memory utilization is less than 75%.
        `False` otherwise.

    """
    try:
        response = device.runCmds(1, ['show version'], 'json')
    except jsonrpc.AppError:
        return None
    try:
        if float(response[0]['memFree']) / float(response[0]['memTotal']) > 0.25:
            return True
        return False
    except KeyError:
        return None

def verify_filesystem_utilization(device, enable_password):

    """
    Verifies each partition on the disk is used less than 75%.

    Args:
        device (jsonrpclib.jsonrpc.ServerProxy): Instance of the class jsonrpclib.jsonrpc.ServerProxy with the uri f'https://{username}:{password}@{ip}/command-api'.
        enable_password (str): Enable password.

    Returns:
        bool: `True` if each partition on the disk is used less than 75%.
        `False` otherwise.

    """

    try:
        response = device.runCmds(1, \
            [{"cmd": "enable", "input": enable_password},'bash timeout 10 df -h'], 'text')
    except jsonrpc.AppError:
        return None
    try:
        for line in response[1]['output'].split('\n')[1:]:
            if 'loop' not in line and len(line) > 0:
                if int(line.split()[4].replace('%', '')) > 75:
                    return False
        return True
    except KeyError:
        return None

def verify_ntp(device, enable_password):

    """
    Verifies NTP is synchronised.

    Args:
        device (jsonrpclib.jsonrpc.ServerProxy): Instance of the class jsonrpclib.jsonrpc.ServerProxy with the uri f'https://{username}:{password}@{ip}/command-api'.
        enable_password (str): Enable password.

    Returns:
        bool: `True` if the NTP is synchronised. `False` otherwise.

    """

    try:
        response = device.runCmds(1, ['show ntp status'], 'text')
    except jsonrpc.AppError:
        return None
    try:
        if response[0]['output'].split('\n')[0].split(' ')[0] == 'synchronised':
            return True
        return False
    except KeyError:
        return None
