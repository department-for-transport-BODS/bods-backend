"""
FareTable Models
"""

from __future__ import annotations

from typing import Annotated

from pydantic import BaseModel, Field

from ..netex_references import ObjectReferences, PricableObjectRefs
from ..netex_utility import MultilingualString, VersionedRef


class FareTableColumn(BaseModel):
    """Definition of a fare table column"""

    id: Annotated[str, Field(description="Column identifier")]
    version: Annotated[str, Field(description="Version")]
    order: Annotated[str | None, Field(description="Column order")] = None
    Name: Annotated[MultilingualString | str, Field(description="Column name")]
    representing: Annotated[
        ObjectReferences | None,
        Field(description="References for what this column represents"),
    ] = None


class FareTableRow(BaseModel):
    """Definition of a fare table row"""

    id: Annotated[str, Field(description="Row identifier")]
    version: Annotated[str, Field(description="Version")]
    order: Annotated[str, Field(description="Row order")]
    Name: Annotated[MultilingualString, Field(description="Row name")]


class DistanceMatrixElementPrice(BaseModel):
    """Definition of a distance matrix element price"""

    id: Annotated[str, Field(description="Price identifier")]
    version: Annotated[str, Field(description="Version")]
    GeographicalIntervalPriceRef: Annotated[
        VersionedRef | None,
        Field(description="Reference to geographical interval price"),
    ] = None
    DistanceMatrixElementRef: Annotated[
        VersionedRef | None, Field(description="Reference to distance matrix element")
    ] = None


class Cell(BaseModel):
    """Definition of a fare table cell"""

    id: Annotated[str, Field(description="Cell identifier")]
    version: Annotated[str, Field(description="Version")]
    order: Annotated[str, Field(description="Cell order")]
    DistanceMatrixElementPrice: Annotated[
        DistanceMatrixElementPrice, Field(description="Price for this cell")
    ]
    ColumnRef: Annotated[
        VersionedRef | None, Field(description="Reference to column")
    ] = None
    RowRef: Annotated[VersionedRef | None, Field(description="Reference to row")] = None


class FareTable(BaseModel):
    """Definition of a fare table"""

    id: Annotated[str, Field(description="Table identifier")]
    version: Annotated[str, Field(description="Version")]
    Name: Annotated[MultilingualString | str, Field(description="Table name")]
    Description: Annotated[
        MultilingualString | str | None,
        Field(description="Table description", default=None),
    ]
    pricesFor: Annotated[
        PricableObjectRefs | None,
        Field(description="References for what these prices are for"),
    ] = None
    usedIn: Annotated[
        dict[str, VersionedRef],
        Field(description="References for where these prices are used"),
    ]
    specifics: Annotated[
        dict[str, VersionedRef], Field(description="Specific references for this table")
    ]
    columns: Annotated[
        list[FareTableColumn], Field(description="list of columns in this table")
    ]
    rows: Annotated[list[FareTableRow], Field(description="list of rows in this table")]
    includes: Annotated[
        list[FareTable], Field(description="list of nested fare tables")
    ]
