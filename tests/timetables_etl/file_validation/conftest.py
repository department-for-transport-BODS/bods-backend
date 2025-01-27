"""
FileValidation Lambda Fixtures
"""

from io import BytesIO

import pytest


@pytest.fixture
def create_xml_file():
    """Fixture providing a function to create XML BytesIO objects."""

    def _create_xml_file(content: bytes) -> BytesIO:
        file_obj = BytesIO(content)
        file_obj.name = "test.xml"
        return file_obj

    return _create_xml_file
