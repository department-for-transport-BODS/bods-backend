import logging
from sqlalchemy.orm.exc import NoResultFound

from common import BodsDB
db = BodsDB()

logger = logging.getLogger(__name__)

class DatasetETLResultCustomeMethods:
    SYSTEM_ERROR = "SYSTEM_ERROR"
    PENDING = "PENDING"
    RECEIVED = "RECEIVED"
    STARTED = "STARTED"
    SUCCESS = "SUCCESS"
    FAILURE = "FAILURE"
    READY = "READY"
    def to_error(self, task_name, error_code):
        if self.status != self.FAILURE:
            self.status = self.FAILURE
            self.completed = now()
            self.task_name_failed = task_name
            self.error_code = error_code

            #BELOW TO BE CHECKED
            # self.revision.to_error()
            # self.revision.save()

            # if (
            #     task_name == "dataset_validate"
            #     or task_name == "post_schema_dataset_validate"
            # ):
            #     # Currently the only error template we have is when the validation
            #     # fails. This may need to be redone if we expand notifying on errors
            #     send_endpoint_validation_error_notification(
            #         self.revision.dataset, task_name
            #     )

            self.save()
    
    def handle_general_pipeline_exception(
        self,
        exception: Exception,
        adapter: PipelineAdapter,
        message: str = None,
        task_name="dataset_validate",
    ):
        message = message or str(exception)
        adapter.error(message, exc_info=True)
        self.to_error(task_name, DatasetETLTaskResult.SYSTEM_ERROR)
        self.additional_info = message
        self.save()
        raise PipelineException(message) from exception
    
    def update_progress(self, progress: int):
        self.progress = progress
        self.save()

# subclass the automapped class
class DatasetETLTaskResult(db.classes.pipelines_datasetetltaskresult, DatasetETLResultCustomeMethods):
    pass
        
class PipelineException(Exception):
    """Basic exception for errors raised by a pipeline"""
    def __init__(self, message: Optional[str] = None):
        if message is None:
            # Set some default error message
            message = "An error occurred in the pipeline"
        super().__init__(message)

def get_etl_task_or_pipeline_exception(pk) -> DatasetETLTaskResult:
    try:
        db = BodsDB()
        with db.session as session:
            task = session.query(DatasetETLTaskResult).filter_by(id=pk).one()
    except NoResultFound as exc:
        message = f"DatasetETLTaskResult {pk} does not exist."
        logger.exception(message, exc_info=True)
        raise PipelineException(message) from exc
    else:
        return task