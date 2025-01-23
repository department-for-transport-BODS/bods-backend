"""
Validations for Operator Section
"""

from lxml import etree
from structlog.stdlib import get_logger

log = get_logger()


def validate_licence_number(_context, elements: list[etree._Element]) -> bool:
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
    ns = {"x": elements[0].nsmap.get(None)}
    for element in elements:
        primary_mode = element.xpath(
            ".//x:PrimaryMode", namespaces=ns  # pyright: ignore
        )
        licence_number = element.xpath(
            ".//x:LicenceNumber", namespaces=ns  # pyright: ignore
        )

        if primary_mode and primary_mode[0].text.lower() == "coach":
            continue
        if not (licence_number and licence_number[0].text):
            return False
    return True
