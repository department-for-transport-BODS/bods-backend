"""
Clam AV Scanner Lambda Tests
"""

from unittest.mock import MagicMock, patch

import pytest
from clamav_scanner import (
    ClamAVConfig,
    FileScanner,
    get_clamav_config,
    lambda_handler,
    process_file_to_s3,
)
from common_layer.exceptions.file_exceptions import SuspiciousFile


@pytest.mark.parametrize(
    "config_scenario",
    [
        pytest.param(
            {
                "env": {"CLAMAV_HOST": "host", "CLAMAV_PORT": "1234"},
            },
            id="Valid Config Settings",
        ),
    ],
)
def test_get_clamav_config_success(config_scenario):
    """Test ClamAV configuration validation"""
    with patch.dict("os.environ", config_scenario["env"], clear=True):
        config = get_clamav_config()
        assert config.host == "host"
        assert config.port == 1234


@pytest.mark.parametrize(
    "config_scenario",
    [
        pytest.param(
            {
                "env": {"CLAMAV_HOST": "host", "CLAMAV_PORT": "invalid"},
            },
            id="Invalid Port Number",
        ),
        pytest.param(
            {
                "env": {"CLAMAV_PORT": "1234"},
            },
            id="Missing Host Setting",
        ),
    ],
)
def test_get_clamav_config_exceptions(config_scenario):
    """Test ClamAV configuration validation"""
    with patch.dict("os.environ", config_scenario["env"], clear=True):
        with pytest.raises(EnvironmentError):
            get_clamav_config()


@pytest.mark.parametrize(
    "file_scenario",
    [
        pytest.param(
            {
                "name": "test.xml",
                "prefix": "ext_test/test.xml",
                "content": b"xml content",
            },
            id="Process XML File",
        ),
        pytest.param(
            {
                "name": "data.json",
                "prefix": "ext_data/data.json",
                "content": b"json data",
            },
            id="Process JSON File",
        ),
    ],
)
def test_process_file_to_s3(file_scenario, tmp_path):
    """Test S3 file processing"""
    test_file = tmp_path / file_scenario["name"]
    test_file.write_bytes(file_scenario["content"])

    mock_s3 = MagicMock()
    result = process_file_to_s3(mock_s3, test_file, "ext")

    assert result.startswith("ext_")
    mock_s3.put_object.assert_called_once()
    args = mock_s3.put_object.call_args[0]
    assert args[0] == file_scenario["prefix"]


def test_scan_file_no_threats_found(tmp_path):
    """
    Test scanning a file with no threats found.
    No exception should be raised
    """
    test_file = tmp_path / "safe_file.txt"
    test_file.write_text("This is a safe file content")

    clamav_config = ClamAVConfig(host="localhost", port=3310)
    mock_clamav = MagicMock()
    mock_clamav.instream.return_value = {"stream": ("OK", None)}

    with patch("clamav_scanner.ClamdNetworkSocket", return_value=mock_clamav):
        scanner = FileScanner(clamav_config)
        scanner.scan(test_file)


def test_scan_file_threats_found(tmp_path):
    """Test scanning a file with threats found."""
    test_file = tmp_path / "infected_file.txt"
    test_file.write_text("This file contains a virus")

    clamav_config = ClamAVConfig(host="localhost", port=3310)
    mock_clamav = MagicMock()
    mock_clamav.instream.return_value = {"stream": ("FOUND", "Eicar-Test-Signature")}

    with patch("clamav_scanner.ClamdNetworkSocket", return_value=mock_clamav):
        scanner = FileScanner(clamav_config)
        with pytest.raises(SuspiciousFile) as exc_info:
            scanner.scan(test_file)
        assert "Eicar-Test-Signature" in str(exc_info.value)
