import json
import re
from common import DbManager
from db.file_processing_result import file_processing_result_to_db
from db.repositories.post_schema_violation import PostSchemaViolationRepository
from db.repositories.dataset_revision import get_revision
from logger import logger
from s3 import S3
from timetables.transxchange import TransXChangeDocument

STEP_NAME = "Timetable Post Schema Check"


def get_violation(file_obj):
    """
    Get schema violation from file object.
    """
    txc_doc = TransXChangeDocument(file_obj)
    results = re.findall("\\\\", txc_doc.get_file_name())
    if len(results) > 0:
        return "PII_ERROR"


@file_processing_result_to_db(step_name=STEP_NAME)
def lambda_handler(event, context):
    """
    Main lambda handler
    """
    logger.info(f"Received event:{json.dumps(event, indent=2)}")
    # Extract the bucket name and object key from the S3 event
    bucket = event["Records"][0]["s3"]["bucket"]["name"]
    key = event["Records"][0]["s3"]["object"]["key"]
    filename = key.split("/")[-1]
    dataset_etl_task_result_id = key.split("/")[0]

    # Get revision
    db = DbManager.get_db()
    revision = get_revision(db, dataset_etl_task_result_id)

    # URL-decode the key if it has special characters
    filename = filename.replace("+", " ")
    try:
        s3_handler = S3(bucket_name=bucket)
        violation = get_violation(s3_handler.get_object(file_path=filename))
        if violation:
            params = dict(filename=filename,
                          details=violation,
                          revision_id=revision.id)
            post_schema_violation = PostSchemaViolationRepository(db)
            post_schema_violation.create(**params)
    except Exception as e:
        logger.error(f"Error {STEP_NAME} '{key}' from bucket '{bucket}'")
        raise e
    msg = f"Successfully ran {STEP_NAME} for file '{key}' from '{bucket}'"
    return {
        "statusCode": 200,
        "body": msg
    }
