#!/usr/bin/env python
# coding: utf-8 -*-

"""
Commands for Anta CLI to run check commands.
"""

import logging
import os

import click
from cvprac.cvp_client import CvpClient
from cvprac.cvp_client_errors import CvpApiError

from anta.cli.utils import setup_logging

from .utils import create_inventory, get_cv_token

logger = logging.getLogger(__name__)


@click.command(no_args_is_help=True)
@click.option('--cvp-ip', '-ip', default=None, help='CVP IP Address', type=str, required=True)
@click.option('--cvp-username', '-u', default=None, help='CVP Username', type=str, required=True)
@click.option('--cvp-password', '-p', default=None, help='CVP Password / token', type=str, required=True)
@click.option('--cvp-container', '-c', default=None, help='Container where devices are configured', type=str, required=False)
@click.option('--inventory-directory', '-d', default=None, help='Path to save inventory file', type=click.Path())
@click.option('--log-level', '--log', help='Logging level of the command', default='info',
              type=click.Choice(['debug', 'info', 'warning', 'critical'], case_sensitive=False))
def from_cvp(inventory_directory: str, cvp_ip: str, cvp_username: str, cvp_password: str, cvp_container: str, log_level: str) -> bool:
    """Build ANTA inventory from Cloudvision"""
    # pylint: disable=too-many-arguments
    setup_logging(level=log_level)
    logger.info(f'Getting auth token from {cvp_ip} for user {cvp_username}')
    token = get_cv_token(cvp_ip=cvp_ip, cvp_username=cvp_username, cvp_password=cvp_password)

    # Create output directory
    cwd = os.getcwd()
    out_dir = os.path.dirname(f"{cwd}/{inventory_directory}/")
    if not os.path.exists(out_dir):
        logger.info(f'Creating inventory folder {out_dir}')
        os.makedirs(out_dir)

    clnt = CvpClient()
    try:
        clnt.connect(nodes=[cvp_ip], username="", password="", api_token=token)
    except CvpApiError as error:
        logger.error(f'Error connecting to cvp: {error}')
    logger.info(f'Connected to CVP {cvp_ip}')

    cvp_inventory = None
    if cvp_container is None:
        # Get a list of all devices
        logger.info(f'Getting full inventory from {cvp_ip}')
        cvp_inventory = clnt.api.get_inventory()
    else:
        # Get devices under a container
        logger.info(f'Getting inventory for container {cvp_container} from {cvp_ip}')
        cvp_inventory = clnt.api.get_devices_in_container(cvp_container)
    create_inventory(cvp_inventory, out_dir, cvp_container)
    return True
