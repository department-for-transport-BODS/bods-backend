"""
Test File Hashing
"""

import platform
from pathlib import Path

import pytest
from common_layer.xml.txc.parser.hashing import get_file_hash


@pytest.mark.parametrize(
    "file_content, expected_hash",
    [
        pytest.param(
            b"Hello, World!",
            "0a0a9f2a6772942557ab5355d76af442f8f65e01",
            id="Simple text file",
        ),
        pytest.param(
            b"",
            "da39a3ee5e6b4b0d3255bfef95601890afd80709",
            id="Empty file",
        ),
        pytest.param(
            b"a" * 10000,
            "a080cbda64850abb7b7f67ee875ba068074ff6fe",
            id="Large file larger than chunk size",
        ),
        pytest.param(
            b"\x00\xFF\x00\xFF",
            "c2a9054a363999348c1203115ea0eb9b07fd1e2d",
            id="Binary file",
        ),
    ],
)
def test_get_file_hash(tmp_path: Path, file_content: bytes, expected_hash: str):
    """
    Test file hash calculation for different file types and sizes
    First create a temp file with the test content, then compare the hash

    tmp_path is a built in pytest fixture that cleans up the file after test
    """
    test_file = tmp_path / "test_file.xml"
    test_file.write_bytes(file_content)

    calculated_hash = get_file_hash(test_file)

    assert calculated_hash == expected_hash


@pytest.mark.parametrize(
    "scenario",
    [
        pytest.param(
            "nonexistent_file.xml",
            id="File does not exist",
        ),
        pytest.param(
            "no_permission.xml",
            id="No read permission",
            marks=pytest.mark.skipif(
                platform.system() == "Windows",
                reason="Permission tests not applicable on Windows",
            ),
        ),
    ],
)
def test_get_file_hash_errors(tmp_path: Path, scenario: str):
    """
    Test file hash calculation error cases
    """
    test_file = tmp_path / scenario

    if scenario == "no_permission.xml":
        test_file.write_bytes(b"test")
        test_file.chmod(0o000)

    with pytest.raises(
        FileNotFoundError if scenario == "nonexistent_file.xml" else PermissionError
    ):
        get_file_hash(test_file)
