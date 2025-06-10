"""
Serviced Organisation Validation
"""

from lxml.etree import _Element  # type: ignore
from structlog.stdlib import get_logger

from ..constants import NAMESPACE

log = get_logger()


def has_servicedorganisation_working_days(
    _: _Element | None, service_organisations: list[_Element]
) -> bool:
    """
    Checks if all service organisations have defined working days.

    This function iterates over a list of service organisations and verifies
    whether each organisation has defined working days by checking the
    corresponding XML structure. If any service organisation lacks working
    days, the function returns False; otherwise, it returns True.

    Args:
        context: The context in which the function is called (not used in the
                 current implementation but may be relevant for future use).
        service_organisations (list): A list of service organisation objects
                                       that are expected to contain XML
                                       elements.

    Returns:
        bool: True if all service organisations have working days defined,
              False otherwise.

    """
    log.info(
        "Validation Start: Serviced Organisation Working Days",
        count=len(service_organisations),
    )
    is_valid = True
    for service_organisation in service_organisations:
        working_days = service_organisation.xpath("x:WorkingDays", namespaces=NAMESPACE)
        if not working_days:
            is_valid = False
    return is_valid
