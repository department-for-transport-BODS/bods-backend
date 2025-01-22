"""
Report module implements the function to generate the CSV files
"""

import csv
from pathlib import Path
from typing import cast, Type
from pydantic import BaseModel

from .calculation import calculate_zip_stats
from .common import log, AnalysisMode
from .models import XMLFileInfo, XMLTagInfo, ZipStats, ZipTagStats


def write_csv_reports(
    xml_files: list[XMLFileInfo] | list[XMLTagInfo],
    base_path: Path,
    mode: AnalysisMode,
    tag_name: str | None = None,
) -> None:
    """
    Write both detailed and summary CSV reports based on the report type (size or tag).
    """
    if not xml_files:
        raise ValueError("No XML files provided")

    if mode == AnalysisMode.SIZE:
        # Make pyright happy
        size_files = cast(list[XMLFileInfo], xml_files)
        # Sort XML files by size
        sorted_xml_files = sorted(size_files, key=lambda x: x.size_mb, reverse=True)
        detailed_path = base_path.with_name(f"{base_path.stem}_detailed.csv")

        stats = cast(dict[str, ZipStats], calculate_zip_stats(size_files, mode))
        sorted_stats = sorted(
            stats.values(), key=lambda x: x.total_size_mb, reverse=True
        )
        stats_path = base_path.with_name(f"{base_path.stem}_stats.csv")

        # Write detailed report
        write_detailed_report(
            sorted_xml_files=sorted_xml_files,
            detailed_path=detailed_path,
        )
        # Write statistics report
        write_stats_report(sorted_stats=sorted_stats, stats_path=stats_path)

    elif mode == AnalysisMode.TAG:
        # Make pyright happy
        tag_files = cast(list[XMLTagInfo], xml_files)
        # Sort XML files by tag count
        sorted_xml_files = sorted(tag_files, key=lambda x: x.tag_count, reverse=True)
        detailed_path = base_path.with_name(f"{base_path.stem}_{tag_name}_detailed.csv")

        stats = cast(dict[str, ZipTagStats], calculate_zip_stats(tag_files, mode))
        sorted_stats = sorted(stats.values(), key=lambda x: x.total_tags, reverse=True)
        stats_path = base_path.with_name(f"{base_path.stem}_{tag_name}_stats.csv")

        # Write detailed report
        write_detailed_report(
            sorted_xml_files=sorted_xml_files,
            detailed_path=detailed_path,
        )

        # Write statistics report
        write_stats_report(sorted_stats=sorted_stats, stats_path=stats_path)
    else:
        raise ValueError("Invalid Analysis Mode")

    log.info(
        "CSV reports generated", detailed_path=detailed_path, stats_path=stats_path
    )


def write_stats_report(
    sorted_stats: list[ZipStats] | list[ZipTagStats],
    stats_path: Path,
) -> None:
    """Write zip statistics report to CSV"""
    model_class = type(sorted_stats[0])
    headers = get_csv_headers(model_class)
    fields = get_fields(model_class)
    with open(stats_path, "w", newline="", encoding="utf-8") as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow(headers)
        for stat in sorted_stats:
            writer.writerow([str(getattr(stat, column, "")) for column in fields])


def write_detailed_report(
    sorted_xml_files: list[XMLFileInfo] | list[XMLTagInfo],
    detailed_path: Path,
) -> None:
    """Write detailed XML report to CSV"""
    model_class = type(sorted_xml_files[0])
    headers = get_csv_headers(model_class)
    fields = get_fields(model_class)
    with open(detailed_path, "w", newline="", encoding="utf-8") as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow(headers)
        for xml_file in sorted_xml_files:
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
    all_fields = {**model_cls.model_fields, **model_cls.model_computed_fields}
    return list(all_fields.keys())
