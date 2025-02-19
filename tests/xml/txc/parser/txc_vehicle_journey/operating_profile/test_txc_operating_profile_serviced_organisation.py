"""
ServicedOrganisationDayType Parsing
"""

import pytest
from common_layer.xml.txc.models.txc_operating_profile import (
    TXCServicedOrganisationDayType,
)
from common_layer.xml.txc.parser.operating_profile import (
    parse_serviced_organisation_days,
)
from lxml import etree


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
                WorkingDays=["080Sch-Thurrock"],
                Holidays=["Organisation2"],
            ),
            id="Both working days and holidays",
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
                WorkingDays=["School1", "School2"],
                Holidays=None,
            ),
            id="Only working days with multiple refs",
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
                WorkingDays=None,
                Holidays=["Holiday1", "Holiday2"],
            ),
            id="Only holidays with multiple refs",
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
