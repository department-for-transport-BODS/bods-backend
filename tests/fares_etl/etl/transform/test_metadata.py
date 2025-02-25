import os
from datetime import datetime, timezone
from pathlib import Path

import pytest
from common_layer.database.models.model_fares import FaresMetadata
from common_layer.xml.netex.parser.netex_publication_delivery import parse_netex

from fares_etl.etl.app.transform.metadata import create_metadata


@pytest.mark.parametrize(
    "netex_file,expected_metadata",
    [
        pytest.param(
            "netex1.xml",
            FaresMetadata(
                datasetmetadata_ptr_id=123,
                num_of_fare_products=1,
                num_of_fare_zones=28,
                num_of_lines=1,
                num_of_pass_products=0,
                num_of_sales_offer_packages=1,
                num_of_trip_products=1,
                num_of_user_profiles=1,
                valid_from=datetime(2025, 1, 14, 0, 0),
                valid_to=datetime(2125, 1, 14, 0, 0),
            ),
        ),
        pytest.param(
            "netex2.xml",
            FaresMetadata(
                datasetmetadata_ptr_id=123,
                num_of_fare_products=1,
                num_of_fare_zones=8,
                num_of_lines=1,
                num_of_pass_products=0,
                num_of_sales_offer_packages=2,
                num_of_trip_products=1,
                num_of_user_profiles=1,
                valid_from=datetime(2025, 5, 1, 0, 0, tzinfo=timezone.utc),
                valid_to=datetime(2029, 5, 1, 23, 59, 59, tzinfo=timezone.utc),
            ),
        ),
    ],
)
def test_extract_metadata(
    netex_file: str,
    expected_metadata: FaresMetadata,
):
    netex = parse_netex(
        Path(os.path.dirname(__file__) + "/../../test_data/" + netex_file)
    )

    data_catalogue = create_metadata(netex, 123)

    assert data_catalogue == expected_metadata
