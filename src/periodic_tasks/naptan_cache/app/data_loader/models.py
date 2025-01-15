"""
Naptan Data Models
"""

from pydantic import BaseModel


class NaptanData(BaseModel):
    """
    Row Data fetched from NAPTAN Stops List
    """

    ATCOCode: str
    NaptanCode: str
    PlateCode: str
    CleardownCode: str
    CommonName: str
    CommonNameLang: str
    ShortCommonName: str
    ShortCommonNameLang: str
    Landmark: str
    LandmarkLang: str
    Street: str
    StreetLang: str
    Crossing: str
    CrossingLang: str
    Indicator: str
    IndicatorLang: str
    Bearing: str
    NptgLocalityCode: str
    LocalityName: str
    ParentLocalityName: str
    GrandParentLocalityName: str
    Town: str
    TownLang: str
    Suburb: str
    SuburbLang: str
    LocalityCentre: str
    GridType: str
    Easting: str
    Northing: str
    Longitude: str
    Latitude: str
    StopType: str
    BusStopType: str
    TimingStatus: str
    DefaultWaitTime: str
    Notes: str
    NotesLang: str
    AdministrativeAreaCode: str
    CreationDateTime: str
    ModificationDateTime: str
    RevisionNumber: str
    Modification: str
    Status: str
