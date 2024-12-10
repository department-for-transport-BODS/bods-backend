"""
TXC Serviced Organisation Models
"""

from datetime import date, datetime

from pydantic import BaseModel, Field

from .txc_types import ModificationType, ServiceOrganisationClassificationT, StatusT


class TXCServicedOrganisationDatePattern(BaseModel):
    """
    Used for WorkingDays and Holidays
    Working days should not overlap with any holidays;
    """

    StartDate: date = Field(..., description="Inclusive of Start Date")
    EndDate: date = Field(..., description="Inclusive of End Date")
    Description: str | None = Field(default=None, description="Context of the range")
    Provisional: bool = Field(
        default=False,
        description="Whether date is provisional or firm. Default is firm (false).",
    )


class TXCServicedOrganisationAnnotatedNptgLocalityRef(BaseModel):
    """
    NPTG locality within which ServicedOrganisation falls.
    Used to associate a specific site with a specific locality
    """

    NptgLocalityRef: str = Field(
        ...,
        description="Unique identifier of the locality.",
        pattern=r"^[EN][0S][0-9]{6}$",
    )
    LocalityName: str | None = Field(default=None, description="")
    LocalityQualifier: str | None = Field(default=None, description="")


class TXCServicedOrganisation(BaseModel):
    """
    An organisation referenced by a bus schedule
    for which specific working days and holidays may be defined.
    """

    # Attributes
    CreationDateTime: datetime | None = Field(
        default=None, description="Creation date and time of the stop point"
    )
    ModificationDateTime: datetime | None = Field(
        default=None, description="Modification date and time of the stop point"
    )
    Modification: ModificationType | None = Field(
        default=None, description="Modification details of the stop point"
    )
    RevisionNumber: int | None = Field(default=None, description="Revision number ")
    Status: StatusT | None = Field(default=None, description="Status of the stop point")
    # Tags
    OrganisationCode: str = Field(
        ...,
        description=(
            "Identifying code for the serviced organisation. "
            "In the case of LEAs and Schools, this should be the Department of Education Number."
        ),
    )
    PrivateCode: str | None = Field(
        default=None,
        description="Alternative Code for legacy compatibility",
    )
    Name: str | None = Field(
        default=None,
        description=("Organisation Name"),
    )
    ServicedOrganisationClassification: ServiceOrganisationClassificationT | None = (
        Field(
            default=None,
            description=("Nature of an organisation" "For which the nature will vary"),
        )
    )
    WorkingDays: list[TXCServicedOrganisationDatePattern] | None = Field(
        default=None,
        description=(
            "The working days of the ServicedOrganisation, for example a LEA's terms"
            "Pattern of days when the serviced organisation is open."
            "Working days should not overlap with any holidays;"
            "if they do, the latter will be used in preference."
        ),
    )
    Holidays: list[TXCServicedOrganisationDatePattern] | None = Field(
        default=None,
        description=(
            "Pattern of days when the serviced organisation is closed."
            "Working days should not overlap with any holidays;"
            "if they do, the latter will be used in preference."
            "Not allowed in PTI"
        ),
    )
    ParentServicedOrganisationRef: str | None = Field(
        default=None,
        description=(
            "Another ServicedOrganisation that is parent to this organisation. "
            "For Educational establishments, can be used to reference the LEA. "
            "The Working Days and Holidays of the referenced Organisation will be inherited,"
            "except where explicitly overridden by the child Organisation."
            "Cyclic references are not allowed."
        ),
    )
    AdministrativeAreaRef: str | None = Field(
        default=None,
        description="NPTG administrative area that manages stop data",
        pattern=r"^[0-9]{3}$",
    )
    AnnotatedNptgLocalityRef: TXCServicedOrganisationAnnotatedNptgLocalityRef | None = (
        Field(
            default=None,
            description="NPTG locality within which ServicedOrganisation falls. ",
        )
    )
    LocalEducationAuthorityRef: str | None = Field(
        default=None,
        description="NPTG Administrative Area within which organisation falls",
    )
