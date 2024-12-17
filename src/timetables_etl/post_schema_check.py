import json
import re

from common_layer.db.constants import StepName
from common_layer.db.file_processing_result import file_processing_result_to_db
from common_layer.db.manager import DbManager
from common_layer.db.repositories.dataset_revision import get_revision
from common_layer.db.repositories.post_schema_violation import (
    PostSchemaViolationRepository,
)
from common_layer.logger import logger
from common_layer.s3 import S3
from common_layer.timetables.transxchange import TransXChangeDocument


def get_violation(file_obj):
    """
    Get schema violation from file object.
    """
    txc_doc = TransXChangeDocument(file_obj)
    results = re.findall("\\\\", txc_doc.get_file_name())
    if len(results) > 0:
        return "PII_ERROR"


@file_processing_result_to_db(step_name=StepName.TIMETABLE_POST_SCHEMA_CHECK)
def lambda_handler(event, context):
    """
    Main lambda handler
    """
    # Extract the bucket name and object key from the S3 event
    bucket = event["Bucket"]
    key = event["ObjectKey"]

    # Get revision
    db = DbManager.get_db()
    revision = get_revision(db, int(event["DatasetRevisionId"]))

    # URL-decode the key if it has special characters
    filename = key.replace("+", " ")
    try:
        s3_handler = S3(bucket_name=bucket)
        violation = get_violation(s3_handler.get_object(file_path=filename))
        if violation:
            params = dict(filename=filename, details=violation, revision_id=revision.id)
            post_schema_violation = PostSchemaViolationRepository(db)
            post_schema_violation.create(**params)
    except Exception as e:
        logger.error(
            f"Error {StepName.TIMETABLE_POST_SCHEMA_CHECK} '{key}' from bucket '{bucket}'"
        )
        raise e
    msg = f"Successfully ran {StepName.TIMETABLE_POST_SCHEMA_CHECK} for file '{key}' from '{bucket}'"
    return {"statusCode": 200, "body": msg}
