"""
Something
"""

import sys
import tempfile
import zipfile
from pathlib import Path
from typing import Annotated

import typer
from pydantic import BaseModel, Field
from structlog.stdlib import get_logger

log = get_logger()


class XmlFile(BaseModel):
    """Represents an XML file extracted from the zip."""

    path: Path
    content: bytes | None = None


class ZipProcessingResult(BaseModel):
    """Represents the result of processing a zip file."""

    total_files: int = 0
    xml_files: int = 0
    processed_xmls: list[XmlFile] = Field(default_factory=list)


def extract_zip(zip_path: Path, extract_to: Path) -> None:
    """Extract all files from a zip file to a directory."""
    log.info("Extracting zip file", zip_path=str(zip_path), extract_to=str(extract_to))
    with zipfile.ZipFile(zip_path, "r") as zip_ref:
        zip_ref.extractall(extract_to)
    log.info("Extraction complete", zip_path=str(zip_path))


def process_file(file_path: Path, result: ZipProcessingResult) -> None:
    """Process a file, handling XML files and nested zip files."""
    result.total_files += 1

    if file_path.suffix.lower() == ".xml":
        log.info("Found XML file", file_path=str(file_path))
        with open(file_path, "rb") as f:
            content = f.read()
        file_info = XmlFile(path=file_path, content=content)
        result.processed_xmls.append(file_info)
        result.xml_files += 1
    elif file_path.suffix.lower() == ".zip":
        log.info("Found nested zip file", file_path=str(file_path))
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            extract_zip(file_path, temp_path)
            process_directory(temp_path, result)


def process_directory(dir_path: Path, result: ZipProcessingResult) -> None:
    """Process a directory, handling all files and subdirectories."""
    log.info("Processing directory", dir_path=str(dir_path))
    for item in dir_path.iterdir():
        if item.is_file():
            process_file(item, result)
        elif item.is_dir():
            process_directory(item, result)


def find_top_level_folder(extract_dir: Path) -> str | None:
    """Find the top level folder in the extracted directory."""
    items = list(extract_dir.iterdir())
    dirs = [item for item in items if item.is_dir()]

    if len(dirs) == 1:
        return dirs[0].name
    return None


def create_lzma_zip(
    output_path: Path, xml_files: list[XmlFile], top_level_folder: str | None
) -> None:
    """Create a new LZMA-compressed zip file with the XML files."""
    log.info(
        "Creating LZMA-compressed zip file",
        output_path=str(output_path),
        top_level_folder=top_level_folder,
    )

    with zipfile.ZipFile(output_path, "w", compression=zipfile.ZIP_LZMA) as zip_out:
        # Track filenames already added to the zip
        added_filenames: set[str] = set()

        for xml_file in xml_files:
            if xml_file.content is not None:
                # Generate a unique path for each XML file
                base_name = xml_file.path.name
                if top_level_folder:
                    filename = base_name

                    # If a file with the same name already exists, add a counter
                    if filename in added_filenames:
                        counter = 1
                        while (
                            f"{xml_file.path.stem}_{counter}{xml_file.path.suffix}"
                            in added_filenames
                        ):
                            counter += 1
                        filename = (
                            f"{xml_file.path.stem}_{counter}{xml_file.path.suffix}"
                        )

                    zip_path = f"{top_level_folder}/{filename}"
                    added_filenames.add(filename)
                else:
                    filename = base_name

                    # If a file with the same name already exists, add a counter
                    if filename in added_filenames:
                        counter = 1
                        while (
                            f"{xml_file.path.stem}_{counter}{xml_file.path.suffix}"
                            in added_filenames
                        ):
                            counter += 1
                        filename = (
                            f"{xml_file.path.stem}_{counter}{xml_file.path.suffix}"
                        )

                    zip_path = filename
                    added_filenames.add(filename)

                log.info(
                    "Adding XML to zip", xml_file=str(xml_file.path), zip_path=zip_path
                )
                zip_out.writestr(zip_path, xml_file.content)

    log.info(
        "LZMA zip creation complete",
        output_path=str(output_path),
        file_count=len(xml_files),
    )


def process_zip_file(input_zip_path: Path, output_zip_path: Path) -> None:
    """Process a zip file to extract XML files and repackage them."""
    log.info(
        "Starting zip processing",
        input_zip=str(input_zip_path),
        output_zip=str(output_zip_path),
    )

    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)
        extract_zip(input_zip_path, temp_path)

        # Find the top level folder
        top_level_folder = find_top_level_folder(temp_path)
        log.info("Identified top level folder", folder=top_level_folder)

        # Process all files and directories
        result = ZipProcessingResult()
        process_directory(temp_path, result)

        log.info(
            "Processing complete",
            total_files=result.total_files,
            xml_files=result.xml_files,
        )

        # Create the output zip
        create_lzma_zip(output_zip_path, result.processed_xmls, top_level_folder)

    log.info(
        "Zip processing complete",
        input_zip=str(input_zip_path),
        output_zip=str(output_zip_path),
        total_files=result.total_files,
        xml_files=result.xml_files,
    )


def repackage(
    input_zip: Annotated[str, typer.Argument(help="Path to the input zip file")],
    output_zip: Annotated[
        str, typer.Argument(help="Path to the output LZMA-compressed zip file")
    ],
) -> None:
    """
    Process a zip file to extract sub zips and repackage as XML files.
    """
    input_path = Path(input_zip)
    output_path = Path(output_zip)

    if not input_path.exists():
        log.error("Input zip file does not exist", input_zip=input_zip)
        sys.exit(1)

    log.info("Starting zip file processing", input_zip=input_zip, output_zip=output_zip)
    process_zip_file(input_path, output_path)
    log.info("Zip file processing complete", input_zip=input_zip, output_zip=output_zip)


if __name__ == "__main__":
    typer.run(repackage)
