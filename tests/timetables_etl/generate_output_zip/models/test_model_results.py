""" """

from datetime import UTC, datetime

import pytest
from common_layer.aws.step.map_results_models import (
    MapExecutionFailed,
    MapExecutionSucceeded,
    MapInputData,
    MapResultFailed,
    MapResultSucceeded,
    MapRunExecutionStatus,
)


@pytest.mark.parametrize(
    "json_str,expected_model",
    [
        pytest.param(
            r"""
            [
                {
                    "ExecutionArn": "arn:aws:states:eu-west-2:228266753808:execution:bods-backend-dev-tt-sm/8c9dd6c6-f907-3584-9153-f8a2f1bfe7ce:ac537772-4599-3a63-bbbc-cf52f4cbb818",
                    "Input": "",
                    "InputDetails": { "Included": false },
                    "Name": "ac537772-4599-3a63-bbbc-cf52f4cbb818",
                    "Output": "",
                    "OutputDetails": { "Included": false },
                    "RedriveCount": 0,
                    "RedriveStatus": "NOT_REDRIVABLE",
                    "RedriveStatusReason": "Execution is SUCCEEDED and cannot be redriven",
                    "StartDate": "2025-01-09T18:13:01.189Z",
                    "StateMachineArn": "arn:aws:states:eu-west-2:228266753808:stateMachine:bods-backend-dev-tt-sm/8c9dd6c6-f907-3584-9153-f8a2f1bfe7ce",
                    "Status": "SUCCEEDED",
                    "StopDate": "2025-01-09T18:14:18.554Z"
                }
            ]
            """,
            [
                MapExecutionSucceeded(
                    ExecutionArn="arn:aws:states:eu-west-2:228266753808:execution:bods-backend-dev-tt-sm/8c9dd6c6-f907-3584-9153-f8a2f1bfe7ce:ac537772-4599-3a63-bbbc-cf52f4cbb818",
                    Input="",
                    InputDetails={"Included": False},
                    Name="ac537772-4599-3a63-bbbc-cf52f4cbb818",
                    Output="",
                    OutputDetails={"Included": False},
                    RedriveCount=0,
                    RedriveStatus="NOT_REDRIVABLE",
                    RedriveStatusReason="Execution is SUCCEEDED and cannot be redriven",
                    StartDate=datetime(2025, 1, 9, 18, 13, 1, 189000, tzinfo=UTC),
                    StateMachineArn="arn:aws:states:eu-west-2:228266753808:stateMachine:bods-backend-dev-tt-sm/8c9dd6c6-f907-3584-9153-f8a2f1bfe7ce",
                    Status=MapRunExecutionStatus.SUCCEEDED,
                    StopDate=datetime(2025, 1, 9, 18, 14, 18, 554000, tzinfo=UTC),
                )
            ],
            id="No Input / Output",
        ),
        pytest.param(
            r"""
            [
                {
                    "ExecutionArn": "arn:aws:states:eu-west-2:228266753808:execution:bods-backend-dev-tt-sm/8c9dd6c6-f907-3584-9153-f8a2f1bfe7ce:ac537772-4599-3a63-bbbc-cf52f4cbb818",
                    "Input": "{\"Bucket\":\"bodds-dev\",\"DatasetRevisionId\":\"3989\",\"detail\":{\"bucket\":{\"name\":\"bodds-dev\"},\"object\":{\"key\":\"coach-data/zip/2024-01-03-CoachData-Subset-with-invalid-files.zip\"},\"datasetRevisionId\":\"3989\",\"datasetType\":\"timetables\"},\"DatasetEtlTaskResultId\":3837,\"Key\":\"2024-01-03-CoachData-Subset-with-invalid-files/d05e3f87-13bb-46d0-8a4f-e7934b916013/dataset-15890-subset-with-invalid-files/ANEA_1D12_ANEAPB0002717239X12_20241104_20241221_1960469.xml\"}",
                    "InputDetails": { "Included": true },
                    "Name": "ac537772-4599-3a63-bbbc-cf52f4cbb818",
                    "Output": "{\"Bucket\":\"bodds-dev\",\"DatasetRevisionId\":\"3989\",\"detail\":{\"bucket\":{\"name\":\"bodds-dev\"},\"object\":{\"key\":\"coach-data/zip/2024-01-03-CoachData-Subset-with-invalid-files.zip\"},\"datasetRevisionId\":\"3989\",\"datasetType\":\"timetables\"},\"DatasetEtlTaskResultId\":3837,\"Key\":\"2024-01-03-CoachData-Subset-with-invalid-files/d05e3f87-13bb-46d0-8a4f-e7934b916013/dataset-15890-subset-with-invalid-files/ANEA_1D12_ANEAPB0002717239X12_20241104_20241221_1960469.xml\",\"fileValidation\":{\"statusCode\":200,\"body\":\"Completed File Validation\"},\"schemaCheck\":{\"statusCode\":200,\"body\":\"Successfully ran the file schema check for file '2024-01-03-CoachData-Subset-with-invalid-files/d05e3f87-13bb-46d0-8a4f-e7934b916013/dataset-15890-subset-with-invalid-files/ANEA_1D12_ANEAPB0002717239X12_20241104_20241221_1960469.xml' from bucket 'bodds-dev' with 0 violations\"},\"postSchemaCheck\":{\"statusCode\":200,\"body\":\"Completed Post Schema Check\"},\"fileAttributesEtl\":{\"id\":37115},\"ptiValidation\":{\"statusCode\":200},\"etlProcess\":{\"status_code\":200,\"message\":\"ETL Completed\"}}",
                    "OutputDetails": { "Included": true },
                    "RedriveCount": 0,
                    "RedriveStatus": "NOT_REDRIVABLE",
                    "RedriveStatusReason": "Execution is SUCCEEDED and cannot be redriven",
                    "StartDate": "2025-01-09T18:13:01.189Z",
                    "StateMachineArn": "arn:aws:states:eu-west-2:228266753808:stateMachine:bods-backend-dev-tt-sm/8c9dd6c6-f907-3584-9153-f8a2f1bfe7ce",
                    "Status": "SUCCEEDED",
                    "StopDate": "2025-01-09T18:14:18.554Z"
                }
            ]
            """,
            [
                MapExecutionSucceeded(
                    ExecutionArn="arn:aws:states:eu-west-2:228266753808:execution:bods-backend-dev-tt-sm/8c9dd6c6-f907-3584-9153-f8a2f1bfe7ce:ac537772-4599-3a63-bbbc-cf52f4cbb818",
                    Input='{"Bucket":"bodds-dev","DatasetRevisionId":"3989","detail":{"bucket":{"name":"bodds-dev"},"object":{"key":"coach-data/zip/2024-01-03-CoachData-Subset-with-invalid-files.zip"},"datasetRevisionId":"3989","datasetType":"timetables"},"DatasetEtlTaskResultId":3837,"Key":"2024-01-03-CoachData-Subset-with-invalid-files/d05e3f87-13bb-46d0-8a4f-e7934b916013/dataset-15890-subset-with-invalid-files/ANEA_1D12_ANEAPB0002717239X12_20241104_20241221_1960469.xml"}',
                    InputDetails={"Included": True},
                    Name="ac537772-4599-3a63-bbbc-cf52f4cbb818",
                    Output='{"Bucket":"bodds-dev","DatasetRevisionId":"3989","detail":{"bucket":{"name":"bodds-dev"},"object":{"key":"coach-data/zip/2024-01-03-CoachData-Subset-with-invalid-files.zip"},"datasetRevisionId":"3989","datasetType":"timetables"},"DatasetEtlTaskResultId":3837,"Key":"2024-01-03-CoachData-Subset-with-invalid-files/d05e3f87-13bb-46d0-8a4f-e7934b916013/dataset-15890-subset-with-invalid-files/ANEA_1D12_ANEAPB0002717239X12_20241104_20241221_1960469.xml","fileValidation":{"statusCode":200,"body":"Completed File Validation"},"schemaCheck":{"statusCode":200,"body":"Successfully ran the file schema check for file \'2024-01-03-CoachData-Subset-with-invalid-files/d05e3f87-13bb-46d0-8a4f-e7934b916013/dataset-15890-subset-with-invalid-files/ANEA_1D12_ANEAPB0002717239X12_20241104_20241221_1960469.xml\' from bucket \'bodds-dev\' with 0 violations"},"postSchemaCheck":{"statusCode":200,"body":"Completed Post Schema Check"},"fileAttributesEtl":{"id":37115},"ptiValidation":{"statusCode":200},"etlProcess":{"status_code":200,"message":"ETL Completed"}}',
                    OutputDetails={"Included": True},
                    RedriveCount=0,
                    RedriveStatus="NOT_REDRIVABLE",
                    RedriveStatusReason="Execution is SUCCEEDED and cannot be redriven",
                    StartDate=datetime(2025, 1, 9, 18, 13, 1, 189000, tzinfo=UTC),
                    StateMachineArn="arn:aws:states:eu-west-2:228266753808:stateMachine:bods-backend-dev-tt-sm/8c9dd6c6-f907-3584-9153-f8a2f1bfe7ce",
                    Status=MapRunExecutionStatus.SUCCEEDED,
                    StopDate=datetime(2025, 1, 9, 18, 14, 18, 554000, tzinfo=UTC),
                )
            ],
            id="Standard version",
        ),
    ],
)
def test_succeeded_parsing_valid(
    json_str: str, expected_model: list[MapExecutionSucceeded]
) -> None:
    """Test parsing valid succeeded execution data by comparing complete model instances"""
    result = MapResultSucceeded.model_validate_json(json_str)
    assert result.root == expected_model


@pytest.mark.parametrize(
    "json_str,expected_model",
    [
        pytest.param(
            r"""
            [
                {
                    "Cause": "An error occurred while executing the state 'ExceptionHandler' (entered at the event id #27). The JSONPath '$.Bucket' specified for the field 'Bucket.$' could not be found in the input '{\"Error\":\"Lambda.Unknown\",\"Cause\":\"The cause could not be determined because Lambda did not return an error type. Returned payload: {\\\"errorMessage\\\":\\\"2025-01-07T10:40:38.651Z ab9a35df-8e8e-4c78-9363-0dd2bf9e782a Task timed out after 60.16 seconds\\\"}\"}'",
                    "Error": "States.Runtime",
                    "ExecutionArn": "arn:aws:states:eu-west-2:228266753808:execution:bods-backend-dev-tt-sm/8c9dd6c6-f907-3584-9153-f8a2f1bfe7ce:55334b15-7c04-3b8d-8ee4-5c6f72f90dbc",
                    "Input": "{\"Bucket\":\"bodds-dev\",\"DatasetRevisionId\":\"3989\",\"detail\":{\"bucket\":{\"name\":\"bodds-dev\"},\"object\":{\"key\":\"3624_extracted_vehicle_journey_runtimes.xml\"},\"datasetRevisionId\":\"3989\",\"datasetType\":\"timetables\"},\"DatasetEtlTaskResultId\":3794,\"Key\":\"ext_3624_extracted_vehicle_journey_runtimes/3624_extracted_vehicle_journey_runtimes.xml\"}",
                    "InputDetails": { "Included": true },
                    "Name": "55334b15-7c04-3b8d-8ee4-5c6f72f90dbc",
                    "OutputDetails": { "Included": true },
                    "RedriveCount": 0,
                    "RedriveStatus": "REDRIVABLE_BY_MAP_RUN",
                    "StartDate": "2025-01-07T10:38:47.702Z",
                    "StateMachineArn": "arn:aws:states:eu-west-2:228266753808:stateMachine:bods-backend-dev-tt-sm/8c9dd6c6-f907-3584-9153-f8a2f1bfe7ce",
                    "Status": "FAILED",
                    "StopDate": "2025-01-07T10:40:38.759Z"
                }
            ]
            """,
            MapResultFailed(
                root=[
                    MapExecutionFailed(
                        Cause='An error occurred while executing the state \'ExceptionHandler\' (entered at the event id #27). The JSONPath \'$.Bucket\' specified for the field \'Bucket.$\' could not be found in the input \'{"Error":"Lambda.Unknown","Cause":"The cause could not be determined because Lambda did not return an error type. Returned payload: {\\"errorMessage\\":\\"2025-01-07T10:40:38.651Z ab9a35df-8e8e-4c78-9363-0dd2bf9e782a Task timed out after 60.16 seconds\\"}"}\'',
                        Error="States.Runtime",
                        ExecutionArn="arn:aws:states:eu-west-2:228266753808:execution:bods-backend-dev-tt-sm/8c9dd6c6-f907-3584-9153-f8a2f1bfe7ce:55334b15-7c04-3b8d-8ee4-5c6f72f90dbc",
                        Input='{"Bucket":"bodds-dev","DatasetRevisionId":"3989","detail":{"bucket":{"name":"bodds-dev"},"object":{"key":"3624_extracted_vehicle_journey_runtimes.xml"},"datasetRevisionId":"3989","datasetType":"timetables"},"DatasetEtlTaskResultId":3794,"Key":"ext_3624_extracted_vehicle_journey_runtimes/3624_extracted_vehicle_journey_runtimes.xml"}',
                        InputDetails={"Included": True},
                        Name="55334b15-7c04-3b8d-8ee4-5c6f72f90dbc",
                        OutputDetails={"Included": True},
                        RedriveCount=0,
                        RedriveStatus="REDRIVABLE_BY_MAP_RUN",
                        StartDate=datetime(2025, 1, 7, 10, 38, 47, 702000, tzinfo=UTC),
                        StateMachineArn="arn:aws:states:eu-west-2:228266753808:stateMachine:bods-backend-dev-tt-sm/8c9dd6c6-f907-3584-9153-f8a2f1bfe7ce",
                        Status=MapRunExecutionStatus.FAILED,
                        StopDate=datetime(2025, 1, 7, 10, 40, 38, 759000, tzinfo=UTC),
                    )
                ]
            ),
            id="Standard Failed Execution Lambda Timeout",
        ),
    ],
)
def test_failed_parsing_valid(json_str: str, expected_model: MapResultFailed) -> None:
    """Test parsing valid failed execution data by comparing complete model instances"""
    result = MapResultFailed.model_validate_json(json_str)
    assert result == expected_model


@pytest.mark.parametrize(
    "json_str,expected_parsed_input",
    [
        pytest.param(
            r"""[{
                "ExecutionArn": "arn:aws:states:eu-west-2:123:execution:test",
                "Input": "{\"mapS3Bucket\":\"test-bucket\",\"mapS3Object\":\"test/key.xml\",\"mapDatasetRevisionId\":123,\"mapDatasetEtlTaskResultId\":456}",
                "InputDetails": { "Included": true },
                "Name": "test-execution",
                "Output": "",
                "OutputDetails": { "Included": false },
                "RedriveCount": 0,
                "RedriveStatus": "NOT_REDRIVABLE",
                "RedriveStatusReason": "Test reason",
                "StartDate": "2025-01-09T18:13:01.189Z",
                "StateMachineArn": "arn:aws:states:eu-west-2:123:stateMachine:test",
                "Status": "SUCCEEDED",
                "StopDate": "2025-01-09T18:14:18.554Z"
            }]""",
            MapInputData(
                Bucket="test-bucket",
                Key="test/key.xml",
                DatasetRevisionId=123,
                mapDatasetEtlTaskResultId=456,
            ),
            id="Map prefixed fields parsing",
        ),
        pytest.param(
            r"""[{
                "ExecutionArn": "arn:aws:states:eu-west-2:123:execution:test",
                "Input": "{\"Bucket\":\"test-bucket\",\"Key\":\"test/key.xml\",\"DatasetRevisionId\":123,\"mapDatasetEtlTaskResultId\":456}",
                "InputDetails": { "Included": true },
                "Name": "test-execution",
                "Output": "",
                "OutputDetails": { "Included": false },
                "RedriveCount": 0,
                "RedriveStatus": "NOT_REDRIVABLE",
                "RedriveStatusReason": "Test reason",
                "StartDate": "2025-01-09T18:13:01.189Z",
                "StateMachineArn": "arn:aws:states:eu-west-2:123:stateMachine:test",
                "Status": "SUCCEEDED",
                "StopDate": "2025-01-09T18:14:18.554Z"
            }]""",
            MapInputData(
                Bucket="test-bucket",
                Key="test/key.xml",
                DatasetRevisionId=123,
                mapDatasetEtlTaskResultId=456,
            ),
            id="Standard field names parsing",
        ),
        pytest.param(
            r"""[{
                "ExecutionArn": "arn:aws:states:eu-west-2:123:execution:test",
                "Input": "{\"invalid_json",
                "InputDetails": { "Included": true },
                "Name": "test-execution",
                "Output": "",
                "OutputDetails": { "Included": false },
                "RedriveCount": 0,
                "RedriveStatus": "NOT_REDRIVABLE",
                "RedriveStatusReason": "Test reason",
                "StartDate": "2025-01-09T18:13:01.189Z",
                "StateMachineArn": "arn:aws:states:eu-west-2:123:stateMachine:test",
                "Status": "SUCCEEDED",
                "StopDate": "2025-01-09T18:14:18.554Z"
            }]""",
            None,
            id="Invalid JSON input",
        ),
    ],
)
def test_parsed_input_field(
    json_str: str, expected_parsed_input: MapInputData | None
) -> None:
    """Test the parsed_input field is correctly populated from Input JSON"""
    result = MapResultSucceeded.model_validate_json(json_str)
    assert result.root[0].parsed_input == expected_parsed_input
