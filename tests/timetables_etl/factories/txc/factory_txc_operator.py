"""
TXC Operator Factories
"""

from common_layer.xml.txc.models import TXCOperator
from factory import Factory


class TXCOperatorFactory(Factory):
    """
    Creates TXC Operator
    """

    class Meta:  # type: ignore[misc]
        model = TXCOperator

    NationalOperatorCode = "NOC123"
    OperatorShortName = "Test Operator"
    OperatorNameOnLicence = "Test Operator Ltd"
    TradingName = "Test Trading Name"
    LicenceNumber = "PD0000123"
    LicenceClassification = "standardNational"
    PrimaryMode = "coach"
