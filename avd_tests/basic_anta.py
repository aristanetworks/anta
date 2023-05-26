import asyncio

from yaml import safe_load
from anta.loader import parse_catalog
from anta.inventory import AntaInventory
from anta.result_manager import ResultManager
from anta.runner import main
from anta.catalog import CatalogBuilder

# AVD structured config file
structured_config_path = "/home/cbaillar/git_projects/ansible-avd-examples/mpls-evpn/intended/structured_configs/NW-CORE.yml"
with open(structured_config_path, "r", encoding="UTF-8") as file:
    structured_config = safe_load(file)

# Existing catalog if required
existing_catalog_path = "/home/cbaillar/git_projects/arista-customers/CN/anta/test_catalog.yaml"
with open(existing_catalog_path, "r", encoding="UTF-8") as file:
    existing_catalog = safe_load(file)

# Devices inventory file ; will be managed by Ansible
inventory = "/home/cbaillar/git_projects/arista-customers/CN/anta/inventory.yaml"


# Create a CatalogBuilder instance
builder = CatalogBuilder(structured_config=structured_config, existing_catalog=existing_catalog)

# Build the new catalog
catalog = builder.build_new_catalog()

# Merge the new catalog with the existing one if not empty
if builder.existing_catalog:
    catalog = builder.merge_catalogs(catalog)

# Parse the new catalog
tests_catalog = parse_catalog(catalog)

# Create a AntaInventory instance ; parameters from Ansible
inventory_anta = AntaInventory(inventory_file=inventory, username="arista", password="arista", enable_password="arista")

# Create a ResultManager instance
results = ResultManager()
                
# Launch ANTA runner
asyncio.run(main(results, inventory_anta, tests_catalog), debug=False)

# Print JSON results
print(results.get_results(output_format="json"))
