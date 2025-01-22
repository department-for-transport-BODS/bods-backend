"""
Test PTI
"""

from pathlib import Path

from .conftest import run_validation_with_exception

DATA_DIR = Path(__file__).parent / "data"

OBSERVATION_ID = 2


def test_is_valid_missing_metadata():
    """Test validation fails when metadata is missing from XML file"""
    run_validation_with_exception(
        filename="missing_filename_metadata.xml",
        data_dir=DATA_DIR,
        observation_id=2,
        expected_exception=ValueError,
        match="Missing metadata in XML file root element",
    )
