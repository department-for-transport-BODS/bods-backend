"""
Convertion of Pydantic TXC Models to transmodel_bookingarrangements
"""

from structlog.stdlib import get_logger

from ..database.client import BodsDB
from ..database.models import TransmodelService
from ..database.repos.repo_transmodel_flexible import TransmodelBookingArrangementsRepo
from ..transform.booking_arrangements import create_booking_arrangements
from ..txc.models import TXCService

log = get_logger()


def process_booking_arrangements(
    txc_service: TXCService,
    tm_service: TransmodelService,
    db: BodsDB,
):
    """
    Process TXC Booking Arrangements
    """
    booking_arrangements = create_booking_arrangements(txc_service, tm_service)
    result = TransmodelBookingArrangementsRepo(db).bulk_insert(booking_arrangements)
    log.info(
        "Added Flexible Service Booking Arrangements to DB",
        tm_service_id=tm_service.id,
        txc_service_code=txc_service.ServiceCode,
        count=len(result),
    )
    return result
