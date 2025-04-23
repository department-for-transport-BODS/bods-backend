"""
Tests for parsing Servied Organisations
"""

from datetime import date

import pytest
from common_layer.xml.txc.models import (
    TXCServicedOrganisation,
    TXCServicedOrganisationAnnotatedNptgLocalityRef,
    TXCServicedOrganisationDatePattern,
)
from common_layer.xml.txc.parser.serviced_organisation import (
    parse_date_range,
    parse_holidays,
    parse_serviced_organisation,
    parse_working_days,
)
from lxml import etree

from tests.xml.conftest import assert_model_equal


@pytest.mark.parametrize(
    "xml_string, expected_result",
    [
        pytest.param(
            """
            <DateRange>
                <StartDate>2024-01-01</StartDate>
                <EndDate>2024-01-05</EndDate>
                <Description>Test Week</Description>
                <Provisional>true</Provisional>
            </DateRange>
            """,
            TXCServicedOrganisationDatePattern(
                StartDate=date(2024, 1, 1),
                EndDate=date(2024, 1, 5),
                Description="Test Week",
                Provisional=True,
            ),
            id="Complete date range with all fields",
        ),
        pytest.param(
            """
            <DateRange>
                <StartDate>2024-01-01</StartDate>
                <EndDate>2024-01-05</EndDate>
            </DateRange>
            """,
            TXCServicedOrganisationDatePattern(
                StartDate=date(2024, 1, 1),
                EndDate=date(2024, 1, 5),
                Description=None,
                Provisional=False,
            ),
            id="Date range with only required fields",
        ),
        pytest.param(
            """
            <DateRange>
                <StartDate>2024-01-01</StartDate>
            </DateRange>
            """,
            None,
            id="Invalid date range missing end date",
        ),
    ],
)
def test_parse_date_range(
    xml_string: str, expected_result: TXCServicedOrganisationDatePattern | None
) -> None:
    """Test parsing of individual date range"""
    xml_element = etree.fromstring(xml_string)
    result = parse_date_range(xml_element)
    assert result == expected_result


@pytest.mark.parametrize(
    "xml_string, expected_result",
    [
        pytest.param(
            """
            <ServicedOrganisation>
                <WorkingDays>
                    <DateRange>
                        <StartDate>2024-01-01</StartDate>
                        <EndDate>2024-01-05</EndDate>
                    </DateRange>
                    <DateRange>
                        <StartDate>2024-01-08</StartDate>
                        <EndDate>2024-01-12</EndDate>
                    </DateRange>
                </WorkingDays>
            </ServicedOrganisation>
            """,
            [
                TXCServicedOrganisationDatePattern(
                    StartDate=date(2024, 1, 1),
                    EndDate=date(2024, 1, 5),
                    Description=None,
                    Provisional=False,
                ),
                TXCServicedOrganisationDatePattern(
                    StartDate=date(2024, 1, 8),
                    EndDate=date(2024, 1, 12),
                    Description=None,
                    Provisional=False,
                ),
            ],
            id="Multiple valid date ranges",
        ),
        pytest.param(
            """
            <ServicedOrganisation>
                <WorkingDays>
                    <DateRange>
                        <StartDate>2024-01-01</StartDate>
                    </DateRange>
                    <DateRange>
                        <StartDate>2024-01-08</StartDate>
                        <EndDate>2024-01-12</EndDate>
                    </DateRange>
                </WorkingDays>
            </ServicedOrganisation>
            """,
            [
                TXCServicedOrganisationDatePattern(
                    StartDate=date(2024, 1, 8),
                    EndDate=date(2024, 1, 12),
                    Description=None,
                    Provisional=False,
                ),
            ],
            id="Mixed valid and invalid date ranges",
        ),
        pytest.param(
            "<ServicedOrganisation><WorkingDays/></ServicedOrganisation>",
            None,
            id="Empty working days",
        ),
        pytest.param(
            "<ServicedOrganisation/>",
            None,
            id="No working days element",
        ),
    ],
)
def test_parse_working_days(
    xml_string: str, expected_result: list[TXCServicedOrganisationDatePattern] | None
) -> None:
    """Test parsing of working days section"""
    xml_element = etree.fromstring(xml_string)
    result = parse_working_days(xml_element)
    assert result == expected_result


@pytest.mark.parametrize(
    "xml_string, expected_result",
    [
        pytest.param(
            """
            <ServicedOrganisation>
                <Holidays>
                    <DateRange>
                        <StartDate>2024-12-25</StartDate>
                        <EndDate>2024-12-26</EndDate>
                        <Description>Christmas</Description>
                    </DateRange>
                </Holidays>
            </ServicedOrganisation>
            """,
            [
                TXCServicedOrganisationDatePattern(
                    StartDate=date(2024, 12, 25),
                    EndDate=date(2024, 12, 26),
                    Description="Christmas",
                    Provisional=False,
                ),
            ],
            id="Single holiday",
        ),
        pytest.param(
            "<ServicedOrganisation><Holidays/></ServicedOrganisation>",
            None,
            id="Empty holidays",
        ),
    ],
)
def test_parse_holidays(
    xml_string: str, expected_result: list[TXCServicedOrganisationDatePattern] | None
) -> None:
    """Test parsing of holidays section"""
    xml_element = etree.fromstring(xml_string)
    result = parse_holidays(xml_element)
    assert result == expected_result


@pytest.mark.parametrize(
    "xml_string, expected_result",
    [
        pytest.param(
            """
        <ServicedOrganisation Modification="new" Status="active">
            <OrganisationCode>080Sch-Thurrock</OrganisationCode>
            <Name>Thurrock Schooldays</Name>
            <WorkingDays>
                <DateRange>
                    <StartDate>2021-06-07</StartDate>
                    <EndDate>2021-06-11</EndDate>
                    <Description>Moo</Description>
                    <Provisional>true</Provisional>
                </DateRange>
                <DateRange>
                    <StartDate>2021-06-14</StartDate>
                    <EndDate>2021-06-18</EndDate>
                </DateRange>
            </WorkingDays>
            <ParentServicedOrganisationRef>Organisation2</ParentServicedOrganisationRef>
        </ServicedOrganisation>
            """,
            TXCServicedOrganisation(
                Modification="new",
                Status="active",
                OrganisationCode="080Sch-Thurrock",
                Name="Thurrock Schooldays",
                WorkingDays=[
                    TXCServicedOrganisationDatePattern(
                        StartDate=date(2021, 6, 7),
                        EndDate=date(2021, 6, 11),
                        Description="Moo",
                        Provisional=True,
                    ),
                    TXCServicedOrganisationDatePattern(
                        StartDate=date(2021, 6, 14),
                        EndDate=date(2021, 6, 18),
                        Description=None,
                        Provisional=False,
                    ),
                ],
                ParentServicedOrganisationRef="Organisation2",
            ),
            id="Organisation with working days and parent ref",
        ),
        pytest.param(
            """
        <ServicedOrganisation Modification="new" Status="active">
            <OrganisationCode>Organisation2</OrganisationCode>
            <Name>Thurrock Schooldays</Name>
            <WorkingDays>
                <DateRange>
                    <StartDate>2021-06-14</StartDate>
                    <EndDate>2021-06-18</EndDate>
                </DateRange>
            </WorkingDays>
            <AdministrativeAreaRef>123</AdministrativeAreaRef>
            <AnnotatedNptgLocalityRef>
                <NptgLocalityRef>E0034965</NptgLocalityRef>
                <LocalityName>Ashgrove</LocalityName>
                <LocalityQualifier>Peasedown St John</LocalityQualifier>
            </AnnotatedNptgLocalityRef>
            <LocalEducationAuthorityRef>123sas</LocalEducationAuthorityRef>
        </ServicedOrganisation>
            """,
            TXCServicedOrganisation(
                Modification="new",
                Status="active",
                OrganisationCode="Organisation2",
                Name="Thurrock Schooldays",
                WorkingDays=[
                    TXCServicedOrganisationDatePattern(
                        StartDate=date(2021, 6, 14),
                        EndDate=date(2021, 6, 18),
                        Description=None,
                        Provisional=False,
                    ),
                ],
                AdministrativeAreaRef="123",
                AnnotatedNptgLocalityRef=TXCServicedOrganisationAnnotatedNptgLocalityRef(
                    NptgLocalityRef="E0034965",
                    LocalityName="Ashgrove",
                    LocalityQualifier="Peasedown St John",
                ),
                LocalEducationAuthorityRef="123sas",
            ),
            id="Organisation with locality ref and admin area",
        ),
        pytest.param(
            """
        <ServicedOrganisation Modification="new" Status="active">
            <Name>Missing Code</Name>
        </ServicedOrganisation>
            """,
            None,
            id="Missing required OrganisationCode",
        ),
        pytest.param(
            """
        <ServicedOrganisation Modification="new" Status="invalid">
            <OrganisationCode>test</OrganisationCode>
        </ServicedOrganisation>
            """,
            TXCServicedOrganisation(OrganisationCode="test", Modification="new"),
            id="Invalid Status value",
        ),
        pytest.param(
            "<ServicedOrganisation/>",
            None,
            id="Empty organisation",
        ),
    ],
)
def test_parse_serviced_organisation(
    xml_string: str, expected_result: TXCServicedOrganisation | None
) -> None:
    """Test parsing of serviced organisation"""
    xml_element = etree.fromstring(xml_string)
    result = parse_serviced_organisation(xml_element)

    if expected_result is None:
        assert result is None
    else:
        assert result is not None
        assert_model_equal(result, expected_result)
