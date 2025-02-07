import os
import unittest
from unittest.mock import MagicMock, patch

from periodic_tasks.iterator import lambda_handler

MODULE_PATH = "periodic_tasks.iterator"


@patch(f"{MODULE_PATH}.client")
@patch(f"{MODULE_PATH}.log")
class TestPtIterator(unittest.TestCase):

    def setUp(self):
        self.context = MagicMock()
        self.event = {"functionName": "test-function", "intervals": [5, 10]}

    def test_lambda_handler_valid_event(self, mock_logger, mock_client):
        mock_response = MagicMock()
        mock_response["Payload"].read.return_value = b"Mock response"
        mock_client.invoke.return_value = mock_response
        result = lambda_handler(self.event, self.context)
        self.assertEqual(mock_client.invoke.call_count, 2)
        mock_client.invoke.assert_called_with(
            FunctionName="test-function", InvocationType="RequestResponse"
        )
        mock_logger.info.assert_any_call("Actioning interval", interval=5)
        mock_logger.info.assert_any_call("Actioning interval", interval=10)
        self.assertTrue(
            any(
                "Synchronous invocation time" in call[0][0]
                for call in mock_logger.info.call_args_list
            ),
            "Expected 'Synchronous invocation time' to be logged",
        )
        mock_logger.info.assert_any_call(f"Response from test-function: Mock response")
        self.assertEqual(
            result,
            {
                "status": "completed",
                "executedIntervals": [5, 10],
                "functionName": "test-function",
                "currentMinute": result["currentMinute"],
            },
        )

    def test_lambda_handler_missing_function_name(self, mock_logger, mock_client):
        self.event.pop("functionName")
        result = lambda_handler(self.event, self.context)
        mock_logger.error.assert_called_once_with(
            "No function name provided in the input!"
        )
        self.assertEqual(result, {"error": "functionName is required"})
        mock_client.invoke.assert_not_called()

    def test_lambda_handler_invoke_error(self, mock_logger, mock_client):
        mock_client.invoke.side_effect = Exception("Invoke failed")
        result = lambda_handler(self.event, self.context)
        mock_logger.error.assert_any_call(
            "Error invoking function", function_name="test-function", exc_info=True
        )
        self.assertEqual(
            result,
            {
                "status": "completed",
                "executedIntervals": [5, 10],
                "functionName": "test-function",
                "currentMinute": result["currentMinute"],
            },
        )

    def test_lambda_handler_empty_intervals(self, mock_logger, mock_client):
        self.event["intervals"] = []
        result = lambda_handler(self.event, self.context)
        mock_client.invoke.assert_not_called()
        self.assertEqual(
            result,
            {
                "status": "completed",
                "executedIntervals": [],
                "functionName": "test-function",
                "currentMinute": result["currentMinute"],
            },
        )

    def test_lambda_handler_waiting(self, mock_logger, mock_client):
        with patch("time.sleep", return_value=None) as mock_sleep:
            mock_client.invoke.return_value = MagicMock(
                Payload=MagicMock(read=lambda: b"Mock response")
            )
            result = lambda_handler(self.event, self.context)
            self.assertEqual(mock_sleep.call_count, 2)
            self.assertEqual(
                result,
                {
                    "status": "completed",
                    "executedIntervals": [5, 10],
                    "functionName": "test-function",
                    "currentMinute": result["currentMinute"],
                },
            )
