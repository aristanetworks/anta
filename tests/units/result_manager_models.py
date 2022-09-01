#!/usr/bin/python
# coding: utf-8 -*-

"""ANTA Result Manager models unit tests."""

import logging
from typing import Dict, Any
import pytest
from anta.result_manager.models import TestResult
from tests.data.utils import generate_test_ids_dict
from tests.data.json_data import TEST_RESULT_UNIT


class Test_InventoryUnitModels():
    """Test components of anta.result_manager.models."""

    @pytest.mark.parametrize("test_definition", TEST_RESULT_UNIT, ids=generate_test_ids_dict)
    def test_anta_result_init_valid(self, test_definition: Dict[str, Any]) -> None:
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
        # pylint: disable=W0703
        except Exception as e:
            logging.error(f'Error loading data:\n{str(e)}')
            assert False

    @pytest.mark.parametrize("test_definition", TEST_RESULT_UNIT, ids=generate_test_ids_dict)
    def test_anta_result_init_invalid(self, test_definition: Dict[str, Any]) -> None:
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
            TestResult(**test_definition['input'])
        except ValueError as e:
            logging.warning(f'Error loading data:\n{str(e)}')
        else:
            logging.error('An exception is expected here')
            assert False

    @pytest.mark.parametrize("test_definition", TEST_RESULT_UNIT, ids=generate_test_ids_dict)
    def test_anta_result_set_status_success(self, test_definition: Dict[str, Any]) -> None:
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
        assert result.result == 'success'
        result_message_len = len(result.messages)

        if 'messages' in test_definition['input']:
            assert result_message_len == len(
                test_definition['input']['messages'])
        else:
            assert result_message_len == 0

        # Adding one message
        result.is_success('it is a great success')
        assert result.result == 'success'
        assert len(result.messages) == result_message_len + 1

    @pytest.mark.parametrize("test_definition", TEST_RESULT_UNIT, ids=generate_test_ids_dict)
    def test_anta_result_set_status_failure(self, test_definition: Dict[str, Any]) -> None:
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
        assert result.result == 'failure'
        result_message_len = len(result.messages)

        if 'messages' in test_definition['input']:
            assert result_message_len == len(
                test_definition['input']['messages'])
        else:
            assert result_message_len == 0

        # Adding one message
        result.is_failure('it is a great failure')
        assert result.result == 'failure'
        assert len(result.messages) == result_message_len + 1

    @pytest.mark.parametrize("test_definition", TEST_RESULT_UNIT, ids=generate_test_ids_dict)
    def test_anta_result_set_status_error(self, test_definition: Dict[str, Any]) -> None:
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
        assert result.result == 'error'
        result_message_len = len(result.messages)

        if 'messages' in test_definition['input']:
            assert result_message_len == len(
                test_definition['input']['messages'])
        else:
            assert result_message_len == 0

        # Adding one message
        result.is_error('it is a great error')
        assert result.result == 'error'
        assert len(result.messages) == result_message_len + 1

    @pytest.mark.parametrize("test_definition", TEST_RESULT_UNIT, ids=generate_test_ids_dict)
    def test_anta_result_set_status_skipped(self, test_definition: Dict[str, Any]) -> None:
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
        assert result.result == 'skipped'
        result_message_len = len(result.messages)

        if 'messages' in test_definition['input']:
            assert result_message_len == len(
                test_definition['input']['messages'])
        else:
            assert result_message_len == 0

        # Adding one message
        result.is_skipped('it is a great skipped')
        assert result.result == 'skipped'
        assert len(result.messages) == result_message_len + 1
