"""
ServiceFrame
"""

from typing import Annotated

from pydantic import BaseModel, Field

from ..netex_types import LineTypeT
from ..netex_utility import MultilingualString, VersionedRef


class ScheduledStopPoint(BaseModel):
    """Definition of a scheduled stop point"""

    version: Annotated[str, Field(description="Version of the stop point")]
    id: Annotated[str, Field(description="Stop point identifier")]
    Name: Annotated[
        MultilingualString | str | None, Field(description="Name of the stop point")
    ] = None


class Line(BaseModel):
    """Definition of a transport line"""

    version: Annotated[str, Field(description="Version of the line")]
    id: Annotated[str, Field(description="Line identifier")]
    Name: Annotated[MultilingualString | str, Field(description="Name of the line")]
    Description: Annotated[
        MultilingualString | str | None,
        Field(description="Description of the line", default=None),
    ] = None
    PublicCode: Annotated[str | None, Field(description="Public facing line code")] = (
        None
    )
    PrivateCode: Annotated[str | None, Field(description="Internal line code")] = None
    OperatorRef: Annotated[
        VersionedRef | None,
        Field(description="Reference to the operator running the line"),
    ] = None
    LineType: Annotated[
        LineTypeT | None,
        Field(description="Type of the line service"),
    ] = None


class ServiceFrame(BaseModel):
    """
    A frame containing service-related definitions including lines
    and scheduled stop points
    """

    # Attributes
    version: Annotated[str, Field(description="Version of the service frame")]
    id: Annotated[str, Field(description="Service frame identifier")]
    dataSourceRef: Annotated[
        str | None, Field(description="Reference to the data source")
    ] = None
    responsibilitySetRef: Annotated[
        str | None, Field(description="Reference to the responsibility set")
    ] = None

    # Children
    Description: Annotated[
        MultilingualString | str | None,
        Field(description="Description of the service frame", default=None),
    ]
    TypeOfFrameRef: Annotated[
        VersionedRef, Field(description="Reference to the type of frame")
    ]

    lines: Annotated[list[Line], Field(description="List of lines in the service")]

    scheduledStopPoints: Annotated[
        list[ScheduledStopPoint], Field(description="List of scheduled stop points")
    ]
