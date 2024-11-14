from io import BytesIO
from boilerplate.db.file_processing_result import (
    txc_file_attributes_to_db,
    file_processing_result_to_db,
)
from boilerplate.logger import logger
from boilerplate.s3 import S3
from boilerplate.timetables.transxchange import TransXChangeDatasetParser
from boilerplate.timetables.dataclasses.transxchange import TXCFile


@file_processing_result_to_db("TxC attributes extraction")
def lambda_handler(event, context):
    """
    Main lambda handler
    """
    # Extract the bucket name and object key from the S3 event
    bucket = event["Records"][0]["s3"]["bucket"]["name"]
    key = event["Records"][0]["s3"]["object"]["key"]
    # ToDo: retrival of revision id is based on payload
    revision_id = event["Records"][0]["s3"]["object"]["revision_id"]

    # URL-decode the key if it has special characters
    key = key.replace("+", " ")
    try:
        # Get S3 handler
        s3_handler = S3(bucket_name=bucket)

        # Fetch the object from S3
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
        txc_file_attributes_to_db(revision_id=revision_id, attributes=files)

    except Exception as exc:
        file_path = f"s3://{bucket}/{key}"
        msg = f"Error while extracting TxC attributes from {file_path}: {str(exc)}"
        logger.error(msg)
        raise exc


# event = {
#    "Records": [
#       {
#          "s3": {
#             "bucket": {
#                "name": "bodds-dev",
#             },
#             "object": {
#                "key": "4.zip",
#                "revision_id": 35657,
#             }
#          }
#       }
#    ]
# }
# lambda_handler(event, None)
