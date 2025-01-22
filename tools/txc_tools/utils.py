"""
Helper Functions
"""

from decimal import Decimal
from typing import IO

from lxml import etree
from structlog.stdlib import get_logger

log = get_logger()


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
