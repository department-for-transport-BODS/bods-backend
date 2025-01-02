"""
Description: Module contains the database functionality for
             FileProcessingResult table
"""

from datetime import datetime
from uuid import uuid4

from common_layer.db import BodsDB
from common_layer.db.constants import StepName
from common_layer.db.manager import DbManager
from common_layer.db.repositories.dataset_revision import get_revision
from sqlalchemy.exc import NoResultFound, SQLAlchemyError
from structlog.stdlib import get_logger

log = get_logger()


def map_exception_to_error_code(exception):
    """
    Maps exceptions to corresponding error codes.
    """
    exception_mapping = {
        "ClamConnectionError": "SYSTEM_ERROR",
        "SuspiciousFile": "SUSPICIOUS_FILE",
        "AntiVirusError": "SUSPICIOUS_FILE",
        "NestedZipForbidden": "NESTED_ZIP_FORBIDDEN",
        "ZipTooLarge": "ZIP_TOO_LARGE",
        "NoDataFound": "NO_DATA_FOUND",
        "FileTooLarge": "FILE_TOO_LARGE",
        "XMLSyntaxError": "XML_SYNTAX_ERROR",
        "DangerousXML": "DANGEROUS_XML_ERROR",
        "NoSchemaDefinition": "NO_SCHEMA_DEFINITION",
        "NoRowFound": "NO_ROW_FOUND",
    }
    return exception_mapping.get(exception.__class__.__name__, "SUSPICIOUS_FILE")


def write_error_to_db(db, uuid, exception):
    error_status = map_exception_to_error_code(exception)
    error_code = get_file_processing_error_code(db, error_status)
    update_data = {
        "status": "FAILURE",
        "completed": datetime.now(),
        "error_code": error_code,
    }
    PipelineFileProcessingResult(db).update(uuid, **update_data)


def get_file_processing_error_code(db, status):
    """
    Retrieves the error code object for a given status.
    """
    model = db.classes.pipelines_pipelineerrorcode
    with db.session as session:
        return session.query(model).filter(model.error == status).one()


def get_or_create_step(db, name, category):
    """
    Gets an existing step or creates it if it doesn't exist.
    """
    with db.session as session:
        class_name = db.classes.pipelines_pipelineprocessingstep
        step = (
            session.query(class_name)
            .filter(class_name.name == name, class_name.category == category)
            .one_or_none()
        )

        if step is None:
            step = class_name(name=name, category=category)
            session.add(step)
            session.commit()
            # session.refresh(step)
        return step


def get_dataset_type(event):
    dataset_type = event.get("DatasetType", "timetables")
    return "TIMETABLES" if dataset_type.startswith("timetable") else "FARES"


def file_processing_result_to_db(step_name: StepName):
    def decorator(func):
        def wrapper(event, context):
            log.info("Processing Step", step_name=step_name, input_data=event)
            _db = DbManager.get_db()
            task_id = str(uuid4())
            try:
                revision = get_revision(_db, int(event["DatasetRevisionId"]))
                step = get_or_create_step(_db, step_name.value, get_dataset_type(event))
                # Create initial processing record
                processing_result = {
                    "task_id": task_id,
                    "status": "STARTED",
                    "filename": event["ObjectKey"].split("/")[-1],
                    "pipeline_processing_step_id": step.id,
                    "revision_id": revision.id,
                    "created": datetime.now(),
                    "modified": datetime.now(),
                }
                PipelineFileProcessingResult(_db).create(processing_result)

                # Execute the Lambda function
                result = func(event, context)
                log.info(" returns: {result}")

                # Update processing record on success
                PipelineFileProcessingResult(_db).update(
                    task_id, status="SUCCESS", completed=datetime.now()
                )
                return result
            except Exception as error:
                log.error("An Exception Occured", exc_info=True)
                write_error_to_db(_db, task_id, error)
                raise error

        return wrapper

    return decorator


class PipelineFileProcessingResult:

    def __init__(self, db):
        self._db: BodsDB = db

    @property
    def db(self):
        return self._db

    def create(self, file_processing_result):
        """
        Creates a new FileProcessingResult instance
        :param self: class instance
        :param file_processing_result: FileProcessingResult data
        :return: None if the operation was successful,
                 otherwise an exception
        """
        with self.db.session as session:
            try:
                row = self.db.classes.pipelines_fileprocessingresult(
                    **file_processing_result
                )
                session.add(row)
                session.commit()
                # session.refresh(row)
                return "File processing entity created successfully!"
            except SQLAlchemyError as err:
                session.rollback()
                log.error(
                    "Failed to Create File Processing Result Entry", exc_info=True
                )
                raise err

    def read(self, revision_id):
        """
        Get file processing result by revision ID
        :param self: class instance
        :param revision_id: int
        :return: return file processing result by revision ID
                 or None if no file processing result was found
        """
        with self.db.session as session:
            try:
                buf_ = self.db.classes.pipelines_fileprocessingresult
                result = (
                    session.query(buf_).filter(buf_.revision_id == revision_id).one()
                )
            except NoResultFound as error:
                msg = (
                    f"Revision {revision_id} "
                    f"doesn't exist pipelines_fileprocessingresult"
                )
                log.error(msg)
                raise error
            else:
                return result

    def update(self, task_id, **kwargs):
        """
        Update file processing result by revision ID
        :param self: class instance
        :param task_id: uuid.uuid4
        :param kwargs: dict of fields to update
        :return:
        """
        with self.db.session as session:
            try:
                # Get the record using task_id
                model = self.db.classes.pipelines_fileprocessingresult
                record = (
                    session.query(model).filter(model.task_id == task_id).one_or_none()
                )
                if not record:
                    log.warning(
                        "No file processing result found for task",
                        task_id=task_id,
                    )
                    return None
                # update the record
                for field, value in kwargs.items():
                    setattr(record, field, value)
                session.add(record)
                session.commit()
                # session.refresh(record)
                return "File processing result updated successfully!"
            except Exception as error:
                session.rollback()
                log.error(
                    "Failed to update file processing result for task",
                    task_id=task_id,
                    exc_info=True,
                )
                raise error
