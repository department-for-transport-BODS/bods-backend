"""
ResourceFrame
"""

from typing import Annotated

from pydantic import BaseModel, Field

from ..netex_utility import MultilingualString, VersionedRef
from .netex_codespaces import Codespace, CodespaceRef


class DataSource(BaseModel):
    """Data source definition"""

    id: Annotated[str, Field(description="Data source identifier")]
    version: Annotated[str, Field(description="Version of the data source")]
    Email: Annotated[
        str | None, Field(description="Contact email for the data source")
    ] = None


class Operator(BaseModel):
    """Operator definition"""

    id: Annotated[str, Field(description="Operator identifier")]
    version: Annotated[str, Field(description="Version")]
    PublicCode: Annotated[
        str | None, Field(description="Public facing operator code")
    ] = None
    Name: Annotated[
        MultilingualString | None, Field(description="Name of the operator")
    ] = None


class ResourceFrame(BaseModel):
    """
    A frame containing resource definitions like codespaces, data sources,
    and organizations
    """

    # Attributes
    version: Annotated[str, Field(description="Version of the resource frame")]
    id: Annotated[str, Field(description="Resource frame identifier")]
    dataSourceRef: Annotated[
        str | None, Field(description="Reference to the data source")
    ] = None
    responsibilitySetRef: Annotated[
        str | None, Field(description="Reference to the responsibility set")
    ] = None

    # Children
    Name: Annotated[
        MultilingualString | str | None, Field(description="Name of the resource frame")
    ]
    TypeOfFrameRef: Annotated[
        VersionedRef | None, Field(description="Reference to the type of frame")
    ] = None

    codespaces: Annotated[
        list[CodespaceRef | Codespace],
        Field(description="list of codespace definitions"),
    ]

    dataSources: Annotated[
        list[DataSource],
        Field(description="list of data sources"),
    ]

    organisations: Annotated[
        list[Operator], Field(description="list of operators and other organizations")
    ]
