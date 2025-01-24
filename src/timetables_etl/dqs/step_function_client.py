import json
from os import environ

import boto3
from structlog.stdlib import get_logger

logger = get_logger()

class StepFunctionsClientWrapper:
    def __init__(self):
        try:
            if environ.get("PROJECT_ENV") == "LOCAL":
                self.sm_client = boto3.client(
                    "stepfunctions",
                    region_name=environ.get("AWS_REGION_NAME", default=""),
                    aws_access_key_id=environ.get("AWS_ACCESS_KEY_ID", default=""),
                    aws_secret_access_key=environ.get("AWS_SECRET_ACCESS_KEY", default=""),
                    aws_session_token=environ.get("AWS_SESSION_TOKEN", default=""),
                )
            else:
                self.sm_client = boto3.client("stepfunctions")
        except Exception as e:
            logger.info(
                f"DQS-StepFunctions:General exception when initialising Step Functions client wrapper: {e}"
            )
            logger.exception(e)
            raise

    def start_execution(self, state_machine_arn: str, input: dict, name: str) -> str:
        """
        Start a Step Functions execution and return the execution ARN.
        """
        try:
            response = self.sm_client.start_execution(
                stateMachineArn=state_machine_arn, input=json.dumps(input), name=name
            )
            return response["executionArn"]
        except Exception as e:
            logger.info(
                f"DQS-StepFunctions:General exception when starting Step Functions execution: {e}"
            )
            raise

