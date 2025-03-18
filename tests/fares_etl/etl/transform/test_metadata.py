import os
from datetime import datetime, timezone
from pathlib import Path
from unittest.mock import Mock, patch

import pytest
from common_layer.database.models import FaresMetadata
from common_layer.xml.netex.parser.netex_publication_delivery import parse_netex

from fares_etl.etl.app.transform.metadata import create_metadata, get_stop_ids


@pytest.mark.parametrize(
    "netex_file,expected_metadata",
    [
        pytest.param(
            "netex1.xml",
            FaresMetadata(
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

    data_catalogue = create_metadata(netex)

    assert data_catalogue == expected_metadata


@pytest.mark.parametrize(
    "netex_file,expected_atco_ids,expected_naptan_ids",
    [
        pytest.param(
            "netex1.xml",
            [
                "5400AWF80423",
                "5400AWF80424",
                "5400AWF80425",
                "5400AWF80888",
                "5400AWF80904",
                "5400AWF80905",
                "5400AWF80906",
                "5400AWF80908",
                "5400AWF80909",
                "5400AWF80911",
                "5400AWF80914",
                "5400AWF80915",
                "5400AWF80917",
                "5400AWF80918",
                "5400AWF80928",
                "5400AWF80929",
                "5400AWF80930",
                "5400AWF80936",
                "5400AWF80937",
                "5400AWF80942",
                "5400AWF80949",
                "5400AWF80954",
                "5400AWP26215",
                "5400AWP26216",
                "5400AWP26394",
                "5400AWP26395",
                "5400AWP26397",
                "5400AWP26398",
                "5400AWP26399",
                "5400AWP26400",
                "5400AWP26579",
                "5400GYX17112",
                "5400GYX17113",
                "5400GYX17360",
                "5400GYX17373",
                "5400GYX17374",
                "5400WDB23730",
                "5400WDB23734",
                "5400WDB23735",
                "5400WDB48283",
                "5400WDB48325",
                "5400WDB48341",
                "5400WDB48359",
            ],
            [
                "gwnapjg",
            ],
        ),
        pytest.param(
            "netex2.xml",
            [
                "25001077",
                "250010849",
                "250010856",
                "250012035",
                "25001218",
                "250012984",
                "250012987",
                "250012993",
                "250012995",
                "250013133",
                "250014403",
                "250015045",
                "2500151",
                "250015209",
                "250015714",
                "250020180",
                "250020205",
                "250020331",
                "2500404",
                "2500428",
                "2500566",
                "2500570",
                "2500737",
                "2500DCL3091",
                "2500DCL3093",
                "2500DCL3095",
                "2500DCL3097",
                "2500DCL3099",
                "2500DCL3121",
                "2500DCL3127",
                "2500DCL320",
                "2500DCL460",
                "2500DCL474",
                "2500DCL555",
                "2500DCL556",
                "2500IMG1302",
                "2500IMG1304",
                "2500IMG1306",
                "2500IMG1318",
                "2500IMG1494",
                "2500IMG1495",
                "2500IMG1508",
                "2500IMG2087",
                "2500IMG2089",
                "2500IMG2090",
                "2500IMG2093",
                "2500IMG2301",
                "2500IMG2303",
                "2500IMG2366",
                "2500IMG2367",
                "2500IMG2371",
                "2500IMG2372",
                "2500IMG2546",
                "2500IMG2547",
                "2500IMG2548",
                "2500IMG2551",
                "2500IMG2553",
                "2500IMG2555",
                "2500IMG2557",
                "2500IMG2560",
                "2500IMG2568",
                "2500IMG2570",
                "2500IMG2572",
                "2500IMG2575",
                "2500IMG2576",
                "2500IMG2577",
                "2500IMG2578",
                "2500IMG2621",
                "2500IMG2623",
                "2500JB78",
                "2500LA00205",
                "2500LA00207",
                "2500LA00208",
                "2500LAA00227",
                "2500LAA00283",
                "2500LAA00286",
                "2500LAA16751",
                "2580AUD0010",
                "2580BBI0004",
                "2580BBS0009",
                "2580BLA0017",
                "2580BLA0038",
                "2580BLA0066",
                "2580BLA0077",
                "2580BLA0094",
                "2580BLA0121",
                "2580BLA0137",
                "2580BLA0139",
                "2580CHT0001",
                "2580CHT0003",
                "2580CHT0007",
                "2580CHT0010",
                "2580CHT0013",
                "2580FCW0002",
                "2580FCW0009",
                "2580FCW0011",
                "2580HHO0002",
                "2580WHB0001",
                "2580WHB0003",
                "2580WIT0001",
                "2580WIT0003",
                "2580WIT0008",
                "2580WSF0018",
                "2580WSF0021",
            ],
            [],
        ),
    ],
)
@patch("common_layer.database.repos.repo_naptan.NaptanStopPointRepo")
def test_extract_stop_ids(
    naptan_stop_point_repo: Mock,
    netex_file: str,
    expected_atco_ids: list[str],
    expected_naptan_ids: list[str],
):
    netex = parse_netex(
        Path(os.path.dirname(__file__) + "/../../test_data/" + netex_file)
    )

    naptan_stop_point_repo.get_by_atco_codes.return_value = ([], [])
    naptan_stop_point_repo.get_by_naptan_codes.return_value = ([], [])

    get_stop_ids(netex, naptan_stop_point_repo)

    naptan_stop_point_repo.get_by_atco_codes.assert_called_with(expected_atco_ids)
    naptan_stop_point_repo.get_by_naptan_codes.assert_called_with(expected_naptan_ids)
