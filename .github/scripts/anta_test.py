"""
This sccript can be used to test the tests defined in the nata package
"""

import logging
import os
import sys
from yaml import safe_load
from anta.inventory import AntaInventory
import anta.tests
import anta.loader

logging.disable(level=logging.WARNING)
dir_path = os.path.dirname(os.path.realpath(__file__))

username = input("username: ")
password = input("password: ")
enable_password = input("enable_password: ")

print("connecting to devices ... please be patient ...")

inventory = AntaInventory(
    inventory_file=f"{dir_path}/../../examples/inventory.yml",
    username=username,
    password=password,
    enable_password=enable_password,
    auto_connect=True,
    timeout=2,
)

devices = inventory.get_inventory(established_only=True)

try:
    with open(f"{dir_path}/../../examples/tests.yaml", "r", encoding="utf8") as file:
        test_catalog = safe_load(file)
except FileNotFoundError:
    print("Error opening tests_catalog")
    sys.exit(1)

tests = anta.loader.parse_catalog(test_catalog)

for device in devices:
    for test in tests:
        print(test[0](device, **test[1]))
