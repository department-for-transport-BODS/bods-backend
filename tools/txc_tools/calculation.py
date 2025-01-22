"""
Module to implement the functionality of different calculations used by TXC
tools
"""

from collections import defaultdict
from decimal import Decimal
from typing import IO

from lxml import etree

from .common import log, AnalysisMode
from .models import XMLTagInfo, XMLFileInfo, ZipStats, ZipTagStats


def calculate_zip_stats(
    xml_files: list[XMLFileInfo] | list[XMLTagInfo], mode: AnalysisMode
) -> dict[str, ZipStats | ZipTagStats]:
    """Calculate statistics for each zip file"""
    stats: dict[str, dict] = defaultdict(
        lambda: {"file_count": 0, "total_size": Decimal("0"), "total_tags": 0}
    )

    for xml_file in xml_files:
        zip_name = xml_file.parent_zip if xml_file.parent_zip else "root"
        stats[zip_name]["file_count"] += 1
        if mode == AnalysisMode.SIZE and isinstance(xml_file, XMLFileInfo):
            stats[zip_name]["total_size"] += xml_file.size_mb
        elif mode == AnalysisMode.TAG and isinstance(xml_file, XMLTagInfo):
            stats[zip_name]["total_tags"] += xml_file.tag_count

    if mode == AnalysisMode.SIZE:
        return {
            zip_name: ZipStats(
                zip_name=zip_name,
                file_count=data["file_count"],
                total_size_mb=data["total_size"].quantize(Decimal("0.01")),
            )
            for zip_name, data in stats.items()
        }
    if mode == AnalysisMode.TAG:
        return {
            zip_name: ZipTagStats(
                zip_name=zip_name,
                file_count=data["file_count"],
                total_tags=data["total_tags"],
            )
            for zip_name, data in stats.items()
        }

    log.error("Unsupported analysis mode", mode=mode)
    raise ValueError("Invalid Analysis Mode")


def count_tags_in_xml(xml_data: bytes, tag_name: str) -> int:
    """Count occurrences of a specific tag in XML content"""
    try:
        root = etree.fromstring(xml_data)
        return len(root.findall(f".//{tag_name}", namespaces=root.nsmap))
    except Exception as e:  # pylint: disable=broad-except
        log.error("Error parsing XML", error=str(e))
        return 0


def get_size_mb(file_obj: IO[bytes]) -> Decimal:
    """Calculate file size in megabytes using constant memory"""
    chunk_size = 8192  # 8KB chunks
    total_size = 0

    while chunk := file_obj.read(chunk_size):
        total_size += len(chunk)

    file_obj.seek(0)  # Reset file pointer
    return Decimal(str(total_size / (1024 * 1024))).quantize(Decimal("0.01"))
