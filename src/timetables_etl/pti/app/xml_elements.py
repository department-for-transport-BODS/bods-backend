"""
XML Element used by PTI
"""

from typing import Self, TypeAlias

from common_layer.exceptions.xml_doc_exceptions import (
    NoElement,
    ParentDoesNotExist,
    TooManyElements,
    XMLAttributeError,
)
from lxml.etree import _Element  # type: ignore
from lxml.etree import QName

TRANSXCAHNGE_NAMESPACE = "http://www.transxchange.org.uk/"
TRANSXCHANGE_NAMESPACE_PREFIX = "x"
XPathInput: TypeAlias = str | list[str] | tuple[str] | bytes


class XMLElement:
    """A class that makes dealing with lxml Element objects easier.

    Args:
        element: lxml.etree.Element you want to traverse.

    """

    namespaces = None

    def __init__(self, element: _Element) -> None:
        self._element = element

    def __eq__(self, other: Self) -> bool:  # type: ignore
        return self._element == other._element

    def __repr__(self):
        attribs = [f"{key}={value!r}" for key, value in self._element.items()]
        if self.text is None:
            text = "None"
        else:
            text = self.text

        attribs.append(f"text={text.strip()!r}")
        attrib_str = ", ".join(attribs)
        return f"{self.localname}({attrib_str})"

    def __getitem__(self, item: str) -> str:
        try:
            return self._element.attrib[item]
        except KeyError as exc:
            msg = f"{self.localname!r} has no attribute {item!r}"
            raise XMLAttributeError(msg) from exc

    def get(self, item: str, default: str | None = None) -> str | None:
        """
        Get Element
        """
        try:
            return self[item]
        except XMLAttributeError:
            return default

    def get_elements(self, xpath: XPathInput) -> list[Self]:
        """Gets elements matching xpath.

        Args:
            xpath: Either list/tuple of strings or a regular xpath string.

        Returns:
            A list of elements.

        Raises:
            NoElement: if xpath returns no elements.
        """
        elements = self.xpath(xpath)
        if len(elements) == 0:
            msg = f"{self.localname} has no xpath {xpath!r}"
            raise NoElement(msg)
        return elements

    def get_element(self, xpath: XPathInput) -> Self:
        """Gets element matching xpath.

        Args:
            xpath: Either list/tuple of strings or a regular xpath string.

        Returns:
            A single element.

        Raises:
            TooManyElements: if xpath returns more than 1 element.
            NoElement: if xpath returns no elements.
        """
        elements = self.get_elements(xpath)

        if len(elements) > 1:
            msg = "More than 1 element found"
            raise TooManyElements(msg)

        return elements[0]

    def get_first_element(self, xpath: XPathInput) -> Self:
        """
        Return the first element
        """
        elements = self.get_elements(xpath)
        return elements[0]

    def get_element_or_none(self, xpath: XPathInput) -> Self | None:
        """
        Get by xpath or return None
        """
        try:
            return self.get_element(xpath)
        except NoElement:
            return None

    def get_elements_or_none(self, xpath: XPathInput) -> list[Self] | None:
        """
        Get List of Elements or none
        """
        try:
            return self.get_elements(xpath)
        except NoElement:
            return None

    def get_first_text_or_default(self, xpath: XPathInput, default: str = "") -> str:
        """
        Get first result of str or a default value
        """
        try:
            element = self.get_first_element(xpath)
        except NoElement:
            return default

        text = element.text
        if text is None:
            return default

        return text

    def get_text_or_default(self, xpath: XPathInput, default: str = "") -> str:
        """
        Get text or default
        """
        element = self.get_element_or_none(xpath)
        if element is None:
            return default
        if element.text is None:
            return default
        return element.text

    def _make_xpath(self, xpath: XPathInput) -> str | bytes:
        if isinstance(xpath, (list, tuple)):
            xpath = "/".join(xpath)
        return xpath

    def _apply_xpath(self, xpath: str | bytes) -> list[Self]:
        elements = self._element.xpath(xpath, namespaces=self.namespaces)
        return [self.__class__(element) for element in elements]

    def find_anywhere(self, xpath: XPathInput) -> list[Self]:
        """Attempts to find a matching xpath anywhere in the tree."""
        processed_xpath = self._make_xpath(xpath)
        if isinstance(processed_xpath, str):
            processed_xpath = ".//" + processed_xpath
        else:
            processed_xpath = b".//" + processed_xpath

        return self._apply_xpath(processed_xpath)

    def xpath(self, xpath: XPathInput) -> list[Self]:
        """Wrapper method around Element.xpath allowing for list tags.

        Allows for xpath to specified as list ["Tag1", "Tag2"], this gets
        converted to "Tag1/Tag2"

        Args:
            xpath: Either list/tuple of strings or a regular xpath string.

        Returns:
            elements: A list XMLElements that match the xpath.

        """
        xpath = self._make_xpath(xpath)
        return self._apply_xpath(xpath)

    @property
    def localname(self) -> str:
        """Returns the localised tag name with namespaces removed."""
        localname = QName(self._element.tag).localname
        return localname

    @property
    def text(self) -> str | None:
        """Returns the text property of the current root element."""
        return self._element.text

    @property
    def children(self) -> list[Self]:
        """Returns the children elements of the current root element."""
        return [self.__class__(element) for element in self._element]

    @property
    def parent(self) -> Self:
        """Returns the parent of the element."""
        element = self._element.getparent()
        if element is None:
            msg = f"{self.localname!r} has no parent element"
            raise ParentDoesNotExist(msg)

        return self.__class__(element)

    @property
    def line_number(self):
        """Returns the line number of the element."""
        return self._element.sourceline


class TransXChangeElement(XMLElement):
    """A wrapper class to easily work lxml elements for TransXChange XML.

    This adds the TransXChange namespaces to the XMLElement class.
    The TransXChangeDocument tree is traversed using the following general
    principle. Child elements are accessed via properties, e.g.
    Service elements are document.services.

    If you expect a bultin type to be returned this will generally
    be a getter method e.g. documents.get_scheduled_stop_points_ids()
    since this returns a list of strings.

    Args:
        root (etree._Element): the root of an lxml _Element.

    Example:
        # Traverse the tree
        tree = etree.parse(netexfile)
        trans = TransXChangeDocument(tree.getroot())
        trans.get_element("PublicationTimestamp")
            PublicationTimestamp(text='2119-06-22T13:51:43.044Z')
        trans.get_elements(["dataObjects", "CompositeFrame"])
            [CompositeFrame(...), CompositeFrame(...)]
        trans.get_elements(["dataObjects", "CompositeFrame", "Name"])
            [Name(...), Name(...)

        # Element attributes are accessed like dict values
        trans["version"]
            '1.1'
    """

    namespaces = {TRANSXCHANGE_NAMESPACE_PREFIX: TRANSXCAHNGE_NAMESPACE}

    def _make_xpath(self, xpath: XPathInput) -> str | bytes:
        if isinstance(xpath, (list, tuple)):
            xpath = [f"{TRANSXCHANGE_NAMESPACE_PREFIX}:{path}" for path in xpath]
        elif isinstance(xpath, str):
            xpath = f"{TRANSXCHANGE_NAMESPACE_PREFIX}:{xpath}"
        else:
            # Handle bytes case
            prefix = f"{TRANSXCHANGE_NAMESPACE_PREFIX}:".encode()
            xpath = prefix + xpath

        return super()._make_xpath(xpath)
