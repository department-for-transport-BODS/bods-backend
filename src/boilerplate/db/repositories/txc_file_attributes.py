import logging
from typing import List, Optional
from common import BodsDB
from db.models import OrganisationTxcfileattributes
from exception import PipelineException
from sqlalchemy.orm.exc import NoResultFound

logger = logging.getLogger(__name__)


class TxcFileAttributesRepository:

    def __init__(self, db: BodsDB):
        self._db = db

    def get(self, **filter_kwargs) -> Optional[OrganisationTxcfileattributes]:
        try:
            with self._db.session as session:
                result = (
                    session.query(self._db.classes.organisation_txcfileattributes).filter_by(**filter_kwargs).scalar()
                )
        except Exception as exc:
            message = f"Exception getting TXCFileAttributes with fields {filter_kwargs}"
            logger.exception(message, exc_info=True)
            raise PipelineException(message) from exc
        else:
            return result

    def get_all(self, **filter_kwargs) -> List[OrganisationTxcfileattributes]:
        try:
            with self._db.session as session:
                result = (
                    session.query(self._db.classes.organisation_txcfileattributes).filter_by(**filter_kwargs).all()
                )
        except Exception as exc:
            message = f"Exception getting all TXCFileAttributes with fields {filter_kwargs}"
            logger.exception(message, exc_info=True)
            raise PipelineException(message) from exc
        else:
            return result

    def exists(self, **filter_kwargs) -> bool:
        try:
            result = self.get(**filter_kwargs) is not None
        except Exception as exc:
            message = f"Exception checking existence of TXCFileAttributes with fields {filter_kwargs}"
            logger.exception(message, exc_info=True)
            raise PipelineException(message) from exc
        else:
            return result
