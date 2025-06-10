"""
Inbound / Outbound Description Validation
"""

from lxml.etree import _Element  # type: ignore
from structlog.stdlib import get_logger

from ...constants import NAMESPACE

log = get_logger()


def check_inbound_outbound_description(
    _: _Element | None, services: list[_Element]
) -> bool:
    """
    Check when file has detected a standard service (includes StandardService):
        - If both InboundDescription and OutboundDescription are not present, return False.
        - All other combinations are acceptable, return True.
    """
    log.info(
        "Validation Start: Check Inbound / Outbound Description",
    )
    for service in services:
        standard_service_list = service.xpath(
            "x:Service/x:StandardService", namespaces=NAMESPACE
        )
        if standard_service_list:
            inbound_description_list = service.xpath(
                "x:Service/x:Lines/x:Line/x:InboundDescription", namespaces=NAMESPACE
            )
            outbound_description_list = service.xpath(
                "x:Service/x:Lines/x:Line/x:OutboundDescription", namespaces=NAMESPACE
            )
            if (
                len(inbound_description_list) == 0
                and len(outbound_description_list) == 0
            ):
                return False

        return True
    return False


def check_description_for_inbound_description(
    _: _Element | None, services: list[_Element]
) -> bool:
    """
    Check if a StandardService has description present for InboundDescription.

    Args:
        context: The context for the check.
        services: A list of service elements to be checked.

    Returns:
        bool: True if all services have descriptions for InboundDescription, False otherwise.
    """
    log.info(
        "Validation Start: Description for Inbound Description",
    )
    for service in services:
        inbound_description_list: list[_Element] = []
        standard_service_list = service.xpath(
            "x:Service/x:StandardService", namespaces=NAMESPACE
        )
        if standard_service_list:
            inbound_description_list = service.xpath(
                "x:Service/x:Lines/x:Line/x:InboundDescription", namespaces=NAMESPACE
            )
        for inbound_description_tag in inbound_description_list:
            if (
                len(
                    inbound_description_tag.xpath("x:Description", namespaces=NAMESPACE)
                )
                == 0
            ):
                return False
        return True
    return False


def check_description_for_outbound_description(
    _: _Element | None, services: list[_Element]
) -> bool:
    """
    Check if a StandardService has description present for OutboundDescription.

    Args:
        context: The context for the check.
        services: A list of service elements to be checked.

    Returns:
        bool: True if all services have descriptions for OutboundDescription, False otherwise.
    """
    log.info(
        "Validation Start: Description for Outbound Description",
    )
    for service in services:
        standard_service_list = service.xpath(
            "x:Service/x:StandardService", namespaces=NAMESPACE
        )
        if standard_service_list:
            outbound_description_list = service.xpath(
                "x:Service/x:Lines/x:Line/x:OutboundDescription", namespaces=NAMESPACE
            )
            for outbound_description_tag in outbound_description_list:
                if (
                    len(
                        outbound_description_tag.xpath(
                            "x:Description", namespaces=NAMESPACE
                        )
                    )
                    == 0
                ):
                    return False
        return True
    return False
