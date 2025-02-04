"""
Parsing of FlexibleService in a TXCService
"""

from lxml.etree import _Element  # type: ignore
from structlog.stdlib import get_logger

from ..models.txc_service_flexible import (
    TXCBookingArrangements,
    TXCFixedStopUsage,
    TXCFlexibleJourneyPattern,
    TXCFlexibleService,
    TXCFlexibleStopUsage,
    TXCPhone,
)
from .utils_tags import get_elem_bool_default, get_element_text

log = get_logger()


def parse_flexible_stop_usage(
    stop_usage_xml: _Element,
) -> TXCFlexibleStopUsage | TXCFixedStopUsage | None:
    """
    Parse flexible stops that may be used for boarding/alighting in a flexible service
    """
    stop_point_ref: str | None = get_element_text(stop_usage_xml, "StopPointRef")
    if not stop_point_ref:
        return None

    if stop_usage_xml.tag == "FlexibleStopUsage":
        return TXCFlexibleStopUsage(StopPointRef=stop_point_ref)
    timing_status: str | None = get_element_text(stop_usage_xml, "TimingStatus")
    return TXCFixedStopUsage(
        StopPointRef=stop_point_ref, TimingStatus=timing_status or ""
    )


def parse_booking_arrangements(booking_xml: _Element) -> TXCBookingArrangements | None:
    """
    Parse booking arrangements for flexible services including contact details
    """
    description: str | None = get_element_text(booking_xml, "Description")

    if not description:
        log.warning(
            "Flexible Service Booking Arrangements Requires Description, skipping"
        )
        return None
    description = " ".join(description.split())
    phone_xml: _Element | None = booking_xml.find("Phone")
    tel_number: str | None = (
        get_element_text(phone_xml, "TelNationalNumber")
        if phone_xml is not None
        else None
    )
    phone: TXCPhone | None = (
        TXCPhone(TelNationalNumber=tel_number) if tel_number is not None else None
    )
    return TXCBookingArrangements(
        Description=description,
        Phone=phone,
        Email=get_element_text(booking_xml, "Email"),
        WebAddress=get_element_text(booking_xml, "WebAddress"),
        AllBookingsTaken=get_elem_bool_default(booking_xml, "AllBookingsTaken", False),
    )


def parse_flexible_journey_pattern(
    pattern_xml: _Element,
) -> TXCFlexibleJourneyPattern | None:
    """Parse flexible journey patterns defining possible stop combinations for flexible routes"""
    pattern_id: str | None = pattern_xml.get("id")
    direction: str | None = get_element_text(pattern_xml, "Direction")

    if not pattern_id or not direction:
        return None

    stop_points: list[TXCFlexibleStopUsage | TXCFixedStopUsage] = []
    flexible_zones: list[TXCFlexibleStopUsage] = []

    for stop_xml in pattern_xml.findall("StopPointsInSequence/*"):
        stop = parse_flexible_stop_usage(stop_xml)
        if stop:
            stop_points.append(stop)

    for stop_xml in pattern_xml.findall("FlexibleZones/*"):
        stop = parse_flexible_stop_usage(stop_xml)
        if isinstance(stop, TXCFlexibleStopUsage):
            flexible_zones.append(stop)

    booking_xml: _Element | None = pattern_xml.find("BookingArrangements")
    booking: TXCBookingArrangements | None = (
        parse_booking_arrangements(booking_xml) if booking_xml is not None else None
    )

    return TXCFlexibleJourneyPattern(
        id=pattern_id,
        Direction=direction,
        StopPointsInSequence=stop_points,
        FlexibleZones=flexible_zones,
        BookingArrangements=booking,
    )


def parse_flexible_service(flex_service_xml: _Element) -> TXCFlexibleService | None:
    """
    Parse flexible service definitions for demand responsive transport services
    """
    origin: str | None = get_element_text(flex_service_xml, "Origin")
    destination: str | None = get_element_text(flex_service_xml, "Destination")

    if not origin or not destination:
        return None

    patterns: list[TXCFlexibleJourneyPattern] = []
    for pattern_xml in flex_service_xml.findall("FlexibleJourneyPattern"):
        pattern = parse_flexible_journey_pattern(pattern_xml)
        if pattern:
            patterns.append(pattern)

    use_all_stops: bool = get_elem_bool_default(
        flex_service_xml, "UseAllStopPoints", False
    )

    return TXCFlexibleService(
        Origin=origin,
        Destination=destination,
        FlexibleJourneyPattern=patterns,
        UseAllStopPoints=use_all_stops,
    )
