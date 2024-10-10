# Copyright (c) 2024 Arista Networks, Inc.
# Use of this source code is governed by the Apache License 2.0
# that can be found in the LICENSE file.
"""
run_eos_commands.py.

This script runs a list of EOS commands on reachable devices.
"""
# This is needed to run the script for python < 3.10 for typing annotations
from __future__ import annotations

import asyncio
from pprint import pprint

from anta.inventory import AntaInventory
from anta.models import AntaCommand


async def main(inv: AntaInventory, commands: list[str]) -> dict[str, list[AntaCommand]]:
    """Run a list of commands against each valid device in the inventory.

    Take an AntaInventory and a list of commands as string
    1. try to connect to every device in the inventory
    2. collect the results of the commands from each device

    Returns
    -------
    dict[str, list[AntaCommand]]
        a dictionary where key is the device name and the value is the list of AntaCommand ran towards the device
    """
    await inv.connect_inventory()

    # Make a list of coroutine to run commands towards each connected device
    coros = []
    # dict to keep track of the commands per device
    result_dict = {}
    for name, device in inv.get_inventory(established_only=True).items():
        anta_commands = [AntaCommand(command=command, ofmt="json") for command in commands]
        result_dict[name] = anta_commands
        coros.append(device.collect_commands(anta_commands))

    # Run the coroutines
    await asyncio.gather(*coros)

    return result_dict


if __name__ == "__main__":
    # Create the AntaInventory instance
    inventory = AntaInventory.parse(
        filename="inventory.yaml",
        username="arista",
        password="@rista123",
    )

    # Create a list of commands with json output
    command_list = ["show version", "show ip bgp summary"]

    # Run the main asyncio  entry point
    res = asyncio.run(main(inventory, command_list))

    pprint(res)
