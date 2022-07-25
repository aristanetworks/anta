#!/usr/bin/python
# coding: utf-8 -*-
# pylint: skip-file

"""ANTA Result Manager models unit tests."""

import pytest
import logging
import yaml
from pydantic import ValidationError
from anta.result_manager.models import TestResult
from tests.data.utils import generate_test_ids_dict
from tests.data.json_data import TEST_RESULT_UNIT


class Test_InventoryUnitModels():
    """Test components of anta.result_manager.models."""

    @pytest.mark.parametrize("test_definition", TEST_RESULT_UNIT, ids=generate_test_ids_dict)
    def test_anta_result_init_valid(self, test_definition):
        """Test Result model.

        Test structure:
        ---------------
            {
                'name': 'valid_full',
                'input': {"host": '1.1.1.1', 'test': 'pytest_unit_test', 'result': 'success', 'messages': ['test']},
                'expected_result': 'valid',
            }

        """
        if test_definition['expected_result'] == 'invalid':
            pytest.skip('Not concerned by the test')
        try:
            result = TestResult(**test_definition['input'])
            logging.info(f'TestResult is {result.dict()}')
        except Exception as e:
            logging.error(f'Error loading data:\n{str(e)}')
            assert False

    @pytest.mark.parametrize("test_definition", TEST_RESULT_UNIT, ids=generate_test_ids_dict)
    def test_anta_result_init_invalid(self, test_definition):
        """Test Result model.

        Test structure:
        ---------------
            {
                'name': 'valid_full',
                'input': {"host": '1.1.1.1', 'test': 'pytest_unit_test', 'result': 'success', 'messages': ['test']},
                'expected_result': 'valid',
            }

        """
        if test_definition['expected_result'] == 'valid':
            pytest.skip('Not concerned by the test')
        try:
            result = TestResult(**test_definition['input'])
        except ValueError as e:
            logging.warning(f'Error loading data:\n{str(e)}')
        else:
            logging.error('An exception is expected here')
            assert False

    @pytest.mark.parametrize("test_definition", TEST_RESULT_UNIT, ids=generate_test_ids_dict)
    def test_anta_result_set_status_success(self, test_definition):
        """Test Result model.

        Test structure:
        ---------------
            {
                'name': 'valid_full',
                'input': {"host": '1.1.1.1', 'test': 'pytest_unit_test', 'result': 'success', 'messages': ['test']},
                'expected_result': 'valid',
            }

        """
        if test_definition['expected_result'] == 'invalid':
            pytest.skip('Not concerned by the test')

        result = TestResult(**test_definition['input'])

        result.is_success()
        if result.result == 'success' and len(result.messages) == len(test_definition['input']['messages']) if 'messages' in test_definition['input'] else 0:
            logging.debug('is_success only is working')

        result.is_success('it is a great success')
        if result.result == 'success' and len(result.messages) == len(test_definition['input']['messages'])+1 if 'messages' in test_definition['input'] else 1:
            logging.debug('is_success with message is working')

    @pytest.mark.parametrize("test_definition", TEST_RESULT_UNIT, ids=generate_test_ids_dict)
    def test_anta_result_set_status_failure(self, test_definition):
        """Test Result model.

        Test structure:
        ---------------
            {
                'name': 'valid_full',
                'input': {"host": '1.1.1.1', 'test': 'pytest_unit_test', 'result': 'success', 'messages': ['test']},
                'expected_result': 'valid',
            }

        """
        if test_definition['expected_result'] == 'invalid':
            pytest.skip('Not concerned by the test')

        result = TestResult(**test_definition['input'])

        result.is_failure()
        if result.result == 'failure' and len(result.messages) == len(test_definition['input']['messages']) if 'messages' in test_definition['input'] else 0:
            logging.debug('is_failure only is working')

        result.is_failure('it is a great failure')
        if result.result == 'failure' and len(result.messages) == len(test_definition['input']['messages'])+1 if 'messages' in test_definition['input'] else 1:
            logging.debug('is_failure with message is working')

    @pytest.mark.parametrize("test_definition", TEST_RESULT_UNIT, ids=generate_test_ids_dict)
    def test_anta_result_set_status_error(self, test_definition):
        """Test Result model.

        Test structure:
        ---------------
            {
                'name': 'valid_full',
                'input': {"host": '1.1.1.1', 'test': 'pytest_unit_test', 'result': 'success', 'messages': ['test']},
                'expected_result': 'valid',
            }

        """
        if test_definition['expected_result'] == 'invalid':
            pytest.skip('Not concerned by the test')

        result = TestResult(**test_definition['input'])

        result.is_error()
        if result.result == 'error' and len(result.messages) == len(test_definition['input']['messages']) if 'messages' in test_definition['input'] else 0:
            logging.debug('is_error only is working')

        result.is_error('it is a great error')
        if result.result == 'error' and len(result.messages) == len(test_definition['input']['messages'])+1 if 'messages' in test_definition['input'] else 1:
            logging.debug('is_error with message is working')

    @pytest.mark.parametrize("test_definition", TEST_RESULT_UNIT, ids=generate_test_ids_dict)
    def test_anta_result_set_status_skipped(self, test_definition):
        """Test Result model.

        Test structure:
        ---------------
            {
                'name': 'valid_full',
                'input': {"host": '1.1.1.1', 'test': 'pytest_unit_test', 'result': 'success', 'messages': ['test']},
                'expected_result': 'valid',
            }

        """
        if test_definition['expected_result'] == 'invalid':
            pytest.skip('Not concerned by the test')

        result = TestResult(**test_definition['input'])

        result.is_skipped()
        if result.result == 'skipped' and len(result.messages) == len(test_definition['input']['messages']) if 'messages' in test_definition['input'] else 0:
            logging.debug('is_skipped only is working')

        result.is_skipped('it is a great skipped')
        if result.result == 'skipped' and len(result.messages) == len(test_definition['input']['messages'])+1 if 'messages' in test_definition['input'] else 1:
            logging.debug('is_skipped with message is working')
