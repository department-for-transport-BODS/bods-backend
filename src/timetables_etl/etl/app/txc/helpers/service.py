"""
Helper Functions to Query the TXCService Pydantic Models
"""

from datetime import date

from structlog.stdlib import get_logger

from ..models.txc_service import TXCService

log = get_logger()


def get_line_names(service: TXCService) -> list[str]:
    """Get all line names from a single TXC Service"""
    line_names = [line.LineName for line in service.Lines]

    if not line_names:
        log.warning("No line names found for service", service_code=service.ServiceCode)

    return line_names


def get_all_line_names(services: list[TXCService]) -> list[str]:
    """Get all line names across multiple TXC Services"""
    line_names = [name for service in services for name in get_line_names(service)]

    if not line_names:
        log.warning("No line names found across services")

    return line_names


def get_service_start_dates(services: list[TXCService]) -> list[date]:
    """Get all service start dates."""
    if not services:
        log.warning("No services found")
        return []
    return [service.StartDate for service in services]


def get_service_end_dates(services: list[TXCService]) -> list[date]:
    """Get all service end dates."""
    if not services:
        log.warning("No services found")
        return []
    dates = [service.EndDate for service in services if service.EndDate is not None]
    if not dates:
        log.warning("No service end dates found")
    return dates


def get_service_origins(services: list[TXCService]) -> list[str]:
    """Get origins from both standard and flexible services."""
    origins = [
        origin
        for service in services
        if (
            origin := (
                (service.StandardService and service.StandardService.Origin)
                or (service.FlexibleService and service.FlexibleService.Origin)
            )
        )
    ]

    if not origins:
        log.warning("No services with origins found")
    return origins


def get_service_destinations(services: list[TXCService]) -> list[str]:
    """Get destinations from both standard and flexible services."""
    destinations = [
        destination
        for service in services
        if (
            destination := (
                (service.StandardService and service.StandardService.Destination)
                or (service.FlexibleService and service.FlexibleService.Destination)
            )
        )
    ]

    if not destinations:
        log.warning("No services with destinations found")
    return destinations
