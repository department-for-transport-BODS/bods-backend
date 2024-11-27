import logging
from typing import Any, Dict, List

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
                query = session.query(self._db.classes.naptan_stoppoint).filter(
                    self._db.classes.naptan_stoppoint.atco_code.in_(atco_codes)
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

    def get_stop_area_map(self) -> List[Dict[str, Any]]:
        """
        Return a map of { <atco_code>: <stop_areas> } for all stops, excluding those with no stop areas.
        """
        try:
            with self._db.session as session:
                stops = (
                    session.query(
                        self._db.classes.naptan_stoppoint.atco_code,
                        self._db.classes.naptan_stoppoint.stop_areas,
                    )
                    .filter(self._db.classes.naptan_stoppoint.stop_areas != [])
                    .all()
                )
                return {stop.atco_code: stop.stop_areas for stop in stops}
        except Exception as exc:
            message = "Error retrieving stops excluding empty stop areas."
            logger.exception(message, exc_info=True)
            raise PipelineException(message) from exc
