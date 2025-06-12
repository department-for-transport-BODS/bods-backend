from unittest.mock import MagicMock, patch

from geoalchemy2.shape import from_shape  # type: ignore
from shapely.geometry import LineString

from timetables_etl.etl.app.api.geometry import OSRMGeometryAPI, OSRMGeometryAPISettings


@patch("timetables_etl.etl.app.api.geometry.requests.get")
def test_osrm_geometry_api_get_geometry_and_distance_success(m_get: MagicMock) -> None:
    coords = [(0.0, 0.0), (0.02, 0.01), (0.03, 0.02)]
    m_get.return_value.json.return_value = {
        "code": "Ok",
        "routes": [
            {
                "distance": 1234.5,
                "geometry": {
                    "type": "LineString",
                    "coordinates": coords,
                },
            }
        ],
    }

    base_url = "test-osrm-router.com"
    expected_url = f"{base_url}/route/v1/driving/0.0,0.0;0.02,0.01;0.03,0.02"
    expected_params = {"overview": "full", "geometries": "geojson"}

    config = OSRMGeometryAPISettings(OSRM_BASE_URL=base_url)
    api = OSRMGeometryAPI(config)
    geom, distance = api.get_geometry_and_distance(coords)

    m_get.assert_called_once_with(expected_url, params=expected_params, timeout=60)
    assert distance == 1234, "distance returned as int"
    assert geom == from_shape(LineString(coords), srid=4326)


@patch("timetables_etl.etl.app.api.geometry.requests.get")
def test_osrm_geometry_api_invalid_status_code(m_get: MagicMock) -> None:
    coords = [(0.0, 0.0), (0.01, 0.01)]
    m_get.return_value.json.return_value = {"code": "InvalidQuery", "routes": []}

    api = OSRMGeometryAPI()
    geom, distance = api.get_geometry_and_distance(coords)

    assert geom is None
    assert distance is None


@patch("timetables_etl.etl.app.api.geometry.requests.get")
def test_osrm_geometry_api_returns_none_on_empty_routes(m_get: MagicMock) -> None:
    coords = [(0.0, 0.0), (0.01, 0.01)]
    m_get.return_value.json.return_value = {"code": "Ok", "routes": []}

    api = OSRMGeometryAPI()
    geom, distance = api.get_geometry_and_distance(coords)

    assert geom is None
    assert distance is None
