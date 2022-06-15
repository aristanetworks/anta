"""
Module that defines various functions to test EOS devices.
"""
def verify_eos_version(device, enable_password, versions = None):
    """
    Verifies the device is running one of the allowed EOS version.

    Args:
        device (jsonrpclib.jsonrpc.ServerProxy):
        Instance of the class jsonrpclib.jsonrpc.ServerProxy with the uri
        'https://%s:%s@%s/command-api' %(username, password, ip).
        enable_password (str): Enable password.
        versions (list): List of allowed EOS versions.

    Returns:
        bool: `True` if the device is running an allowed EOS version.
        `False` otherwise.

    """
    if not versions:
        return None
    try:
        response = device.runCmds(1, ['show version'], 'json')
        if response[0]['version'] in versions:
            return True
        return False
    except:
        return None

def verify_terminattr_version(device, enable_password, versions = None):
    """
    Verifies the device is running one of the allowed TerminAttr version.

    Args:
        device (jsonrpclib.jsonrpc.ServerProxy):
        Instance of the class jsonrpclib.jsonrpc.ServerProxy with the uri
        'https://%s:%s@%s/command-api' %(username, password, ip).
        enable_password (str): Enable password.
        versions (list): List of allowed TerminAttr versions.

    Returns:
        bool: `True` if the device is running an allowed TerminAttr version. `False` otherwise.

    """
    if not versions:
        return None
    try:
        response = device.runCmds(1, ['show version detail'], 'json')
        if response[0]['details']['packages']['TerminAttr-core']['version'] in versions:
            return True
        return False
    except:
        return None

def verify_eos_extensions(device, enable_password):
    """
    Verifies all EOS extensions installed on the device are enabled for boot persistence.

    Args:
        device (jsonrpclib.jsonrpc.ServerProxy):
        Instance of the class jsonrpclib.jsonrpc.ServerProxy with the uri
        'https://%s:%s@%s/command-api' %(username, password, ip).
        enable_password (str): Enable password.

    Returns:
        bool: `True` if the device has all installed its EOS extensions enabled for boot persistence.
        `False` otherwise.

    """
    try:
        response = device.runCmds(1, ['show extensions', 'show boot-extensions'], 'json')
        installed_extensions = []
        boot_extensions = []
        for extension in response[0]['extensions']:
            if response[0]['extensions'][extension]['status'] == 'installed':
                installed_extensions.append(extension)
        for extension in response[1]['extensions']:
            extension = extension.strip('\n')
            if extension == '':
                pass
            else:
                boot_extensions.append(extension)
        installed_extensions.sort()
        boot_extensions.sort()
        if installed_extensions == boot_extensions:
            return True
        return False
    except:
        return None

def verify_field_notice_44_resolution(device, enable_password):
    """
    Verifies the device is using an Aboot version that fix the bug discussed
    in the field notice 44 (Aboot manages system settings prior to EOS initialization).

    Args:
        device (jsonrpclib.jsonrpc.ServerProxy):
        Instance of the class jsonrpclib.jsonrpc.ServerProxy with the uri
        'https://%s:%s@%s/command-api' %(username, password, ip).
        enable_password (str): Enable password.

    Returns:
        bool: `True` if the device is using an Aboot version that fix the bug discussed
        in the field notice 44 or if the device model is not affected.
        `False` otherwise.

    """
    try:
        response = device.runCmds(1, ['show version detail'], 'json')
        devices = ['DCS-7010T-48',
                   'DCS-7010T-48-DC',
                   'DCS-7050TX-48',
                   'DCS-7050TX-64',
                   'DCS-7050TX-72',
                   'DCS-7050TX-72Q',
                   'DCS-7050TX-96',
                   'DCS-7050TX2-128',
                   'DCS-7050SX-64',
                   'DCS-7050SX-72',
                   'DCS-7050SX-72Q',
                   'DCS-7050SX2-72Q',
                   'DCS-7050SX-96',
                   'DCS-7050SX2-128',
                   'DCS-7050QX-32S',
                   'DCS-7050QX2-32S',
                   'DCS-7050SX3-48YC12',
                   'DCS-7050CX3-32S',
                   'DCS-7060CX-32S',
                   'DCS-7060CX2-32S',
                   'DCS-7060SX2-48YC6',
                   'DCS-7160-48YC6',
                   'DCS-7160-48TC6',
                   'DCS-7160-32CQ',
                   'DCS-7280SE-64',
                   'DCS-7280SE-68',
                   'DCS-7280SE-72',
                   'DCS-7150SC-24-CLD',
                   'DCS-7150SC-64-CLD',
                   'DCS-7020TR-48',
                   'DCS-7020TRA-48',
                   'DCS-7020SR-24C2',
                   'DCS-7020SRG-24C2',
                   'DCS-7280TR-48C6',
                   'DCS-7280TRA-48C6',
                   'DCS-7280SR-48C6',
                   'DCS-7280SRA-48C6',
                   'DCS-7280SRAM-48C6',
                   'DCS-7280SR2K-48C6-M',
                   'DCS-7280SR2-48YC6',
                   'DCS-7280SR2A-48YC6',
                   'DCS-7280SRM-40CX2',
                   'DCS-7280QR-C36',
                   'DCS-7280QRA-C36S']
        variants = ['-SSD-F',
                    '-SSD-R',
                    '-M-F',
                    '-M-R',
                    '-F',
                    '-R']
        model = response[0]['modelName']
        for variant in variants:
            model = model.replace(variant, '')
        if model not in devices:
            return True
        else:
            for component in response[0]['details']['components']:
                if component['name'] == 'Aboot':
                    aboot_version = component['version'].split('-')[2]
            if aboot_version.startswith('4.0.') and int(aboot_version.split('.')[2]) < 7:
                return False
            elif aboot_version.startswith('4.1.') and int(aboot_version.split('.')[2]) < 1:
                return False
            elif aboot_version.startswith('6.0.') and int(aboot_version.split('.')[2]) < 9:
                return False
            elif aboot_version.startswith('6.1.') and int(aboot_version.split('.')[2]) < 7:
                return False
            else:
                return True
    except:
        return None

def verify_uptime(device, enable_password, minimum = None):
    """
    Verifies the device uptime is higher than a value.

    Args:
        device (jsonrpclib.jsonrpc.ServerProxy):
        Instance of the class jsonrpclib.jsonrpc.ServerProxy with the uri
        'https://%s:%s@%s/command-api' %(username, password, ip).
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
        if response[0]['upTime'] > minimum:
            return True
        return False
    except:
        return None

def verify_reload_cause(device, enable_password):
    """
    Verifies the last reload of the device was requested by a user.

    Args:
        device (jsonrpclib.jsonrpc.ServerProxy):
        Instance of the class jsonrpclib.jsonrpc.ServerProxy with the uri
        'https://%s:%s@%s/command-api' %(username, password, ip).
        enable_password (str): Enable password.

    Returns:
        bool: `True` if the device last reload was requested by a user.
        `False` otherwise.

    """
    try:
        response = device.runCmds(1, ['show version','show reload cause'], 'json')
        if response[0]['resetCauses'][0]['description'] == 'Reload requested by the user.':
            return True
        return False
    except:
        return None

def verify_coredump(device, enable_password):
    """
    Verifies there is no core file.

    Args:
        device (jsonrpclib.jsonrpc.ServerProxy):
        Instance of the class jsonrpclib.jsonrpc.ServerProxy with the uri
        'https://%s:%s@%s/command-api' %(username, password, ip).
        enable_password (str): Enable password.

    Returns:
        bool: `True` if the device has no core file. `False` otherwise.

    """
    try:
        response = device.runCmds(1, \
            [{"cmd": "enable", "input": enable_password},'bash timeout 10 ls /var/core'], 'text')
        if len(response[1]['output']) == 0:
            return True
        return False
    except:
        return None

def verify_agent_logs(device, enable_password):
    """
    Verifies there is no agent crash reported on the device.

    Args:
        device (jsonrpclib.jsonrpc.ServerProxy):
        Instance of the class jsonrpclib.jsonrpc.ServerProxy with the uri
        'https://%s:%s@%s/command-api' %(username, password, ip).
        enable_password (str): Enable password.

    Returns:
        bool: `True` if the device has no agent crash reported.
        `False` otherwise.

    """
    try:
        response = device.runCmds(1, ['show agent logs crash'], 'text')
        if len(response[0]['output']) == 0:
            return True
        return False
    except:
        return None

def verify_syslog(device, enable_password):
    """
    Verifies the device had no syslog message with a severity of warning (or a more severe message)
    during the last 7 days.

    Args:
        device (jsonrpclib.jsonrpc.ServerProxy):
        Instance of the class jsonrpclib.jsonrpc.ServerProxy with the uri
        'https://%s:%s@%s/command-api' %(username, password, ip).
        enable_password (str): Enable password.

    Returns:
        bool: `True` if the device had no syslog message with a severity of warning (or a more severe message)
        during the last 7 days.
        `False` otherwise.

    """
    try:
        response = device.runCmds(1, ['show logging last 7 days threshold warnings'], 'text')
        if len(response[0]['output']) == 0:
            return True
        return False
    except:
        return None

def verify_cpu_utilization(device, enable_password):
    """
    Verifies the CPU utilization is less than 75%.

    Args:
        device (jsonrpclib.jsonrpc.ServerProxy):
        Instance of the class jsonrpclib.jsonrpc.ServerProxy with the uri
        'https://%s:%s@%s/command-api' %(username, password, ip).
        enable_password (str): Enable password.

    Returns:
        bool: `True` if the device CPU utilization is less than 75%.
        `False` otherwise.

    """
    try:
        response = device.runCmds(1, ['show processes top once'], 'json')
        if response[0]['cpuInfo']['%Cpu(s)']['idle'] > 25:
            return True
        return False
    except:
        return None

def verify_memory_utilization(device, enable_password):
    """
    Verifies the memory utilization is less than 75%.

    Args:
        device (jsonrpclib.jsonrpc.ServerProxy):
        Instance of the class jsonrpclib.jsonrpc.ServerProxy with the uri
        'https://%s:%s@%s/command-api' %(username, password, ip).
        enable_password (str): Enable password.

    Returns:
        bool: `True` if the device memory utilization is less than 75%.
        `False` otherwise.

    """
    try:
        response = device.runCmds(1, ['show version'], 'json')
        if float(response[0]['memFree']) / float(response[0]['memTotal']) > 0.25:
            return True
        return False
    except:
        return None

def verify_filesystem_utilization(device, enable_password):

    """
    Verifies each partition on the disk is used less than 75%.

    Args:
        device (jsonrpclib.jsonrpc.ServerProxy):
        Instance of the class jsonrpclib.jsonrpc.ServerProxy with the uri
        'https://%s:%s@%s/command-api' %(username, password, ip).
        enable_password (str): Enable password.

    Returns:
        bool: `True` if each partition on the disk is used less than 75%.
        `False` otherwise.

    """

    try:
        response = device.runCmds(1, \
            [{"cmd": "enable", "input": enable_password},'bash timeout 10 df -h'], 'text')
        for line in response[1]['output'].split('\n')[1:]:
            if 'loop' not in line and len(line) > 0:
                if int(line.split()[4].replace('%', '')) > 75:
                    return False
        return True
    except:
        return None

def verify_transceivers_manufacturers(device, enable_password, manufacturers = None):

    """
    Verifies the device is only using transceivers from supported manufacturers.

    Args:
        device (jsonrpclib.jsonrpc.ServerProxy):
        Instance of the class jsonrpclib.jsonrpc.ServerProxy with the uri
        'https://%s:%s@%s/command-api' %(username, password, ip).
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
        for interface in response[0]['xcvrSlots']:
            if response[0]['xcvrSlots'][interface]['mfgName'] not in manufacturers:
                return False
        return True
    except:
        return None

def verify_system_temperature(device, enable_password):

    """
    Verifies the device temperature is currently OK
    and the device did not report any temperature alarm in the past.

    Args:
        device (jsonrpclib.jsonrpc.ServerProxy):
        Instance of the class jsonrpclib.jsonrpc.ServerProxy with the uri
        'https://%s:%s@%s/command-api' %(username, password, ip).
        enable_password (str): Enable password.

    Returns:
        bool: `True` if the device temperature is OK.
        `False` otherwise.

    """
    try:
        response = device.runCmds(1, ['show system environment temperature'], 'json')
        if response[0]['systemStatus'] != 'temperatureOk':
            return False
        else:
            return True
    except:
        return None

def verify_transceiver_temperature(device, enable_password):

    """
    Verifies the transceivers temperature is currently OK
    and the device did not report any alarm in the past for its transceivers temperature.

    Args:
        device (jsonrpclib.jsonrpc.ServerProxy):
        Instance of the class jsonrpclib.jsonrpc.ServerProxy with the uri
        'https://%s:%s@%s/command-api' %(username, password, ip).
        enable_password (str): Enable password.

    Returns:
        bool: `True` if the transceivers temperature of the device is currently OK
        and if the device did not report any alarm in the past for its transceivers temperature.
        `False` otherwise.

    """
    try:
        response = device.runCmds(1, ['show system environment temperature transceiver'], 'json')
        for sensor in response[0]['tempSensors']:
            if sensor['hwStatus'] != 'ok' or sensor['alertCount'] != 0:
                return False
        return True
    except:
        return None

def verify_environment_cooling(device, enable_password):

    """
    Verifies the fans status is OK.

    Args:
        device (jsonrpclib.jsonrpc.ServerProxy):
        Instance of the class jsonrpclib.jsonrpc.ServerProxy with the uri
        'https://%s:%s@%s/command-api' %(username, password, ip).
        enable_password (str): Enable password.

    Returns:
        bool: `True` if the if the fans status is OK.
        `False` otherwise.

    """
    try:
        response = device.runCmds(1, ['show system environment cooling'], 'json')
        if response[0]['systemStatus'] != 'coolingOk':
            return False
        else:
            return True
    except:
        return None

def verify_environment_power(device, enable_password):

    """
    Verifies the power supplies status is OK.

    Args:
        device (jsonrpclib.jsonrpc.ServerProxy):
        Instance of the class jsonrpclib.jsonrpc.ServerProxy with the uri
        'https://%s:%s@%s/command-api' %(username, password, ip).
        enable_password (str): Enable password.

    Returns:
        bool: `True` if the power supplies is OK.
        `False` otherwise.

    """
    try:
        response = device.runCmds(1, ['show system environment power'], 'json')
        for powersupply in response[0]['powerSupplies']:
            if response[0]['powerSupplies'][powersupply]['state'] != 'ok':
                return False
        return True
    except:
        return None

def verify_zerotouch(device, enable_password):

    """
    Verifies ZeroTouch is disabled.

    Args:
        device (jsonrpclib.jsonrpc.ServerProxy):
        Instance of the class jsonrpclib.jsonrpc.ServerProxy with the uri
        'https://%s:%s@%s/command-api' %(username, password, ip).
        enable_password (str): Enable password.

    Returns:
        bool: `True` if ZeroTouch is disabled.
        `False` otherwise.

    """
    try:
        response = device.runCmds(1, ['show zerotouch'], 'json')
        if response[0]['mode'] == 'disabled':
            return True
        return False
    except:
        return None

def verify_running_config_diffs(device, enable_password):

    """
    Verifies there is no difference between the running-config and the startup-config.

    Args:
        device (jsonrpclib.jsonrpc.ServerProxy):
        Instance of the class jsonrpclib.jsonrpc.ServerProxy with the uri
        'https://%s:%s@%s/command-api' %(username, password, ip).
        enable_password (str): Enable password.

    Returns:
        bool: `True` if there is no difference between the running-config and the startup-config.
        `False` otherwise.

    """
    try:
        response = device.runCmds(1, \
            [{"cmd": "enable", "input": enable_password},'show running-config diffs'], 'text')
        if len(response[1]['output']) == 0:
            return True
        return False
    except:
        return None

def verify_unified_forwarding_table_mode(device, enable_password, mode = None):

    """
    Verifies the device is using the expected Unified Forwarding Table mode.

    Args:
        device (jsonrpclib.jsonrpc.ServerProxy):
        Instance of the class jsonrpclib.jsonrpc.ServerProxy with the uri
        'https://%s:%s@%s/command-api' %(username, password, ip).
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
        if response[0]['uftMode'] == str(mode):
            return True
        return False
    except:
        return None

def verify_tcam_profile(device, enable_password, profile):

    """
    Verifies the configured TCAM profile is the expected one.

    Args:
        device (jsonrpclib.jsonrpc.ServerProxy):
        Instance of the class jsonrpclib.jsonrpc.ServerProxy with the uri
        'https://%s:%s@%s/command-api' %(username, password, ip).
        enable_password (str): Enable password.
        profile (str): The expected TCAM profile.

    Returns:
        bool: `True` if the device is configured with the expected TCAM profile.
        `False` otherwise.

    """
    try:
        response = device.runCmds(1, ['show hardware tcam profile'], 'json')
        if (response[0]['pmfProfiles']['FixedSystem']['status'] == response[0]['pmfProfiles']['FixedSystem']['config'])\
            and (response[0]['pmfProfiles']['FixedSystem']['status'] == profile):
            return True
        return False
    except:
        return None

def verify_adverse_drops(device, enable_password):

    """
    Verifies there is no adverse drops on DCS-7280E and DCS-7500E switches.

    Args:
        device (jsonrpclib.jsonrpc.ServerProxy):
        Instance of the class jsonrpclib.jsonrpc.ServerProxy with the uri
        'https://%s:%s@%s/command-api' %(username, password, ip).
        enable_password (str): Enable password.

    Returns:
        bool: `True` if the device (DCS-7280E and DCS-7500E) doesnt reports adverse drops.
        `False` if the device (DCS-7280E and DCS-7500E) report adverse drops.

    """

    try:
        response = device.runCmds(1, ['show hardware counter drop'], 'json')
        if response[0]['totalAdverseDrops'] == 0:
            return True
        return False
    except:
        return None

def verify_ntp(device, enable_password):

    """
    Verifies NTP is synchronised.

    Args:
        device (jsonrpclib.jsonrpc.ServerProxy):
        Instance of the class jsonrpclib.jsonrpc.ServerProxy with the uri
        'https://%s:%s@%s/command-api' %(username, password, ip).
        enable_password (str): Enable password.

    Returns:
        bool: `True` if the NTP is synchronised. `False` otherwise.

    """

    try:
        response = device.runCmds(1, ['show ntp status'], 'text')
        if response[0]['output'].split('\n')[0].split(' ')[0] == 'synchronised':
            return True
        return False
    except:
        return None

def verify_interface_utilization(device, enable_password):

    """
    Verifies interfaces utilization is below 75%.

    Args:
        device (jsonrpclib.jsonrpc.ServerProxy):
        Instance of the class jsonrpclib.jsonrpc.ServerProxy with the uri
        'https://%s:%s@%s/command-api' %(username, password, ip).
        enable_password (str): Enable password.

    Returns:
        bool: `True` if interfaces utilization is below 75%. `False` otherwise.

    """
    try:
        response = device.runCmds(1, ['show interfaces counters rates'], 'text')
        for line in response[0]['output'].split('\n')[1:]:
            if len(line) > 0:
                if line.split()[-5] == '-' or line.split()[-2] == '-':
                    pass
                elif float(line.split()[-5].replace('%', '')) > 75.0:
                    return False
                elif float(line.split()[-2].replace('%', '')) > 75.0:
                    return False
        return True
    except:
        return None

def verify_interface_errors(device, enable_password):

    """
    Verifies interfaces error counters are equal to zero.

    Args:
        device (jsonrpclib.jsonrpc.ServerProxy):
        Instance of the class jsonrpclib.jsonrpc.ServerProxy with the uri
        'https://%s:%s@%s/command-api' %(username, password, ip).
        enable_password (str): Enable password.

    Returns:
        bool: `True` if the interfaces error counters are equal to zero.
        `False` otherwise.

    """
    try:
        response = device.runCmds(1, ['show interfaces counters errors'], 'json')
        for interface in response[0]['interfaceErrorCounters']:
            for counter in response[0]['interfaceErrorCounters'][interface]:
                if response[0]['interfaceErrorCounters'][interface][counter] != 0:
                    return False
        return True
    except:
        return None

def verify_interface_discards(device, enable_password):

    """
    Verifies interfaces packet discard counters are equal to zero.

    Args:
        device (jsonrpclib.jsonrpc.ServerProxy):
        Instance of the class jsonrpclib.jsonrpc.ServerProxy with the uri
        'https://%s:%s@%s/command-api' %(username, password, ip).
        enable_password (str): Enable password.

    Returns:
        bool: `True` if the interfaces packet discard counters are equal to zero.
        `False` otherwise.

    """
    try:
        response = device.runCmds(1, ['show interfaces counters discards'], 'json')
        for interface in response[0]['interfaces']:
            for counter in response[0]['interfaces'][interface]:
                if response[0]['interfaces'][interface][counter] != 0:
                    return False
        return True
    except:
        return None

def verify_interface_errdisabled(device, enable_password):

    """
    Verifies there is no interface in error disable state.

    Args:
        device (jsonrpclib.jsonrpc.ServerProxy):
        Instance of the class jsonrpclib.jsonrpc.ServerProxy with the uri
        'https://%s:%s@%s/command-api' %(username, password, ip).
        enable_password (str): Enable password.

    Returns:
        bool: `True` if there is no interface in error disable state..
        `False` otherwise.

    """

    try:
        response = device.runCmds(1, ['show interfaces status'], 'json')
        for interface in response[0]['interfaceStatuses']:
            if response[0]['interfaceStatuses'][interface]['linkStatus'] == 'errdisabled':
                return False
        return True
    except:
        return None

def verify_interfaces_status(device, enable_password, minimum = None):
    """
    Verifies the number of Ethernet interfaces up/up on the device is higher or equal than a value.

    Args:
        device (jsonrpclib.jsonrpc.ServerProxy):
        Instance of the class jsonrpclib.jsonrpc.ServerProxy with the uri
        'https://%s:%s@%s/command-api' %(username, password, ip).
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
        nbr = 0
        for item in response[0]['interfaceDescriptions']:
            if ('Ethernet' in item) \
                and (response[0]['interfaceDescriptions'][item]['lineProtocolStatus'] == 'up')\
                and (response[0]['interfaceDescriptions'][item]['interfaceStatus'] == 'up'):
                nbr = nbr + 1
        if nbr >= minimum:
            return True
        return False
    except:
        return None


def verify_storm_control_drops(device, enable_password):
    """
    Verifies the device did not drop packets due its to storm-control configuration.

    Args:
        device (jsonrpclib.jsonrpc.ServerProxy):
        Instance of the class jsonrpclib.jsonrpc.ServerProxy with the uri
        'https://%s:%s@%s/command-api' %(username, password, ip).
        enable_password (str): Enable password.

    Returns:
        bool: `True` if the device did not drop packet due to its storm-control configuration.
        `False` otherwise.

    """
    try:
        response = device.runCmds(1, ['show storm-control'], 'json')
        for interface in response[0]['interfaces']:
            for traffic_type in ['all', 'unknown-unicast', 'multicast', 'broadcast']:
                if traffic_type in response[0]['interfaces'][interface]["trafficTypes"]:
                    if 'drop' in response[0]['interfaces'][interface]["trafficTypes"][traffic_type] \
                        and response[0]['interfaces'][interface]["trafficTypes"][traffic_type]['drop'] != 0:
                        return False
        return True
    except:
        return None

def verify_portchannels(device, enable_password):

    """
    Verifies there is no inactive port in port channels.

    Args:
        device (jsonrpclib.jsonrpc.ServerProxy):
        Instance of the class jsonrpclib.jsonrpc.ServerProxy with the uri
        'https://%s:%s@%s/command-api' %(username, password, ip).
        enable_password (str): Enable password.

    Returns:
        bool: `True` if there is no inactive port in port channels.
        `False` otherwise.

    """
    try:
        response = device.runCmds(1, ['show port-channel'], 'json')
        if len(response[0]['portChannels']) == 0:
            return None
        else:
            for portchannel in response[0]['portChannels']:
                if len(response[0]['portChannels'][portchannel]['inactivePorts']) != 0:
                    return False
            return True
    except:
        return None

def verify_illegal_lacp(device, enable_password):

    """
    Verifies there is no illegal LACP packets received.

    Args:
        device (jsonrpclib.jsonrpc.ServerProxy):
        Instance of the class jsonrpclib.jsonrpc.ServerProxy with the uri
        'https://%s:%s@%s/command-api' %(username, password, ip).
        enable_password (str): Enable password.

    Returns:
        bool: `True` if there is no illegal LACP packets received.
        `False` otherwise.

    """

    try:
        response = device.runCmds(1, ['show lacp counters all-ports'], 'json')
        if len(response[0]['portChannels']) == 0:
            return None
        else:
            for portchannel in response[0]['portChannels']:
                for interface in response[0]['portChannels'][portchannel]['interfaces']:
                    if response[0]['portChannels'][portchannel]['interfaces'][interface]['illegalRxCount'] != 0:
                        return False
            return True
    except:
        return None

def verify_mlag_status(device, enable_password):

    """
    Verifies the MLAG status:
    state is active, negotiation status is connected, local int is up, peer link is up.

    Args:
        device (jsonrpclib.jsonrpc.ServerProxy):
        Instance of the class jsonrpclib.jsonrpc.ServerProxy with the uri
        'https://%s:%s@%s/command-api' %(username, password, ip).
        enable_password (str): Enable password.

    Returns:
        bool: `True` if the MLAG status is OK.
        `False` otherwise.

    """
    try:
        response = device.runCmds(1, ['show mlag'], 'json')
        if response[0]['state'] == 'disabled':
            return None
        elif response[0]['state'] != 'active':
            return False
        elif response[0]['negStatus'] != 'connected':
            return False
        elif response[0]['localIntfStatus'] != 'up':
            return False
        elif response[0]['peerLinkStatus'] != 'up':
            return False
        else:
            return True
    except:
        return None

def verify_mlag_interfaces(device, enable_password):
    """
    Verifies there is no inactive or active-partial MLAG interfaces.

    Args:
        device (jsonrpclib.jsonrpc.ServerProxy):
        Instance of the class jsonrpclib.jsonrpc.ServerProxy with the uri
        'https://%s:%s@%s/command-api' %(username, password, ip).
        enable_password (str): Enable password.

    Returns:
        bool: `True` if there is no inactive or active-partial MLAG interfaces.
        `False` otherwise.

    """
    try:
        response = device.runCmds(1, ['show mlag'], 'json')
        if response[0]['state'] == 'disabled':
            return None
        elif response[0]['mlagPorts']['Inactive'] != 0:
            return False
        elif response[0]['mlagPorts']['Active-partial'] != 0:
            return False
        else:
            return True
    except:
        return None


def verify_mlag_config_sanity(device, enable_password):
    """
    Verifies there is no MLAG config-sanity warnings.

    Args:
        device (jsonrpclib.jsonrpc.ServerProxy):
        Instance of the class jsonrpclib.jsonrpc.ServerProxy with the uri
        'https://%s:%s@%s/command-api' %(username, password, ip).
        enable_password (str): Enable password.

    Returns:
        bool: `True` if there is no MLAG config-sanity warnings.
        `False` otherwise.
    """
    try:
        response = device.runCmds(1, ['show mlag config-sanity'],'json')
        if response[0]['response']['mlagActive'] is False:
            # MLAG isn't running
            return None
        else:
            if len(response[0]['response']['globalConfiguration']) > 0 or \
                len(response[0]['response']['interfaceConfiguration']) > 0:
                return False
            else:
                return True
    except:
        return None


def verify_loopback_count(device, enable_password, number = None):
    """
    Verifies the number of loopback interfaces on the device is the one we expect.
    And if none of the loopback is down.

    Args:
        device (jsonrpclib.jsonrpc.ServerProxy):
        Instance of the class jsonrpclib.jsonrpc.ServerProxy with the uri
        'https://%s:%s@%s/command-api' %(username, password, ip).
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
        if (response[0]['output'].count('\n') == number) and (response[0]['output'].count('down') == 0) :
            return True
        return False
    except:
        return None

def verify_vxlan(device, enable_password):
    """
    Verifies the interface vxlan 1 status is up/up.

    Args:
        device (jsonrpclib.jsonrpc.ServerProxy):
        Instance of the class jsonrpclib.jsonrpc.ServerProxy with the uri
        'https://%s:%s@%s/command-api' %(username, password, ip).
        enable_password (str): Enable password.

    Returns:
        bool: `True` if the interface vxlan 1 status is up/up.
        `False` otherwise.

    """
    try:
        response = device.runCmds(1, ['show interfaces description | include Vx1'], 'text')
        if response[0]['output'].count('up') == 2:
            return True
        return False
    except:
        return None

def verify_vxlan_config_sanity(device, enable_password):
    """
    Verifies there is no VXLAN config-sanity warnings.

    Args:
        device (jsonrpclib.jsonrpc.ServerProxy):
        Instance of the class jsonrpclib.jsonrpc.ServerProxy with the uri
        'https://%s:%s@%s/command-api' %(username, password, ip).
        enable_password (str): Enable password.

    Returns:
        bool: `True` if there is no VXLAN config-sanity warnings.
        `False` otherwise.
    """
    try:
        response = device.runCmds(1, ['show vxlan config-sanity'], 'json')
        if len(response[0]['categories']) == 0:
            return None
        else:
            for category in response[0]['categories']:
                if category in ['localVtep', 'mlag']:
                    if response[0]['categories'][category]['allCheckPass'] is not True:
                        return False
            return True
    except:
        return None

def verify_svi(device, enable_password):
    """
    Verifies there is no interface vlan down.

    Args:
        device (jsonrpclib.jsonrpc.ServerProxy):
        Instance of the class jsonrpclib.jsonrpc.ServerProxy with the uri
        'https://%s:%s@%s/command-api' %(username, password, ip).
        enable_password (str): Enable password.

    Returns:
        bool: `True` if there is no interface vlan down. `False` otherwise.
    """
    try:
        response = device.runCmds(1, ['show ip interface brief | include Vl'], 'text')
        if response[0]['output'].count('down') == 0:
            return True
        return False
    except:
        return None

def verify_spanning_tree_blocked_ports(device, enable_password):

    """
    Verifies there is no spanning-tree blocked ports.

    Args:
        device (jsonrpclib.jsonrpc.ServerProxy):
        Instance of the class jsonrpclib.jsonrpc.ServerProxy with the uri
        'https://%s:%s@%s/command-api' %(username, password, ip).
        enable_password (str): Enable password.

    Returns:
        bool: `True` there is no spanning-tree blocked ports.
        `False` otherwise.
    """
    try:
        response = device.runCmds(1, ['show spanning-tree blockedports'], 'json')
        if len(response[0]['spanningTreeInstances']) == 0:
            return True
        return False
    except:
        return None

def verify_routing_protocol_model(device, enable_password, model = None):

    """
    Verifies the configured routing protocol model is the one we expect.
    And if there is no mismatch between the configured and operating routing protocol model.

    Args:
        device (jsonrpclib.jsonrpc.ServerProxy):
        Instance of the class jsonrpclib.jsonrpc.ServerProxy with the uri
        'https://%s:%s@%s/command-api' %(username, password, ip).
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
        if (response[0]['protoModelStatus']['configuredProtoModel'] == response[0]['protoModelStatus']['operatingProtoModel']) \
            and (response[0]['protoModelStatus']['operatingProtoModel'] == model):
            return True
        return False
    except:
        return None

def verify_routing_table_size(device, enable_password, minimum = None, maximum = None):
    """
    Verifies the size of the IP routing table (default VRF).
    Should be between the two provided thresholds.

    Args:
        device (jsonrpclib.jsonrpc.ServerProxy):
        Instance of the class jsonrpclib.jsonrpc.ServerProxy with the uri
        'https://%s:%s@%s/command-api' %(username, password, ip).
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
        if (response[0]['vrfs']['default']['totalRoutes'] >= minimum) \
            and (response[0]['vrfs']['default']['totalRoutes'] <= maximum):
            return True
        return False
    except:
        return None

def verify_bfd(device, enable_password):
    """
    Verifies there is no BFD peer in down state (all VRF, IPv4 neighbors).

    Args:
        device (jsonrpclib.jsonrpc.ServerProxy):
        Instance of the class jsonrpclib.jsonrpc.ServerProxy with the uri
        'https://%s:%s@%s/command-api' %(username, password, ip).
        enable_password (str): Enable password.

    Returns:
        bool: `True` if there is no BFD peer in down state (all VRF, IPv4 neighbors, single-hop).
        `False` otherwise.

    """
    try:
        response = device.runCmds(1, ['show bfd peers'], 'json')
        for vrf in response[0]['vrfs']:
            for neighbor in response[0]['vrfs'][vrf]['ipv4Neighbors']:
                for interface in response[0]['vrfs'][vrf]['ipv4Neighbors'][neighbor]['peerStats']:
                    if response[0]['vrfs'][vrf]['ipv4Neighbors'][neighbor]['peerStats'][interface]['status'] != 'up':
                        return False
            return True
    except:
        return None

def verify_bgp_ipv4_unicast_state(device, enable_password):
    """
    Verifies all IPv4 unicast BGP sessions are established (for all VRF)
    and all BGP messages queues for these sessions are empty (for all VRF).

    Args:
        device (jsonrpclib.jsonrpc.ServerProxy):
        Instance of the class jsonrpclib.jsonrpc.ServerProxy with the uri
        'https://%s:%s@%s/command-api' %(username, password, ip).
        enable_password (str): Enable password.

    Returns:
        bool: `True` if all IPv4 unicast BGP sessions are established (for all VRF)
        and all BGP messages queues for these sessions are empty (for all VRF).
        `False` otherwise.

    """
    try:
        response = device.runCmds(1, ['show bgp ipv4 unicast summary vrf all'], 'json')
        if len(response[0]['vrfs']) == 0:
            return None
        for vrf in response[0]['vrfs']:
            for peer in response[0]['vrfs'][vrf]['peers']:
                if (response[0]['vrfs'][vrf]['peers'][peer]['peerState'] != 'Established') \
                    or (response[0]['vrfs'][vrf]['peers'][peer]["inMsgQueue"] != 0) \
                        or (response[0]['vrfs'][vrf]['peers'][peer]["outMsgQueue"] != 0):
                    return False
        return True
    except:
        return None

def verify_bgp_ipv4_unicast_count(device, enable_password, number, vrf = 'default'):
    """
    Verifies all IPv4 unicast BGP sessions are established
    and all BGP messages queues for these sessions are empty
    and the actual number of BGP IPv4 unicast neighbors is the one we expect.

    Args:
        device (jsonrpclib.jsonrpc.ServerProxy):
        Instance of the class jsonrpclib.jsonrpc.ServerProxy with the uri
        'https://%s:%s@%s/command-api' %(username, password, ip).
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
    try:
        count = 0
        command = 'show bgp ipv4 unicast summary vrf ' + vrf
        response = device.runCmds(1, [command], 'json')
        for peer in response[0]['vrfs'][vrf]['peers']:
            if (response[0]['vrfs'][vrf]['peers'][peer]['peerState'] != 'Established') \
                or (response[0]['vrfs'][vrf]['peers'][peer]["inMsgQueue"] != 0) \
                    or (response[0]['vrfs'][vrf]['peers'][peer]["outMsgQueue"] != 0):
                return False
            count = count + 1
        if count == number:
            return True
        return False
    except:
        return None

def verify_bgp_ipv6_unicast_state(device, enable_password):
    """
    Verifies all IPv6 unicast BGP sessions are established (for all VRF)
    and all BGP messages queues for these sessions are empty (for all VRF).

    Args:
        device (jsonrpclib.jsonrpc.ServerProxy):
        Instance of the class jsonrpclib.jsonrpc.ServerProxy with the uri
        'https://%s:%s@%s/command-api' %(username, password, ip).
        enable_password (str): Enable password.

    Returns:
        bool: `True` if all IPv6 unicast BGP sessions are established (for all VRF)
        and all BGP messages queues for these sessions are empty (for all VRF).
        `False` otherwise.

    """
    try:
        response = device.runCmds(1, ['show bgp ipv6 unicast summary vrf all'], 'json')
        if len(response[0]['vrfs']) == 0:
            return None
        for vrf in response[0]['vrfs']:
            for peer in response[0]['vrfs'][vrf]['peers']:
                if (response[0]['vrfs'][vrf]['peers'][peer]['peerState'] != 'Established') \
                    or (response[0]['vrfs'][vrf]['peers'][peer]["inMsgQueue"] != 0) or \
                        (response[0]['vrfs'][vrf]['peers'][peer]["outMsgQueue"] != 0):
                    return False
        return True
    except:
        return None

def verify_bgp_evpn_state(device, enable_password):

    """
    Verifies all EVPN BGP sessions are established (default VRF).

    Args:
        device (jsonrpclib.jsonrpc.ServerProxy):
        Instance of the class jsonrpclib.jsonrpc.ServerProxy with the uri
        'https://%s:%s@%s/command-api' %(username, password, ip).
        enable_password (str): Enable password.

    Returns:
        bool: `True` if all EVPN BGP sessions are established.
        `False` otherwise.

    """
    try:
        response = device.runCmds(1, ['show bgp evpn summary'], 'json')
        if len(response[0]['vrfs']['default']['peers']) == 0:
            return None
        for peer in response[0]['vrfs']['default']['peers']:
            if response[0]['vrfs']['default']['peers'][peer]['peerState'] != 'Established':
                return False
        return True
    except:
        return None

def verify_bgp_evpn_count(device, enable_password, number):
    """
    Verifies all EVPN BGP sessions are established (default VRF)
    and the actual number of BGP EVPN neighbors is the one we expect (default VRF).

    Args:
        device (jsonrpclib.jsonrpc.ServerProxy):
        Instance of the class jsonrpclib.jsonrpc.ServerProxy with the uri
        'https://%s:%s@%s/command-api' %(username, password, ip).
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
        count = 0
        for peer in response[0]['vrfs']['default']['peers']:
            if response[0]['vrfs']['default']['peers'][peer]['peerState'] != 'Established':
                return False
            count = count + 1
        if count == number:
            return True
        return False
    except:
        return None

def verify_bgp_rtc_state(device, enable_password):

    """
    Verifies all RTC BGP sessions are established (default VRF).

    Args:
        device (jsonrpclib.jsonrpc.ServerProxy):
        Instance of the class jsonrpclib.jsonrpc.ServerProxy with the uri
        'https://%s:%s@%s/command-api' %(username, password, ip).
        enable_password (str): Enable password.

    Returns:
        bool: `True` if all RTC BGP sessions are established.
        `False` otherwise.

    """
    try:
        response = device.runCmds(1, ['show bgp rt-membership summary'], 'json')
        if len(response[0]['vrfs']['default']['peers']) == 0:
            return None
        for peer in response[0]['vrfs']['default']['peers']:
            if response[0]['vrfs']['default']['peers'][peer]['peerState'] != 'Established':
                return False
        return True
    except:
        return None

def verify_bgp_rtc_count(device, enable_password, number):
    """
    Verifies all RTC BGP sessions are established (default VRF)
    and the actual number of BGP RTC neighbors is the one we expect (default VRF).

    Args:
        device (jsonrpclib.jsonrpc.ServerProxy):
        Instance of the class jsonrpclib.jsonrpc.ServerProxy with the uri
        'https://%s:%s@%s/command-api' %(username, password, ip).
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
        count = 0
        for peer in response[0]['vrfs']['default']['peers']:
            if response[0]['vrfs']['default']['peers'][peer]['peerState'] != 'Established':
                return False
            count = count + 1
        if count == number:
            return True
        return False
    except:
        return None

def verify_ospf_state(device, enable_password):
    """
    Verifies all OSPF neighbors are in FULL state.

    Args:
        device (jsonrpclib.jsonrpc.ServerProxy):
        Instance of the class jsonrpclib.jsonrpc.ServerProxy with the uri
        'https://%s:%s@%s/command-api' %(username, password, ip).
        enable_password (str): Enable password.

    Returns:
        bool: `True` if all OSPF neighbors are in FULL state.
        `False` otherwise.

    """
    try:
        response = device.runCmds(1, ['show ip ospf neighbor | exclude FULL|Address'], 'text')
        if response[0]['output'].count('\n') == 0:
            return True
        return False
    except:
        return None

def verify_ospf_count(device, enable_password, number = None):
    """
    Verifies the number of OSPF neighbors in FULL state is the one we expect.

    Args:
        device (jsonrpclib.jsonrpc.ServerProxy):
        Instance of the class jsonrpclib.jsonrpc.ServerProxy with the uri
        'https://%s:%s@%s/command-api' %(username, password, ip).
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
        if response[0]['output'].count('FULL') == number:
            return True
        return False
    except:
        return None

def verify_igmp_snooping_vlans(device, enable_password, vlans, configuration):
    """
    Verifies the IGMP snooping configuration for some VLANs.

    Args:
        device (jsonrpclib.jsonrpc.ServerProxy):
        Instance of the class jsonrpclib.jsonrpc.ServerProxy with the uri
        'https://%s:%s@%s/command-api' %(username, password, ip).
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
        for vlan in vlans:
            if response[0]['vlans'][str(vlan)]['igmpSnoopingState'] != configuration:
                return False
        return True
    except:
        return None

def verify_igmp_snooping_global(device, enable_password,  configuration):

    """

    Verifies the IGMP snooping global configuration.

    Args:
        device (jsonrpclib.jsonrpc.ServerProxy):
        Instance of the class jsonrpclib.jsonrpc.ServerProxy with the uri
        'https://%s:%s@%s/command-api' %(username, password, ip).
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
        if response[0]['igmpSnoopingState'] == configuration:
            return True
        return False
    except:
        return None

