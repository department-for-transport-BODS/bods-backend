import os
import unittest
from unittest.mock import patch, MagicMock
from periodic_tasks.pt_iterator import lambda_handler

MODULE_PATH = "periodic_tasks.pt_iterator"


@patch.dict(os.environ, {"TARGET_FUNCTION_NAMES": "function1,function2"})
@patch(f"{MODULE_PATH}.client")
@patch(f"{MODULE_PATH}.logger")
class TestPtIterator(unittest.TestCase):

    def setUp(self):
        self.event = {"iterator": {"count": 3, "index": 0}}
        self.context = MagicMock()

    def test_lambda_handler(self, mock_logger, mock_client):
        mock_client.invoke.return_value = {"StatusCode": 202}

        result = lambda_handler(self.event, self.context)

        self.assertEqual(mock_client.invoke.call_count, 2)
        mock_client.invoke.assert_any_call(FunctionName="function1", InvocationType="Event")
        mock_client.invoke.assert_any_call(FunctionName="function2", InvocationType="Event")

        mock_logger.info.assert_any_call("Target functions to invoke: function1,function2")
        mock_logger.info.assert_any_call("Invoking function: function1")
        mock_logger.info.assert_any_call("Invoking function: function2")

        self.assertEqual(result, {"index": 1, "continue": True, "count": 3})

    def test_lambda_handler_with_invoke_error(self, mock_logger, mock_client):
        self.event["iterator"]["count"] = 2  # Adjust event for this test
        self.event["iterator"]["index"] = 1
        mock_client.invoke.side_effect = Exception("Invoke failed")

        result = lambda_handler(self.event, self.context)

        mock_logger.error.assert_any_call("Error invoking function1: Invoke failed")
        mock_logger.error.assert_any_call("Error invoking function2: Invoke failed")
        self.assertEqual(result, {"index": 2, "continue": False, "count": 2})

    @patch.dict(os.environ, {"TARGET_FUNCTION_NAMES": ""})
    def test_lambda_handler_empty_env_var(self, mock_logger, mock_client):
        result = lambda_handler(self.event, self.context)

        mock_client.invoke.assert_not_called()
        self.assertEqual(result, {"index": 1, "continue": True, "count": 3})

    @patch.dict(os.environ, {}, clear=True)
    def test_lambda_handler_missing_env_var(self, mock_logger, mock_client):
        result = lambda_handler(self.event, self.context)

        mock_client.invoke.assert_not_called()
        self.assertEqual(result, {"index": 1, "continue": True, "count": 3})

    def test_lambda_handler_continue_false(self, mock_logger, mock_client):
        self.event["iterator"]["count"] = 2
        self.event["iterator"]["index"] = 2

        result = lambda_handler(self.event, self.context)

        self.assertEqual(result, {"index": 3, "continue": False, "count": 2})

    def test_lambda_handler_invoke_response_logging(self, mock_logger, mock_client):
        mock_response = {
            "ResponseMetadata": {
                "RequestId": "fbd8255b-74a6-4ca9-8a08-536d723f7692",
                "HTTPStatusCode": 202,
                "HTTPHeaders": {
                    "date": "Thu, 31 Oct 2024 16:26:19 GMT",
                    "content-length": "0",
                    "connection": "keep-alive",
                    "x-amzn-requestid": "fbd8255b-74a6-4ca9-8a08-536d723f7692",
                    "x-amzn-remapped-content-length": "0",
                    "x-amzn-trace-id": "root=1-6723afaa-485515d7477ce5026f0623f1;parent=331ebce9b206f571;sampled=0;lineage=1:81df51dd:0"
                },
                "RetryAttempts": 0
            },
            "StatusCode": 202,
            "Payload": MagicMock()
        }
        mock_client.invoke.return_value = mock_response

        lambda_handler(self.event, self.context)

        mock_logger.info.assert_any_call(f"Response from invoking function1: {mock_response}")
        mock_logger.info.assert_any_call(f"Response from invoking function2: {mock_response}")