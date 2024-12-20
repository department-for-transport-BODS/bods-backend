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
from common_layer.logger import logger
from sqlalchemy.exc import NoResultFound, SQLAlchemyError


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
    return exception_mapping.get(exception.__class__.__name__,
                                 "SUSPICIOUS_FILE")


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
        step = session.query(class_name).filter(
            class_name.name == name, class_name.category == category
        ).one_or_none()

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
            logger.info(f"processing step: {step_name}, event: {event}")
            _db = DbManager.get_db()
            task_id = str(uuid4())
            try:
                revision = get_revision(_db, int(event["DatasetRevisionId"]))
                step = get_or_create_step(_db,
                                          step_name.value,
                                          get_dataset_type(event))
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
                logger.info(f"lambda returns: {result}")

                # Update processing record on success
                PipelineFileProcessingResult(_db).update(
                    task_id, status="SUCCESS", completed=datetime.now()
                )
                return result
            except Exception as error:
                logger.error(error, exc_info=True)
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
                    **file_processing_result)
                session.add(row)
                session.commit()
                # session.refresh(row)
                return "File processing entity created successfully!"
            except SQLAlchemyError as err:
                session.rollback()
                logger.error(f" Failed to add record {err}", exc_info=True)
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
                    session.query(buf_).filter(
                        buf_.revision_id == revision_id).one()
                )
            except NoResultFound as error:
                msg = (
                    f"Revision {revision_id} "
                    f"doesn't exist pipelines_fileprocessingresult"
                )
                logger.error(msg)
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
                record = session.query(model).filter(
                    model.task_id == task_id).one_or_none()
                if not record:
                    logger.warning(
                        f"No file processing result found for task {task_id}"
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
                msg = (
                    f"Failed to update file processing result for task "
                    f"{task_id} {error}"
                )
                logger.error(msg)
                raise error


def txc_file_attributes_to_db(revision_id, attributes):
    """
    Writes TXC file attributes to the database in bulk.
    """
    try:
        db_: BodsDB = DbManager.get_db()
        with db_.session as session_:
            db_table = db_.classes.organisation_txcfileattributes
            buffer = [
                db_table(
                    revision_id=revision_id,
                    schema_version=it.header.schema_version,
                    modification=it.header.modification,
                    revision_number=it.header.revision_number,
                    creation_datetime=it.header.creation_datetime,
                    modification_datetime=it.header.modification_datetime,
                    filename=it.header.filename,
                    national_operator_code=it.operator.national_operator_code,
                    licence_number=it.operator.licence_number,
                    service_code=it.service.service_code,
                    origin=it.service.origin,
                    destination=it.service.destination,
                    operating_period_start_date=it.service.operating_period_start_date,
                    operating_period_end_date=it.service.operating_period_end_date,
                    public_use=it.service.public_use,
                    line_names=[line.line_name for line in it.service.lines],
                    hash=it.hash,
                )
                for it in attributes
            ]
            session_.bulk_save_objects(buffer)
            session_.commit()
    except Exception as error:
        session_.rollback()
        logger.error(f"Failed to add record {error}", exc_info=True)
        raise error
