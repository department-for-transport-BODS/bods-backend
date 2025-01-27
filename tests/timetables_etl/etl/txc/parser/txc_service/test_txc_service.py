"""
Test Parsing TXC Service
"""

from datetime import date

import pytest
from common_layer.txc.models import (
    TXCBookingArrangements,
    TXCFixedStopUsage,
    TXCFlexibleJourneyPattern,
    TXCFlexibleService,
    TXCFlexibleStopUsage,
    TXCJourneyPattern,
    TXCLine,
    TXCLineDescription,
    TXCPhone,
    TXCService,
    TXCStandardService,
)
from common_layer.txc.parser.services import parse_service
from lxml import etree

from ..utils import assert_model_equal


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
