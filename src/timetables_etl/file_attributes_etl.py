from io import BytesIO
from common_layer.db.manager import DbManager
from common_layer.db.constants import StepName
from common_layer.db.file_processing_result import (
    txc_file_attributes_to_db,
    file_processing_result_to_db,
)
from common_layer.db.repositories.dataset_revision import get_revision
from common_layer.logger import logger
from common_layer.s3 import S3
from common_layer.timetables.transxchange import TransXChangeDatasetParser
from common_layer.timetables.dataclasses.transxchange import TXCFile


@file_processing_result_to_db(StepName.TXC_ATTRIBUTE_EXTRACTION)
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
    key = key.replace("+", " ")
    try:
        # Get S3 handler
        s3_handler = S3(bucket_name=bucket)

        # Fetch the object from common_layer.s3
        file_object = BytesIO(s3_handler.get_object(key).read())
        # file_object = s3_handler.get_object(file_path=key)

        parser = TransXChangeDatasetParser(file_object)
        files = [
            TXCFile.from_txc_document(doc, use_path_filename=True)
            for doc in parser.get_documents()
        ]
        if not files:
            logger.error(f"No file to process - s3://{bucket}/{key}")
            raise Exception(f"No file to process - s3://{bucket}/{key}")

        # write to db, table name organisation_txcfileattributes
        txc_file_attributes_to_db(revision_id=revision.id, attributes=files)

    except Exception as exc:
        file_path = f"s3://{bucket}/{key}"
        msg = f"Error while extracting TxC attributes from {file_path}: {str(exc)}"
        logger.error(msg)
        raise exc
