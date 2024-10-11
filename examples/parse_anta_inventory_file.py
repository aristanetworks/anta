# Copyright (c) 2024 Arista Networks, Inc.
# Use of this source code is governed by the Apache License 2.0
# that can be found in the LICENSE file.
"""Script that parses an ANTA inventory file, connects to devices and print their status."""
import asyncio

from anta.inventory import AntaInventory


async def main(inv: AntaInventory) -> None:
    """Read an AntaInventory and try to connect to every device in the inventory.

    Print a message for every device connection status
    """
    await inv.connect_inventory()

    for device in inv.values():
        if device.established:
            print(f"Device {device.name} is online")
        else:
            print(f"Could not connect to device {device.name}")


if __name__ == "__main__":
    # Create the AntaInventory instance
    inventory = AntaInventory.parse(
        filename="inventory.yaml",
        username="arista",
        password="@rista123",
    )

    # Run the main coroutine
    res = asyncio.run(main(inventory))
