"""
ServiceFrame
"""

from functools import cached_property
from typing import Annotated

from pydantic import BaseModel, Field, computed_field

from ..netex_types import LineTypeT
from ..netex_utility import MultilingualString, VersionedRef


class ScheduledStopPoint(BaseModel):
    """Definition of a scheduled stop point"""

    version: Annotated[str, Field(description="Version of the stop point")]
    id: Annotated[str, Field(description="Stop point identifier")]
    Name: Annotated[
        MultilingualString | str | None, Field(description="Name of the stop point")
    ] = None

    @computed_field
    @cached_property
    def atco_code(self) -> str | None:
        """
        Extracts the full ATCO code (everything after 'atco:').
        Returns None if the ID is invalid or doesn't follow the expected format.
        """
        if not self.id:
            return None

        if not self.id.startswith("atco:"):
            return None

        try:
            parts = self.id.split(":")
            if len(parts) != 2:
                return None
            code = parts[1]
        except IndexError:
            return None

        if not code:
            return None

        return code

    @computed_field
    @cached_property
    def atco_area_code(self) -> str | None:
        """
        Extracts the ATCO area code (first 3 digits) from the stop point ID.
        Returns None if the ID is invalid or doesn't follow the expected format.
        e.g.
            <ScheduledStopPoint id="atco:260014801">
        """
        atco = self.atco_code
        if not atco or len(atco) < 3:
            return None

        area_code = atco[:3]
        if not area_code.isnumeric():
            return None

        return area_code


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
    responsibilitySetRef: Annotated[
        str | None, Field(description="Reference to the responsibility set")
    ] = None
    dataSourceRef: Annotated[
        str | None, Field(description="Reference to the data source")
    ] = None

    # Children
    Description: Annotated[
        MultilingualString | str | None,
        Field(description="Description of the service frame", default=None),
    ]
    TypeOfFrameRef: Annotated[
        VersionedRef | None, Field(description="Reference to the type of frame")
    ]

    lines: Annotated[list[Line], Field(description="List of lines in the service")]

    scheduledStopPoints: Annotated[
        list[ScheduledStopPoint], Field(description="List of scheduled stop points")
    ]
