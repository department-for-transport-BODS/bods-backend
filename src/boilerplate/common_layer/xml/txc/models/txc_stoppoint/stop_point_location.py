"""
Location / Place
"""

from pydantic import BaseModel, Field, model_validator


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
