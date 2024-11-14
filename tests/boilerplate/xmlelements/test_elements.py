import unittest
from unittest.mock import MagicMock, patch
from lxml import etree
from boilerplate.xmlelements import XMLElement
from exceptions.xml_doc_exceptions import (
    NoElement,
    TooManyElements,
)


class TestXMLElement(unittest.TestCase):
    def setUp(self):
        # Define a sample XML structure to use in tests
        self.xml_content = b"""
        <PublicationDelivery version="1.1">
            <PublicationTimestamp>2119-06-22T13:51:43.044Z</PublicationTimestamp>
            <ParticipantRef>SYS001</ParticipantRef>
            <PublicationRequest version="1.0">
                <RequestTimestamp>2119-06-22T13:51:43.044Z</RequestTimestamp>
                <ParticipantRef>SYS002</ParticipantRef>
                <Description>Request for HCTY Line_16.</Description>
            </PublicationRequest>
            <Description>Example  of simple point to point fares</Description>
            <dataObjects>
                <CompositeFrame>composite_frame</CompositeFrame>
                <CompositeFrame>composite_frame2</CompositeFrame>
            </dataObjects>
        </PublicationDelivery>
        """

        # Parse the XML and initialize an XMLElement instance for testing
        self.tree = etree.fromstring(self.xml_content)
        self.root_element = XMLElement(self.tree)

    def test_eq_same_element(self):
        # Create an XML element
        element1 = etree.Element("test")

        # Initialize XMLElement instances with identical elements
        xml_element1 = XMLElement(element1)
        xml_element2 = XMLElement(element1)

        # Assert that two XMLElement instances with the same lxml element are equal
        self.assertEqual(xml_element1, xml_element2)

    def test_repr_with_attributes_and_text(self):
        # Create an XML element with attributes and text
        element = etree.Element("test", attrib={"id": "123", "class": "my-class"})
        element.text = "Hello, World!"

        # Initialize XMLElement
        xml_element = XMLElement(element)

        # Expected __repr__ output
        expected_repr = "test(id='123', class='my-class', text='Hello, World!')"
        self.assertEqual(repr(xml_element), expected_repr)

    def test_repr_with_no_text(self):
        # Create an XML element with attributes but no text
        element = etree.Element("test", attrib={"id": "123"})

        # Initialize XMLElement
        xml_element = XMLElement(element)

        # Expected __repr__ output with text=None
        expected_repr = "test(id='123', text='None')"
        self.assertEqual(repr(xml_element), expected_repr)

    @patch.object(XMLElement, 'get_elements')
    def test_get_element_raises_too_many_elements(self, mock_get_elements):
        # Set up the mock to return more than one element
        mock_get_elements.return_value = [MagicMock(), MagicMock()]

        # Create an instance of XMLElement
        element = MagicMock()  # Mock the actual element
        xml_element = XMLElement(element)

        # Assert that TooManyElements is raised with the expected message
        with self.assertRaises(TooManyElements) as context:
            xml_element.get_element("some/xpath")

        self.assertEqual(str(context.exception), "More than 1 element found")
        mock_get_elements.assert_called_once_with("some/xpath")

    def test_get_elements(self):
        # Test getting multiple child elements
        children = self.root_element.get_elements("ParticipantRef")
        self.assertEqual(len(children), 1)
        self.assertEqual(children[0].text, "SYS001")

    @patch.object(XMLElement, 'get_elements')
    def test_get_elements_or_none_returns_elements(self, mock_get_elements):
        # Set up the mock to return a list of elements
        mock_elements = [MagicMock(), MagicMock()]  # Example elements
        mock_get_elements.return_value = mock_elements

        # Create an instance of XMLElement
        element = MagicMock()
        xml_element = XMLElement(element)

        # Call get_elements_or_none and verify it returns the elements
        result = xml_element.get_elements_or_none("some/xpath")
        self.assertEqual(result, mock_elements)
        mock_get_elements.assert_called_once_with("some/xpath")

    @patch.object(XMLElement, 'get_elements')
    def test_get_elements_returns_none_on_no_element(self, mock_get_elements):
        # Set up the mock to raise a NoElement exception
        mock_get_elements.side_effect = NoElement("No elements found")

        # Create an instance of XMLElement
        element = MagicMock()
        xml_element = XMLElement(element)

        # Call get_elements_or_none and verify it returns None
        result = xml_element.get_elements_or_none("some/xpath")
        self.assertIsNone(result)
        mock_get_elements.assert_called_once_with("some/xpath")

    @patch.object(XMLElement, 'get_first_element')
    def test_get_first_text_or_default_with_text(self, mock_get_first_element):
        # Mock get_first_element to return an element with text
        mock_element = MagicMock()
        mock_element.text = "Sample Text"
        mock_get_first_element.return_value = mock_element

        # Create an instance of XMLElement
        element = MagicMock()
        xml_element = XMLElement(element)

        # Call get_first_text_or_default and verify it returns the text
        result = xml_element.get_first_text_or_default("some/xpath", default="Default Text")
        self.assertEqual(result, "Sample Text")
        mock_get_first_element.assert_called_once_with("some/xpath")

    @patch.object(XMLElement, 'get_first_element')
    def test_get_first_text_or_default_with_none_text(self, mock_get_first_element):
        # Mock get_first_element to return an element with None as text
        mock_element = MagicMock()
        mock_element.text = None
        mock_get_first_element.return_value = mock_element

        # Create an instance of XMLElement
        element = MagicMock()
        xml_element = XMLElement(element)

        # Call get_first_text_or_default and verify it returns the default
        result = xml_element.get_first_text_or_default("some/xpath", default="Default Text")
        self.assertEqual(result, "Default Text")
        mock_get_first_element.assert_called_once_with("some/xpath")

    @patch.object(XMLElement, 'get_first_element')
    def test_get_first_text_or_default_no_element(self, mock_get_first_element):
        # Mock get_first_element to raise a NoElement exception
        mock_get_first_element.side_effect = NoElement("No elements found")

        # Create an instance of XMLElement
        element = MagicMock()
        xml_element = XMLElement(element)

        # Call get_first_text_or_default and verify it returns the default
        result = xml_element.get_first_text_or_default("some/xpath", default="Default Text")
        self.assertEqual(result, "Default Text")
        mock_get_first_element.assert_called_once_with("some/xpath")

    def test_get_element(self):
        # Test getting a single element
        parent = self.root_element.get_element("PublicationRequest")
        self.assertEqual(parent.localname, "PublicationRequest")
        self.assertEqual(parent.get_element("ParticipantRef").text, "SYS002")

    def test_get_element_or_none(self):
        # Test getting an element that exists
        existing_element = self.root_element.get_element_or_none("PublicationRequest")
        self.assertIsNotNone(existing_element)
        self.assertEqual(existing_element.localname, "PublicationRequest")

        # Test getting an element that does not exist
        non_existing_element = self.root_element.get_element_or_none("nonexistent")
        self.assertIsNone(non_existing_element)

    def test_get_text_or_default(self):
        # Test getting text of an existing element
        text = self.root_element.get_text_or_default("PublicationRequest/ParticipantRef", "SYS002")
        self.assertEqual(text, "SYS002")

        # Test getting default text for a non-existent element
        default_text = self.root_element.get_text_or_default("PublicationRequest/nonexistent", "SYS002")
        self.assertEqual(default_text, "SYS002")

    def test_get_attribute(self):
        # Test accessing an attribute of an element
        child = self.root_element.get_element("PublicationRequest")
        self.assertEqual(child.get("version"), "1.0")

        # Test accessing a non-existent attribute with a default
        self.assertEqual(child.get("nonexistent", "default_value"), "default_value")

    def test_get_first_element(self):
        # Test getting the first element that matches the XPath
        first_child = self.root_element.get_first_element("ParticipantRef")
        self.assertEqual(first_child.text, "SYS001")

    def test_find_anywhere(self):
        # Test finding an element anywhere in the tree
        subchild = self.root_element.find_anywhere("ParticipantRef")[0]
        self.assertEqual(subchild.text, "SYS001")

    def test_children_property(self):
        # Test retrieving children elements of the root
        children = self.root_element.children
        self.assertEqual(len(children), 5)
        self.assertEqual(children[1].localname, "ParticipantRef")
        self.assertEqual(children[4].localname, "dataObjects")

    def test_parent_property(self):
        # Test getting the parent of a child element
        child_element = self.root_element.get_element("ParticipantRef")
        parent = child_element.parent
        self.assertEqual(parent.localname, "PublicationDelivery")

    def test_line_number(self):
        # Test retrieving line number of an element
        child_element = self.root_element.get_element("ParticipantRef")
        self.assertIsNotNone(child_element.line_number)

    def test_element_not_found(self):
        # Test that NoElement is raised when expected element is not found
        with self.assertRaises(NoElement):
            self.root_element.get_element("nonexistent")


if __name__ == "__main__":
    unittest.main()