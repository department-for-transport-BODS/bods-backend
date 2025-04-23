from datetime import date, datetime

import pytest
from common_layer.database.models import FaresDataCatalogueMetadata, FaresMetadata

from fares_etl.metadata_aggregation.app.transform.transform_metadata import (
    aggregate_metadata,
    get_min_schema_version,
    sum_metadata_fields,
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
    "metadata,data_catalogues,expected_aggregated_metadata",
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
            [],
            FaresMetadata(
                num_of_fare_products=2,
                num_of_fare_zones=1,
                num_of_lines=0,
                num_of_pass_products=0,
                num_of_sales_offer_packages=8,
                num_of_trip_products=0,
                num_of_user_profiles=0,
                valid_from=datetime(2025, 1, 1, 23, 30, 10),
                valid_to=datetime(2026, 12, 12, 12, 10, 0),
            ),
            id="Single metadata item with empty data catalogues",
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
            [],  # Empty data_catalogues
            FaresMetadata(
                num_of_fare_products=6,
                num_of_fare_zones=7,
                num_of_lines=1,
                num_of_pass_products=0,
                num_of_sales_offer_packages=10,
                num_of_trip_products=0,
                num_of_user_profiles=0,
                valid_from=datetime(2024, 11, 1, 23, 30, 10),
                valid_to=datetime(2026, 12, 12, 12, 10, 0),
            ),
            id="Multiple metadata items with empty data catalogues",
        ),
    ],
)
def test_aggregate_metadata(
    metadata: list[FaresMetadata],
    data_catalogues: list[FaresDataCatalogueMetadata],
    expected_aggregated_metadata: FaresMetadata,
) -> None:
    """
    Test generating the aggregate metadata
    """
    aggregated_metadata = aggregate_metadata(metadata, data_catalogues)

    assert aggregated_metadata == expected_aggregated_metadata


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
                num_of_pass_products=0,
                num_of_sales_offer_packages=8,
                num_of_trip_products=0,
                num_of_user_profiles=0,
                valid_from=datetime(2025, 1, 1, 23, 30, 10),
                valid_to=datetime(2026, 12, 12, 12, 10, 0),
            ),
            id="Sum single metadata item fields",
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
                num_of_pass_products=0,
                num_of_sales_offer_packages=10,
                num_of_trip_products=0,
                num_of_user_profiles=0,
                valid_from=datetime(2024, 11, 1, 23, 30, 10),
                valid_to=datetime(2026, 12, 12, 12, 10, 0),
            ),
            id="Sum multiple metadata item fields with date range calculation",
        ),
    ],
)
def test_sum_metadata_fields(
    metadata: list[FaresMetadata],
    expected_aggregated_metadata: FaresMetadata,
) -> None:
    """
    Test summing metadata fields
    """
    aggregated_metadata = sum_metadata_fields(metadata)

    assert aggregated_metadata == expected_aggregated_metadata


@pytest.mark.parametrize(
    "metadata,data_catalogues,expected_aggregated_metadata",
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
            [
                FaresDataCatalogueMetadata(
                    xml_file_name="file1.xml",
                    valid_from=date(2025, 1, 1),
                    valid_to=date(2026, 12, 12),
                    national_operator_code=["NOC1"],
                    line_id=["LINE1"],
                    line_name=["Line 1"],
                    atco_area=[1],
                    tariff_basis=["zone"],
                    product_type=["dayPass", "singleTrip"],
                    product_name=["Day Pass", "Single Trip"],
                    user_type=["adult", "child"],
                ),
                FaresDataCatalogueMetadata(
                    xml_file_name="file2.xml",
                    valid_from=date(2024, 11, 1),
                    valid_to=date(2025, 12, 12),
                    national_operator_code=["NOC2"],
                    line_id=["LINE2"],
                    line_name=["Line 2"],
                    atco_area=[2],
                    tariff_basis=["pointToPoint"],
                    product_type=["periodPass", "dayReturnTrip"],
                    product_name=["Period Pass", "Day Return Trip"],
                    user_type=["adult", "senior"],
                ),
            ],
            FaresMetadata(
                num_of_fare_products=2,
                num_of_fare_zones=1,
                num_of_lines=0,
                num_of_pass_products=2,  # dayPass, periodPass
                num_of_sales_offer_packages=8,
                num_of_trip_products=2,  # singleTrip, dayReturnTrip
                num_of_user_profiles=3,  # adult, child, senior
                valid_from=datetime(2025, 1, 1, 23, 30, 10),
                valid_to=datetime(2026, 12, 12, 12, 10, 0),
            ),
            id="Calculate unique counts from data catalogues",
        ),
    ],
)
def test_aggregate_metadata_with_data_catalogues(
    metadata: list[FaresMetadata],
    data_catalogues: list[FaresDataCatalogueMetadata],
    expected_aggregated_metadata: FaresMetadata,
) -> None:
    """
    Test generating the aggregate metadata with data catalogues
    """
    aggregated_metadata = aggregate_metadata(metadata, data_catalogues)

    assert aggregated_metadata == expected_aggregated_metadata
