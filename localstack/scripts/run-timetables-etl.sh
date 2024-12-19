#!/bin/bash

awslocal stepfunctions --endpoint http://localhost:4566 start-execution \
    --state-machine arn:aws:states:eu-west-2:000000000000:stateMachine:bods-backend-local-tt-sm\
    --input "$(cat <<EOF
[
    {
        "detail": {
            "bucket": {
                "name": "timetables-etl"
            },
            "object": {
                "key": "test-timetable-dataset.zip"
            },
            "datasetType": "timetables",
            "datasetRevisionId": 8
        }
    }
]
EOF
)" | jq -r '.executionArn'
