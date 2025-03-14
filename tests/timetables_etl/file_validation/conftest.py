"""
FileValidation Lambda Fixtures
"""

from io import BytesIO
from typing import Callable

import pytest


@pytest.fixture
def create_xml_file() -> Callable[..., BytesIO]:
    """Fixture providing a function to create XML BytesIO objects."""

    def _create_xml_file(content: bytes) -> BytesIO:
        file_obj = BytesIO(content)
        file_obj.name = "test.xml"
        return file_obj

    return _create_xml_file
