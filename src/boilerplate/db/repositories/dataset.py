import logging
from common import BodsDB
from db.models import OrganisationDataset

from exception import PipelineException
from sqlalchemy.orm.exc import NoResultFound

logger = logging.getLogger(__name__)

class DatasetRepository:

    def __init__(self, db: BodsDB):
        self._db = db

    def get_by_id(self, id: int) -> OrganisationDataset:
        try:
            with self._db.session as session:
                result = session.query(self._db.classes.organisation_dataset).filter_by(id=id).one()
        except NoResultFound as exc:
            message = f"Dataset {id} does not exist."
            logger.exception(message, exc_info=True)
            raise PipelineException(message) from exc
        else:
            return result

