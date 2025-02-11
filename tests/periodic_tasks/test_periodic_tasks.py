"""
Unit test for create_sirivm_zipfile lambda
"""

import importlib
import pytest

MAPPING_LAMBDAS = {
    "create_sirivm_zip": "sirivm",
    "create_sirivm_tfl_zip": "sirivm tfl",
    "create_gtfsrt_zip": "gtfsrt"
}


def test_lambda_handler_success(mocker):
    """
    Test the lambda_handler when process_archive returns a valid file name.
    """
    for module_name, text in MAPPING_LAMBDAS.items():
        lambda_module = importlib.import_module(f"periodic_tasks.{module_name}")
        lambda_handler = lambda_module.lambda_handler
        bucket_name = lambda_module.BUCKET_NAME
        event = {"key": "value"}
        context = mocker.Mock()
        dummy_archived_file_name = "gtfsrt_2025-02-11_123456.zip"

        mocker.patch(f"periodic_tasks.{module_name}.configure_logging")
        mocker.patch(f"periodic_tasks.{module_name}.bind_contextvars")
        mock_clear_contextvars = mocker.patch(
            f"periodic_tasks.{module_name}.clear_contextvars"
        )

        mock_process_archive = mocker.patch(
            f"periodic_tasks.{module_name}.process_archive",
            return_value=dummy_archived_file_name,
        )

        mocker.patch(f"periodic_tasks.{module_name}.SqlDB", autospec=True)

        result = lambda_handler(event, context)

        expected_body = (
            f"Successfully archived {text} data to file '{dummy_archived_file_name}' "
            f"in bucket '{bucket_name}'"
        )
        assert result["statusCode"] == 200
        assert result["body"] == expected_body

        mock_clear_contextvars.assert_called_once()

        mock_process_archive.assert_called_once()


def test_lambda_handler_failure(mocker):
    """
    Test the lambda_handler when process_archive raises an exception.
    """
    for module_name in MAPPING_LAMBDAS:
        lambda_module = importlib.import_module(f"periodic_tasks.{module_name}")
        lambda_handler = lambda_module.lambda_handler
        event = {"key": "value"}
        context = mocker.Mock()
        dummy_exception = Exception("process_archive failure")

        mocker.patch(f"periodic_tasks.{module_name}.configure_logging")
        mocker.patch(f"periodic_tasks.{module_name}.bind_contextvars")
        mock_clear_contextvars = mocker.patch(
            f"periodic_tasks.{module_name}.clear_contextvars"
        )

        mocker.patch(
            f"periodic_tasks.{module_name}.process_archive", side_effect=dummy_exception
        )
        mocker.patch(f"periodic_tasks.{module_name}.SqlDB", autospec=True)

        with pytest.raises(Exception, match="process_archive failure"):
            lambda_handler(event, context)

        mock_clear_contextvars.assert_called_once()
