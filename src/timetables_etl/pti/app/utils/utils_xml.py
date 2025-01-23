"""
XML Utils
"""

import re
from typing import Sequence

from dateutil import parser
from lxml.etree import _Element
from structlog.stdlib import get_logger

log = get_logger()

ElementsOrStr = _Element | Sequence[_Element] | list[str] | str
PROHIBITED_CHARS = r",[]{}^=@:;#$£?%+<>«»\/|~_¬"


def extract_text(elements: ElementsOrStr, default=None) -> str | None:
    """
    Extract Text from a LXML Elements
    """
    text = ""
    if isinstance(elements, list) and len(elements) > 0:
        item = elements[0]
        if isinstance(item, str):
            text = item
        else:
            text = getattr(item, "text")
    elif isinstance(elements, str):
        text = elements
    elif hasattr(elements, "text"):
        text = getattr(elements, "text")
    else:
        text = default
    return text


def cast_to_date(_context, date) -> float:
    """
    Casts a lxml date element to an int.
    """
    text = extract_text(date) or ""
    return parser.parse(text).timestamp()


def cast_to_bool(_context, elements: ElementsOrStr) -> bool:
    """
    Casts either a list of str, list of Elements or a str to a boolean
    """
    text = extract_text(elements, default="false")
    return text == "true"


def has_prohibited_chars(_context, element: ElementsOrStr) -> bool:
    """
    Check if Element has disallowed XML characters
    """
    log.info(
        "Validation Start: Prohibited Characters",
    )
    chars = extract_text(element) or ""
    return len([c for c in chars if c in PROHIBITED_CHARS]) > 0


def regex(_context, element: ElementsOrStr, pattern) -> bool:
    """
    Checks if element's text content matches the provided regular expression pattern
    """
    chars = extract_text(element) or ""
    return re.match(pattern, chars) is not None


def is_member_of(_context, element: ElementsOrStr, *args) -> bool:
    """
    Checks if the text content of an element is a member of the provided arguments
    """
    text = extract_text(element, default="")
    return text in args


def strip(_context, text: str) -> str:
    """
    Removes leading and trailing whitespace from element's text content
    """
    text = extract_text(text) or ""
    return text.strip()


def contains_date(_context, text: ElementsOrStr) -> bool:
    """
    Determines if the input text contains any date-like strings.
    """
    text = extract_text(text) or ""
    for word in text.split():
        try:
            if word.isdigit():
                continue
            parser.parse(word)
        except parser.ParserError:
            pass
        else:
            return True
    return False


def has_name(_context, elements: _Element | Sequence[_Element], *names: str) -> bool:
    """
    Checks if elements are in the list of names.
    """
    elements_list = [elements] if not isinstance(elements, Sequence) else elements

    return all(el.xpath("local-name()") in names for el in elements_list)
