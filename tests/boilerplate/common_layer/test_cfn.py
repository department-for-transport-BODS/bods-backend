"""
Tests Cloudformation Response decorator
To ensure that Custom Cloudformation Lambdas correctly return always without causing hangs
"""

import json
from typing import Any
from unittest.mock import Mock, patch

import pytest
from common_layer.aws.cfn import cloudformation_response


@pytest.fixture
def mock_context() -> Mock:
    """Mock Lambda context with a predefined log stream name."""
    context = Mock()
    context.log_stream_name = "test-log-stream-1234"
    return context


@pytest.fixture
def base_cloudformation_event() -> dict[str, Any]:
    """Creates a base CloudFormation event with standard required fields."""
    return {
        "StackId": "arn:aws:cloudformation:us-east-1:123456789012:stack/test-stack",
        "RequestId": "test-request-1234",
        "LogicalResourceId": "TestResource",
        "ResponseURL": "https://cloudformation-custom-resource.amazonaws.com/response",
        "ResourceProperties": {"CustomProperty": "test-value"},
    }


class TestCloudFormationResponseDecorator:
    """
    Tests the CloudFormation response decorator's handling of custom resource events.
    Need to ensure the correct response is returned otherwise CFN will hang for more than an hour
    """

    @pytest.mark.parametrize(
        "event_data,expected_status,expected_response",
        [
            pytest.param(
                {"RequestType": "Create", "additional_data": "test"},
                200,
                {"message": "Operation completed successfully"},
                id="Create New Resource",
            ),
            pytest.param(
                {"RequestType": "Update", "additional_data": "updated"},
                200,
                {"message": "Operation completed successfully"},
                id="Update Existing Resource",
            ),
            pytest.param(
                {"RequestType": "Delete"},
                200,
                {"message": "Nothing to delete"},
                id="Delete Resource",
            ),
            pytest.param(
                {"RequestType": "Invalid"},
                400,
                {"message": "Unsupported request type: Invalid"},
                id="Invalid Request Type",
            ),
        ],
    )
    @patch("common_layer.cfn.http.request")
    def test_cloudformation_requests(
        self,
        mock_http_request: Mock,
        event_data: dict[str, Any],
        expected_status: int,
        expected_response: dict[str, str],
        base_cloudformation_event: dict[str, Any],
        mock_context: Mock,
    ) -> None:
        """
        Test handling the different kinds of cloudformation operation
        """
        # Setup
        mock_http_request.return_value.status = 200
        event = {**base_cloudformation_event, **event_data}

        # Create test handler
        @cloudformation_response()
        def test_handler(event: dict[str, Any], context: Any) -> dict[str, Any]:
            return {
                "statusCode": 200,
                "message": "Operation completed successfully",
                "data": {"result": "success"},
            }

        # Execute
        result = test_handler(event, mock_context)

        # Verify HTTP request was made with correct data
        if event_data["RequestType"] != "Invalid":
            mock_http_request.assert_called_once()
            call_args = mock_http_request.call_args
            assert call_args[0][0] == "PUT"
            assert call_args[0][1] == event["ResponseURL"]

            sent_body = json.loads(call_args[1]["body"].decode("utf-8"))
            assert (
                sent_body["Status"] == "SUCCESS"
                if event_data["RequestType"] != "Invalid"
                else "FAILED"
            )
            assert sent_body["PhysicalResourceId"] == mock_context.log_stream_name
            assert sent_body["StackId"] == event["StackId"]
            assert sent_body["RequestId"] == event["RequestId"]
            assert sent_body["LogicalResourceId"] == event["LogicalResourceId"]

        # Verify response
        assert result["statusCode"] == expected_status
        assert result.get("body") == expected_response["message"]

    @pytest.mark.parametrize(
        "event_data,expected_result",
        [
            pytest.param(
                {"input": "test-data"},
                {"statusCode": 200, "message": "Operation completed successfully"},
                id="Direct Lambda Invocation",
            ),
        ],
    )
    def test_direct_lambda_invocation(
        self,
        event_data: dict[str, Any],
        expected_result: dict[str, Any],
        mock_context: Mock,
    ) -> None:
        """
        Test when the lambda is invoked outside of a cloud formation custom resource
        """

        @cloudformation_response()
        def test_handler(event: dict[str, Any], context: Any) -> dict[str, Any]:
            return {"statusCode": 200, "message": "Operation completed successfully"}

        result = test_handler(event_data, mock_context)
        assert result == expected_result

    @patch("common_layer.cfn.http.request")
    def test_error_handling(
        self,
        mock_http_request: Mock,
        base_cloudformation_event: dict[str, Any],
        mock_context: Mock,
    ) -> None:
        """
        Ensure that errors are constructed correctly for the cfn api
        """
        mock_http_request.return_value.status = 200
        event = {**base_cloudformation_event, "RequestType": "Create"}

        @cloudformation_response()
        def test_handler(event: dict[str, Any], context: Any) -> dict[str, Any]:
            raise ValueError("Test error")

        with pytest.raises(ValueError, match="Test error"):
            test_handler(event, mock_context)

        # Verify error was reported to CloudFormation
        mock_http_request.assert_called_once()
        call_args = mock_http_request.call_args
        sent_body = json.loads(call_args[1]["body"].decode("utf-8"))
        assert sent_body["Status"] == "FAILED"
        assert sent_body["Data"]["Error"] == "Test error"
