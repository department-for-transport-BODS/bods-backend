"""
Validations for Operator Section
"""

from lxml.etree import _Element  # type: ignore
from structlog.stdlib import get_logger

from ..constants import NAMESPACE

log = get_logger()


def validate_licence_number(
    _context: _Element | None, elements: list[_Element]
) -> bool:
    """
    Validate the license number within a list of XML elements if Primary Mode is not coach.

    If PrimaryMode is not "coach", then LicenceNumber is mandatory and should be non-empty.

    Args:
        context: The context in which the function is called.
        elements (list): A list of XML elements to validate

    Returns:
        bool: True if all elements are valid according to the specified rules,
              False otherwise.
    """
    log.info(
        "Validation Start: Licence Number",
        count=len(elements),
    )
    for element in elements:
        primary_mode = element.xpath(".//x:PrimaryMode", namespaces=NAMESPACE)
        licence_number = element.xpath(".//x:LicenceNumber", namespaces=NAMESPACE)

        if primary_mode and primary_mode[0].text.lower() == "coach":
            continue
        if not (licence_number and licence_number[0].text):
            return False
    return True
