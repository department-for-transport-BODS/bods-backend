"""
Test Parsing TXC Service
"""

from datetime import date

import pytest
from lxml import etree

from timetables_etl.etl.app.txc.models.txc_service import (
    TXCJourneyPattern,
    TXCLine,
    TXCLineDescription,
    TXCService,
    TXCStandardService,
)
from timetables_etl.etl.app.txc.models.txc_service_flexible import (
    TXCBookingArrangements,
    TXCFixedStopUsage,
    TXCFlexibleJourneyPattern,
    TXCFlexibleService,
    TXCFlexibleStopUsage,
    TXCPhone,
)
from timetables_etl.etl.app.txc.parser.services import (
    parse_journey_pattern,
    parse_line,
    parse_line_description,
    parse_service,
    parse_standard_service,
)

from .utils import assert_model_equal


@pytest.mark.parametrize(
    "xml_string, expected_result",
    [
        pytest.param(
            """
            <JourneyPattern id="jp_1">
                <PrivateCode>PC123</PrivateCode>
                <DestinationDisplay>City Center</DestinationDisplay>
                <Direction>outbound</Direction>
                <RouteRef>route_1</RouteRef>
                <JourneyPatternSectionRefs>section_1</JourneyPatternSectionRefs>
                <Description>Main Route</Description>
                <LayoverPoint>stop_1</LayoverPoint>
                <OperatorRef>op_1</OperatorRef>
            </JourneyPattern>
            """,
            TXCJourneyPattern(
                id="jp_1",
                PrivateCode="PC123",
                DestinationDisplay="City Center",
                Direction="outbound",
                RouteRef="route_1",
                JourneyPatternSectionRefs=["section_1"],
                Description="Main Route",
                LayoverPoint="stop_1",
                OperatorRef="op_1",
            ),
            id="Full journey pattern",
        ),
        pytest.param(
            """
            <JourneyPattern id="jp_2">
                <DestinationDisplay>City Center</DestinationDisplay>
                <Direction>inbound</Direction>
                <RouteRef>route_2</RouteRef>
                <JourneyPatternSectionRefs>section_1</JourneyPatternSectionRefs>
            </JourneyPattern>
            """,
            TXCJourneyPattern(
                id="jp_2",
                DestinationDisplay="City Center",
                Direction="inbound",
                RouteRef="route_2",
                JourneyPatternSectionRefs=["section_1"],
            ),
            id="Minimal journey pattern",
        ),
    ],
)
def test_parse_journey_pattern(xml_string, expected_result):
    """Test parsing of JourneyPattern section"""
    xml_element = etree.fromstring(xml_string)
    result = parse_journey_pattern(xml_element)
    assert result == expected_result


@pytest.mark.parametrize(
    "xml_string, expected_result",
    [
        pytest.param(
            """
            <StandardService>
                <Origin>Start Town</Origin>
                <Destination>End City</Destination>
                <JourneyPattern id="jp_1">
                    <DestinationDisplay>End City</DestinationDisplay>
                    <Direction>outbound</Direction>
                    <RouteRef>route_1</RouteRef>
                    <JourneyPatternSectionRefs>section_1</JourneyPatternSectionRefs>
                </JourneyPattern>
            </StandardService>
            """,
            TXCStandardService(
                Origin="Start Town",
                Destination="End City",
                JourneyPattern=[
                    TXCJourneyPattern(
                        id="jp_1",
                        DestinationDisplay="End City",
                        Direction="outbound",
                        RouteRef="route_1",
                        JourneyPatternSectionRefs=["section_1"],
                    )
                ],
            ),
            id="Standard service with journey pattern",
        ),
        pytest.param(
            """
            <StandardService>
                <Origin>Start Town</Origin>
                <Destination>End City</Destination>
            </StandardService>
            """,
            TXCStandardService(
                Origin="Start Town", Destination="End City", JourneyPattern=[]
            ),
            id="Minimal standard service",
        ),
    ],
)
def test_parse_standard_service(xml_string, expected_result):
    """Test parsing of StandardService section"""
    xml_element = etree.fromstring(xml_string)
    result = parse_standard_service(xml_element)
    assert result == expected_result


@pytest.mark.parametrize(
    "xml_string, expected_result",
    [
        pytest.param(
            """
            <OutboundDescription>
                <Origin>Start</Origin>
                <Destination>End</Destination>
                <Description>Via Center</Description>
            </OutboundDescription>
            """,
            TXCLineDescription(
                Origin="Start", Destination="End", Description="Via Center"
            ),
            id="Complete outbound description",
        ),
        pytest.param(
            """
            <InboundDescription>
                <Origin>End</Origin>
                <Destination>Start</Destination>
                <Description>Return via Center</Description>
            </InboundDescription>
            """,
            TXCLineDescription(
                Origin="End", Destination="Start", Description="Return via Center"
            ),
            id="Complete inbound description",
        ),
        pytest.param(
            """
            <OutboundDescription>
                <Origin>Knighton Saffron Crossroads</Origin>
                <Destination>Knighton Weldon Road</Destination>
                <Vias>
                    <Via>Roehampton Drive</Via>
                </Vias>
                <Description>Knighton Saffron Crossroads to Knighton Weldon Road</Description>
            </OutboundDescription>
            """,
            TXCLineDescription(
                Origin="Knighton Saffron Crossroads",
                Destination="Knighton Weldon Road",
                Description="Knighton Saffron Crossroads to Knighton Weldon Road",
                Vias=["Roehampton Drive"],
            ),
            id="Description with 1 Via",
        ),
        pytest.param(
            """
            <OutboundDescription>
                <Origin>London Victoria</Origin>
                <Destination>Edinburgh</Destination>
                <Vias>
                    <Via>Manchester</Via>
                    <Via>Leeds</Via>
                </Vias>
                <Description>A Journey</Description>
            </OutboundDescription>
            """,
            TXCLineDescription(
                Origin="London Victoria",
                Destination="Edinburgh",
                Description="A Journey",
                Vias=["Manchester", "Leeds"],
            ),
            id="Description with 2 Vias",
        ),
        pytest.param(
            """
            <OutboundDescription>
                <Description>Direct service</Description>
            </OutboundDescription>
            """,
            TXCLineDescription(Description="Direct service"),
            id="Minimal description with only required field",
        ),
    ],
)
def test_parse_line_description(xml_string, expected_result):
    """Test parsing of LineDescription section"""
    xml_element = etree.fromstring(xml_string)
    result = parse_line_description(xml_element)
    assert result == expected_result


@pytest.mark.parametrize(
    "xml_string, expected_result",
    [
        pytest.param(
            """
            <Line id="line_1">
                <LineName>42</LineName>
                <MarketingName>Express</MarketingName>
                <OutboundDescription>
                    <Origin>Start</Origin>
                    <Destination>End</Destination>
                    <Description>Via Center</Description>
                </OutboundDescription>
                <InboundDescription>
                    <Origin>End</Origin>
                    <Destination>Start</Destination>
                    <Description>Via Center Return</Description>
                </InboundDescription>
            </Line>
            """,
            TXCLine(
                id="line_1",
                LineName="42",
                MarketingName="Express",
                OutboundDescription=TXCLineDescription(
                    Origin="Start", Destination="End", Description="Via Center"
                ),
                InboundDescription=TXCLineDescription(
                    Origin="End", Destination="Start", Description="Via Center Return"
                ),
            ),
            id="Complete line",
        ),
        pytest.param(
            """
            <Line id="line_2">
                <LineName>43</LineName>
            </Line>
            """,
            TXCLine(id="line_2", LineName="43"),
            id="Minimal line",
        ),
    ],
)
def test_parse_line(xml_string, expected_result):
    """Test parsing of Line section"""
    xml_element = etree.fromstring(xml_string)
    result = parse_line(xml_element)
    assert result == expected_result


@pytest.mark.parametrize(
    "xml_string, expected_result",
    [
        pytest.param(
            """
            <Service RevisionNumber="5">
                <ServiceCode>UZ000FLIX:UK045</ServiceCode>
                <PrivateCode>UK045</PrivateCode>
                <Lines>
                    <Line id="FLIX:UZ000FLIX:UK045:UK045">
                        <LineName>UK045</LineName>
                        <OutboundDescription>
                            <Origin>London</Origin>
                            <Destination>Plymouth</Destination>
                            <Description>London - Plymouth</Description>
                        </OutboundDescription>
                        <InboundDescription>
                            <Origin>Plymouth</Origin>
                            <Destination>London</Destination>
                            <Description>Plymouth - London</Description>
                        </InboundDescription>
                    </Line>
                </Lines>
                <OperatingPeriod>
                    <StartDate>2024-11-11</StartDate>
                    <EndDate>2025-01-05</EndDate>
                </OperatingPeriod>
                <RegisteredOperatorRef>FLIX</RegisteredOperatorRef>
                <Mode>coach</Mode>
                <PublicUse>true</PublicUse>
                <StandardService>
                    <Origin>London</Origin>
                    <Destination>Plymouth</Destination>
                    <JourneyPattern id="JP1">
                        <DestinationDisplay>Victoria Coach Station - Plymouth Coach Station</DestinationDisplay>
                        <OperatorRef>FLIX</OperatorRef>
                        <Direction>inbound</Direction>
                        <Description>Victoria Coach Station - Plymouth Coach Station</Description>
                        <RouteRef>R1</RouteRef>
                        <JourneyPatternSectionRefs>JPS1</JourneyPatternSectionRefs>
                    </JourneyPattern>
                    <JourneyPattern id="JP2">
                        <DestinationDisplay>Plymouth Coach Station - Victoria Coach Station</DestinationDisplay>
                        <OperatorRef>FLIX</OperatorRef>
                        <Direction>outbound</Direction>
                        <Description>Plymouth Coach Station - Victoria Coach Station</Description>
                        <RouteRef>R2</RouteRef>
                        <JourneyPatternSectionRefs>JPS2</JourneyPatternSectionRefs>
                    </JourneyPattern>
                </StandardService>
            </Service>
            """,
            TXCService(
                RevisionNumber=5,
                ServiceCode="UZ000FLIX:UK045",
                PrivateCode="UK045",
                RegisteredOperatorRef="FLIX",
                PublicUse=True,
                StartDate=date(2024, 11, 11),
                EndDate=date(2025, 1, 5),
                StandardService=TXCStandardService(
                    Origin="London",
                    Destination="Plymouth",
                    JourneyPattern=[
                        TXCJourneyPattern(
                            id="JP1",
                            DestinationDisplay="Victoria Coach Station - Plymouth Coach Station",
                            OperatorRef="FLIX",
                            Direction="inbound",
                            Description="Victoria Coach Station - Plymouth Coach Station",
                            RouteRef="R1",
                            JourneyPatternSectionRefs=["JPS1"],
                        ),
                        TXCJourneyPattern(
                            id="JP2",
                            DestinationDisplay="Plymouth Coach Station - Victoria Coach Station",
                            OperatorRef="FLIX",
                            Direction="outbound",
                            Description="Plymouth Coach Station - Victoria Coach Station",
                            RouteRef="R2",
                            JourneyPatternSectionRefs=["JPS2"],
                        ),
                    ],
                ),
                Lines=[
                    TXCLine(
                        id="FLIX:UZ000FLIX:UK045:UK045",
                        LineName="UK045",
                        OutboundDescription=TXCLineDescription(
                            Origin="London",
                            Destination="Plymouth",
                            Description="London - Plymouth",
                        ),
                        InboundDescription=TXCLineDescription(
                            Origin="Plymouth",
                            Destination="London",
                            Description="Plymouth - London",
                        ),
                    )
                ],
                Mode="coach",
            ),
            id="StandardService",
        ),
        pytest.param(
            """
            <Service>
            <ServiceCode>PB0002032:467</ServiceCode>
            <Lines>
                <Line id="ARBB:PB0002032:467:53M">
                <LineName>53M</LineName>
                </Line>
            </Lines>
            <OperatingPeriod>
                <StartDate>2022-01-01</StartDate>
            </OperatingPeriod>
            <OperatingProfile>
                <RegularDayType>
                <DaysOfWeek>
                    <Monday />
                </DaysOfWeek>
                </RegularDayType>
                <BankHolidayOperation>
                <DaysOfNonOperation>
                    <ChristmasDay />
                    <BoxingDay />
                    <GoodFriday />
                    <NewYearsDay />
                    <LateSummerBankHolidayNotScotland />
                    <MayDay />
                    <EasterMonday />
                    <SpringBank />
                    <ChristmasDayHoliday />
                    <BoxingDayHoliday />
                    <NewYearsDayHoliday />
                    <OtherPublicHoliday>
                    <Description>CoronationBankHoliday</Description>
                    <Date>2023-05-08</Date>
                    </OtherPublicHoliday>
                    <ChristmasEve />
                    <NewYearsEve />
                </DaysOfNonOperation>
                </BankHolidayOperation>
            </OperatingProfile>
            <ServiceClassification>
                <Flexible />
            </ServiceClassification>
            <RegisteredOperatorRef>O1</RegisteredOperatorRef>
            <PublicUse>true</PublicUse>
            <Description>Flexible on demand service for Market Rasen Area</Description>
            <SchematicMap>CallConnect-Market-Rasen.jpg</SchematicMap>
            <FlexibleService>
                <Origin>Market Rasen</Origin>
                <Destination>Market Rasen</Destination>
                <FlexibleJourneyPattern id="jp_1">
                <Direction>outbound</Direction>
                <StopPointsInSequence>
                    <FixedStopUsage>
                    <StopPointRef>02903501</StopPointRef>
                    <TimingStatus>otherPoint</TimingStatus>
                    </FixedStopUsage>
                    <FlexibleStopUsage>
                    <StopPointRef>02901353</StopPointRef>
                    </FlexibleStopUsage>
                </StopPointsInSequence>
                <BookingArrangements>
                    <Description>The booking office is open for all advance booking Monday to Friday 8:30am
                    – 6:30pm, Saturday 9am – 5pm</Description>
                    <Phone>
                    <TelNationalNumber>0345 234 3344</TelNationalNumber>
                    </Phone>
                    <Email>CallConnect@lincolnshire.gov.uk</Email>
                    <WebAddress>https://callconnect.opendrt.co.uk/OpenDRT/</WebAddress>
                    <AllBookingsTaken>true</AllBookingsTaken>
                </BookingArrangements>
                </FlexibleJourneyPattern>
            </FlexibleService>
            </Service>
        """,
            TXCService(
                ServiceCode="PB0002032:467",
                RegisteredOperatorRef="O1",
                PublicUse=True,
                StartDate=date(2022, 1, 1),
                Lines=[TXCLine(id="ARBB:PB0002032:467:53M", LineName="53M")],
                FlexibleService=TXCFlexibleService(
                    Origin="Market Rasen",
                    Destination="Market Rasen",
                    UseAllStopPoints=False,
                    FlexibleJourneyPattern=[
                        TXCFlexibleJourneyPattern(
                            id="jp_1",
                            Direction="outbound",
                            StopPointsInSequence=[
                                TXCFixedStopUsage(
                                    StopPointRef="02903501", TimingStatus="otherPoint"
                                ),
                                TXCFlexibleStopUsage(StopPointRef="02901353"),
                            ],
                            BookingArrangements=TXCBookingArrangements(
                                Description="The booking office is open for all advance booking Monday to Friday 8:30am – 6:30pm, Saturday 9am – 5pm",
                                Phone=TXCPhone(TelNationalNumber="0345 234 3344"),
                                Email="CallConnect@lincolnshire.gov.uk",
                                WebAddress="https://callconnect.opendrt.co.uk/OpenDRT/",
                                AllBookingsTaken=True,
                            ),
                        )
                    ],
                ),
            ),
            id="Flexible service with booking arrangements",
        ),
        pytest.param(
            """
            <Service>
                <ServiceCode>UZ000WOCT:216</ServiceCode>
                <Lines>
                    <Line id="ARBB:UZ000WOCT:216:53M">
                        <LineName>53M</LineName>
                        <OutboundDescription>
                            <Description>Putteridge High School to Church Street</Description>
                        </OutboundDescription>
                    </Line>
                </Lines>
                <OperatingPeriod>
                    <StartDate>2022-01-01</StartDate>
                </OperatingPeriod>
                <RegisteredOperatorRef>O1</RegisteredOperatorRef>
                <PublicUse>true</PublicUse>
                <FlexibleService>
                    <Origin>Market Rasen</Origin>
                    <Destination>Market Rasen</Destination>
                    <FlexibleJourneyPattern id="jp_2">
                        <Direction>outbound</Direction>
                        <FlexibleZones>
                            <FlexibleStopUsage>
                                <StopPointRef>02901278</StopPointRef>
                            </FlexibleStopUsage>
                        </FlexibleZones>
                        <BookingArrangements>
                            <Description>The booking office is open for all advance booking Monday to Friday 8:30am – 6:30pm, Saturday 9am – 5pm</Description>
                            <WebAddress>https://callconnect.opendrt.co.uk/OpenDRT/</WebAddress>
                            <AllBookingsTaken>true</AllBookingsTaken>
                        </BookingArrangements>
                    </FlexibleJourneyPattern>
                </FlexibleService>
            </Service>
            """,
            TXCService(
                ServiceCode="UZ000WOCT:216",
                RegisteredOperatorRef="O1",
                PublicUse=True,
                StartDate=date(2022, 1, 1),
                Lines=[
                    TXCLine(
                        id="ARBB:UZ000WOCT:216:53M",
                        LineName="53M",
                        OutboundDescription=TXCLineDescription(
                            Description="Putteridge High School to Church Street"
                        ),
                    )
                ],
                FlexibleService=TXCFlexibleService(
                    Origin="Market Rasen",
                    Destination="Market Rasen",
                    UseAllStopPoints=False,
                    FlexibleJourneyPattern=[
                        TXCFlexibleJourneyPattern(
                            id="jp_2",
                            Direction="outbound",
                            StopPointsInSequence=[],
                            FlexibleZones=[
                                TXCFlexibleStopUsage(StopPointRef="02901278")
                            ],
                            BookingArrangements=TXCBookingArrangements(
                                Description="The booking office is open for all advance booking Monday to Friday 8:30am – 6:30pm, Saturday 9am – 5pm",
                                WebAddress="https://callconnect.opendrt.co.uk/OpenDRT/",
                                AllBookingsTaken=True,
                            ),
                        )
                    ],
                ),
            ),
            id="Flexible service with zones and partial line description",
        ),
    ],
)
def test_parse_service(xml_string: str, expected_result: TXCService):
    """Test parsing of Service section"""
    xml_element = etree.fromstring(xml_string)
    result = parse_service(xml_element)
    if result is not None:

        assert_model_equal(result, expected_result)
    else:
        assert expected_result == result
