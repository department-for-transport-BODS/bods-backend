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
from timetables_etl.app.database.repos import (
    ServicePatternAssociation,
    TransmodelServiceServicePatternRepo,
)

log = get_logger()


def link_service_to_service_patterns(
    service: TransmodelService,
    service_patterns: list[TransmodelServicePattern],
    db: BodsDB,
) -> list[TransmodelServiceServicePattern]:
    """
    Associative table between service and service pattern
    """
    associations = [
        ServicePatternAssociation(service_id=service.id, pattern_id=pattern.id)
        for pattern in service_patterns
    ]
    result = TransmodelServiceServicePatternRepo(db).add_associations(associations)
    log.info("Associations between Service and Service Pattern Created")
    return result
