"""
Transmodel Booking Arrangements
"""

from datetime import UTC, datetime
from typing import NamedTuple

from common_layer.database.models import (
    TransmodelBookingArrangements,
    TransmodelService,
)
from common_layer.xml.txc.models import TXCService
from structlog.stdlib import get_logger

log = get_logger()


class ArrangementKey(NamedTuple):
    """Unique key for identifying duplicate booking arrangements."""

    description: str
    email: str | None
    phone: str | None
    web_address: str | None


def create_booking_arrangements(
    txc_service: TXCService, tm_service: TransmodelService
) -> list[TransmodelBookingArrangements]:
    """
    Create a booking Arrangement Row
    """
    if not txc_service.FlexibleService:
        return []

    unique_arrangements: dict[ArrangementKey, TransmodelBookingArrangements] = {}
    now = datetime.now(UTC)

    for pattern in txc_service.FlexibleService.FlexibleJourneyPattern:
        if not pattern.BookingArrangements:
            continue

        booking = pattern.BookingArrangements
        arrangement_key = ArrangementKey(
            description=booking.Description,
            email=booking.Email,
            phone=booking.Phone.TelNationalNumber if booking.Phone else None,
            web_address=booking.WebAddress,
        )

        if arrangement_key not in unique_arrangements:
            arrangement = TransmodelBookingArrangements(
                description=booking.Description,
                email=booking.Email,
                phone_number=booking.Phone.TelNationalNumber if booking.Phone else None,
                web_address=booking.WebAddress,
                created=now,
                last_updated=now,
                service_id=tm_service.id,
            )
            unique_arrangements[arrangement_key] = arrangement
    booking_arrangements = list(unique_arrangements.values())
    log.info(
        "Found Flexible Service Booking Arrangements", count=len(booking_arrangements)
    )
    return booking_arrangements
