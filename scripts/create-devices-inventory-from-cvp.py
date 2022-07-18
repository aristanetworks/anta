#!/usr/bin/env python3

"""
This script:
- uses CVP REST API to generate a token
- uses cvprac with this token to get the device inventory
- creates a text file with the devices IP address under the container passed in argument
- if we dont provide the argument `c` it creates a text file with all the devices IP address from the CVP inventory.

usage: ./create-devices-inventory-from-cvp.py --help
requirement: pip install cvprac==1.2.0
"""

import json
import os
from argparse import ArgumentParser
from getpass import getpass
import requests
from cvprac.cvp_client import CvpClient

# Ignore certificate warnings
# pylint: disable=E1101
requests.packages.urllib3.disable_warnings()

def main():
    parser = ArgumentParser(
        description='Create devices inventory based on CVP containers'
        )
    parser.add_argument(
        '-cvp',
        help='CVP address',
        dest='cvp',
        required=True
        )
    parser.add_argument(
        '-u',
        help='CVP username',
        dest='username',
        required=True
        )
    parser.add_argument(
        '-c',
        help='CVP container',
        dest='container',
        required=False
        )
    parser.add_argument(
        '-o',
        help='Output directory',
        dest='output_directory',
        required=True
        )
    args = parser.parse_args()
    args.password = getpass(prompt='CVP password: ')

    # use CVP REST API to generate a token
    URL = f"https://{args.cvp}/cvpservice/login/authenticate.do"
    payload = json.dumps({
      "userId": args.username,
      "password": args.password
    })
    headers = {
      'Content-Type': 'application/json',
      'Accept': 'application/json'
    }
    response = requests.request("POST", URL, headers=headers, data=payload, verify=False)
    token = response.json()['sessionId']

    # Create output directory
    cwd = os.getcwd()
    out_dir = os.path.dirname(cwd + "/" + args.output_directory + "/")
    if not os.path.exists(out_dir):
        os.makedirs(out_dir)

    # CvpClient is a class in the module cvprac.cvp_client
    # clnt is an object, instance of the class CvpClient
    clnt = CvpClient()

    # help(clnt.connect)
    clnt.connect(nodes=[args.cvp], username='',password='',api_token=token)

    if args.container is None:
        # Get a list of all devices
        inventory = clnt.api.get_inventory()
        # write the IP addresses in a file
        out_file = f'{out_dir}/all.yml'
        with open(out_file, 'w', encoding="utf8") as out_file:
            out_file.write("anta_inventory:")
            out_file.write('\n')
            out_file.write("  hosts:")
            out_file.write('\n')
            for dev in inventory:
                out_file.write("  - host: " + dev['ipAddress'])
                out_file.write('\n')
    else:
        # Get devices under a container
        container = args.container
        container_inventory = clnt.api.get_devices_in_container(container)
        # write the devices IP address in a file
        out_file = f'{out_dir}/{container}.yml'
        with open(out_file, 'w', encoding="utf8") as out_file:
            out_file.write("anta_inventory:")
            out_file.write('\n')
            out_file.write("  hosts:")
            out_file.write('\n')
            for dev in container_inventory:
                out_file.write("  - host: " + dev['ipAddress'])
                out_file.write('\n')

if __name__ == '__main__':
    main()
