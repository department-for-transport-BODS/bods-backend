CURRENT_STEP_FUNCTION_EXECUTION_ARN=$(awslocal stepfunctions --endpoint http://localhost:4566 start-execution \
    --state-machine arn:aws:states:eu-west-2:000000000000:stateMachine:bods-backend-local-timetables-etl-sm \
    --input "$(cat <<EOF
{
    "detail": {
        "bucket": {
            "name": "bucket-name"
        },
        "object": {
            "key": "object-key"
        }
    }
}
EOF
)" | jq -r '.executionArn')
    
export CURRENT_STEP_FUNCTION_EXECUTION_ARN
echo "Execution ARN set to: $CURRENT_STEP_FUNCTION_EXECUTION_ARN"
