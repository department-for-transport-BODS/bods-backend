"""
Test Parsing a FareZone
"""

import pytest
from common_layer.xml.netex.models import (
    MultilingualString,
    PointRefs,
    ScheduledStopPointReference,
)
from common_layer.xml.netex.models.fare_frame.netex_fare_zone import FareZone
from common_layer.xml.netex.parser import parse_fare_zone

from tests.xml.conftest import assert_model_equal
from tests.xml.netex.conftest import parse_xml_str_as_netex


@pytest.mark.parametrize(
    "xml_str,expected",
    [
        pytest.param(
            """
            <FareZone id="fs@1501" version="1.0">
              <Name>Ilkeston</Name>
              <members>
                <ScheduledStopPointRef ref="atco:1000DINR5456" version="any">Brooke Street</ScheduledStopPointRef>
                <ScheduledStopPointRef ref="atco:1000DINR5491" version="any">Dale Street</ScheduledStopPointRef>
                <ScheduledStopPointRef ref="atco:1000DINR5451" version="any">Manners Street</ScheduledStopPointRef>
                <ScheduledStopPointRef ref="atco:1000DISS5490" version="any">South Street</ScheduledStopPointRef>
                <ScheduledStopPointRef ref="atco:1000DIWR5593" version="any">Ilkeston Market Place</ScheduledStopPointRef>
                <ScheduledStopPointRef ref="atco:1000DINR5493" version="any">Kensington School</ScheduledStopPointRef>
              </members>
            </FareZone>
            """,
            FareZone(
                id="fs@1501",
                version="1.0",
                Name=MultilingualString(value="Ilkeston"),
                members=PointRefs(
                    ScheduledStopPointRef=[
                        ScheduledStopPointReference(
                            ref="atco:1000DINR5456",
                            version="any",
                            Name="Brooke Street",
                            atco_code="1000DINR5456",
                        ),
                        ScheduledStopPointReference(
                            ref="atco:1000DINR5491",
                            version="any",
                            Name="Dale Street",
                            atco_code="1000DINR5491",
                        ),
                        ScheduledStopPointReference(
                            ref="atco:1000DINR5451",
                            version="any",
                            Name="Manners Street",
                            atco_code="1000DINR5451",
                        ),
                        ScheduledStopPointReference(
                            ref="atco:1000DISS5490",
                            version="any",
                            Name="South Street",
                            atco_code="1000DISS5490",
                        ),
                        ScheduledStopPointReference(
                            ref="atco:1000DIWR5593",
                            version="any",
                            Name="Ilkeston Market Place",
                            atco_code="1000DIWR5593",
                        ),
                        ScheduledStopPointReference(
                            ref="atco:1000DINR5493",
                            version="any",
                            Name="Kensington School",
                            atco_code="1000DINR5493",
                        ),
                    ]
                ),
            ),
            id="Complete fare zone with multiple stops",
        ),
        pytest.param(
            """
            <FareZone id="fs@1502" version="1.0">
              <Name lang="en">City Centre</Name>
              <members>
                <ScheduledStopPointRef ref="atco:1000DINR5456" version="1.0">Central Station</ScheduledStopPointRef>
              </members>
            </FareZone>
            """,
            FareZone(
                id="fs@1502",
                version="1.0",
                Name=MultilingualString(value="City Centre", lang="en"),
                members=PointRefs(
                    ScheduledStopPointRef=[
                        ScheduledStopPointReference(
                            ref="atco:1000DINR5456",
                            version="1.0",
                            Name="Central Station",
                            atco_code="1000DINR5456",
                        )
                    ]
                ),
            ),
            id="Fare zone with language tag",
        ),
        pytest.param(
            """
            <FareZone id="fs@1503" version="1.0">
              <Name>Empty Zone</Name>
              <members/>
            </FareZone>
            """,
            FareZone(
                id="fs@1503",
                version="1.0",
                Name=MultilingualString(value="Empty Zone"),
                members=PointRefs(),
            ),
            id="Fare zone with no members",
        ),
    ],
)
def test_parse_fare_zone(xml_str: str, expected: FareZone) -> None:
    """Test parsing of fare zones with various inputs."""
    elem = parse_xml_str_as_netex(xml_str)
    result = parse_fare_zone(elem)
    assert result is not None
    assert_model_equal(result, expected)


@pytest.mark.parametrize(
    "xml_str,expected",
    [
        pytest.param(
            """
            <FareZone version="1.0">
              <Name>Missing ID</Name>
              <members/>
            </FareZone>
            """,
            None,
            id="Missing required id",
        ),
        pytest.param(
            """
            <FareZone id="fs@1504">
              <Name>Missing Version</Name>
              <members/>
            </FareZone>
            """,
            None,
            id="Missing required version",
        ),
        pytest.param(
            """
            <FareZone id="fs@1505" version="1.0">
              <members/>
            </FareZone>
            """,
            None,
            id="Missing required name",
        ),
        pytest.param(
            """
            <FareZone id="fs@1506" version="1.0">
              <Name></Name>
              <members/>
            </FareZone>
            """,
            None,
            id="Empty name",
        ),
    ],
)
def test_parse_fare_zone_validation_errors(xml_str: str, expected: None) -> None:
    """Test parsing of fare zones with invalid or missing required fields."""
    elem = parse_xml_str_as_netex(xml_str)
    result = parse_fare_zone(elem)
    assert result == expected
