"""
CSV Output Functions
"""

import csv
from pathlib import Path
from typing import Type, cast, Any, Callable

from pydantic import BaseModel
from pydantic.fields import ComputedFieldInfo, FieldInfo
from structlog.stdlib import get_logger

from .models import (
    AnalysisMode,
    XMLFileInfo,
    XMLTagInfo,
    ZipStats,
    ZipTagStats,
    XmlTagLookUpInfo,
)
from .utils import calculate_zip_stats

log = get_logger()


def generate_xml_info_report(**kwargs: dict[str, Any]) -> None:
    """
    Generate report for XML tag info and size info
    """
    xml_files = kwargs.get("xml_files", [])
    assert isinstance(xml_files, list)

    base_path = kwargs.get("base_path")
    assert isinstance(base_path, Path)

    mode = kwargs.get("mode")
    assert isinstance(mode, AnalysisMode)

    xml_files = (
        cast(list[XMLFileInfo], xml_files)
        if mode == AnalysisMode.SIZE
        else cast(list[XMLTagInfo], xml_files)
    )
    sorted_xml_files = (
        sorted(
            [x for x in xml_files if isinstance(x, XMLFileInfo)],
            key=lambda x: x.size_mb,
            reverse=True,
        )
        if mode == AnalysisMode.SIZE
        else sorted(
            [x for x in xml_files if isinstance(x, XMLTagInfo)],
            key=lambda x: x.tag_count,
            reverse=True,
        )
    )
    stats = calculate_zip_stats(sorted_xml_files, mode)
    sorted_stats = (
        sorted(
            [item for item in stats.values() if isinstance(item, ZipStats)],
            key=lambda x: x.total_size_mb,
            reverse=True,
        )
        if mode == AnalysisMode.SIZE
        else sorted(
            [item for item in stats.values() if isinstance(item, ZipTagStats)],
            key=lambda x: x.total_tags,
            reverse=True,
        )
    )

    lookup_details = kwargs.get("lookup_info")
    assert isinstance(lookup_details, XmlTagLookUpInfo)

    tag_name = lookup_details.tag_name if lookup_details else None
    tag_name = f"_{tag_name}" if tag_name else ""
    detailed_path = base_path.with_name(f"{base_path.stem}{tag_name}_detailed.csv")
    stats_path = base_path.with_name(f"{base_path.stem}{tag_name}_stats.csv")

    # Write detailed report
    generate_csv_reports(
        xml_datas=cast(list[BaseModel], sorted_xml_files),
        file_path=detailed_path,
    )

    # Write statistics report
    generate_csv_reports(
        xml_datas=cast(list[BaseModel], sorted_stats),
        file_path=stats_path,
    )

    log.info(
        "CSV reports generated", detailed_path=detailed_path, stats_path=stats_path
    )


def generate_xml_txc_report(**kwargs: dict[str, Any]) -> None:
    """
    Generate report for XML TxC data
    """
    xml_files = kwargs.get("xml_files", [])
    base_path = kwargs.get("base_path")
    assert isinstance(base_path, Path)
    file_path = base_path.with_name(f"{base_path.stem}_inventory.csv")

    generate_csv_reports(
        xml_datas=cast(list[BaseModel], xml_files),
        file_path=file_path,
    )

    log.info("CSV reports generated", inventory_path=file_path)


def generate_xml_tag_with_parent_report(**kwargs: dict[str, Any]) -> None:
    """
    Generate report for XML tag with parent report
    """
    xml_files = kwargs.get("xml_files", [])
    base_path = kwargs.get("base_path")

    assert isinstance(base_path, Path)

    search_details = kwargs.get("lookup_info")
    assert isinstance(search_details, XmlTagLookUpInfo)
    assert search_details.tag_name
    assert search_details.search_path

    tag_name = f"_{search_details.tag_name}"
    search_path = search_details.search_path.split(":")[-1]
    search_path = f"_{search_path}"

    file_path = base_path.with_name(f"{base_path.stem}{tag_name}{search_path}.csv")

    generate_csv_reports(
        xml_datas=cast(list[BaseModel], xml_files),
        file_path=file_path,
    )

    log.info("CSV reports generated", inventory_path=file_path)


REPORTS: dict[AnalysisMode, Callable[..., None]] = {
    AnalysisMode.SIZE: generate_xml_info_report,
    AnalysisMode.TAG: generate_xml_info_report,
    AnalysisMode.TXC: generate_xml_txc_report,
    AnalysisMode.TAG_PARENT_CHILD: generate_xml_tag_with_parent_report,
}


def write_csv_reports(**kwargs: dict[str, Any]) -> None:
    """
    Write both detailed and summary CSV reports based on the report type (size or tag).
    """

    if not kwargs.get("xml_files", []):
        raise ValueError("No XML files provided")

    mode = kwargs.get("mode")
    if not isinstance(mode, AnalysisMode):
        raise ValueError(
            "Invalid mode provided. Expected a valid AnalysisMode instance."
        )

    report_func = REPORTS.get(mode)
    if report_func is None:
        raise ValueError(f"No report function available for the mode: {mode}")

    report_func(**kwargs)


def generate_csv_reports(xml_datas: list[BaseModel], file_path: Path) -> None:
    """
    Generate CSV reports.
    """
    if not xml_datas:
        raise ValueError("xml_datas must not be empty")

    model_class = type(xml_datas[0])
    headers = get_csv_headers(model_class)
    fields = get_fields(model_class)
    with open(file_path, "w", newline="", encoding="utf-8") as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow(headers)
        for xml_file in xml_datas:
            writer.writerow([str(getattr(xml_file, column, "")) for column in fields])


def get_csv_headers(model_cls: Type[BaseModel]) -> list[str]:
    """Extract CSV headers from field titles"""
    headers: list[str] = []
    all_fields: dict[str, FieldInfo | ComputedFieldInfo] = {
        **model_cls.model_fields,
        **model_cls.model_computed_fields,
    }
    for field_name, field in all_fields.items():
        if field.title:
            headers.append(field.title)
        elif field.description:
            headers.append(field.description)
        else:
            headers.append(field_name)
    return headers


def get_fields(model_cls: Type[BaseModel]) -> list[str]:
    """
    Extract fields from data model
    """
    all_fields = {**model_cls.model_fields, **model_cls.model_computed_fields}
    return list(all_fields.keys())
