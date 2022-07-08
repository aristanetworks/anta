#!/usr/bin/python
# coding: utf-8 -*-

"""ANTA Inventory unit tests."""

import pytest
import logging
import yaml
from pydantic import ValidationError
from anta.inventory import AntaInventory
from anta.inventory.models import InventoryDevice
from anta.inventory.exceptions import InventoryIncorrectSchema, InventoryRootKeyErrors
from tests.data.utils import generate_test_ids_dict
from tests.data.json_data import ANTA_INVENTORY_TESTS


class Test_AntaInventory():
    """Test AntaInventory class."""

    def create_inventory(self, content, tmp_path):
        tmp_inventory = tmp_path / "mydir/myfile"
        tmp_inventory.parent.mkdir()
        tmp_inventory.touch()
        tmp_inventory.write_text(yaml.dump(content, allow_unicode=True))
        return str(tmp_inventory)

    def check_parameter(self, parameter: str, test_definition):
        if 'parameters' not in test_definition.keys() or parameter not in test_definition['parameters'].keys():
            return False
        return True

    @pytest.mark.parametrize("test_definition", ANTA_INVENTORY_TESTS, ids=generate_test_ids_dict)
    def test_init_valid(self, test_definition, tmp_path):
        if test_definition['expected_result'] == 'invalid':
            pytest.skip('Not concerned by the test')

        inventory_file = self.create_inventory(content=test_definition['input'], tmp_path=tmp_path)
        try:
            inventory_test = AntaInventory(
                inventory_file=inventory_file,
                username='arista',
                password='arista123',
                auto_connect=False
            )
        except ValidationError as exc:
            logging.error('Exceptions is: %s', str(exc))
            assert False
        else:
            assert True

    @pytest.mark.parametrize("test_definition", ANTA_INVENTORY_TESTS, ids=generate_test_ids_dict)
    def test_init_invalid(self, test_definition, tmp_path):
        if test_definition['expected_result'] == 'valid':
            pytest.skip('Not concerned by the test')

        inventory_file = self.create_inventory(content=test_definition['input'], tmp_path=tmp_path)
        try:
            inventory_test = AntaInventory(
                inventory_file=inventory_file,
                username='arista',
                password='arista123',
                auto_connect=False
            )
        except InventoryIncorrectSchema as exc:
            logging.warning('Exception is: %s', exc)
            assert True
        except InventoryRootKeyErrors as exc:
            logging.warning('Exception is: %s', exc)
            assert True
        else:
            assert False

    @pytest.mark.parametrize("test_definition", ANTA_INVENTORY_TESTS, ids=generate_test_ids_dict)
    def test_is_ip_exists(self, test_definition, tmp_path):
        if test_definition['expected_result'] == 'invalid':
            pytest.skip('Not concerned by the test')

        if not self.check_parameter(parameter='ipaddress_in_scope', test_definition=test_definition):
            pytest.skip('Test data has no ipaddress parameter configured')

        inventory_file = self.create_inventory(content=test_definition['input'], tmp_path=tmp_path)
        inventory_test = AntaInventory(
            inventory_file=inventory_file,
            username='arista',
            password='arista123',
            auto_connect=False
        )
        logging.info('Checking if %s is in inventory', str(test_definition['parameters']['ipaddress_in_scope']))
        assert inventory_test._is_ip_exist(ip=test_definition['parameters']['ipaddress_in_scope'])

    @pytest.mark.parametrize("test_definition", ANTA_INVENTORY_TESTS, ids=generate_test_ids_dict)
    def test_is_ip_exists_false(self, test_definition, tmp_path):
        if test_definition['expected_result'] == 'invalid':
            pytest.skip('Not concerned by the test')

        if not self.check_parameter(parameter='ipaddress_out_of_scope', test_definition=test_definition):
            pytest.skip('Test data has no ipaddress parameter configured')

        inventory_file = self.create_inventory(content=test_definition['input'], tmp_path=tmp_path)
        inventory_test = AntaInventory(
            inventory_file=inventory_file,
            username='arista',
            password='arista123',
            auto_connect=False
        )
        logging.info('Checking if %s is in inventory', str(test_definition['parameters']['ipaddress_out_of_scope']))
        assert not inventory_test._is_ip_exist(ip=test_definition['parameters']['ipaddress_out_of_scope'])

    @pytest.mark.parametrize("test_definition", ANTA_INVENTORY_TESTS, ids=generate_test_ids_dict)
    def test_device_get(self,  test_definition, tmp_path):
        if test_definition['expected_result'] == 'invalid':
            pytest.skip('Not concerned by the test')

        if not self.check_parameter(parameter='ipaddress_in_scope', test_definition=test_definition):
            pytest.skip('Test data has no ipaddress parameter configured')

        inventory_file = self.create_inventory(content=test_definition['input'], tmp_path=tmp_path)
        inventory_test = AntaInventory(
            inventory_file=inventory_file,
            username='arista',
            password='arista123',
            auto_connect=False
        )
        logging.info('Getting if %s from inventory', str(test_definition['parameters']['ipaddress_in_scope']))
        device = inventory_test.device_get(host_ip= str(test_definition['parameters']['ipaddress_in_scope']))
        assert isinstance(device,InventoryDevice)
        assert str(device.host) == str(test_definition['parameters']['ipaddress_in_scope'])