"""
TranXchange 2.4 PTI 1.1.A
Stop Point
"""

from datetime import datetime

from pydantic import BaseModel, Field

from .stop_point_availability import StopAvailabilityStructure
from .stop_point_descriptor import DescriptorStructure
from .stop_point_location import PlaceStructure
from .stoppoint_classification import StopClassificationStructure


class AnnotatedStopPointRef(BaseModel):
    """
    PTI Model for Stop Point Ref
    napt/NaPT_stop-v2-4.xsd
    """

    StopPointRef: str = Field(..., description="Reference to a NaPTAN stop")
    CommonName: str = Field(..., description="Common name for the stop")
    Indicator: str | None = Field(
        default=None,
        description="Brief additional description to further distinguish the stop",
    )
    LocalityName: str | None = Field(
        default=None,
        description="Name of NPTG Locality in which stop lies",
    )
    LocalityQualifier: str | None = Field(
        default=None,
        description="Any qualifier of NPTG Locality in which stop lies",
    )


class TXCStopPoint(BaseModel):
    """PTI Model for Stop Point (napt/NaPT_stop-v2-4.xsd)."""

    AtcoCode: str = Field(
        ...,
        description=(
            "Full NaPTAN stop identifier that uniquely identifies the stop within the UK"
        ),
    )

    @property
    def StopPointRef(self) -> str:  # pylint: disable=invalid-name
        """
        Allows Accessingthe AtcoCode in the same way
        """
        return self.AtcoCode

    NaptanCode: str | None = Field(
        default=None,
        description=(
            "Short NaPTAN code for passengers to use when uniquely identifying the stop "
            "by SMS and other self-service channels"
        ),
    )
    PlateCode: str | None = Field(
        default=None,
        description=(
            "Plate number for stop. An arbitrary asset number that may be placed on "
            "stop to identify it"
        ),
    )
    PrivateCode: str | None = Field(
        default=None,
        description=(
            "A private code that uniquely identifies the stop. May be used for "
            "interoperating with other (legacy) systems"
        ),
    )
    CleardownCode: int | None = Field(
        default=None,
        description=(
            "A 20 bit number used for wireless cleardown of stop displays by some AVL "
            "systems. Number format defined by RTIG"
        ),
    )
    FormerStopPointRef: str | None = Field(
        default=None,
        description=(
            "If stop was created to replace a previous stop, for example, because of a "
            "boundary change, this can be used to provide traceability back to the "
            "previous stop record"
        ),
    )
    Descriptor: DescriptorStructure = Field(
        ..., description="Structured textual description of stop"
    )
    AlternativeDescriptors: list[DescriptorStructure] | None = Field(
        default=None,
        description=(
            "Alternative name for stop. Can be used to provide both aliases and "
            "bilingual support"
        ),
    )
    Place: PlaceStructure = Field(..., description="Place where stop is located")
    StopClassification: StopClassificationStructure = Field(
        ...,
        description=(
            "Classification, e.g. on-street bus stop; platform at a railway station"
        ),
    )
    StopAreas: list[str] | None = Field(
        default=None, description="The StopAreas to which the stop belongs"
    )
    AdministrativeAreaRef: str = Field(
        ..., description="NPTG administrative area that manages stop data"
    )
    PlusbusZones: list[str] | None = Field(
        default=None, description="PlusbusZones that stop belongs to"
    )
    Notes: str | None = Field(default=None, description="Notes about a stop")
    Public: bool | None = Field(
        default=None,
        description="Whether stop is for use by the general public. Default is true",
    )
    StopAvailability: StopAvailabilityStructure | None = Field(
        default=None,
        description=(
            "Availability of stop for use. Note that the Status attribute on StopPoint "
            "should correspond with the StopValidity in effect at the ModificationDateTime. "
            "If no explicit stop validity is present, stop is assumed to have validity as "
            "indicated by Status attribute indefinitely"
        ),
    )
    CreationDateTime: datetime | None = Field(
        default=None, description="Creation date and time of the stop point"
    )
    ModificationDateTime: datetime | None = Field(
        default=None, description="Modification date and time of the stop point"
    )
    Modification: str | None = Field(
        default=None, description="Modification details of the stop point"
    )
    RevisionNumber: str | None = Field(
        default=None, description="Revision number of the stop point"
    )
    Status: str | None = Field(default=None, description="Status of the stop point")
