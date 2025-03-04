from datetime import datetime

import pytest
from common_layer.database.models.model_fares import FaresMetadata

from fares_etl.metadata_aggregation.app.transform.transform_metadata import (
    aggregate_metadata,
    get_min_schema_version,
)


@pytest.mark.parametrize(
    "schema_versions,expected_min_schema_version",
    [
        pytest.param(["1.10", "1.11", "1.09"], "1.09"),
        pytest.param(["1.10", "1.09c", "1.11a"], "1.09c"),
    ],
)
def test_get_min_schema_version(
    schema_versions: list[str],
    expected_min_schema_version: str,
):
    min_schema_version = get_min_schema_version(schema_versions)

    assert min_schema_version == expected_min_schema_version


@pytest.mark.parametrize(
    "metadata,expected_aggregated_metadata",
    [
        pytest.param(
            [
                FaresMetadata(
                    num_of_fare_products=2,
                    num_of_fare_zones=1,
                    num_of_lines=0,
                    num_of_pass_products=3,
                    num_of_sales_offer_packages=8,
                    num_of_trip_products=1,
                    num_of_user_profiles=0,
                    valid_from=datetime(2025, 1, 1, 23, 30, 10),
                    valid_to=datetime(2026, 12, 12, 12, 10, 0),
                )
            ],
            FaresMetadata(
                num_of_fare_products=2,
                num_of_fare_zones=1,
                num_of_lines=0,
                num_of_pass_products=3,
                num_of_sales_offer_packages=8,
                num_of_trip_products=1,
                num_of_user_profiles=0,
                valid_from=datetime(2025, 1, 1, 23, 30, 10),
                valid_to=datetime(2026, 12, 12, 12, 10, 0),
            ),
        ),
        pytest.param(
            [
                FaresMetadata(
                    num_of_fare_products=2,
                    num_of_fare_zones=1,
                    num_of_lines=0,
                    num_of_pass_products=3,
                    num_of_sales_offer_packages=8,
                    num_of_trip_products=1,
                    num_of_user_profiles=0,
                    valid_from=datetime(2025, 1, 1, 23, 30, 10),
                    valid_to=datetime(2026, 12, 12, 12, 10, 0),
                ),
                FaresMetadata(
                    num_of_fare_products=4,
                    num_of_fare_zones=6,
                    num_of_lines=1,
                    num_of_pass_products=8,
                    num_of_sales_offer_packages=2,
                    num_of_trip_products=4,
                    num_of_user_profiles=2,
                    valid_from=datetime(2024, 11, 1, 23, 30, 10),
                    valid_to=datetime(2025, 12, 12, 12, 10, 0),
                ),
            ],
            FaresMetadata(
                num_of_fare_products=6,
                num_of_fare_zones=7,
                num_of_lines=1,
                num_of_pass_products=11,
                num_of_sales_offer_packages=10,
                num_of_trip_products=5,
                num_of_user_profiles=2,
                valid_from=datetime(2024, 11, 1, 23, 30, 10),
                valid_to=datetime(2026, 12, 12, 12, 10, 0),
            ),
        ),
    ],
)
def test_aggregate_metadata(
    metadata: list[FaresMetadata],
    expected_aggregated_metadata: FaresMetadata,
):
    aggregated_metadata = aggregate_metadata(metadata)

    assert aggregated_metadata == expected_aggregated_metadata
