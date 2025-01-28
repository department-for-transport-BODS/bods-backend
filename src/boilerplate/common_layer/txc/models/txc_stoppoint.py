"""
TranXchange 2.4 PTI 1.1.A
Stop Point
"""

from datetime import date, datetime

from pydantic import BaseModel, Field, field_validator, model_validator

from .txc_types import BusStopTypeT, CompassPointT, TimingStatusT, TXCStopTypeT


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


class DescriptorStructure(BaseModel):
    """Structured text description of a stop."""

    CommonName: str = Field(
        ..., description="Common name for the stop in a specified language"
    )
    ShortCommonName: str | None = Field(
        default=None,
        description=(
            "Alternative short name for stop. Length limit is set by administrative "
            "area. Standard abbreviations should be used to condense name elements. "
            "If omitted, defaults to CommonName, truncated if necessary"
        ),
    )
    Landmark: str | None = Field(
        default=None,
        description=(
            "Description of the nearest landmark to the stop, for example 'Town Hall'. "
            "Or nearest street crossing that can be used to distinguish stop from "
            "other stops in the street, i.e. Landmark may be a crossing"
        ),
    )
    Street: str | None = Field(
        default=None, description="Street of stop. May be road name eg B2710"
    )
    Crossing: str | None = Field(
        default=None,
        description=(
            "Where there is a street that intersects the Street, as well as a "
            "Landmark, the name of the crossing street may be included separately here"
        ),
    )
    Indicator: str | None = Field(
        default=None,
        description=(
            "Indicative description of the relative position of the stop, for example, "
            "'100 yards from Town Hall'. Bay Stand or Stance number should be placed here"
        ),
    )


class NptgLocalityRefStructure(BaseModel):
    """Reference to an NPTG locality."""

    value: str = Field(..., description="NPTG locality code")
    lang: str | None = Field(default=None, description="Language of the locality name")


class LocationStructure(BaseModel):
    """Geospatial coordinates of a location."""

    Longitude: str | None = Field(default=None, description="Longitude of location")
    Latitude: str | None = Field(default=None, description="Latitude of location")
    Easting: str | None = Field(default=None, description="Easting of location")
    Northing: str | None = Field(default=None, description="Northing of location")

    @model_validator(mode="after")
    def check_sets(self):
        """
        Check if at least a pair of
           - logitude and latitude
           - easting or northing
        is set after instantiating
        """
        if not ((self.Longitude and self.Latitude) or (self.Easting and self.Northing)):
            raise ValueError(
                "At least a pair of (Longitude and Latitude) or (Easting and Northing) must be set"
            )
        return self


class PlaceStructure(BaseModel):
    """Place where a stop is located."""

    NptgLocalityRef: str = Field(
        ..., description="NPTG locality within which stop lies"
    )
    LocalityName: str | None = Field(
        default=None,
        description=(
            "Name of the locality. This is a derived value obtained from the NPTG "
            "Locality database. It is included in the StopPoint definition as an "
            "informative label for presenting the data. It should not be stored as "
            "stop data but rather should be fetched from the NPTG database using "
            "the NptgLocalityRef"
        ),
    )
    AlternativeNptgLocalities: list[NptgLocalityRefStructure] | None = Field(
        default=None, description="Additional NPTG localities within which stop lies"
    )
    MainNptgLocalities: list[NptgLocalityRefStructure] | None = Field(
        default=None,
        description=(
            "NPTG Localities for which the stop is a main interchange point, that is "
            "one of the main PTANs for accessing the network"
        ),
    )
    Suburb: str | None = Field(
        default=None, description="Suburb within which stop lies"
    )
    Town: str | None = Field(default=None, description="Town within which stop lies")
    LocalityCentre: bool | None = Field(
        default=None, description="Whether the locality is a centre or not"
    )
    Location: LocationStructure = Field(..., description="Spatial coordinates of stop")


class DateRangeStructure(BaseModel):
    """Date range with start and optional end date."""

    StartDate: date = Field(..., description="Start date of the date range")
    EndDate: date | None = Field(
        default=None,
        description=(
            "End date of the date range. If omitted, the range end is open-ended"
        ),
    )


class BearingStructure(BaseModel):
    """
    Compass Bearing
    """

    CompassPoint: CompassPointT = Field(
        ...,
        description="Eight point compass bearing (N, S, E, W etc). Enumerated value.",
    )


class MarkedPointStructure(BaseModel):
    """
    [BCT - MKD] Marked stop - for example a pole or a shelter. Point footprint.
    """

    Bearing: BearingStructure = Field(
        ...,
        description=(
            "Direction along street in which vehicle is pointing when stopped at stopping point."
        ),
    )


class UnmarkedPointStructure(BaseModel):
    """
    [BCT - CUS] Unmarked stop (or only marked on the road). Point footprint.
    """

    Bearing: BearingStructure = Field(
        ...,
        description=(
            "Direction along street in which vehicle is pointing when stopped at stopping point."
        ),
    )


class BusStopStructure(BaseModel):
    """
    Data type for Type of Bus Stop.
    Some stop types have required subelements.
    """

    BusStopType: BusStopTypeT = Field(
        ..., description="Legacy classification of bus stop sub type. Enumerated value."
    )
    TimingStatus: TimingStatusT = Field(
        ...,
        description=("Status of the registration of the bus stop as a timing point"),
    )
    MarkedPoint: MarkedPointStructure | None = Field(
        default=None,
        description="[BCT - MKD] Marked stop - for example a pole or a shelter. Point footprint.",
    )

    UnmarkedPoint: UnmarkedPointStructure | None = Field(
        default=None,
        description="Unmarked stop (or only marked on the road).",
    )

    @field_validator("BusStopType", mode="before")
    @classmethod
    def map_stop_type(cls, v: str):
        """
        Map BusStopType Codes
        Cases are:
          - Abbreviations to full names
        http/www.transxchange.org.uk/schema/2.4/napt/NaPT_stop-v2-4.xsd
        """
        stop_type_mapping = {
            "MKD": "marked",
            "HAR": "hailAndRide",
            "CUS": "custom",
            "FLX": "flexible",
        }

        # If it's a three-letter code, map it to the full name
        if v in stop_type_mapping:
            return stop_type_mapping[v]

        if v not in BusStopTypeT.__args__:
            raise ValueError(f"Invalid stop type: {v}")

        return v


class OnStreetStructure(BaseModel):
    """
    On Street Stop Information
    """

    Bus: BusStopStructure = Field(..., description="A bus, coach or tram stop.")


class StopClassificationStructure(BaseModel):
    """Classification of a stop."""

    StopType: TXCStopTypeT = Field(
        ...,
        description=(
            "Classification of the stop as one of the NaPTAN stop types. Enumerated value"
        ),
    )
    OnStreet: OnStreetStructure = Field(..., description="On street access point.")

    @field_validator("StopType", mode="before")
    @classmethod
    def map_stop_type(cls, v: str):
        """
        Map Stop Type Codes
        Cases are:
          - Abbreviations to full names
          - Deprecated values to new values
        http/www.transxchange.org.uk/schema/2.4/napt/NaPT_stop-v2-4.xsd
        """
        stop_type_mapping: dict[str, str] = {
            "BCT": "busCoachTrolleyOnStreetPoint",
            "BCS": "busCoachTrolleyStationBay",
            "BCQ": "busCoachTrolleyStationVariableBay",
            "BST": "busCoachTrolleyOnStreetPoint",
            "BCE": "busCoachTrolleyStationEntrance",
            "BCP": "busCoachTrolleyOnStreetPoint",
            "RPL": "railPlatform",
            "RLY": "railAccessArea",
            "RSE": "railStationEntrance",
            "PLT": "tramMetroUndergroundPlatform",
            "MET": "tramMetroUndergroundAccessArea",
            "TMU": "tramMetroUndergroundStationEntrance",
            "FER": "ferryDockAccessArea",
            "FTD": "ferryTerminalDockEntrance",
            "TXR": "taxiRank",
            "STR": "sharedTaxiRank",
            "AIR": "airportEntrance",
            "GAT": "airAccessArea",
            "busCoachTramStationEntrance": "busCoachTrolleyStationEntrance",
            "busCoachTramStationBay": "busCoachTrolleyStationBay",
            "busCoachTramStationVariableBay": "busCoachTrolleyStationBay",
            "busCoachTramOnStreetPoint": "busCoachTrolleyOnStreetPoint",
            "FerryBerth": "ferryBerth",
        }

        # If it's a three-letter code, map it to the full name
        if v in stop_type_mapping:
            return stop_type_mapping[v]
        # If it's already a full name, validate that it's in the TXCStopTypeT Literal
        if v not in TXCStopTypeT.__args__:
            raise ValueError(f"Invalid stop type: {v}")

        return v


class StopValidityStructure(BaseModel):
    """Validity period and status of a stop."""

    DateRange: DateRangeStructure = Field(
        ...,
        description=(
            "Validity period for which Active/Suspended or Transferred status applies. "
            "Each StartDate closes any previous open-ended date range of a previous "
            "validity element"
        ),
    )
    Active: bool | None = Field(
        default=None,
        description="Stop is active during the period defined by date range",
    )
    Suspended: bool | None = Field(
        default=None,
        description="Stop is suspended during the period specified by date range",
    )
    Transferred: str | None = Field(
        default=None,
        description=(
            "Stop is suspended during period specified by date range, and use is "
            "transferred to the indicated stop. Transference should not be cyclic"
        ),
    )
    Note: str | None = Field(
        default=None,
        description=(
            "Note explaining any reason for activation, transfer or suspension"
        ),
    )


class StopAvailabilityStructure(BaseModel):
    """Availability of a stop for use."""

    StopValidity: list[StopValidityStructure] = Field(
        ...,
        description=(
            "Description of periods for stop activity. Stop validity elements should "
            "be listed in historical order of Date Range Start date"
        ),
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
    def StopPointRef(self) -> str:
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
