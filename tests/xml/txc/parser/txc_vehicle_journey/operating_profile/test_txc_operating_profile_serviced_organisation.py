"""
ServicedOrganisationDayType Parsing
"""

import pytest
from common_layer.xml.txc.models.txc_operating_profile import (
    TXCServicedOrganisationDays,
    TXCServicedOrganisationDayType,
)
from common_layer.xml.txc.parser.operating_profile_serviced_org import (
    parse_serviced_organisation_day_element,
    parse_serviced_organisation_days,
)
from lxml import etree


@pytest.mark.parametrize(
    "xml_string, expected_result",
    [
        pytest.param(
            """
            <DaysElement>
                <WorkingDays>
                    <ServicedOrganisationRef>080Sch-Thurrock</ServicedOrganisationRef>
                </WorkingDays>
                <Holidays>
                    <ServicedOrganisationRef>Organisation2</ServicedOrganisationRef>
                </Holidays>
            </DaysElement>
            """,
            TXCServicedOrganisationDays(
                WorkingDays=["080Sch-Thurrock"],
                Holidays=["Organisation2"],
            ),
            id="Both working days and holidays",
        ),
        pytest.param(
            """
            <DaysElement>
                <WorkingDays>
                    <ServicedOrganisationRef>School1</ServicedOrganisationRef>
                    <ServicedOrganisationRef>School2</ServicedOrganisationRef>
                </WorkingDays>
            </DaysElement>
            """,
            TXCServicedOrganisationDays(
                WorkingDays=["School1", "School2"],
                Holidays=[],
            ),
            id="Only working days with multiple refs",
        ),
        pytest.param(
            """
            <DaysElement>
                <Holidays>
                    <ServicedOrganisationRef>Holiday1</ServicedOrganisationRef>
                    <ServicedOrganisationRef>Holiday2</ServicedOrganisationRef>
                </Holidays>
            </DaysElement>
            """,
            TXCServicedOrganisationDays(
                WorkingDays=[],
                Holidays=["Holiday1", "Holiday2"],
            ),
            id="Only holidays with multiple refs",
        ),
        pytest.param(
            """
            <DaysElement>
            </DaysElement>
            """,
            None,
            id="Empty days element",
        ),
        pytest.param(
            """
            <DaysElement>
                <WorkingDays></WorkingDays>
                <Holidays></Holidays>
            </DaysElement>
            """,
            None,
            id="Empty working days and holidays",
        ),
        pytest.param(
            None,
            None,
            id="None element",
        ),
    ],
)
def test_parse_serviced_organisation_day_element(
    xml_string: str | None, expected_result: TXCServicedOrganisationDays | None
):
    """
    Test parsing a single day element into a TXCServicedOrganisationDays object
    """
    if xml_string is None:
        xml_element = None
    else:
        xml_element = etree.fromstring(xml_string)

    result = parse_serviced_organisation_day_element(xml_element)
    assert result == expected_result


@pytest.mark.parametrize(
    "xml_string, expected_result",
    [
        pytest.param(
            """
            <ServicedOrganisationDayType>
                <DaysOfOperation>
                    <WorkingDays>
                        <ServicedOrganisationRef>080Sch-Thurrock</ServicedOrganisationRef>
                    </WorkingDays>
                    <Holidays>
                        <ServicedOrganisationRef>Organisation2</ServicedOrganisationRef>
                    </Holidays>
                </DaysOfOperation>
            </ServicedOrganisationDayType>
            """,
            TXCServicedOrganisationDayType(
                DaysOfOperation=[
                    TXCServicedOrganisationDays(
                        WorkingDays=["080Sch-Thurrock"],
                        Holidays=["Organisation2"],
                    )
                ],
                DaysOfNonOperation=[],
            ),
            id="Days of operation with both working days and holidays",
        ),
        pytest.param(
            """
            <ServicedOrganisationDayType>
                <DaysOfOperation>
                    <WorkingDays>
                        <ServicedOrganisationRef>School1</ServicedOrganisationRef>
                        <ServicedOrganisationRef>School2</ServicedOrganisationRef>
                    </WorkingDays>
                </DaysOfOperation>
            </ServicedOrganisationDayType>
            """,
            TXCServicedOrganisationDayType(
                DaysOfOperation=[
                    TXCServicedOrganisationDays(
                        WorkingDays=["School1", "School2"],
                        Holidays=[],
                    )
                ],
                DaysOfNonOperation=[],
            ),
            id="Days of operation with only working days",
        ),
        pytest.param(
            """
            <ServicedOrganisationDayType>
                <DaysOfOperation>
                    <Holidays>
                        <ServicedOrganisationRef>Holiday1</ServicedOrganisationRef>
                        <ServicedOrganisationRef>Holiday2</ServicedOrganisationRef>
                    </Holidays>
                </DaysOfOperation>
            </ServicedOrganisationDayType>
            """,
            TXCServicedOrganisationDayType(
                DaysOfOperation=[
                    TXCServicedOrganisationDays(
                        WorkingDays=[],
                        Holidays=["Holiday1", "Holiday2"],
                    )
                ],
                DaysOfNonOperation=[],
            ),
            id="Days of operation with only holidays",
        ),
        pytest.param(
            """
            <ServicedOrganisationDayType>
                <DaysOfNonOperation>
                    <WorkingDays>
                        <ServicedOrganisationRef>MVSERVLESS</ServicedOrganisationRef>
                    </WorkingDays>
                </DaysOfNonOperation>
            </ServicedOrganisationDayType>
            """,
            TXCServicedOrganisationDayType(
                DaysOfOperation=[],
                DaysOfNonOperation=[
                    TXCServicedOrganisationDays(
                        WorkingDays=["MVSERVLESS"],
                        Holidays=[],
                    )
                ],
            ),
            id="Days of non-operation with working days",
        ),
        pytest.param(
            """
            <ServicedOrganisationDayType>
                <DaysOfOperation>
                    <WorkingDays>
                        <ServicedOrganisationRef>School1</ServicedOrganisationRef>
                    </WorkingDays>
                    <Holidays>
                        <ServicedOrganisationRef>Holiday1</ServicedOrganisationRef>
                    </Holidays>
                </DaysOfOperation>
                <DaysOfNonOperation>
                    <WorkingDays>
                        <ServicedOrganisationRef>MVSERVLESS</ServicedOrganisationRef>
                    </WorkingDays>
                    <Holidays>
                        <ServicedOrganisationRef>NonOperationHoliday</ServicedOrganisationRef>
                    </Holidays>
                </DaysOfNonOperation>
            </ServicedOrganisationDayType>
            """,
            TXCServicedOrganisationDayType(
                DaysOfOperation=[
                    TXCServicedOrganisationDays(
                        WorkingDays=["School1"],
                        Holidays=["Holiday1"],
                    )
                ],
                DaysOfNonOperation=[
                    TXCServicedOrganisationDays(
                        WorkingDays=["MVSERVLESS"],
                        Holidays=["NonOperationHoliday"],
                    )
                ],
            ),
            id="Both days of operation and non-operation",
        ),
        pytest.param(
            """
            <ServicedOrganisationDayType>
            </ServicedOrganisationDayType>
            """,
            None,
            id="Empty serviced organisation",
        ),
        pytest.param(
            """
            <ServicedOrganisationDayType>
                <DaysOfOperation>
                </DaysOfOperation>
            </ServicedOrganisationDayType>
            """,
            None,
            id="Empty days of operation",
        ),
        pytest.param(
            """
            <ServicedOrganisationDayType>
                <DaysOfNonOperation>
                </DaysOfNonOperation>
            </ServicedOrganisationDayType>
            """,
            None,
            id="Empty days of non-operation",
        ),
    ],
)
def test_parse_serviced_organisation_days(
    xml_string: str, expected_result: TXCServicedOrganisationDayType | None
):
    """
    Test parsing serviced organisation day types
    """
    xml_element = etree.fromstring(xml_string)
    result = parse_serviced_organisation_days(xml_element)
    assert result == expected_result
