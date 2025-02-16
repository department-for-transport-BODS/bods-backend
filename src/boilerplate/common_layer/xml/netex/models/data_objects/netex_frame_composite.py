"""
dataObject Models
"""

from typing import Annotated

from pydantic import BaseModel, Field

from ..netex_utility import FromToDate, MultilingualString, VersionedRef
from .netex_codespaces import Codespace, CodespaceRef
from .netex_frame_resource import ResourceFrame
from .netex_frame_service import ServiceFrame


class FrameDefaultsStructure(BaseModel):
    """
    Default values for the frame
    """

    DefaultCodespaceRef: Annotated[
        CodespaceRef | None, Field(description="Default codespace reference")
    ] = None
    DefaultDataSourceRef: Annotated[
        VersionedRef | None, Field(description="Default data source reference")
    ] = None
    DefaultCurrency: Annotated[
        str | None, Field(description="Default currency for the frame")
    ] = None


class CompositeFrame(BaseModel):
    """
    A grouping of frames
    """

    # Attributes
    version: Annotated[str, Field(description="Version")]
    id: Annotated[str, Field(description="Id")]
    dataSourceRef: Annotated[str, Field(description="Id")]
    responsibilitySetRef: Annotated[str, Field(description="Id")]

    # Children
    ValidBetween: Annotated[FromToDate, Field(description="Validity")]
    Name: Annotated[MultilingualString | str, Field(description="Name of the frame")]
    Description: Annotated[
        MultilingualString | str | None,
        Field(description="Description of the frame", default=None),
    ]
    TypeOfFrameRef: Annotated[VersionedRef | None, Field(description="")]

    codespaces: Annotated[
        list[CodespaceRef | Codespace],
        Field(description="list of codespace references"),
    ]
    FrameDefaults: Annotated[
        FrameDefaultsStructure | None, Field(description="Default values for the frame")
    ] = None
    frames: Annotated[
        list[ResourceFrame | ServiceFrame],
        Field(description="list of contained frames"),
    ]
