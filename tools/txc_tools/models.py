"""
Model definitions for txc tools
"""

import queue
import zipfile
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass
from datetime import date
from decimal import Decimal
from enum import Enum

from pydantic import BaseModel, ConfigDict, Field, computed_field


class XMLFileInfo(BaseModel):
    """Pydantic model for XML file information"""

    model_config = ConfigDict(frozen=True)
    file_path: str = Field(
        ..., title="File Path", description="Path to the XML file within the zip"
    )
    size_mb: Decimal = Field(
        ...,
        title="Size (MB)",
        description="Size of the XML file in megabytes",
        decimal_places=2,
    )
    parent_zip: str | None = Field(
        None, title="Parent Zip", description="Name of the parent zip file if nested"
    )


class XMLSearchResult(BaseModel):
    """Model for XML search results."""

    parent_zip: str | None = Field(
        None, title="Parent Zip", description="Name of the parent zip file if nested"
    )
    file_path: str = Field(
        ..., title="File Path", description="Path to the XML file within the zip"
    )
    path_found: bool = Field(
        default=True,
        title="Tag Path Found",
        description="Always True when included in results",
    )
    element_tag: str = Field(title="Name", description="Tag name of the found element")
    has_child: bool | None = Field(
        default=None, title="Has Child", description="Whether specified child exists"
    )
    identifier: str | None = Field(
        default=None, title="Indentifier", description="Identifier value if found"
    )


class XMLTagInfo(BaseModel):
    """Pydantic model for XML tag count information"""

    model_config = ConfigDict(frozen=True)

    file_path: str = Field(
        ..., title="File Path", description="Path to the XML file within the zip"
    )
    tag_count: int = Field(
        ..., title="Tag Count", description="Number of occurrences of the specified tag"
    )
    parent_zip: str | None = Field(
        None, title="Parent Zip", description="Name of the parent zip file if nested"
    )


class ZipStats(BaseModel):
    """Pydantic model for zip file statistics"""

    model_config = ConfigDict(frozen=True)

    zip_name: str = Field(..., title="Zip Names", description="Name of the zip file")
    file_count: int = Field(
        ...,
        title="Number of Files in Zip",
        ge=0,
        description="Number of XML files in the zip",
    )
    total_size_mb: Decimal = Field(
        ...,
        title="Total Size of XMLs in Zip (MB)",
        description="Total size of all XMLs in megabytes",
        decimal_places=2,
    )

    @computed_field(
        return_type=Decimal, alias="avg_file_size_mb", title="Average File Size (MB)"
    )
    def avg_file_size_mb(self) -> Decimal:
        """Average size of XML files in the zip"""
        if self.file_count == 0:
            return Decimal("0")
        return (self.total_size_mb / self.file_count).quantize(Decimal("0.01"))


class ZipTagStats(BaseModel):
    """Pydantic model for zip file tag statistics"""

    model_config = ConfigDict(frozen=True)

    zip_name: str = Field(..., title="Zip Names", description="Name of the zip file")
    file_count: int = Field(
        ...,
        ge=0,
        title="Number of Files with Tag",
        description="Number of files containing the tag",
    )
    total_tags: int = Field(
        ...,
        title="Total Tag Occurrences",
        description="Total number of tag occurrences",
    )


class AnalysisMode(str, Enum):
    """Type of file processing"""

    SIZE = "size"
    TAG = "tag"
    TXC = "txc"
    SEARCH = "search"


@dataclass
class XmlTagLookUpInfo:
    """
    Tag search details
    """

    tag_name: str | None = None
    search_path: str | None = None
    id_elements: list[str] | None = None


@dataclass
class WorkerConfig:
    """
    Worker configuration
    """

    zip_ref: zipfile.ZipFile
    file_list: list[zipfile.ZipInfo]
    xml_queue: queue.Queue
    future_queue: queue.Queue
    executor: ThreadPoolExecutor
    mode: AnalysisMode
    lookup_info: XmlTagLookUpInfo | None = None


class XmlTxcInventory(BaseModel):
    """Pydantic model for txc inventory"""

    model_config = ConfigDict(frozen=True)

    national_operator_code: str | None = Field(
        None, title="National Operator Code", description="National Operator Code"
    )
    operator_short_name: str | None = Field(
        None, title="Operator Short Name", description="Operator Short Name"
    )
    line_name: str | None = Field(None, title="Line Name", description="Line Name")
    service_code: str | None = Field(
        None, title="Service Code", description="Service Code"
    )
    out_bound_description: str | None = Field(
        None, title="Outbound Description", description="Outbound Description"
    )
    in_bound_description: str | None = Field(
        None, title="Inbound Description", description="Inbound Description"
    )
    total_stop_points: int | None = Field(
        None, title="Total Stop Points", description="Total Stop Points"
    )
    custom_stop_points: int | None = Field(
        None, title="Custom Stop Points", description="Number of custom stop points"
    )
    route_sections: int | None = Field(
        None, title="Route Sections", description="Number of route sections"
    )
    routes: int | None = Field(None, title="Routes", description="Routes")
    journey_pattern_sections: int | None = Field(
        None, title="Journey Pattern Sections", description="Journey Pattern Sections"
    )
    vehicle_journeys: int | None = Field(
        None, title="Vehicle Journeys", description="Vehicle Journeys"
    )
    file_path: str = Field(
        ..., title="File Path", description="Path to the XML file within the zip"
    )
    service_start_date: date | None = Field(
        None, title="Service Start Date", description="Service Start Date"
    )
    service_end_date: date | None = Field(
        None, title="Service End Date", description="Service End Date"
    )
    event_service: int | str | None = Field(
        None, title="Event Service", description="Event Service"
    )
    txc_parser: str | None = Field(
        None, title="TxC Parser", description="TxC parser exception"
    )
