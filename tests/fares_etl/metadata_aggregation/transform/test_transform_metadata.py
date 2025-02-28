import os
from datetime import date
from pathlib import Path

import pytest
from common_layer.database.models.model_fares import FaresDataCatalogueMetadata
from common_layer.xml.netex.parser.netex_publication_delivery import parse_netex

from fares_etl.etl.app.transform.data_catalogue import create_data_catalogue
from fares_etl.metadata_aggregation.app.transform.transform_metadata import (
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
