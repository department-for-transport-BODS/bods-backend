"""
Service Validations
"""

import re

from lxml.etree import _Element  # type: ignore
from structlog.stdlib import get_logger

from ...utils import get_namespaces

log = get_logger()
registered_code_regex = re.compile("[a-zA-Z]{2}\\d{7}:[a-zA-Z0-9]+$")
unregistered_code_regex = re.compile("UZ[a-zA-Z0-9]{7}:[a-zA-Z0-9]+$")


def has_flexible_or_standard_service(
    _: _Element | None, services: list[_Element]
) -> bool:
    """
    If it is a non-flexible service (flexible service is not defined),
    then it should have a StandardService defined. If validation fails,
    then a validation issue should be recorded in validation report.
    """
    log.info(
        "Validation Start: Has Flexible or Standard Service",
    )
    for service in services:
        ns = get_namespaces(service)
        service_classification = service.xpath(
            "x:ServiceClassification/x:Flexible", namespaces=ns
        )

        if service_classification:
            flexible_service_list = service.xpath("x:FlexibleService", namespaces=ns)
            if flexible_service_list:
                return True
            return False
        standard_service_list = service.xpath("x:StandardService", namespaces=ns)
        return bool(standard_service_list)

    return False


def check_service_group_validations(
    _: _Element | None, services: list[_Element]
) -> bool:
    """
    Enforces the following rules:
    1. A service group can contain exactly one service of any type, OR
    2. A service group can contain multiple services ONLY IF:
       - It contains exactly one registered flexible service
       - It contains NO registered standard services

    The function categorizes services into:
    - Registered StandardService (ServiceCode format: XX9999999:*)
    - Unregistered StandardService (ServiceCode format: UZ[A-Z0-9]{7}:*)
    - Registered FlexibleService (ServiceCode matches registered format + has Flexible)
    """
    log.info(
        "Validation Start: Service Group Validations",
        count=len(services),
    )
    service = services[0]
    ns = get_namespaces(services[0])
    service_list: list[_Element] = service.xpath("x:Service", namespaces=ns)

    registered_standard_service = len(
        list(
            filter(
                lambda s: registered_code_regex.match(
                    s.xpath("string(x:ServiceCode)", namespaces=ns)
                )
                and s.xpath("x:StandardService", namespaces=ns),
                service_list,
            )
        )
    )
    unregistered_services = len(
        list(
            filter(
                lambda s: unregistered_code_regex.match(
                    s.xpath("string(x:ServiceCode)", namespaces=ns)
                ),
                service_list,
            )
        )
    )
    registered_flexible_service = len(
        list(
            filter(
                lambda s: registered_code_regex.match(
                    s.xpath("string(x:ServiceCode)", namespaces=ns)
                )
                and s.xpath("x:ServiceClassification/x:Flexible", namespaces=ns),
                service_list,
            )
        )
    )

    total_services = (
        registered_standard_service
        + registered_flexible_service
        + unregistered_services
    )

    # More than one services are allowed only when there is a registered flexible service.
    # If there is a registered standard service then no other service types should be present
    if total_services == 1 or (
        total_services > 1
        and registered_flexible_service == 1
        and registered_standard_service == 0
    ):
        return True

    return False
