"""
Description: Module contains the database functionality for
             FileProcessingResult table
"""
from datetime import datetime
from uuid import uuid4
from sqlalchemy.exc import SQLAlchemyError, NoResultFound
from common import BodsDB
from bods_exception import *
from logger import logger


def write_error_to_db(db, uuid, exceptions):
    status, error_status = "FAILURE", "SUSPICIOUS_FILE"
    if isinstance(exceptions, ClamConnectionError):
        status, error_status = "FAILURE", "SYSTEM_ERROR"
    elif isinstance(exceptions, SuspiciousFile):
        status, error_status = "FAILURE", "SUSPICIOUS_FILE"
    elif isinstance(exceptions, AntiVirusError):
        status, error_status = "FAILURE", "SUSPICIOUS_FILE"
    elif isinstance(exceptions, NestedZipForbidden):
        status, error_status = "FAILURE", "NESTED_ZIP_FORBIDDEN"
    elif isinstance(exceptions, ZipTooLarge):
        status, error_status = "FAILURE", "ZIP_TOO_LARGE"
    elif isinstance(exceptions, NoDataFound):
        status, error_status = "FAILURE", "NO_DATA_FOUND"
    elif isinstance(exceptions, FileTooLarge):
        status, error_status = "FAILURE", "FILE_TOO_LARGE"
    elif isinstance(exceptions, XMLSyntaxError):
        status, error_status = "FAILURE", "XML_SYNTAX_ERROR"
    elif isinstance(exceptions, DangerousXML):
        status, error_status = "FAILURE", "DANGEROUS_XML_ERROR"

    result_obj = PipelineFileProcessingResult(db)
    result = dict(
        status=status,
        completed=datetime.now(),
        error_code=get_file_processing_error_code(db, error_status)
    )
    result_obj.update(uuid, **result)


def get_file_processing_result_obj(db, **kwargs):
    return db.classes.pipelines_fileprocessingresult(
        task_id=kwargs.get('task_id'),
        status=kwargs.get('status'),
        filename=kwargs.get('filename'),
        pipeline_processing_step_id=kwargs.get('step'),
        revision_id=kwargs.get('revision')
    )


def get_record(db, class_name, filter_condition, error_message):
    with db.session as session:
        try:
            result = session.query(class_name).filter(filter_condition).one()
        except NoResultFound as error:
            logger.error(error_message)
            raise error
        else:
            return result


def get_file_processing_error_code(db, status):
    class_name = db.classes.pipeline_error_code
    filter_condition = class_name.status == status
    error_message = f"Processing error status {status} doesn't exist"
    return get_record(db, class_name, filter_condition, error_message)


def write_processing_step(db, name, category):
    with db.session as session_:
        try:
            class_name = db.classes.pipeline_processing_step
            new_step = class_name(name=name, category=category)
            session_.add(new_step)
            session_.commit()
            return new_step.id
        except SQLAlchemyError as err:
            session_.rollback()
            logger.error(f" Failed to add record {err}", exc_info=True)
            raise err


def file_processing_result_to_db(step_name):
    def decorator(func):
        def wrapper(event, context):
            _db = BodsDB()
            uuid = str(uuid4())
            try:
                file_path = event["Records"][0]["s3"]["object"]["key"]
                revision, file_name = file_path.split("/")
                step = write_processing_step(_db, step_name, "TIMETABLES")
                result = get_file_processing_result_obj(
                    db=_db,
                    task_id=uuid,
                    status="STARTED",
                    filename=file_name,
                    pipeline_processing_step_id=step,
                    revision_id=revision
                )
                fpr_ins = PipelineFileProcessingResult(_db)
                # Add lambda entry
                fpr_ins.create(result)

                # Call the original Lambda handler function
                result = func(event, context)

                # Add lambda exit
                params = dict(
                    status="SUCCESS",
                    completed=datetime.now()
                )
                fpr_ins.update(uuid, **params)

                return result
            except Exception as error:
                write_error_to_db(_db, uuid, error)
                raise error
        return wrapper
    return decorator


class PipelineFileProcessingResult:

    def __init__(self, db):
        self._db: BodsDB = db

    def create(self, file_processing_result):
        """
        Creates a new FileProcessingResult instance
        :param self: class instance
        :param file_processing_result: FileProcessingResult data
        :return: None if the operation was successful,
                 otherwise an exception
        """
        with self._db.session as session:
            try:
                session.add(file_processing_result)
                session.commit()
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
        with self._db.session as session:
            try:
                buf_ = self._db.classes.pipelines_fileprocessingresult
                result = session.query(buf_).filter(buf_.revision_id == revision_id).one()
            except NoResultFound as error:
                msg = f"Revision {revision_id } doesn't exist pipelines_fileprocessingresult"
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
        with self._db.session as session:
            try:
                # Get the record using task_id
                buf_ = self._db.classes.pipelines_fileprocessingresult
                result = session.query(buf_).filter(buf_.task_id == task_id).one()
                if not result:
                    logger.warning(f"No file processing result found for task {task_id}")
                    return None
                # update the record
                if kwargs.get("status"):
                    result.status = kwargs.get("status")
                if kwargs.get("completed"):
                    result.completed = kwargs.get("completed")
                if kwargs.get("error_message"):
                    result.error_message = kwargs.get("error_message")

                session.add(result)
                session.commit()
                return "File processing result updated successfully!"
            except Exception as error:
                session.rollback()
                msg = f"Failed to update file processing result for task {task_id} {error}"
                logger.error(msg)
                raise error
