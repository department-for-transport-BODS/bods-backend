"""
FrameDefaults

Default Settings for a Frame

"""

from typing import Annotated

from pydantic import BaseModel, Field

from ..data_objects.netex_codespaces import CodespaceRef
from ..netex_utility import VersionedRef


class DefaultLocaleStructure(BaseModel):
    """Default locale settings"""

    TimeZoneOffset: Annotated[str | None, Field(description="Time zone offset")] = None
    TimeZone: Annotated[str | None, Field(description="Time zone")] = None
    SummerTimeZoneOffset: Annotated[
        str | None, Field(description="Summer time offset")
    ] = None
    SummerTimeZone: Annotated[str | None, Field(description="Summer time zone")] = None
    DefaultLanguage: Annotated[str | None, Field(description="Default language")] = None


class FrameDefaultsStructure(BaseModel):
    """Default values for the frame"""

    DefaultCodespaceRef: Annotated[
        CodespaceRef | None, Field(description="Default codespace reference")
    ] = None
    DefaultDataSourceRef: Annotated[
        VersionedRef | None, Field(description="Default data source reference")
    ] = None
    DefaultResponsibilitySetRef: Annotated[
        VersionedRef | None, Field(description="Default responsibility set reference")
    ] = None
    DefaultLocale: Annotated[
        DefaultLocaleStructure | None, Field(description="Default locale settings")
    ] = None
    DefaultLocationSystem: Annotated[
        str | None, Field(description="Default location system")
    ] = None
    DefaultSystemOfUnits: Annotated[
        str | None, Field(description="Default system of units")
    ] = None
    DefaultCurrency: Annotated[
        str | None, Field(description="Default currency for the frame")
    ] = None
