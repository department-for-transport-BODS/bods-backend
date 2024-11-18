"""
Helper Functions to Query the TXCService Pydantic Models
"""

from datetime import date

from structlog.stdlib import get_logger

from ..models.txc_service import TXCService

log = get_logger()


def get_line_names(services: list[TXCService]) -> list[str]:
    """
    Get a list of line names from a TXC's Services
    """
    line_names = [line.LineName for service in services for line in service.Lines]

    if not line_names:
        log.warning("No line names found")

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
    """
    TODO: Handle Flexible Service Origins
    """
    origins = [service.StandardService.Origin for service in services]
    if not origins:
        log.warning("No services with origins found")
    return origins


def get_service_destinations(services: list[TXCService]) -> list[str]:
    """
    TODO: Handle Flexible Service Origins
    """
    destinations = [service.StandardService.Destination for service in services]
    if not destinations:
        log.warning("No services with Destinations found")
    return destinations
