#!/bin/bash
CURRENT_STEP_FUNCTION_EXECUTION_ARN=$1
awslocal stepfunctions --endpoint http://localhost:4566 describe-execution --execution-arn "$CURRENT_STEP_FUNCTION_EXECUTION_ARN"
