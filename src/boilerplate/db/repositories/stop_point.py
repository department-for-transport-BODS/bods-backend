import logging
from typing import Any, List

from common import BodsDB
from exceptions.pipeline_exceptions import PipelineException

logger = logging.getLogger(__name__)


class StopPointRepository:

    def __init__(self, db: BodsDB):
        self._db = db

    # TODO: Typing for return type (DB Model)
    def get_count(self, atco_codes: List[str], **filter_kwargs) -> List[Any]:
        try:
            with self._db.session as session:
                query = (
                    session.query(self._db.classes.naptan_stoppoint).filter(
                        self._db.classes.naptan_stoppoint.atco_code.in_(atco_codes)
                    )
                )
                if filter_kwargs:
                    query = query.filter_by(**filter_kwargs)
                result = query.count()
        except Exception as exc:
            message = f"Exception counting StopPoints with atco_code in {atco_codes} and fields {filter_kwargs}"
            logger.exception(message, exc_info=True)
            raise PipelineException(message) from exc
        else:
            return result
