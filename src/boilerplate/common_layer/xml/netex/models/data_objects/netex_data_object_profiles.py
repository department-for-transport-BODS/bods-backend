"""
Profiles for Users
"""

from typing import Annotated

from pydantic import BaseModel, Field

from ..netex_utility import MultilingualString, VersionedRef


class CompanionProfile(BaseModel):
    """Definition of a companion profile"""

    id: Annotated[str, Field(description="Profile identifier")]
    version: Annotated[str, Field(description="Version")]
    UserProfileRef: Annotated[
        VersionedRef | None, Field(description="Reference to user profile")
    ]
    MinimumNumberOfPersons: Annotated[
        int | None, Field(description="Minimum number of companions")
    ]
    MaximumNumberOfPersons: Annotated[
        int | None, Field(description="Maximum number of companions")
    ]
    DiscountBasis: Annotated[
        str | None, Field(description="Basis for discount", default=None)
    ]


class UserProfile(BaseModel):
    """Definition of a user profile"""

    id: Annotated[str, Field(description="Profile identifier")]
    version: Annotated[str, Field(description="Version")]
    Name: Annotated[MultilingualString | str, Field(description="Name of the profile")]
    Description: Annotated[
        MultilingualString | str | None,
        Field(description="Description of the profile", default=None),
    ] = None
    TypeOfConcessionRef: Annotated[
        VersionedRef | None, Field(description="Reference to concession type")
    ] = None
    MinimumAge: Annotated[
        int | None, Field(description="Minimum age", default=None)
    ] = None
    MaximumAge: Annotated[
        int | None, Field(description="Maximum age", default=None)
    ] = None
    ProofRequired: Annotated[
        str | None, Field(description="Required proof", default=None)
    ] = None
    DiscountBasis: Annotated[
        str | None, Field(description="Basis for discount", default=None)
    ] = None
    companionProfiles: Annotated[
        list[CompanionProfile] | None,
        Field(description="list of companion profiles", default=None),
    ] = None
