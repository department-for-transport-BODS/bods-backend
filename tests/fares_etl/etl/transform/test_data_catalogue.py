import os
from datetime import date
from pathlib import Path

import pytest
from common_layer.database.models.model_fares import FaresDataCatalogueMetadata
from common_layer.xml.netex.parser.netex_publication_delivery import parse_netex

from fares_etl.etl.app.transform.data_catalogue import create_data_catalogue


@pytest.mark.parametrize(
    "netex_file,expected_data_catalogue",
    [
        pytest.param(
            "netex1.xml",
            FaresDataCatalogueMetadata(
                xml_file_name="netex1.xml",
                valid_from=date(2024, 6, 11),
                valid_to=None,
                national_operator_code=["ACYM"],
                line_id=["ACYM:PG0007245:491:G8"],
                line_name=["G8"],
                atco_area=[540],
                tariff_basis=["pointToPoint"],
                product_type=["dayReturnTrip"],
                product_name=["AD RTN"],
                user_type=["adult"],
            ),
        ),
        pytest.param(
            "netex2.xml",
            FaresDataCatalogueMetadata(
                xml_file_name="netex2.xml",
                valid_from=date(2025, 5, 1),
                valid_to=date(2029, 5, 1),
                national_operator_code=["LNUD"],
                line_id=["LNUD:PC0005248:1:152"],
                line_name=["152"],
                atco_area=[250, 258],
                tariff_basis=["zoneToZone"],
                product_type=["singleTrip"],
                product_name=["Adult Standard single"],
                user_type=["adult"],
            ),
        ),
    ],
)
def test_extract_data_catalogue(
    netex_file: str,
    expected_data_catalogue: FaresDataCatalogueMetadata,
):
    netex = parse_netex(
        Path(os.path.dirname(__file__) + "/../../test_data/" + netex_file)
    )

    data_catalogue = create_data_catalogue(netex, netex_file)

    assert data_catalogue == expected_data_catalogue
