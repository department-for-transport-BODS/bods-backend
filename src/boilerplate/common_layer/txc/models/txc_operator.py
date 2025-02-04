"""
TranXchange 2.4 PTI 1.1.A
Operator
"""

from pydantic import BaseModel, Field

from .txc_types import LicenceClassificationT, TransportModeT


class TXCOperator(BaseModel):
    """
    TXC Operator
    """

    NationalOperatorCode: str = Field(
        ...,
        description=(
            "Code held within the National Operator Code database (NOC) "
            "maintained and operated by Traveline Information Limited (TIL)"
        ),
    )
    OperatorShortName: str = Field(
        ...,
        description="Where possible this should match the Operator Public Name field in NOC.",
    )
    OperatorNameOnLicence: str | None = Field(
        default=None,
        description="Where appropriate to aid readability / traceability.",
    )

    TradingName: str | None = Field(
        ...,
        description="Shall be provided, where this is different from the name given in NOC. ",
    )
    LicenceNumber: str | None = Field(
        ...,
        description=(
            "Where more than one O-licence use the licence number relevant to the service "
            "Details about the licence shall be obtained via reference to OTC"
        ),
    )
    LicenceClassification: LicenceClassificationT | None = Field(
        default=None,
        description="Shall be provided, where this is different from the name given in NOC. ",
    )
    PrimaryMode: TransportModeT = Field(
        default="bus",
        description=("The main mode the operator provides"),
    )
    Note: str | None = Field(
        default=None,
        description="Operator Notes",
    )
