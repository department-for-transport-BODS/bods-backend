import json
import logging

import boto3
from django.conf import settings

logger = logging.getLogger(__name__)


class StepFunctionsClientWrapper:
    def __init__(self):
        try:
            if settings.AWS_ENVIRONMENT == "LOCAL":
                self.sm_client = boto3.client(
                    "stepfunctions",
                    region_name=settings.AWS_REGION_NAME,
                    aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
                    aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
                    aws_session_token=settings.AWS_SESSION_TOKEN,
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

