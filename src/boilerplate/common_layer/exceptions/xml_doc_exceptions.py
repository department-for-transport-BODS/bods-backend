"""
Exceptions used by XMLElement in src/boilerplate/common_layer/xmlelements/elements.py
Which is used by TransXChangeElement in src/boilerplate/common_layer/timetables/transxchange.py
(Should be Replaced/Removed)
"""


class XMLElementException(Exception):
    """
    General XML Exception
    """


class XMLAttributeError(XMLElementException):
    """
    XML Attributes Issue
    """


class NoElement(XMLElementException):
    """
    Missing Element
    """


class TooManyElements(XMLElementException):
    """
    Too Many Elements
    """


class ParentDoesNotExist(XMLElementException):
    """
    Parent does not exist
    """
