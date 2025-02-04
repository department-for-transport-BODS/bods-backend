"""
Convertion of Pydantic TXC Models to transmodel_bookingarrangements
"""

from common_layer.database.client import SqlDB
from common_layer.database.models import TransmodelService
from common_layer.database.repos.repo_transmodel_flexible import (
    TransmodelBookingArrangementsRepo,
)
from common_layer.txc.models import TXCService
from structlog.stdlib import get_logger

from ..transform.booking_arrangements import create_booking_arrangements

log = get_logger()


def process_booking_arrangements(
    txc_service: TXCService,
    tm_service: TransmodelService,
    db: SqlDB,
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
