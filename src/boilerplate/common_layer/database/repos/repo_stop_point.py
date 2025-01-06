import logging
from typing import Any, Dict, Iterable, List

from common_layer.database import SqlDB
from common_layer.database.models.model_naptan import NaptanStopPoint
from common_layer.exceptions.pipeline_exceptions import PipelineException

logger = logging.getLogger(__name__)


class StopPointRepo:

    def __init__(self, db: SqlDB):
        self._db = db

    def get_count(self, atco_codes: List[str], **filter_kwargs) -> int:
        try:
            with self._db.session_scope() as session:
                query = session.query(NaptanStopPoint).filter(
                    NaptanStopPoint.atco_code.in_(atco_codes)
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

    def get_stop_area_map(self) -> Iterable[Dict[str, Any]]:
        """
        Return a map of { <atco_code>: <stop_areas> } for all stops, excluding those with no stop areas.
        """
        try:
            with self._db.session_scope() as session:
                stops = (
                    session.query(
                        NaptanStopPoint.atco_code,
                        NaptanStopPoint.stop_areas,
                    )
                    .filter(NaptanStopPoint.stop_areas != [])
                    .all()
                )
                return {stop.atco_code: stop.stop_areas for stop in stops}
        except Exception as exc:
            message = "Error retrieving stops excluding empty stop areas."
            logger.exception(message, exc_info=True)
            raise PipelineException(message) from exc
