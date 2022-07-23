"""
Test functions related to system-level features and protocols
"""
from jsonrpclib import jsonrpc
from anta.inventory.models import InventoryDevice
from anta.result_manager.models import TestResult


def verify_uptime(device: InventoryDevice, minimum=None):
    """
    Verifies the device uptime is higher than a value.

    Args:
        device (InventoryDevice): InventoryDevice instance containing all devices information.
        minimum (int): Minimum uptime in seconds.

    Returns:
        TestResult instance with
        * result = "unset" if test has not been executed
        * result = "success" if uptime is greater than minimun
        * result = "failure" otherwise.
        * result = "error" if any exception is caught

    """
    result = TestResult(host=str(device.host),
                        test="verify_uptime")
    if not minimum:
        result.is_skipped(
            "verify_uptime was not run as no minimum were givem"
        )
        return result
    try:
        response = device.session.runCmds(1, ['show uptime'], 'json')
        response_data = response[0]['upTime']
        if response[0]['upTime'] > minimum:
            result.is_success()
        else:
            result.is_failure(f'Uptime is {response_data}')
    except (jsonrpc.AppError, KeyError) as e:
        result.is_error(str(e))
    return result

def verify_reload_cause(device: InventoryDevice) -> TestResult:
    """
    Verifies the last reload of the device was requested by a user.

    Test considers the following messages as normal and will return success. Failure is for other messages
    * Reload requested by the user.
    * Reload requested after FPGA upgrade

    Args:
        device (InventoryDevice): InventoryDevice instance containing all devices information.

    Returns:
        TestResult instance with
        * result = "unset" if test has not been executed
        * result = "success" if reload cause is standard
        * result = "failure" otherwise.
        * result = "error" if any exception is caught

    """
    result = TestResult(host=str(device.host),
                        test="verify_reload_cause")
    try:
        response = device.session.runCmds(1, ['show version','show reload cause'], 'json')
        response_data = response[0]['response']['resetCauses'][0]['description']
        if response_data in ['Reload requested by the user.', 'Reload requested after FPGA upgrade']:
            result.is_success()
        else:
            result.is_failure(f'Reload cause is {response_data}')
    except (jsonrpc.AppError, KeyError) as e:
        result.is_error(str(e))
    return result

def verify_coredump(device: InventoryDevice) -> TestResult:
    """
    Verifies there is no core file.

    Args:
        device (InventoryDevice): InventoryDevice instance containing all devices information.

    Returns:
        TestResult instance with
        * result = "unset" if test has not been executed
        * result = "success" if device has no core-dump
        * result = "failure" otherwise.
        * result = "error" if any exception is caught

    """
    result = TestResult(host=str(device.host),
                        test="verify_coredump")
    try:
        response = device.session.runCmds(1, \
            [{"cmd": "enable", "input": str(device.enable_password)},'bash timeout 10 ls /var/core'], 'text')
        response_data = response[1]['output']
        if len(response_data) == 0:
            result.is_success()
        else:
            result.is_failure(f'Core-dump(s) have been found: {response_data}')
    except (jsonrpc.AppError, KeyError) as e:
        result.is_error(str(e))
    return result

def verify_agent_logs(device: InventoryDevice) -> TestResult:
    """
    Verifies there is no agent crash reported on the device.

    Args:
        device (InventoryDevice): InventoryDevice instance containing all devices information.

    Returns:
        TestResult instance with
        * result = "unset" if test has not been executed
        * result = "success" if there is no agent crash
        * result = "failure" otherwise.
        * result = "error" if any exception is caught

    """
    result = TestResult(host=str(device.host),
                        test="verify_agent_logs")
    try:
        response = device.session.runCmds(1, ['show agent logs crash'], 'text')
        response_data = response[0]['output']
        if len(response_data) == 0:
            result.is_success()
        else:
            result.is_failure(f'device reported some agent crashes: {response_data}')
    except (jsonrpc.AppError, KeyError) as e:
        result.is_error(str(e))
    return result

def verify_syslog(device: InventoryDevice) -> TestResult:
    """
    Verifies the device had no syslog message with a severity of warning (or a more severe message)
    during the last 7 days.

    Args:
        device (InventoryDevice): InventoryDevice instance containing all devices information.

    Returns:
        TestResult instance with
        * result = "unset" if test has not been executed
        * result = "success" if syslog has no WARNING message
        * result = "failure" otherwise.
        * result = "error" if any exception is caught
    """
    result = TestResult(host=str(device.host),
                        test="verify_syslog")
    try:
        response = device.session.runCmds(1, ['show logging last 7 days threshold warnings'], 'text')
        response_data = response[0]['output']
        if len(response_data) == 0:
            result.is_success()
        else:
            result.is_failure('Device has some log messages with a severity WARNING or higher')
    except (jsonrpc.AppError, KeyError) as e:
        result.is_error(str(e))
    return result

def verify_cpu_utilization(device: InventoryDevice) -> TestResult:
    """
    Verifies the CPU utilization is less than 75%.

    Args:
        device (InventoryDevice): InventoryDevice instance containing all devices information.

    Returns:
        TestResult instance with
        * result = "unset" if test has not been executed
        * result = "success" if CPU usage is lower than 75%
        * result = "failure" otherwise.
        * result = "error" if any exception is caught
    """
    result = TestResult(host=str(device.host),
                        test="verify_cpu_utilization")
    try:
        response = device.session.runCmds(1, ['show processes top once'], 'json')
        response_data = response[0]['cpuInfo']['%Cpu(s)']['idle']
        if response_data > 25:
            result.is_success()
        else:
            result.is_failure(
                f'device reported a high CPU utilization ({response_data}%)')
    except (jsonrpc.AppError, KeyError) as e:
        result.is_error(str(e))
    return result

def verify_memory_utilization(device: InventoryDevice) -> TestResult:
    """
    Verifies the memory utilization is less than 75%.

    Args:
        device (InventoryDevice): InventoryDevice instance containing all devices information.

    Returns:
        TestResult instance with
        * result = "unset" if test has not been executed
        * result = "success" if memory usage is lower than 75%
        * result = "failure" otherwise.
        * result = "error" if any exception is caught
    """
    result = TestResult(host=str(device.host),
                        test="verify_memory_utilization")
    try:
        response = device.session.runCmds(1, ['show version'], 'json')
        memory_usage = float(response[0]['memFree']) / \
            float(response[0]['memTotal'])
        if memory_usage > 0.25:
            result.is_success()
        else:
            result.is_failure(f'device report a high memory usage: {memory_usage*100}%')
    except (jsonrpc.AppError, KeyError) as e:
        result.is_error(str(e))
    return result

def verify_filesystem_utilization(device: InventoryDevice) -> TestResult:

    """
    Verifies each partition on the disk is used less than 75%.

    Args:
        device (InventoryDevice): InventoryDevice instance containing all devices information.

    Returns:
        TestResult instance with
        * result = "unset" if test has not been executed
        * result = "success" if disk is used less than 75%
        * result = "failure" otherwise.
        * result = "error" if any exception is caught
    """
    result = TestResult(host=str(device.host),
                        test="verify_filesystem_utilization")
    try:
        response = device.session.runCmds(1, \
            [{"cmd": "enable", "input": device.enable_password},'bash timeout 10 df -h'], 'text')
        result.is_success()
        for line in response[1]['output'].split('\n')[1:]:
            if 'loop' not in line and len(line) > 0:
                if int(line.split()[4].replace('%', '')) > 75:
                    result.is_failure(f'mount point {line} is higher than 75% (reprted {int(line.split()[4].replace(" % ", ""))})')
    except (jsonrpc.AppError, KeyError) as e:
        result.is_error(str(e))
    return result

def verify_ntp(device: InventoryDevice) -> TestResult:

    """
    Verifies NTP is synchronised.

    Args:
        device (InventoryDevice): InventoryDevice instance containing all devices information.

    Returns:
        TestResult instance with
        * result = "unset" if test has not been executed
        * result = "success" if synchronized with NTP server
        * result = "failure" otherwise.
        * result = "error" if any exception is caught
    """
    result = TestResult(host=str(device.host),
                        test="verify_ntp")
    try:
        response = device.session.runCmds(1, ['show ntp status'], 'text')
        if response[0]['output'].split('\n')[0].split(' ')[0] == 'synchronised':
            result.is_success()
        else:
            data = response[0]["output"].split("\n")[0]
            result.is_failure(f'not sync with NTP server ({data})')
    except (jsonrpc.AppError, KeyError) as e:
        result.is_error(str(e))
    return result
