import unittest
from unittest.mock import patch, MagicMock
from io import BytesIO
from common_layer.xml_validator import (
    FileValidator,
    XMLValidator,
    get_lxml_schema
)
from common_layer.exceptions.xml_file_exceptions import (
    FileTooLarge,
    XMLSyntaxError,
    DangerousXML
)
from lxml import etree


class TestFileValidator(unittest.TestCase):
    def test_is_file(self):
        """Test is_file property with file-like and non-file-like objects."""
        file_like = BytesIO(b"test content")
        non_file_like = "path/to/file.txt"

        validator = FileValidator(file_like)
        self.assertTrue(validator.is_file)

        validator = FileValidator(non_file_like)
        self.assertFalse(validator.is_file)

    def test_is_too_large(self):
        """Test is_too_large with a file exceeding max size."""
        large_file = BytesIO(b"A" * int(1e9 + 1))  # 1 GB + 1 byte
        validator = FileValidator(large_file, max_file_size=1e9)

        self.assertTrue(validator.is_too_large())

    def test_validate_too_large(self):
        """Test that validate raises FileTooLarge if file is too big."""
        large_file = BytesIO(b"A" * int(2))
        large_file.name = "sample.zip"
        validator = FileValidator(large_file, max_file_size=1)

        with self.assertRaises(FileTooLarge):
            validator.validate()


class TestXMLValidator(unittest.TestCase):
    def test_dangerous_xml(self):
        """Test that dangerous XML raises DangerousXML exception."""
        dangerous_xml = BytesIO(
            b"<!DOCTYPE foo [<!ENTITY xxe SYSTEM 'file:///etc/passwd'> ]><foo>&xxe;</foo>"
        )
        dangerous_xml.name = "dangerous.xml"
        validator = XMLValidator(dangerous_xml)

        violations = validator.validate()
        self.assertTrue(any(isinstance(v, DangerousXML) for v in violations))

    def test_invalid_xml_syntax(self):
        """Test that invalid XML syntax raises XMLSyntaxError."""
        invalid_xml = BytesIO(
            b"<root><element></root>"
        )  # Missing closing tag for <element>
        invalid_xml.name = "invalid.xml"
        validator = XMLValidator(invalid_xml)

        violations = validator.validate()
        self.assertTrue(any(isinstance(v, XMLSyntaxError) for v in violations))

    def test_valid_xml_no_schema(self):
        """Test that valid XML with no schema passes validation."""
        valid_xml = BytesIO(b"<root><element>test</element></root>")
        valid_xml.name = "valid.xml"
        validator = XMLValidator(valid_xml)

        violations = validator.validate()
        self.assertEqual(len(violations), 0)  # No violations expected

    def test_valid_xml_with_schema(self):
        """Test that XML validation works against a schema."""
        valid_xml = BytesIO(b"<root><element>test</element></root>")
        valid_xml.name = "valid.xml"
        # Define a simple XML schema for testing
        schema_xml = b"""<xs:schema xmlns:xs="http://www.w3.org/2001/XMLSchema">
            <xs:element name="root">
                <xs:complexType>
                    <xs:sequence>
                        <xs:element name="element" type="xs:string"/>
                    </xs:sequence>
                </xs:complexType>
            </xs:element>
        </xs:schema>"""
        schema = etree.XMLSchema(etree.fromstring(schema_xml))

        validator = XMLValidator(valid_xml, schema=schema)
        violations = validator.validate()
        self.assertEqual(len(violations), 0)  # Expect no violations for valid XML

    def test_invalid_xml_against_schema(self):
        """Test that invalid XML against schema raises XMLSyntaxError."""
        invalid_xml = BytesIO(b"<root><invalid_element>test</invalid_element></root>")
        invalid_xml.name = "invalid.xml"
        schema_xml = b"""<xs:schema xmlns:xs="http://www.w3.org/2001/XMLSchema">
            <xs:element name="root">
                <xs:complexType>
                    <xs:sequence>
                        <xs:element name="element" type="xs:string"/>
                    </xs:sequence>
                </xs:complexType>
            </xs:element>
        </xs:schema>"""
        schema = etree.XMLSchema(etree.fromstring(schema_xml))

        validator = XMLValidator(invalid_xml, schema=schema)
        violations = validator.validate()
        self.assertTrue(any(isinstance(v, XMLSyntaxError) for v in violations))

    def test_is_too_large_with_xml_validator(self):
        """Test XMLValidator's file size check, ensuring FileTooLarge is raised."""
        large_file = BytesIO(b"A" * int(5e9 + 1))  # Just above 5 GB limit
        large_file.name = "large.zip"
        validator = XMLValidator(large_file, max_file_size=5e9)

        violations = validator.validate()
        self.assertTrue(any(isinstance(v, FileTooLarge) for v in violations))

    def test_get_lxml_schema_none(self):
        # Test with schema = None, expecting None as the result
        result = get_lxml_schema(None)
        self.assertIsNone(result)

    def test_get_lxml_schema_already_xmlschema(self):
        # Test with an etree.XMLSchema instance
        mock_schema = MagicMock(spec=etree.XMLSchema)

        # Should return the same schema instance without parsing
        result = get_lxml_schema(mock_schema)
        self.assertIs(result, mock_schema)


if __name__ == "__main__":
    unittest.main()
