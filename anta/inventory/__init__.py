#!/usr/bin/python
# coding: utf-8 -*-

import logging
import yaml
import ssl
from jinja2 import Template
from socket import setdefaulttimeout
from jsonrpclib import Server, jsonrpc, ProtocolError
from yaml.loader import SafeLoader
from netaddr import IPNetwork
from pydantic import ValidationError

from .models import AntaInventoryInput, InventoryDevice

# pylint: disable=protected-access
ssl._create_default_https_context = ssl._create_unverified_context

class AntaInventory(object):
    """
    Inventory Abstraction for ANTA framework

    Inventory file example:
    ----------------------
    anta_read_inventory:
      hosts:
        - hosts: 1.1.1.1
        - host: 2.2.2.2
      networks:
        - network: 10.0.0.0/8
        - network: 192.168.0.0/16
    """

    # Root key of inventory part of the inventory file
    INVENTORY_ROOT_KEY = 'anta_inventory'
    EAPI_SESSION_TPL = 'https://{{device_username}}:{{device_password}}@{{device}}/command-api'

    def __init__(self, inventory_file: str, username: str, password: str, connect: bool = False):
        """
        __init__ Class constructor

        Args:
            inventory_file (str): Path to inventory YAML file where user has described his inputs
            username (str): Username to use to connect to devices
            password (str): Password to use to connect to devices
            connect (bool, optional): Automatically build eAPI context for every devices. Defaults to False.
        """
        self._username = username
        self._password = password
        self._inventory = []

        with open(inventory_file, 'r', encoding='utf8') as f:
            data = yaml.load(f, Loader=SafeLoader)

        # Load data using Pydantic
        try:
            self._read_inventory = AntaInventoryInput( **data[self.INVENTORY_ROOT_KEY] )
        except KeyError:
            logging.error(f'Inventory root key is missing: {self.INVENTORY_ROOT_KEY}')
        except ValidationError as error:
            logging.error('Inventory data are not compliant with inventory models')
            logging.error(f'error is: {error}')

        # Read data from input
        if self._read_inventory.dict()['hosts'] is not None:
            self._read_hosts()
        if self._read_inventory.dict()['networks'] is not None:
            self._read_networks()

        # Create RPC connection for all devices
        if connect:
            self.refresh_sessions()

    def _build_session_path(self, host: str, username: str, password: str):
        """
        _build_session_path Construct URL to reach device using eAPI

        Jinja2 render to build URL to use for eAPI session

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

    def _create_session(self, device : InventoryDevice, timeout: int = 5):
        """
        _create_session Create eAPI RPC session to Arista EOS devices

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
            connection.runCmds(1,['show version'])
        # except TransportError:
        #     logging.error(f'Incorrect credentials for device f{device.host}')
        #     device.session = None
        except ConnectionRefusedError:
            logging.error(f'Service not running on device {device.host}')
            device.session = None
        else:
            device.established = True
            device.session = connection
        return device


    def get_session(self, host_ip: str):
        """
        get_session Get session of a device

        If device has already a session, function only returns active session, if not, try to build a new session

        Args:
            host_ip (str): IP address of the device

        Returns:
            InventoryDevice: Updated InventoryDevice information with RPC session
        """
        device = [ dev for dev in self._inventory if str(dev.host) == str(host_ip)][0]
        if not device.established:
            logging.debug(f'trying to connect to device')
            device = self._create_session(device=device)
            [device if dev.host == device.host else dev for dev in self._inventory]
        return device

    def refresh_sessions(self):
        """
        refresh_sessions Helper to build RPC sessions to all devices
        """
        for device in self._inventory:
            self.get_session(host_ip=device.host)

    def _read_hosts(self):
        """
        _read_hosts Read input data from hosts section and create inventory structure

        Build InventoryDevice structure for all hosts under hosts section
        """
        for host in self._read_inventory.hosts:
            device = InventoryDevice(
                host=host.host,
                username=self._username,
                password=self._password,
                url=self._build_session_path(
                    host=host.host,
                    username=self._username,
                    password=self._password
                )
            )
            self._inventory.append(device)

    def _read_networks(self):
        """
        _read_networks Read input data from networks section and create inventory structure

        Build InventoryDevice structure for all IPs available in each declared subnet
        """
        for network in self._read_inventory.networks:
            for host_ip in IPNetwork(str(network.network)):
                device = InventoryDevice(
                    host=host_ip,
                    username=self._username,
                    password=self._password,
                    url=self._build_session_path(
                        host=host_ip,
                        username=self._username,
                        password=self._password
                    )
                )
                self._inventory.append(device)

    def get_inventory(self, format: str = 'native', established_only: bool = True):
        """
        get_inventory Expose device inventory

        Provides inventory has a list of InventoryDevice objects. If requried, it can be exposed in JSON format. Also, by default expose only active devices.

        Args:
            format (str, optional): Format output, can be native or JSON. Defaults to 'native'.
            established_only (bool, optional): Allow to expose also unreachable devices. Defaults to True.

        Returns:
            List: List of InventoryDevice
        """
        if established_only:
            devices = [dev for dev in self._inventory if dev.established]
        else:
            devices = self._inventory

        if format == 'json':
            return [dev.dict() for dev in devices]
        else:
            return devices
