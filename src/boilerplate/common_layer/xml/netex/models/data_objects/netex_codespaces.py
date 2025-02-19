"""
Codespaces
"""

from typing import Annotated

from pydantic import BaseModel, Field

from ..netex_utility import MultilingualString


class CodespaceRef(BaseModel):
    """Reference to a codespace"""

    ref: Annotated[str, Field(description="Reference to codespace")]


class Codespace(BaseModel):
    """Full codespace definition"""

    id: Annotated[str, Field(description="Codespace identifier")]
    Xmlns: Annotated[str, Field(description="XML namespace")]
    XmlnsUrl: Annotated[str | None, Field(description="XML namespace URL")] = None
    Description: Annotated[
        MultilingualString | str | None,
        Field(description="Description of the codespace", default=None),
    ]
