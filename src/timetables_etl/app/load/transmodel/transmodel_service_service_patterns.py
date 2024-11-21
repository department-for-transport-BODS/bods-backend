"""
Association Table Linking transmodel_service and transmodel_servicepattern
"""

from structlog.stdlib import get_logger

from timetables_etl.app.database.client import BodsDB
from timetables_etl.app.database.models import (
    TransmodelService,
    TransmodelServicePattern,
    TransmodelServiceServicePattern,
)
from timetables_etl.app.database.repos import TransmodelServiceServicePatternRepo

log = get_logger()


def link_service_to_service_patterns(
    service: TransmodelService,
    service_patterns: list[TransmodelServicePattern],
    db: BodsDB,
) -> list[TransmodelServiceServicePattern]:
    """
    Associative table between service and service pattern
    """
    pattern_ids = [pattern.id for pattern in service_patterns]
    associations = [
        TransmodelServiceServicePattern(
            service_id=service.id, servicepattern_id=pattern_id
        )
        for pattern_id in pattern_ids
    ]
    result = TransmodelServiceServicePatternRepo(db).bulk_insert(associations)
    log.info(
        "Associations between Service and Service Pattern Created",
        service_id=service.id,
        service_pattern_ids=pattern_ids,
    )
    return result
