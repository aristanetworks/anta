#!/usr/bin/python
# coding: utf-8 -*-

"""
Inventory Module for ANTA.
"""

import logging
import ssl
from multiprocessing import Pool
from socket import setdefaulttimeout
from typing import List

import yaml
from jinja2 import Template
from jsonrpclib import Server
from netaddr import IPAddress, IPNetwork
from pydantic import ValidationError
from yaml.loader import SafeLoader

from .exceptions import (InventoryIncorrectSchema, InventoryRootKeyErrors,
                         InventoryUnknownFormat)
from .models import AntaInventoryInput, InventoryDevice, InventoryDevices

# pylint: disable=W1309

# pylint: disable=W0212
ssl._create_default_https_context = ssl._create_unverified_context

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)


class AntaInventory():
    """Inventory Abstraction for ANTA framework.

    Inventory file example:
    ----------------------
    >>> print(inventory.yml)
    >>> anta_inventory:
    >>>   hosts:
    >>>     - hosts: 1.1.1.1
    >>>     - host: 2.2.2.2
    >>>   networks:
    >>>     - network: 10.0.0.0/8
    >>>     - network: 192.168.0.0/16
    >>>   ranges:
    >>>     - start: 10.0.0.1
    >>>       end: 10.0.0.11

    Inventory Output:
    ------------------
    >>> test = AntaInventory(inventory_file='examples/inventory.yml', username='ansible',
                             password='ansible', auto_connect=True)
    >>> test.get_inventory()
    >>> [
    >>>     "InventoryDevice(host=IPv4Address('192.168.0.17')",
    >>>     "username='ansible'",
    >>>     "password='ansible'",
    >>>     "session=<ServerProxy for ansible:ansible@192.168.0.17/command-api>",
    >>>     "url='https://ansible:ansible@192.168.0.17/command-api'",
    >>>     "established=True",
    >>>     "is_online=True",
    >>>     "hw_model=cEOS-LAB",

    >>>     "InventoryDevice(host=IPv4Address('192.168.0.2')",
    >>>     "username='ansible'",
    >>>     "password='ansible'",
    >>>     "session=None",
    >>>     "url='https://ansible:ansible@192.168.0.2/command-api'",
    >>>     "established=False"
    >>>     "is_online=False",
    >>>     "hw_model=unset",
    >>> ]
    """

    # Root key of inventory part of the inventory file
    INVENTORY_ROOT_KEY = 'anta_inventory'
    # Template to build eAPI connection URL
    EAPI_SESSION_TPL = 'https://{{device_username}}:{{device_password}}@{{device}}/command-api'
    # Supported Output format
    INVENTORY_OUTPUT_FORMAT = ['native', 'json']
    # HW model definition in show version
    HW_MODEL_KEY = 'modelName'

    # pylint: disable=R0913
    def __init__(self, inventory_file: str, username: str, password: str,
                 auto_connect: bool = True, timeout: float = 5) -> None:
        """Class constructor.

        Args:
            inventory_file (str): Path to inventory YAML file where user has described his inputs
            username (str): Username to use to connect to devices
            password (str): Password to use to connect to devices
            auto_connect (bool, optional): Automatically build eAPI context for every devices. Defaults to True.
            timeout (float, optional): Timeout in second to wait before marking device down. Defaults to 5sec.
        """
        self._username = username
        self._password = password
        self.timeout = timeout
        self._inventory = InventoryDevices()

        with open(inventory_file, 'r', encoding='utf8') as f:
            data = yaml.load(f, Loader=SafeLoader)

        # Load data using Pydantic
        try:
            self._read_inventory = AntaInventoryInput(**data[self.INVENTORY_ROOT_KEY])
        except KeyError as exc:
            logger.error(f'Inventory root key is missing: {self.INVENTORY_ROOT_KEY}')
            raise InventoryRootKeyErrors(
                f'Inventory root key ({self.INVENTORY_ROOT_KEY}) is not defined in your inventory') from exc
        except ValidationError as exc:
            logger.error('Inventory data are not compliant with inventory models')
            raise InventoryIncorrectSchema(
                'Inventory is not following schema') from exc

        # Read data from input
        if self._read_inventory.dict()['hosts'] is not None:
            self._inventory_read_hosts()
        if self._read_inventory.dict()['networks'] is not None:
            self._inventory_read_networks()
        if self._read_inventory.dict()['ranges'] is not None:
            self._inventory_read_ranges()

        # Create RPC connection for all devices
        if auto_connect:
            self.connect_inventory()

    ###########################################################################
    # Boolean methods
    ###########################################################################

    def _is_ip_exist(self, ip: str) -> bool:
        """Check if an IP is part of the current inventory.

        Args:
            ip (str): IP address to search in our inventory

        Returns:
            bool: True if device is in our inventory, False if not
        """
        logger.debug(f'Checking if device {ip} is in ourr inventory')
        return len([str(dev.host) for dev in self._inventory if str(ip) == str(dev.host)]) == 1

    def _is_device_online(self, device: InventoryDevice, timeout: float = 5) -> bool:
        """
        _is_device_online Check if device is online.

        Execute an eAPI call to check if device is online and has eAPI working as expected
        If device is ready to serve request, method returns True, else return False.

        Args:
            device (InventoryDevice): InventoryDevice structure to test
            timeout (float, optional): Request timeout. Defaults to 5.

        Returns:
            bool: True if device ready, False by default.
        """
        logger.debug(f'Checking if device {device.host} is online')
        connection = Server(device.url)
        # Check connectivity
        try:
            setdefaulttimeout(timeout)
            connection.runCmds(1, ['show version'])
        # pylint: disable=W0703
        except Exception:
            logger.warning(f'Service not running on device {device.host}')
            return False
        else:
            return True

    ###########################################################################
    # Internal methods
    ###########################################################################

    def _read_device_hw(self, device: InventoryDevice, timeout: float = 5) -> str:
        """
        _read_device_hw Read HW model from the device and update entry with correct value.

        It returns HW model name from show version or None if device is not reachable
        or if it cannot find the modelName key

        Args:
            device (InventoryDevice): Device to update
            timeout (float, optional): Connection timeout. Defaults to 5.

        Returns:
            str: HW value read from the device using show version.
        """
        logger.debug(f'Reading HW information for {device.host}')
        connection = Server(device.url)
        try:
            setdefaulttimeout(timeout)
            response = connection.runCmds(1, ['show version'])
        # pylint: disable=W0703
        except Exception:
            logger.warning(f'Service not running on device {device.host}')
            return None
        else:
            return response[0][self.HW_MODEL_KEY] if self.HW_MODEL_KEY in response[0] else None

    def _get_from_device(self, device: InventoryDevice) -> InventoryDevice:
        """
        _get_from_device Update online flag for InventoryDevice.

        It updates following keys:
        - is_online
        - hw_model

        Args:
            device (InventoryDevice): Device to check using InventoryDevice structure.

        Returns:
            InventoryDevice: Updated structure with devices information (is_online, HW model)
        """
        logger.debug(f'Refreshing is_online flag for device {device.host}')
        device.is_online = self._is_device_online(
            device=device, timeout=self.timeout)
        if device.is_online:
            device.hw_model = self._read_device_hw(device=device, timeout=self.timeout)
        return device

    def _build_device_session_path(self, host: str, username: str, password: str) -> str:
        """Construct URL to reach device using eAPI.

        Jinja2 render to build URL to use for eAPI session.

        Args:
            host (str): IP Address of the device to target in the eAPI session
            username (str): Username for authentication
            password (str): Password for authentication

        Returns:
            str: String to use to create eAPI session
        """
        session_template = Template(self.EAPI_SESSION_TPL)
        return session_template.render(
            device=host,
            device_username=username,
            device_password=password
        )

    def _build_device_session(self, device: InventoryDevice, timeout: float = 5) -> InventoryDevice:
        """Create eAPI RPC session to Arista EOS devices.

        Args:
            device (InventoryDevice): Device information based on InventoryDevice structure
            timeout (int, optional): Device timeout to declare host as down. Defaults to 5.

        Returns:
            InventoryDevice: Updated device structure with its RPC connection
        """
        connection = Server(device.url)
        # Check connectivity
        try:
            setdefaulttimeout(timeout)
            connection.runCmds(1, ['show version'])
        # pylint: disable=W0703
        except Exception:
            logger.warning(f'Service not running on device {device.host}')
            device.session = None
        else:
            device.established = True
            device.session = connection
        return device

    def _add_device_to_inventory(self, host_ip) -> None:
        """Add a InventoryDevice to final inventory.

        Create InventoryDevice and append to existing inventory

        Args:
            host_ip (str): IP address of the host
        """
        device = InventoryDevice(
            host=host_ip,
            username=self._username,
            password=self._password,
            url=self._build_device_session_path(
                host=host_ip,
                username=self._username,
                password=self._password
            )
        )
        self._inventory.append(device)

    def _inventory_read_hosts(self) -> None:
        """Read input data from hosts section and create inventory structure.

        Build InventoryDevice structure for all hosts under hosts section
        """
        for host in self._read_inventory.hosts:
            self._add_device_to_inventory(host_ip=host.host)

    def _inventory_read_networks(self) -> None:
        """Read input data from networks section and create inventory structure.

        Build InventoryDevice structure for all IPs available in each declared subnet
        """
        for network in self._read_inventory.networks:
            for host_ip in IPNetwork(str(network.network)):
                self._add_device_to_inventory(host_ip=host_ip)

    def _inventory_read_ranges(self) -> None:
        """Read input data from ranges section and create inventory structure.

        Build InventoryDevice structure for all IPs available in each declared range
        """
        for range_def in self._read_inventory.ranges:
            range_increment = IPAddress(str(range_def.start))
            range_stop = IPAddress(str(range_def.end))
            while range_increment <= range_stop:
                self._add_device_to_inventory(host_ip=str(range_increment))
                range_increment += 1

    def _inventory_rebuild(self, list_devices: List[InventoryDevice]) -> InventoryDevices:
        """
        _inventory_rebuild Transform a list of InventoryDevice into a InventoryDevices object.

        Args:
            list_devices (List[InventoryDevice]): List of devices to add into InventoryDevices

        Returns:
            InventoryDevices: An object with all the devices.
        """
        logger.debug('Create a new version of InventoryDevices')
        inventory = InventoryDevices()
        for device in list_devices:
            inventory.append(device)
        return inventory

    def _filtered_inventory(self, established_only: bool = False) -> InventoryDevices:
        """
        _filtered_inventory Generate a temporary inventory filtered.

        Args:
            established_only (bool, optional): Do we have to include non-established devices. Defaults to False.

        Returns:
            InventoryDevices: A inventory with concerned devices
        """
        inventory = InventoryDevices()
        if established_only is False:
            return self._inventory

        for device in self._inventory:
            if device.established:
                inventory.append(device)
        return inventory

    ###########################################################################
    # Public methods
    ###########################################################################

    ###########################################################################
    # GET methods

    def get_inventory(self, format_out: str = 'native', established_only: bool = True) -> InventoryDevices:
        """get_inventory Expose device inventory.

        Provides inventory has a list of InventoryDevice objects. If required, it can be exposed in JSON format.
        By default expose only active devices.

        Args:
            format (str, optional): Format output, can be native, list or JSON. Defaults to 'native'.
            established_only (bool, optional): Allow to expose also unreachable devices. Defaults to True.

        Returns:
            InventoryDevices: List of InventoryDevice
        """
        if format_out not in ['native', 'json', 'list']:
            raise InventoryUnknownFormat(
                f'Unsupported inventory format: {format_out}. '
                f'Only supported format are: {self.INVENTORY_OUTPUT_FORMAT}')

        inventory = self._filtered_inventory(established_only)

        if format_out == 'list':
            # pylint: disable=R1721
            return [dev for dev in inventory]

        if format_out == 'json':
            return inventory.json()

        return inventory

    def get_device(self, host_ip) -> InventoryDevice:
        """Get device information from a given IP.

        Args:
            host_ip (str): IP address of the device

        Returns:
            InventoryDevice: Device information
        """
        if self._is_ip_exist(host_ip):
            return [dev for dev in self._inventory if str(dev.host) == str(host_ip)][0]
        return None

    def get_device_session(self, host_ip: str) -> Server:
        """Expose RPC session of a given host from our inventory.

        Provide RPC session if the session exists, if not, it returns None

        Args:
            host_ip (str): IP address of the host to match

        Returns:
            jsonrpclib.Server: Instance to the device. None if session does not exist
        """
        device = self.get_device(host_ip=host_ip)
        if device is None:
            return None
        return device.session

    ###########################################################################
    # CREATE methods

    def create_all_sessions(self, refresh_online_first: bool = False) -> None:
        """Helper to build RPC sessions to all devices.

         Args:
            refresh_online_first (bool): Run  a refresh of is_online flag for all devices.
        """
        if refresh_online_first:
            logger.debug('Running a refresh for devices online')
            self.refresh_device_facts()

        for device in self._inventory:
            self.create_device_session(host_ip=device.host)

    def create_device_session(self, host_ip: str) -> bool:
        """Get session of a device.

        If device has already a session, function only returns active session, if not, try to build a new session

        Args:
            host_ip (str): IP address of the device

        Returns:
            bool: True if update succeed, False if not
        """
        logger.debug(
            f'Searching for device {host_ip} in {[str(dev.host) for dev in self._inventory]}')
        if len([dev for dev in self._inventory if str(dev.host) == str(host_ip)]) > 0:
            device = [dev for dev in self._inventory if str(
                dev.host) == str(host_ip)][0]
            logger.debug(f'Search result is: {device}')
            if device.is_online and not device.established and self._is_ip_exist(host_ip):
                logger.debug(f'Trying to connect to device {str(device.host)}')
                device = self._build_device_session(
                    device=device, timeout=self.timeout)
                # pylint: disable=W0104
                [device if dev.host == device.host else dev for dev in self._inventory]
                return True
        return False

    ###########################################################################
    # MISC methods

    def connect_inventory(self):
        """connect_inventory Helper to prepare inventory with network data."""
        # Check if devices are online & update is_online flag
        self.refresh_device_facts()

        # Create eAPI session for all online devices
        self.create_all_sessions()

    def refresh_device_facts(self) -> None:
        """
        refresh_online_flag_inventory Update is_online flag for all devices.

        Execute in parallel a call to _refresh_online_flag_device to test device connectivity.
        """
        logger.debug('Refreshing facts for current inventory')
        number_of_devices = len([dev.host for dev in self._inventory])
        with Pool(processes=number_of_devices) as pool:
            logger.debug('Check devices using multiprocessing')
            results_map = pool.map(
                self._get_from_device,  self._inventory)
            logger.debug('Update inventory with updated data')
            self._inventory = self._inventory_rebuild(results_map)
