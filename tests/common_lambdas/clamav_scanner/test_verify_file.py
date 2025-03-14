"""
Tests for Verifying a file
"""

import zipfile
from pathlib import Path

import pytest
from common_layer.exceptions import NestedZipForbidden, ZipNoDataFound

from common_lambdas.clamav_scanner.app.verify_file import verify_zip_file


def create_zip_with_files(zip_path: Path, files: dict[str, bytes]):
    """Creates a tmp zip file with specified files and their content"""
    with zipfile.ZipFile(zip_path, "w") as zipf:
        for file_name, content in files.items():
            zipf.writestr(file_name, content)


def test_verify_zip_file_valid(tmp_path: Path):
    """
    Test valid ZIP file does not raise errors
    """
    filename = "valid.zip"
    zip_path = tmp_path / filename
    create_zip_with_files(
        zip_path, {"data.xml": b"<XML></XML>", "readme.txt": b"Ignored text file"}
    )
    # No exceptions raised
    verify_zip_file(zip_path, filename)


def test_verify_zip_file_nested_zip(tmp_path: Path):
    """
    Test ZIP file with a nested ZIP raises NestedZipForbidden
    """
    filename = "nested.zip"
    zip_path = tmp_path / filename
    create_zip_with_files(zip_path, {"nested.zip": b"zip content"})

    with pytest.raises(
        NestedZipForbidden, match=f"Zip file {filename} contains another zip file."
    ):
        verify_zip_file(zip_path, filename)


def test_verify_zip_file_no_xml(tmp_path: Path):
    """
    Test ZIP file with no XML files raises ZipNoDataFound
    """
    filename = "no_xml.zip"
    zip_path = tmp_path / filename
    create_zip_with_files(
        zip_path, {"image.jpg": b"binarydata", "notes.txt": b"hello world"}
    )

    with pytest.raises(
        ZipNoDataFound, match=f"Zip file {filename} contains no data files"
    ):
        verify_zip_file(zip_path, filename)
