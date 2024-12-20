"""
TXC Stoppoint XML to Pydantic Test
"""

import pytest
from common_layer.txc.models import (
    AnnotatedStopPointRef,
    BearingStructure,
    BusStopStructure,
    DescriptorStructure,
    LocationStructure,
    MarkedPointStructure,
    OnStreetStructure,
    PlaceStructure,
    StopClassificationStructure,
    TXCStopPoint,
)
from common_layer.txc.parser.stop_points import (
    parse_bearing_structure,
    parse_bus_stop_structure,
    parse_descriptor_structure,
    parse_location_structure,
    parse_marked_point_structure,
    parse_on_street_structure,
    parse_place_structure,
    parse_stop_classification_structure,
    parse_stop_points,
    parse_txc_stop_point,
)
from lxml.etree import fromstring


@pytest.mark.parametrize(
    "xml_input, expected_output",
    [
        pytest.param(
            """
            <TransXChange>
            <StopPoints>
                <AnnotatedStopPointRef>
                    <StopPointRef>490014051VC</StopPointRef>
                    <CommonName>Victoria Coach Station</CommonName>
                    <LocalityName>Belgravia</LocalityName>
                    <LocalityQualifier>Victoria</LocalityQualifier>
                </AnnotatedStopPointRef>
            </StopPoints>
            </TransXChange>
            """,
            [
                AnnotatedStopPointRef(
                    StopPointRef="490014051VC",
                    CommonName="Victoria Coach Station",
                    Indicator=None,
                    LocalityName="Belgravia",
                    LocalityQualifier="Victoria",
                )
            ],
            id="Single Stop With Full Location Details",
        ),
        pytest.param(
            """
            <TransXChange>
            <StopPoints>
                <AnnotatedStopPointRef>
                    <StopPointRef>490014051VC</StopPointRef>
                    <CommonName>Victoria Coach Station</CommonName>
                </AnnotatedStopPointRef>
                <AnnotatedStopPointRef>
                    <StopPointRef>490016736W</StopPointRef>
                    <CommonName>London Victoria Coach Station Arrivals</CommonName>
                    <Indicator>Arrivals</Indicator>
                </AnnotatedStopPointRef>
            </StopPoints>
            </TransXChange>
            """,
            [
                AnnotatedStopPointRef(
                    StopPointRef="490014051VC",
                    CommonName="Victoria Coach Station",
                    Indicator=None,
                    LocalityName=None,
                    LocalityQualifier=None,
                ),
                AnnotatedStopPointRef(
                    StopPointRef="490016736W",
                    CommonName="London Victoria Coach Station Arrivals",
                    Indicator="Arrivals",
                    LocalityName=None,
                    LocalityQualifier=None,
                ),
            ],
            id="Multiple Stops With Different Optional Fields",
        ),
        pytest.param(
            """
            <StopPoints></StopPoints>
            """,
            [],
            id="Empty Stop Points",
        ),
        pytest.param(
            """
            <InvalidTopLevel></InvalidTopLevel>
            """,
            [],
            id="Invalid Top Level Element",
        ),
    ],
)
def test_parse_stop_points(
    xml_input: str, expected_output: list[AnnotatedStopPointRef]
):
    """
    Test the generation of stop point pydantic models.

    """
    xml_data = fromstring(xml_input)
    stoppoints = parse_stop_points(xml_data)
    assert stoppoints == expected_output


@pytest.mark.parametrize(
    "bus_xml_str, expected_result",
    [
        # Valid BusStopStructure
        pytest.param(
            """
            <Bus>
                <BusStopType>MKD</BusStopType>
                <TimingStatus>principalTimingPoint</TimingStatus>
                <MarkedPoint>
                    <Bearing>
                        <CompassPoint>N</CompassPoint>
                    </Bearing>
                </MarkedPoint>
            </Bus>
            """,
            BusStopStructure(
                BusStopType="MKD",
                TimingStatus="principalTimingPoint",
                MarkedPoint=MarkedPointStructure(
                    Bearing=BearingStructure(CompassPoint="N")
                ),
            ),
            id="Correctly Parse",
        ),
        pytest.param(
            """
            <Bus>
                <TimingStatus>principalTimingPoint</TimingStatus>
                <MarkedPoint>
                    <Bearing>
                        <CompassPoint>N</CompassPoint>
                    </Bearing>
                </MarkedPoint>
            </Bus>
            """,
            None,
            id="Missing BusStopType",
        ),
        pytest.param(
            """
            <Bus>
                <BusStopType>MKD</BusStopType>
                <TimingStatus>InvalidStatus</TimingStatus>
                <MarkedPoint>
                    <Bearing>
                        <CompassPoint>N</CompassPoint>
                    </Bearing>
                </MarkedPoint>
            </Bus>
            """,
            None,
            id="Missing TimingStatus",
        ),
    ],
)
def test_parse_bus_stop_structure(bus_xml_str, expected_result):
    """
    Parsing of Bus Stop Structure
    """
    bus_xml = fromstring(bus_xml_str)
    assert parse_bus_stop_structure(bus_xml) == expected_result


@pytest.mark.parametrize(
    "bearing_xml_str, expected_result",
    [
        pytest.param(
            "<Bearing><CompassPoint>N</CompassPoint></Bearing>",
            BearingStructure(CompassPoint="N"),
            id="Valid BearingStructure",
        ),
        pytest.param(
            "<Bearing></Bearing>",
            None,
            id="Missing CompassPoint",
        ),
        pytest.param(
            "<Bearing><CompassPoint>InvalidPoint</CompassPoint></Bearing>",
            None,
            id="nvalid CompassPoint",
        ),
    ],
)
def test_parse_bearing_structure(bearing_xml_str, expected_result):
    """
    Parsing of Bus Stop Structure
    """
    bearing_xml = fromstring(bearing_xml_str)
    assert parse_bearing_structure(bearing_xml) == expected_result


@pytest.mark.parametrize(
    "marked_point_xml_str, expected_result",
    [
        pytest.param(
            """
            <MarkedPoint>
                <Bearing>
                    <CompassPoint>N</CompassPoint>
                </Bearing>
            </MarkedPoint>
            """,
            MarkedPointStructure(Bearing=BearingStructure(CompassPoint="N")),
            id="Valid MarkedPointStructure",
        ),
        pytest.param(
            "<MarkedPoint></MarkedPoint>",
            None,
            id="Missing Bearing",
        ),
        pytest.param(
            """
            <MarkedPoint>
                <Bearing>
                    <CompassPoint>InvalidPoint</CompassPoint>
                </Bearing>
            </MarkedPoint>
            """,
            None,
            id="Invalid Bearing",
        ),
    ],
)
def test_parse_marked_point_structure(marked_point_xml_str, expected_result):
    """
    Test Parsing a Marked Point Structure
    """
    marked_point_xml = fromstring(marked_point_xml_str)
    assert parse_marked_point_structure(marked_point_xml) == expected_result


@pytest.mark.parametrize(
    "on_street_xml_str, expected_result",
    [
        pytest.param(
            """
            <OnStreet>
                <Bus>
                    <BusStopType>MKD</BusStopType>
                    <TimingStatus>principalTimingPoint</TimingStatus>
                    <MarkedPoint>
                        <Bearing>
                            <CompassPoint>N</CompassPoint>
                        </Bearing>
                    </MarkedPoint>
                </Bus>
            </OnStreet>
            """,
            OnStreetStructure(
                Bus=BusStopStructure(
                    BusStopType="MKD",
                    TimingStatus="principalTimingPoint",
                    MarkedPoint=MarkedPointStructure(
                        Bearing=BearingStructure(CompassPoint="N")
                    ),
                )
            ),
            id="Valid OnStreet Structure",
        ),
        pytest.param(
            "<OnStreet></OnStreet>",
            None,
            id="Missing Bus XML",
        ),
        pytest.param(
            """
            <OnStreet>
                <Bus>
                    <BusStopType>InvalidType</BusStopType>
                    <TimingStatus>principalTimingPoint</TimingStatus>
                    <MarkedPoint>
                        <Bearing>
                            <CompassPoint>N</CompassPoint>
                        </Bearing>
                    </MarkedPoint>
                </Bus>
            </OnStreet>
            """,
            None,
            id="Invalid Bus Stop Structure",
        ),
    ],
)
def test_parse_on_street_structure(on_street_xml_str, expected_result):
    """
    Test Parsing On Street Structure
    """
    on_street_xml = fromstring(on_street_xml_str)
    assert parse_on_street_structure(on_street_xml) == expected_result


@pytest.mark.parametrize(
    "stop_classification_xml_str, expected_result",
    [
        pytest.param(
            """
            <StopClassification>
                <StopType>busCoachTrolleyOnStreetPoint</StopType>
                <OnStreet>
                    <Bus>
                        <BusStopType>MKD</BusStopType>
                        <TimingStatus>principalTimingPoint</TimingStatus>
                        <MarkedPoint>
                            <Bearing>
                                <CompassPoint>N</CompassPoint>
                            </Bearing>
                        </MarkedPoint>
                    </Bus>
                </OnStreet>
            </StopClassification>
            """,
            StopClassificationStructure(
                StopType="busCoachTrolleyOnStreetPoint",
                OnStreet=OnStreetStructure(
                    Bus=BusStopStructure(
                        BusStopType="MKD",
                        TimingStatus="principalTimingPoint",
                        MarkedPoint=MarkedPointStructure(
                            Bearing=BearingStructure(CompassPoint="N")
                        ),
                    )
                ),
            ),
            id="Valid Stop Classification Structure",
        ),
        pytest.param(
            """
            <StopClassification>
                <StopType>busCoachTrolleyOnStreetPoint</StopType>
            </StopClassification>
            """,
            None,
            id="Missing OnStreet XML",
        ),
        pytest.param(
            """
            <StopClassification>
                <OnStreet>
                    <Bus>
                        <BusStopType>MKD</BusStopType>
                        <TimingStatus>PTP</TimingStatus>
                        <MarkedPoint>
                            <Bearing>
                                <CompassPoint>N</CompassPoint>
                            </Bearing>
                        </MarkedPoint>
                    </Bus>
                </OnStreet>
            </StopClassification>
            """,
            None,
            id="Missing Stop Type",
        ),
    ],
)
def test_parse_stop_classification_structure(
    stop_classification_xml_str, expected_result
):
    """
    Stop Classification Parsing test
    """
    stop_classification_xml = fromstring(stop_classification_xml_str)
    assert (
        parse_stop_classification_structure(stop_classification_xml) == expected_result
    )


@pytest.mark.parametrize(
    "location_xml_str, expected_result",
    [
        pytest.param(
            """
            <Location>
                <Translation>
                    <Longitude>-6.253318</Longitude>
                    <Latitude>53.347398</Latitude>
                    <Easting>117018</Easting>
                    <Northing>391827</Northing>
                </Translation>
            </Location>
            """,
            LocationStructure(
                Longitude="-6.253318",
                Latitude="53.347398",
                Easting="117018",
                Northing="391827",
            ),
            id="Valid Location Structure",
        ),
        pytest.param(
            """
            <Location>
                <Translation>
                    <Longitude>-6.253318</Longitude>
                    <Latitude>53.347398</Latitude>
                </Translation>
            </Location>
            """,
            LocationStructure(
                Longitude="-6.253318",
                Latitude="53.347398",
                Easting=None,
                Northing=None,
            ),
            id="Missing Easting and Northing",
        ),
    ],
)
def test_parse_location_structure(location_xml_str, expected_result):
    """
    Testing location structure parsing
    """
    location_xml = fromstring(location_xml_str)
    assert parse_location_structure(location_xml) == expected_result


@pytest.mark.parametrize(
    "descriptor_xml_str, expected_result",
    [
        pytest.param(
            """
            <Descriptor>
                <CommonName>Dublin (George's Quay) Stop 135141</CommonName>
                <ShortCommonName>Dublin Stop</ShortCommonName>
                <Landmark>George's Quay</Landmark>
                <Street>Tara St</Street>
                <Crossing>George's Quay</Crossing>
                <Indicator>Stop 135141</Indicator>
            </Descriptor>
            """,
            DescriptorStructure(
                CommonName="Dublin (George's Quay) Stop 135141",
                ShortCommonName="Dublin Stop",
                Landmark="George's Quay",
                Street="Tara St",
                Crossing="George's Quay",
                Indicator="Stop 135141",
            ),
            id="Valid Descriptor Structure",
        ),
        pytest.param(
            """
            <Descriptor>
                <ShortCommonName>Dublin Stop</ShortCommonName>
                <Landmark>George's Quay</Landmark>
                <Street>Tara St</Street>
                <Crossing>George's Quay</Crossing>
                <Indicator>Stop 135141</Indicator>
            </Descriptor>
            """,
            None,
            id="Missing CommonName",
        ),
    ],
)
def test_parse_descriptor_structure(descriptor_xml_str, expected_result):
    """
    Parse Descriptor
    """
    descriptor_xml = fromstring(descriptor_xml_str)
    assert parse_descriptor_structure(descriptor_xml) == expected_result


@pytest.mark.parametrize(
    "place_xml_str, expected_result",
    [
        pytest.param(
            """
            <Place>
                <NptgLocalityRef>N0075743</NptgLocalityRef>
                <LocalityName>Dublin - George's Quay (Tara St Station)</LocalityName>
                <Location>
                    <Translation>
                        <Longitude>-6.253318</Longitude>
                        <Latitude>53.347398</Latitude>
                        <Easting>117018</Easting>
                        <Northing>391827</Northing>
                    </Translation>
                </Location>
            </Place>
            """,
            PlaceStructure(
                NptgLocalityRef="N0075743",
                LocalityName="Dublin - George's Quay (Tara St Station)",
                Location=LocationStructure(
                    Longitude="-6.253318",
                    Latitude="53.347398",
                    Easting="117018",
                    Northing="391827",
                ),
            ),
            id="Valid Place Structure",
        ),
        pytest.param(
            """
            <Place>
                <LocalityName>Dublin - George's Quay (Tara St Station)</LocalityName>
                <Location>
                    <Translation>                
                        <Longitude>-6.253318</Longitude>
                        <Latitude>53.347398</Latitude>
                        <Easting>117018</Easting>
                        <Northing>391827</Northing>
                    </Translation>
                </Location>
            </Place>
            """,
            None,
            id="Missing NptgLocalityRef",
        ),
        pytest.param(
            """
            <Place>
                <NptgLocalityRef>N0075743</NptgLocalityRef>
                <LocalityName>Dublin - George's Quay (Tara St Station)</LocalityName>
            </Place>
            """,
            None,
            id="Missing Location",
        ),
    ],
)
def test_parse_place_structure(place_xml_str, expected_result):
    """
    Parsing entire place structure
    """
    place_xml = fromstring(place_xml_str)
    assert parse_place_structure(place_xml) == expected_result


@pytest.mark.parametrize(
    "stop_xml_str, expected_result",
    [
        pytest.param(
            """
            <StopPoint>
                <AtcoCode>900000001</AtcoCode>
                <Descriptor>
                    <CommonName>Stop 1</CommonName>
                </Descriptor>
                <Place>
                    <NptgLocalityRef>N0075743</NptgLocalityRef>
                    <Location>
                        <Translation>
                            <Longitude>-6.253318</Longitude>
                            <Latitude>53.347398</Latitude>
                            <Easting>117018</Easting>
                            <Northing>391827</Northing>
                        </Translation>
                    </Location>
                </Place>
                <StopClassification>
                    <StopType>busCoachTrolleyOnStreetPoint</StopType>
                    <OnStreet>
                        <Bus>
                            <BusStopType>MKD</BusStopType>
                            <TimingStatus>principalTimingPoint</TimingStatus>
                            <MarkedPoint>
                                <Bearing>
                                    <CompassPoint>N</CompassPoint>
                                </Bearing>
                            </MarkedPoint>
                        </Bus>
                    </OnStreet>
                </StopClassification>
                <StopAreas>Area1</StopAreas>
                <StopAreas>Area2</StopAreas>
                <AdministrativeAreaRef>AdministrativeArea1</AdministrativeAreaRef>
            </StopPoint>
            """,
            TXCStopPoint(
                AtcoCode="900000001",
                Descriptor=DescriptorStructure(CommonName="Stop 1"),
                Place=PlaceStructure(
                    NptgLocalityRef="N0075743",
                    Location=LocationStructure(
                        Longitude="-6.253318",
                        Latitude="53.347398",
                        Easting="117018",
                        Northing="391827",
                    ),
                ),
                StopClassification=StopClassificationStructure(
                    StopType="busCoachTrolleyOnStreetPoint",
                    OnStreet=OnStreetStructure(
                        Bus=BusStopStructure(
                            BusStopType="MKD",
                            TimingStatus="principalTimingPoint",
                            MarkedPoint=MarkedPointStructure(
                                Bearing=BearingStructure(CompassPoint="N")
                            ),
                        )
                    ),
                ),
                StopAreas=["Area1", "Area2"],
                AdministrativeAreaRef="AdministrativeArea1",
            ),
            id="Valid TXCStopPoint with StopAreas",
        ),
        pytest.param(
            """
            <StopPoint>
                <AtcoCode>900000002</AtcoCode>
                <Descriptor>
                    <CommonName>Stop 2</CommonName>
                </Descriptor>
                <Place>
                    <NptgLocalityRef>N0075744</NptgLocalityRef>
                    <Location>
                        <Translation>
                            <Longitude>-6.253318</Longitude>
                            <Latitude>53.347398</Latitude>
                            <Easting>117018</Easting>
                            <Northing>391827</Northing>
                        </Translation>
                    </Location>
                </Place>
                <StopClassification>
                    <StopType>busCoachTrolleyOnStreetPoint</StopType>
                    <OnStreet>
                        <Bus>
                            <BusStopType>MKD</BusStopType>
                            <TimingStatus>principalTimingPoint</TimingStatus>
                            <MarkedPoint>
                                <Bearing>
                                    <CompassPoint>N</CompassPoint>
                                </Bearing>
                            </MarkedPoint>
                        </Bus>
                    </OnStreet>
                </StopClassification>
                <AdministrativeAreaRef>AdministrativeArea2</AdministrativeAreaRef>
            </StopPoint>
            """,
            TXCStopPoint(
                AtcoCode="900000002",
                Descriptor=DescriptorStructure(CommonName="Stop 2"),
                Place=PlaceStructure(
                    NptgLocalityRef="N0075744",
                    Location=LocationStructure(
                        Longitude="-6.253318",
                        Latitude="53.347398",
                        Easting="117018",
                        Northing="391827",
                    ),
                ),
                StopClassification=StopClassificationStructure(
                    StopType="busCoachTrolleyOnStreetPoint",
                    OnStreet=OnStreetStructure(
                        Bus=BusStopStructure(
                            BusStopType="MKD",
                            TimingStatus="principalTimingPoint",
                            MarkedPoint=MarkedPointStructure(
                                Bearing=BearingStructure(CompassPoint="N")
                            ),
                        )
                    ),
                ),
                StopAreas=None,
                AdministrativeAreaRef="AdministrativeArea2",
            ),
            id="Valid TXCStopPoint without StopAreas",
        ),
        pytest.param(
            """
            <StopPoint>
                <Descriptor>
                    <CommonName>Stop 3</CommonName>
                </Descriptor>
                <Place>
                    <NptgLocalityRef>N0075745</NptgLocalityRef>
                    <Location>
                        <Longitude>-6.253318</Longitude>
                        <Latitude>53.347398</Latitude>
                        <Easting>117018</Easting>
                        <Northing>391827</Northing>
                    </Location>
                </Place>
                <StopClassification>
                    <StopType>busCoachTrolleyOnStreetPoint</StopType>
                    <OnStreet>
                        <Bus>
                            <BusStopType>MKD</BusStopType>
                            <TimingStatus>PTP</TimingStatus>
                            <MarkedPoint>
                                <Bearing>
                                    <CompassPoint>N</CompassPoint>
                                </Bearing>
                            </MarkedPoint>
                        </Bus>
                    </OnStreet>
                </StopClassification>
                <AdministrativeAreaRef>AdministrativeArea3</AdministrativeAreaRef>
            </StopPoint>
            """,
            None,
            id="Missing AtcoCode",
        ),
    ],
)
def test_parse_txc_stop_point(stop_xml_str, expected_result):
    """
    Test Parsing a Stop Point
    """
    stop_xml = fromstring(stop_xml_str)
    assert parse_txc_stop_point(stop_xml) == expected_result
