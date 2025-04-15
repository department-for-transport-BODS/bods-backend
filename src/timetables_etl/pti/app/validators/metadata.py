"""
Validator Helper functions
"""

from lxml.etree import _Element  # type: ignore
from structlog.stdlib import get_logger

log = get_logger()


def validate_modification_date_time(
    _context: _Element | None, roots: list[_Element]
) -> bool:
    """
    Validates modification datetime against creation datetime
    """
    log.info(
        "Validation Start: Modification Datetime",
        count=len(roots),
    )
    root = roots[0]
    modification_date = root.attrib.get("ModificationDateTime")
    creation_date = root.attrib.get("CreationDateTime")
    revision_number = root.attrib.get("RevisionNumber")

    if revision_number == "0":
        return modification_date == creation_date
    if creation_date is None or modification_date is None:
        return False
    return creation_date < modification_date
