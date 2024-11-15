from typing import List, Tuple, Union
from lxml import etree
from .exceptions import (
    NoElement,
    ParentDoesNotExist,
    TooManyElements,
    XMLAttributeError,
)
from .constants import TRANSXCAHNGE_NAMESPACE, TRANSXCHANGE_NAMESPACE_PREFIX
class XMLElement:
    """A class that makes dealing with lxml Element objects easier.
    Args:
        element: lxml.etree.Element you want to traverse.
    """
    namespaces = None
    def __init__(self, element):
        self._element = element
    def __eq__(self, other):
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
    def __getitem__(self, item):
        try:
            return self._element.attrib[item]
        except KeyError as exc:
            msg = f"{self.localname!r} has no attribute {item!r}"
            raise XMLAttributeError(msg) from exc
    def get(self, item, default=None):
        try:
            return self[item]
        except XMLAttributeError:
            return default
    def get_elements(self, xpath: Union[str, List[str], Tuple[str]]):
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
    def get_element(self, xpath: Union[str, List[str], Tuple[str]]):
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
    def get_first_element(self, xpath: Union[str, List[str], Tuple[str]]):
        elements = self.get_elements(xpath)
        return elements[0]
    def get_element_or_none(self, xpath: Union[str, List[str], Tuple[str]]):
        try:
            return self.get_element(xpath)
        except NoElement:
            return None
    def get_elements_or_none(self, xpath: Union[str, List[str], Tuple[str]]):
        try:
            return self.get_elements(xpath)
        except NoElement:
            return None
    def get_first_text_or_default(
        self, xpath: Union[str, List[str], Tuple[str]], default: str = ""
    ):
        try:
            element = self.get_first_element(xpath)
        except NoElement:
            return default
        text = element.text
        if text is None:
            return default
        return text
    def get_text_or_default(
        self, xpath: Union[str, List[str], Tuple[str]], default: str = ""
    ) -> str:
        element = self.get_element_or_none(xpath)
        if element is None:
            return default
        if element.text is None:
            return default
        return element.text
    def _make_xpath(self, xpath) -> str:
        if isinstance(xpath, (list, tuple)):
            xpath = "/".join(xpath)
        return xpath
    def _apply_xpath(self, xpath):
        elements = self._element.xpath(xpath, namespaces=self.namespaces)
        return [self.__class__(element) for element in elements]
    def find_anywhere(self, xpath: Union[str, List[str], Tuple[str]]):
        """Attempts to find a matching xpath anywhere in the tree."""
        xpath = self._make_xpath(xpath)
        xpath = ".//" + xpath
        return self._apply_xpath(xpath)
    def xpath(self, xpath: Union[str, List[str], Tuple[str]]):
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
    def localname(self):
        """Returns the localised tag name with namespaces removed."""
        localname = etree.QName(self._element.tag).localname
        return localname
    @property
    def text(self):
        """Returns the text property of the current root element."""
        return self._element.text
    @property
    def children(self):
        """Returns the children elements of the current root element."""
        return [self.__class__(element) for element in self._element.getchildren()]
    @property
    def parent(self):
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
    def _make_xpath(self, xpath):
        if isinstance(xpath, (list, tuple)):
            xpath = [TRANSXCHANGE_NAMESPACE_PREFIX + ":" + path for path in xpath]
        else:
            xpath = TRANSXCHANGE_NAMESPACE_PREFIX + ":" + xpath
        return super()._make_xpath(xpath)
    
class TransXChangeDocument:
    """A class for handling and validating TransXChange XML Documents."""
    def __init__(self, source):
        """Initialise class.
        Args:
            source (path|file|url): Something that can parsed by `lxml.etree.parse`.
        """
        self.hash = None
        if hasattr(source, "seek"):
            source.seek(0)
            self.hash = sha1sum(source.read())
            source.seek(0)
        self.source = source
        self.name = getattr(source, "name", source)
        self._tree = etree.parse(self.source)
        self._root = TransXChangeElement(self._tree.getroot())
    def __repr__(self):
        class_name = self.__class__.__name__
        return f"{class_name}(source={self.name!r})"
    def __getattr__(self, attr):
        try:
            return getattr(self._root, attr)
        except AttributeError:
            msg = f"{self.__class__.__name__!r} has no attribute {attr!r}"
            raise AttributeError(msg)
    def get_file_name(self) -> str:
        """
        Gets the FileName attribute from a TxC file.
        Returns:
            str: Returns the value in FileName.
        """
        return self._root.get("FileName", "")
    
    #Add the rest of the methods to access elements as and when needed 
