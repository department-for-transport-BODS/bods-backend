"""
Test Parsing the Operators section
"""

import pytest
from common_layer.txc.models import LicenceClassificationT, TransportModeT, TXCOperator
from common_layer.txc.parser.operators import (
    parse_licence_classification,
    parse_operator,
    parse_operators,
    parse_transport_mode,
)
from lxml import etree


@pytest.mark.parametrize(
    "xml_string, expected",
    [
        pytest.param(
            "<Operator><PrimaryMode>coach</PrimaryMode></Operator>",
            "coach",
            id="Bus Transport Mode",
        ),
        pytest.param(
            "<Operator><PrimaryMode>rail</PrimaryMode></Operator>",
            "rail",
            id="Rail Transport Mode",
        ),
        pytest.param(
            "<Operator><PrimaryMode>ABCDEFG</PrimaryMode></Operator>",
            "bus",
            id="Incorrect Transport Mode Default to bus",
        ),
        pytest.param("<Operator></Operator>", "bus", id="Missing Transport Mode"),
    ],
)
def test_parse_transport_mode(xml_string: str, expected: TransportModeT):
    """
    Test parsing transport mode from XML
    """
    operator_xml = etree.fromstring(xml_string)
    assert parse_transport_mode(operator_xml) == expected


@pytest.mark.parametrize(
    "xml_string, expected",
    [
        pytest.param(
            "<Operator><LicenceClassification>standardNational</LicenceClassification></Operator>",
            "standardNational",
            id="Valid Licence Classification",
        ),
        pytest.param(
            "<Operator><LicenceClassification>invalid</LicenceClassification></Operator>",
            None,
            id="Invalid Licence Classification",
        ),
        pytest.param(
            "<Operator></Operator>", None, id="Missing Licence Classification"
        ),
    ],
)
def test_parse_licence_classification(
    xml_string: str, expected: LicenceClassificationT | None
):
    """
    Test parsing licence classification from XML
    """
    operator_xml = etree.fromstring(xml_string)
    assert parse_licence_classification(operator_xml) == expected


@pytest.mark.parametrize(
    "xml_string, expected",
    [
        pytest.param(
            """
            <Operator>
                <NationalOperatorCode>ABC</NationalOperatorCode>
                <OperatorShortName>ABC Operator</OperatorShortName>
                <TradingName>ABC Trading</TradingName>
                <LicenceNumber>LN123</LicenceNumber>
                <PrimaryMode>bus</PrimaryMode>
                <OperatorNameOnLicence>ABC Operator Name</OperatorNameOnLicence>
                <LicenceClassification>standardNational</LicenceClassification>
            </Operator>
            """,
            TXCOperator(
                NationalOperatorCode="ABC",
                OperatorShortName="ABC Operator",
                TradingName="ABC Trading",
                LicenceNumber="LN123",
                PrimaryMode="bus",
                OperatorNameOnLicence="ABC Operator Name",
                LicenceClassification="standardNational",
            ),
            id="Valid Operator",
        ),
        pytest.param(
            """
            <Operator>
                <NationalOperatorCode>ABC</NationalOperatorCode>
                <OperatorShortName>ABC Operator</OperatorShortName>
                <PrimaryMode>invalid</PrimaryMode>
                <LicenceClassification>invalid</LicenceClassification>
            </Operator>
            """,
            TXCOperator(
                NationalOperatorCode="ABC",
                OperatorShortName="ABC Operator",
                TradingName=None,
                LicenceNumber=None,
                PrimaryMode="bus",
                OperatorNameOnLicence=None,
                LicenceClassification=None,
            ),
            id="Invalid Transport Mode and Licence Classification",
        ),
        pytest.param(
            """
            <Operator>
                <NationalOperatorCode>ABC</NationalOperatorCode>
            </Operator>
            """,
            None,
            id="Missing Required Fields",
        ),
    ],
)
def test_parse_operator(xml_string: str, expected: TXCOperator | None):
    """
    Test parsing operator from XML
    """
    operator_xml = etree.fromstring(xml_string)
    assert parse_operator(operator_xml) == expected


@pytest.mark.parametrize(
    "xml_string, expected",
    [
        pytest.param(
            """
            <TransXChange>
                <Operators>
                    <Operator>
                        <NationalOperatorCode>ABC</NationalOperatorCode>
                        <OperatorShortName>ABC Operator</OperatorShortName>
                        <TradingName>ABC Trading</TradingName>
                        <LicenceNumber>LN123</LicenceNumber>
                        <PrimaryMode>bus</PrimaryMode>
                        <OperatorNameOnLicence>ABC Operator Name</OperatorNameOnLicence>
                        <LicenceClassification>standardNational</LicenceClassification>
                    </Operator>
                </Operators>
            </TransXChange>
            """,
            [
                TXCOperator(
                    NationalOperatorCode="ABC",
                    OperatorShortName="ABC Operator",
                    TradingName="ABC Trading",
                    LicenceNumber="LN123",
                    PrimaryMode="bus",
                    OperatorNameOnLicence="ABC Operator Name",
                    LicenceClassification="standardNational",
                ),
            ],
            id="Parse Operator",
        ),
        pytest.param(
            """
            <TransXChange>
                <Operators>
                    <LicensedOperator>
                        <NationalOperatorCode>XYZ</NationalOperatorCode>
                        <OperatorShortName>XYZ Operator</OperatorShortName>
                        <TradingName>XYZ Trading</TradingName>
                        <LicenceNumber>LN456</LicenceNumber>
                        <PrimaryMode>coach</PrimaryMode>
                        <OperatorNameOnLicence>XYZ Operator Name</OperatorNameOnLicence>
                        <LicenceClassification>standardInternational</LicenceClassification>
                    </LicensedOperator>
                </Operators>
            </TransXChange>
            """,
            [
                TXCOperator(
                    NationalOperatorCode="XYZ",
                    OperatorShortName="XYZ Operator",
                    TradingName="XYZ Trading",
                    LicenceNumber="LN456",
                    PrimaryMode="coach",
                    OperatorNameOnLicence="XYZ Operator Name",
                    LicenceClassification="standardInternational",
                ),
            ],
            id="LicensedOperator to Operator",
        ),
        pytest.param(
            """
            <TransXChange>
                <Operators>
                    <Operator>
                        <NationalOperatorCode>ABC</NationalOperatorCode>
                        <OperatorShortName>ABC Operator</OperatorShortName>
                        <TradingName>ABC Trading</TradingName>
                        <LicenceNumber>LN123</LicenceNumber>
                        <PrimaryMode>bus</PrimaryMode>
                        <OperatorNameOnLicence>ABC Operator Name</OperatorNameOnLicence>
                        <LicenceClassification>standardNational</LicenceClassification>
                    </Operator>
                    <LicensedOperator>
                        <NationalOperatorCode>XYZ</NationalOperatorCode>
                        <OperatorShortName>XYZ Operator</OperatorShortName>
                        <TradingName>XYZ Trading</TradingName>
                        <LicenceNumber>LN456</LicenceNumber>
                        <PrimaryMode>coach</PrimaryMode>
                        <OperatorNameOnLicence>XYZ Operator Name</OperatorNameOnLicence>
                        <LicenceClassification>standardInternational</LicenceClassification>
                    </LicensedOperator>
                </Operators>
            </TransXChange>
            """,
            [
                TXCOperator(
                    NationalOperatorCode="ABC",
                    OperatorShortName="ABC Operator",
                    TradingName="ABC Trading",
                    LicenceNumber="LN123",
                    PrimaryMode="bus",
                    OperatorNameOnLicence="ABC Operator Name",
                    LicenceClassification="standardNational",
                ),
                TXCOperator(
                    NationalOperatorCode="XYZ",
                    OperatorShortName="XYZ Operator",
                    TradingName="XYZ Trading",
                    LicenceNumber="LN456",
                    PrimaryMode="coach",
                    OperatorNameOnLicence="XYZ Operator Name",
                    LicenceClassification="standardInternational",
                ),
            ],
            id="Mix of Operators",
        ),
        pytest.param(
            """
            <TransXChange>
                <Operators>
                    <Operator>
                        <NationalOperatorCode>ABC</NationalOperatorCode>
                        <OperatorShortName>ABC Operator</OperatorShortName>
                    </Operator>
                    <UnknownOperator>
                        <NationalOperatorCode>XYZ</NationalOperatorCode>
                        <OperatorShortName>XYZ Operator</OperatorShortName>
                    </UnknownOperator>
                </Operators>
            </TransXChange>
            """,
            [
                TXCOperator(
                    NationalOperatorCode="ABC",
                    OperatorShortName="ABC Operator",
                    TradingName=None,
                    LicenceNumber=None,
                    PrimaryMode="bus",
                    OperatorNameOnLicence=None,
                    LicenceClassification=None,
                ),
            ],
            id="Unknown Operator Type",
        ),
    ],
)
def test_parse_operators(xml_string: str, expected: list[TXCOperator]):
    """
    Test parsing operators from XML
    """
    xml_data = etree.fromstring(xml_string)
    assert parse_operators(xml_data) == expected
