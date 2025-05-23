"""
Clam AV Scanner Lambda Tests
"""

from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
from common_layer.exceptions import SuspiciousFile
from common_layer.s3.upload import process_file_to_s3

from common_lambdas.clamav_scanner.app.av_scan import FileScanner, get_clamav_config
from common_lambdas.clamav_scanner.app.models import ClamAVConfig


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
def test_get_clamav_config_success(config_scenario: dict[str, dict[str, str]]):
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
def test_get_clamav_config_exceptions(config_scenario: dict[str, dict[str, str]]):
    """Test ClamAV configuration validation"""
    with patch.dict("os.environ", config_scenario["env"], clear=True):
        with pytest.raises(EnvironmentError):
            get_clamav_config()


@pytest.mark.parametrize(
    "file_name, file_prefix, file_content",
    [
        pytest.param(
            "test.xml",
            "ext/test.xml",
            b"xml content",
            id="Process XML File",
        ),
        pytest.param(
            "data.json",
            "ext/data.json",
            b"json data",
            id="Process JSON File",
        ),
    ],
)
def test_process_file_to_s3(
    file_name: str, file_prefix: str, file_content: bytes, tmp_path: Path
):
    """Test S3 file processing"""
    test_file = tmp_path / file_name
    test_file.write_bytes(file_content)

    mock_s3 = MagicMock()
    result, _stats = process_file_to_s3(mock_s3, test_file, "ext/")

    assert result.startswith("ext/")
    mock_s3.put_object.assert_called_once()
    args = mock_s3.put_object.call_args[0]
    assert args[0] == file_prefix


def test_scan_file_no_threats_found(tmp_path: Path):
    """
    Test scanning a file with no threats found.
    No exception should be raised
    """
    test_file = tmp_path / "safe_file.txt"
    test_file.write_text("This is a safe file content")

    clamav_config = ClamAVConfig(host="localhost", port=3310)
    mock_clamav = MagicMock()
    mock_clamav.instream.return_value = {"stream": ("OK", None)}

    with patch(
        "common_lambdas.clamav_scanner.app.av_scan.ClamdNetworkSocket",
        return_value=mock_clamav,
    ):
        scanner = FileScanner(clamav_config)
        scanner.scan(test_file)


def test_scan_file_threats_found(tmp_path: Path):
    """Test scanning a file with threats found."""
    test_file = tmp_path / "infected_file.txt"
    test_file.write_text("This file contains a virus")

    clamav_config = ClamAVConfig(host="localhost", port=3310)
    mock_clamav = MagicMock()
    mock_clamav.instream.return_value = {"stream": ("FOUND", "Eicar-Test-Signature")}

    with patch(
        "common_lambdas.clamav_scanner.app.av_scan.ClamdNetworkSocket",
        return_value=mock_clamav,
    ):
        scanner = FileScanner(clamav_config)
        with pytest.raises(SuspiciousFile) as exc_info:
            scanner.scan(test_file)
        assert "Eicar-Test-Signature" in str(exc_info.value)
