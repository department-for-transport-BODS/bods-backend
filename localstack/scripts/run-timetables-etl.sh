#!/bin/bash

awslocal stepfunctions --endpoint http://localhost:4566 start-execution \
    --state-machine arn:aws:states:eu-west-2:000000000000:stateMachine:bods-backend-local-tetl-sm \
    --input "$(cat <<EOF
{
    "detail": {
        "bucket": {
            "name": "bodds-local-sirivm"
        },
        "object": {
            "key": "4.zip"
        },
        "dataset_type": "timetables",
        "dataset_revision_id": 2
    }
}
EOF
)" | jq -r '.executionArn'
