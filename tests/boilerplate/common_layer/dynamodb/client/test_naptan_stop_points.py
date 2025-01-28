from unittest.mock import patch

import pytest
from common_layer.dynamodb.client import NaptanStopPointDynamoDBClient
from common_layer.dynamodb.client.naptan_stop_points import NaptanDynamoDBSettings
from common_layer.txc.models.txc_stoppoint import TXCStopPoint


@pytest.fixture
def m_boto3_client():
    """
    Fixture to patch the boto3 client used by the DynamoDB base class.
    """
    with patch("common_layer.dynamodb.client.base.boto3.client") as m_boto3:
        yield m_boto3


def get_stop_point_stored_document(atco_code: str):
    return {
        "AtcoCode": {"S": atco_code},
        "NaptanCode": {"S": "bstjaja"},
        "Descriptor": {
            "M": {
                "CommonName": {"S": "Temple Meads Stn"},
                "ShortCommonName": {"S": "Temple Meads Stn"},
                "Street": {"S": "Station Approach"},
                "Indicator": {"S": "T6"},
            }
        },
        "Place": {
            "M": {
                "NptgLocalityRef": {"S": "N0077020"},
                "Location": {
                    "M": {
                        "Longitude": {"S": "-2.58262"},
                        "Latitude": {"S": "51.44898"},
                        "Easting": {"S": "359609"},
                        "Northing": {"S": "172383"},
                    }
                },
            }
        },
        "StopClassification": {
            "M": {
                "StopType": {"S": "busCoachTrolleyOnStreetPoint"},
                "OnStreet": {
                    "M": {
                        "Bus": {
                            "M": {
                                "BusStopType": {"S": "marked"},
                                "TimingStatus": {"S": "otherPoint"},
                                "MarkedPoint": {
                                    "M": {
                                        "Bearing": {"M": {"CompassPoint": {"S": "NE"}}}
                                    }
                                },
                            }
                        }
                    }
                },
            }
        },
        "AdministrativeAreaRef": {"S": "009"},
    }


def test_get_by_atco_codes(m_boto3_client):
    """
    Test get_by_atco_codes correctly batches requests and handles results.
    """
    table_name = "naptan-stop-point-table"

    m_boto3_client.return_value.batch_get_item.side_effect = [
        {"Responses": {table_name: [get_stop_point_stored_document("ATCO001")]}},
        {"Responses": {table_name: [get_stop_point_stored_document("ATCO003")]}},
    ]
    settings = NaptanDynamoDBSettings(DYNAMODB_NAPTAN_STOP_POINT_TABLE_NAME=table_name)
    stop_point_client = NaptanStopPointDynamoDBClient(settings)

    atco_codes = [
        f"ATCO00{i}" for i in range(150)
    ]  # 150 items (exceeding single batch size)

    stop_points, missing_codes = stop_point_client.get_by_atco_codes(atco_codes)

    assert len(stop_points) == 2
    assert stop_points[0].AtcoCode == "ATCO001"
    assert stop_points[1].AtcoCode == "ATCO003"

    assert len(missing_codes) == 148

    assert m_boto3_client.return_value.batch_get_item.call_count == 2

    # First batch get request
    m_boto3_client.return_value.batch_get_item.assert_any_call(
        RequestItems={
            table_name: {
                "Keys": [{"AtcoCode": {"S": f"ATCO00{i}"}} for i in range(100)]
            }
        }
    )

    # Second batch get request
    m_boto3_client.return_value.batch_get_item.assert_any_call(
        RequestItems={
            table_name: {
                "Keys": [{"AtcoCode": {"S": f"ATCO00{i}"}} for i in range(100, 150)]
            }
        }
    )


def test_get_stop_area_map(m_boto3_client):
    """
    Test that get_stop_area_map returns the expected mapping
    """
    client = NaptanStopPointDynamoDBClient()

    with patch.object(client, "get_by_atco_codes") as m_get_by_atco_codes:

        stop_point_1 = TXCStopPoint.model_construct(
            AtcoCode="ATCO001", StopAreas=["Area1"]
        )
        stop_point_2 = TXCStopPoint.model_construct(
            AtcoCode="ATCO002", StopAreas=["Area2", "Area3"]
        )
        m_get_by_atco_codes.return_value = ([stop_point_1, stop_point_2], [])

        atco_codes = ["ATCO001", "ATCO002"]
        stop_area_map = client.get_stop_area_map(atco_codes)

        assert stop_area_map == {
            "ATCO001": ["Area1"],
            "ATCO002": ["Area2", "Area3"],
        }

        m_get_by_atco_codes.assert_called_once_with(atco_codes)
