"""
Report module implements the function to generate the CSV files
"""

import csv
from pathlib import Path
from typing import Any, Callable, List, Type, cast

from pydantic import BaseModel

from .calculation import calculate_zip_stats
from .common import ReportMode, log
from .models import XMLFileInfo, XMLTagInfo, ZipStats, ZipTagStats


def generate_xml_info_report(**kwargs: dict[str, Any]) -> None:
    """
    Generate report for XML tag info and size info
    """
    xml_files = kwargs.get("xml_files", [])
    assert isinstance(xml_files, list)

    base_path = kwargs.get("base_path")
    assert isinstance(base_path, Path)

    mode = kwargs.get("mode")
    assert isinstance(mode, ReportMode)

    xml_files = (
        cast(List[XMLFileInfo], xml_files)
        if mode == ReportMode.SIZE
        else cast(List[XMLTagInfo], xml_files)
    )
    sorted_xml_files = (
        sorted(
            [x for x in xml_files if isinstance(x, XMLFileInfo)],
            key=lambda x: x.size_mb,
            reverse=True,
        )
        if mode == ReportMode.SIZE
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
        if mode == ReportMode.SIZE
        else sorted(
            [item for item in stats.values() if isinstance(item, ZipTagStats)],
            key=lambda x: x.total_tags,
            reverse=True,
        )
    )
    tag_name = kwargs.get("tag_name", None)
    tag_name = f"_{tag_name}" if tag_name else ""
    detailed_path = base_path.with_name(f"{base_path.stem}{tag_name}_detailed.csv")
    stats_path = base_path.with_name(f"{base_path.stem}{tag_name}_stats.csv")
    # # Write detailed report
    # generate_csv_reports(
    #     xml_datas=sorted_xml_files,
    #     file_path=detailed_path,
    # )

    # # Write statistics report
    # generate_csv_reports(xml_datas=sorted_stats, file_path=stats_path)

    # Write detailed report
    generate_csv_reports(
        xml_datas=cast(List[BaseModel], sorted_xml_files),
        file_path=detailed_path,
    )

    # Write statistics report
    generate_csv_reports(
        xml_datas=cast(List[BaseModel], sorted_stats),
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
    tag_name = kwargs.get("tag_name", None)
    assert isinstance(base_path, Path)
    file_path = base_path.with_name(f"{base_path.stem}{tag_name}_inventory.csv")

    generate_csv_reports(
        xml_datas=cast(List[BaseModel], xml_files),
        file_path=file_path,
    )

    log.info("CSV reports generated", inventory_path=file_path)


REPORTS: dict[ReportMode, Callable[..., None]] = {
    ReportMode.SIZE: generate_xml_info_report,
    ReportMode.TAG: generate_xml_info_report,
    ReportMode.TXC: generate_xml_txc_report,
}


def write_csv_reports(**kwargs: dict[str, Any]) -> None:
    """
    Write both detailed and summary CSV reports based on the report type (size or tag).
    """

    if not kwargs.get("xml_files", []):
        raise ValueError("No XML files provided")

    mode = kwargs.get("mode")
    if not isinstance(mode, ReportMode):
        raise ValueError("Invalid mode provided. Expected a valid ReportMode instance.")

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
    all_fields = {**model_cls.model_fields, **model_cls.model_computed_fields}
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
    return list(model_cls.__fields__.keys())
