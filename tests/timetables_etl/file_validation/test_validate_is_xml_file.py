"""
Test whether a file is an XML
"""

import pytest
from common_layer.exceptions.xml_file_exceptions import FileNotXML
from file_validation.app.xml_checks import validate_is_xml_file


@pytest.mark.parametrize(
    "file_name",
    [
        pytest.param(
            "valid.xml",
            id="Basic XML extension",
        ),
        pytest.param(
            "UPPERCASE.XML",
            id="Uppercase XML extension",
        ),
        pytest.param(
            "path/to/file.xml",
            id="XML with path",
        ),
        pytest.param(
            ".xml",
            id="Just extension",
        ),
        pytest.param(
            "multiple.dots.xml",
            id="Multiple dots",
        ),
    ],
)
def test_valid_xml_filenames(file_name: str) -> None:
    """
    Test that valid XML filenames are correctly identified.
    Tests various patterns of valid .xml extensions.
    """
    assert validate_is_xml_file(file_name) is True


@pytest.mark.parametrize(
    "file_name",
    [
        pytest.param(
            "not_xml.txt",
            id="Wrong extension",
        ),
        pytest.param(
            "xml_without_extension",
            id="No extension",
        ),
        pytest.param(
            "fake.xmlx",
            id="Similar but wrong extension",
        ),
        pytest.param(
            "xml.doc",
            id="Different extension",
        ),
        pytest.param(
            "",
            id="Empty filename",
        ),
    ],
)
def test_invalid_xml_filenames(file_name: str) -> None:
    """
    Test that invalid XML filenames raise FileNotXML exception.
    Tests various patterns of invalid or missing .xml extensions.
    """
    with pytest.raises(FileNotXML):
        validate_is_xml_file(file_name)
