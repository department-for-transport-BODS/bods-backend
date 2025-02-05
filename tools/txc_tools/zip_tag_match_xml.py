"""
Module to support the functionality to zip the xml when tag matches.
"""

from collections import defaultdict
from io import BytesIO
from pathlib import Path
from typing import Any
import zipfile
from pydantic import BaseModel
from structlog.stdlib import get_logger

from .models import AnalysisMode

log = get_logger()


def get_nested_zip_xml(
    src_zip: zipfile.ZipFile, nested_zip_name: str, xml_files: set[str]
):
    """
    Extracts and filters XML files from a nested ZIP
    inside the main ZIP, returning a new ZIP in memory.
    """
    log.info("Extracting XML files from zip", name=nested_zip_name)
    nested_zip_data = BytesIO(src_zip.read(nested_zip_name))
    with zipfile.ZipFile(nested_zip_data, "r") as nested_src_zip:
        for file_info in nested_src_zip.infolist():
            if not file_info.is_dir() and file_info.filename in xml_files:
                # Read the file from the original nested ZIP
                with nested_src_zip.open(file_info.filename) as file:
                    yield file_info.filename, file.read()


def generate_zip_file_structure(**kwargs: dict[str, Any]) -> None:
    """
    Managing and generating a ZIP file structure.
    """
    valid_xmls = kwargs.get("valid_xmls", {})
    file_info = kwargs.get("file_info")
    file_structure = kwargs.get("file_structure")
    src_zip = kwargs.get("src_zip")
    dst_zip = kwargs.get("dst_zip")

    assert isinstance(src_zip, zipfile.ZipFile)
    assert isinstance(dst_zip, zipfile.ZipFile)
    assert isinstance(file_info, zipfile.ZipInfo)

    for zip_keys, xml_files in valid_xmls.items():
        if zip_keys and zip_keys.endswith(file_info.filename):
            if file_structure == "flat":
                for file_name, xml_str in get_nested_zip_xml(
                    src_zip, zip_keys, xml_files
                ):
                    dst_zip.writestr(file_name, xml_str)
            else:
                nested_zip_data = BytesIO()
                with zipfile.ZipFile(
                    nested_zip_data, "w", zipfile.ZIP_DEFLATED
                ) as nested_dst_zip:
                    for file_name, xml_str in get_nested_zip_xml(
                        src_zip, zip_keys, xml_files
                    ):
                        nested_dst_zip.writestr(file_name, xml_str)

                nested_zip_data.seek(0)
                dst_zip.writestr(file_info.filename, nested_zip_data.read())


def build_zip_with_matching_tag_xmls(
    xml_datas: list[BaseModel],
    mode: AnalysisMode,
    source_zip: str,
    target_zip: Path,
    file_structure: str = "flat",
) -> None:
    """
    Create zip file with xml have the tag
    """
    log.info("Building zip with xml matching tags", file_structure=file_structure)
    if not mode in (AnalysisMode.TAG, AnalysisMode.SEARCH):
        raise ValueError(f"Invalid tag name '{mode}' to zip")

    filtered_items = (
        [it for it in xml_datas if hasattr(it, "tag_count")]
        if mode == AnalysisMode.TAG
        else [it for it in xml_datas if getattr(it, "element_tag", None)]
    )
    valid_xmls = defaultdict(set)
    for item in filtered_items:
        parent_zip = getattr(item, "parent_zip", None)
        file_path = getattr(item, "file_path", None)

        if parent_zip and file_path:
            valid_xmls[parent_zip].add(file_path)

    if not valid_xmls:
        log.info("No matching tag found, hence no zip file created")
        return

    with zipfile.ZipFile(source_zip, "r") as src_zip:
        with zipfile.ZipFile(target_zip, "w", zipfile.ZIP_DEFLATED) as dst_zip:
            for file_info in src_zip.infolist():
                if file_info.is_dir():
                    continue

                if file_info.filename.endswith(".xml"):
                    if any(it.endswith(file_info.filename) for it in valid_xmls[None]):
                        with src_zip.open(file_info.filename) as file:
                            dst_zip.writestr(file_info.filename, file.read())

                elif file_info.filename.endswith(".zip"):
                    file_details = {
                        "valid_xmls": valid_xmls,
                        "file_info": file_info,
                        "file_structure": file_structure,
                        "src_zip": src_zip,
                        "dst_zip": dst_zip,
                    }
                    generate_zip_file_structure(**file_details)

    log.info("Zip created with xml matching tags", xml_datas=target_zip)
