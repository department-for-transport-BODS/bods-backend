"""
DynamoDB cache tests
"""

from datetime import date, datetime
from unittest.mock import MagicMock, patch

from common_layer.database.models.model_fares import (
    FaresDataCatalogueMetadata,
    FaresMetadata,
)
from common_layer.dynamodb.client.fares_metadata import (
    DynamoDBFaresMetadata,
    FaresDynamoDBMetadataInput,
    FaresViolation,
)


@patch("time.time", MagicMock(return_value=1741892041))
def test_put_metadata(m_boto_client):
    """
    Test DynamoDB Put Metadata
    """

    m_boto_client.return_value.put_item.return_value = {}

    dynamodb = DynamoDBFaresMetadata()
    # pylint: disable=protected-access
    dynamodb._client.put_item = MagicMock()

    dynamodb.put_metadata(
        123,
        FaresDynamoDBMetadataInput(
            file_name="test.xml",
            data_catalogue=FaresDataCatalogueMetadata(
                atco_area=[123, 456],
                line_id=["1", "2"],
                line_name=["line1", "line2"],
                national_operator_code=["TEST"],
                product_name=["Product1"],
                product_type=["dayPass", "dayReturnTrip"],
                tariff_basis=["flat"],
                user_type=["adult"],
                valid_from=date(2025, 2, 27),
                valid_to=date(2026, 2, 27),
                xml_file_name="test.xml",
            ),
            metadata=FaresMetadata(
                num_of_fare_products=2,
                num_of_fare_zones=1,
                num_of_lines=4,
                num_of_pass_products=2,
                num_of_sales_offer_packages=2,
                num_of_trip_products=0,
                num_of_user_profiles=1,
                valid_from=datetime(2023, 1, 1, 23, 59, 59),
                valid_to=datetime(2025, 12, 31, 23, 59, 59),
            ),
            stop_ids=[1, 2, 3, 4, 5],
            netex_schema_version="1.1",
        ),
    )

    # pylint: disable=protected-access
    dynamodb._client.put_item.assert_called_once_with(
        Item={
            "DataCatalogue": {
                "M": {
                    "atco_area": {
                        "L": [
                            {
                                "N": "123",
                            },
                            {
                                "N": "456",
                            },
                        ],
                    },
                    "fares_metadata_id": {
                        "NULL": True,
                    },
                    "id": {
                        "NULL": True,
                    },
                    "line_id": {
                        "L": [
                            {
                                "S": "1",
                            },
                            {
                                "S": "2",
                            },
                        ],
                    },
                    "line_name": {
                        "L": [
                            {
                                "S": "line1",
                            },
                            {
                                "S": "line2",
                            },
                        ],
                    },
                    "national_operator_code": {
                        "L": [
                            {
                                "S": "TEST",
                            },
                        ],
                    },
                    "product_name": {
                        "L": [
                            {
                                "S": "Product1",
                            },
                        ],
                    },
                    "product_type": {
                        "L": [
                            {
                                "S": "dayPass",
                            },
                            {
                                "S": "dayReturnTrip",
                            },
                        ],
                    },
                    "tariff_basis": {
                        "L": [
                            {
                                "S": "flat",
                            },
                        ],
                    },
                    "user_type": {
                        "L": [
                            {
                                "S": "adult",
                            },
                        ],
                    },
                    "valid_from": {
                        "S": "2025-02-27",
                    },
                    "valid_to": {
                        "S": "2026-02-27",
                    },
                    "xml_file_name": {
                        "S": "test.xml",
                    },
                },
            },
            "Metadata": {
                "M": {
                    "datasetmetadata_ptr_id": {
                        "NULL": True,
                    },
                    "num_of_fare_products": {
                        "N": "2",
                    },
                    "num_of_fare_zones": {
                        "N": "1",
                    },
                    "num_of_lines": {
                        "N": "4",
                    },
                    "num_of_pass_products": {
                        "N": "2",
                    },
                    "num_of_sales_offer_packages": {
                        "N": "2",
                    },
                    "num_of_trip_products": {
                        "N": "0",
                    },
                    "num_of_user_profiles": {
                        "N": "1",
                    },
                    "valid_from": {
                        "S": "2023-01-01T23:59:59",
                    },
                    "valid_to": {
                        "S": "2025-12-31T23:59:59",
                    },
                },
            },
            "NetexSchemaVersion": {"S": "1.1"},
            "PK": {
                "N": "123",
            },
            "SK": {
                "S": "METADATA#test.xml",
            },
            "StopIds": {
                "L": [
                    {
                        "N": "1",
                    },
                    {
                        "N": "2",
                    },
                    {
                        "N": "3",
                    },
                    {
                        "N": "4",
                    },
                    {
                        "N": "5",
                    },
                ],
            },
            "ttl": {"N": "1741978441"},
        },
        ReturnValues="NONE",
        TableName="",
    )


@patch("time.time", MagicMock(return_value=1741892041))
def test_put_violations(m_boto_client):
    """
    Test DynamoDB Put Metadata
    """

    m_boto_client.return_value.put_item.return_value = {}

    dynamodb = DynamoDBFaresMetadata()
    # pylint: disable=protected-access
    dynamodb._client.put_item = MagicMock()

    dynamodb.put_violations(
        123,
        "test.xml",
        [
            FaresViolation(category="test", line=1, observation="test"),
        ],
    )

    # pylint: disable=protected-access
    dynamodb._client.put_item.assert_called_once_with(
        Item={
            "FileName": {
                "S": "test.xml",
            },
            "PK": {
                "N": "123",
            },
            "SK": {
                "S": "VIOLATION#test.xml",
            },
            "Violations": {
                "L": [
                    {
                        "M": {
                            "category": {
                                "S": "test",
                            },
                            "line": {
                                "N": "1",
                            },
                            "observation": {
                                "S": "test",
                            },
                        },
                    },
                ],
            },
            "ttl": {"N": "1741978441"},
        },
        ReturnValues="NONE",
        TableName="",
    )
