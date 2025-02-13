"""
dataObject Models
"""

from typing import Annotated, Literal

from pydantic import BaseModel, Field

from ..netex_utility import FromToDate, MultilingualString, VersionedRef


class CodespaceRef(BaseModel):
    """Reference to a codespace"""

    ref: Annotated[str, Field(description="Reference to codespace")]


class Codespace(BaseModel):
    """Full codespace definition"""

    id: Annotated[str, Field(description="Codespace identifier")]
    Xmlns: Annotated[str, Field(description="XML namespace")]
    Description: Annotated[
        MultilingualString | str | None,
        Field(description="Description of the codespace", default=None),
    ]


class FrameDefaults(BaseModel):
    """Default values for the frame"""

    DefaultCodespaceRef: Annotated[
        CodespaceRef, Field(description="Default codespace reference")
    ]
    DefaultDataSourceRef: Annotated[
        VersionedRef, Field(description="Default data source reference")
    ]
    DefaultCurrency: Annotated[str, Field(description="Default currency for the frame")]


class DataSource(BaseModel):
    """Data source definition"""

    id: Annotated[str, Field(description="Data source identifier")]
    version: Annotated[str, Field(description="Version of the data source")]
    Email: Annotated[str, Field(description="Contact email for the data source")]


class Operator(BaseModel):
    """Operator definition"""

    id: Annotated[str, Field(description="Operator identifier")]
    version: Annotated[str, Field(description="Version")]
    PublicCode: Annotated[str, Field(description="Public facing operator code")]
    Name: Annotated[str, Field(description="Name of the operator")]


class ResourceFrame(BaseModel):
    """
    A frame containing resource definitions like codespaces, data sources,
    and organizations
    """

    # Attributes
    version: Annotated[str, Field(description="Version of the resource frame")]
    id: Annotated[str, Field(description="Resource frame identifier")]
    dataSourceRef: Annotated[str, Field(description="Reference to the data source")]
    responsibilitySetRef: Annotated[
        str, Field(description="Reference to the responsibility set")
    ]

    # Children
    Name: Annotated[
        MultilingualString | str, Field(description="Name of the resource frame")
    ]
    TypeOfFrameRef: Annotated[
        VersionedRef, Field(description="Reference to the type of frame")
    ]

    codespaces: Annotated[
        list[Codespace], Field(description="list of codespace definitions")
    ]

    dataSources: Annotated[
        list[DataSource],
        Field(description="list of data sources"),
    ]

    organisations: Annotated[
        list[Operator], Field(description="list of operators and other organizations")
    ]


class Line(BaseModel):
    """Definition of a transport line"""

    version: Annotated[str, Field(description="Version of the line")]
    id: Annotated[str, Field(description="Line identifier")]
    Name: Annotated[MultilingualString | str, Field(description="Name of the line")]
    Description: Annotated[
        MultilingualString | str | None,
        Field(description="Description of the line", default=None),
    ]
    PublicCode: Annotated[str, Field(description="Public facing line code")]
    PrivateCode: Annotated[str, Field(description="Internal line code")]
    OperatorRef: Annotated[
        VersionedRef, Field(description="Reference to the operator running the line")
    ]
    LineType: Annotated[
        Literal["local", "regional", "national"],
        Field(description="Type of the line service"),
    ]


class ScheduledStopPoint(BaseModel):
    """Definition of a scheduled stop point"""

    version: Annotated[str, Field(description="Version of the stop point")]
    id: Annotated[str, Field(description="Stop point identifier")]
    Name: Annotated[
        MultilingualString | str, Field(description="Name of the stop point")
    ]


class ServiceFrame(BaseModel):
    """
    A frame containing service-related definitions including lines
    and scheduled stop points
    """

    # Attributes
    version: Annotated[str, Field(description="Version of the service frame")]
    id: Annotated[str, Field(description="Service frame identifier")]
    dataSourceRef: Annotated[str, Field(description="Reference to the data source")]
    responsibilitySetRef: Annotated[
        str, Field(description="Reference to the responsibility set")
    ]

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
        FrameDefaults, Field(description="Default values for the frame")
    ]
    frames: Annotated[
        list[ResourceFrame | ServiceFrame],
        Field(description="list of contained frames"),
    ]
