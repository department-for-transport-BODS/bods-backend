import os
import json
from pathlib import Path
from logger import logger
from s3 import S3
from zipfile import ZipFile
from lxml import etree
from boilerplate.transxchange import TransXChangeDocument
from db.post_schema_violation import PostSchemaViolationRepository
#from db.dataset_revision import DatasetRevisionRepository
from common import BodsDB
    
class PostSchemaValidator:
    def __init__(self, file_object):
        self.violations = []
        self.txc_doc = TransXChangeDocument(file_object)
    def check_file_names_pii_information(self):
        """
        Checks if FileName attribute within the TransXchange root
        element has personal identifiable information (PII).
        """
        result = []
        file_name_pii_check = re.findall("\\\\", self.txc_doc.get_file_name())
        if len(file_name_pii_check) > 0:
            return True
        return False
    def get_violations(self):
        """
        Returns any revision violations.
        """
        result = self.check_file_names_pii_information()
        if result:
            self.violations.append('PII_ERROR')
        return self.violations
@file_processing_result_to_db(step_name="Timetable Post Schema Check")
def lambda_handler(event, context):
    """
    Main lambda handler
    """
    logger.info(f"Received event:{json.dumps(event, indent=2)}")
    # Extract the bucket name and object key from the S3 event
    bucket = event["Records"][0]["s3"]["bucket"]["name"]
    key = event["Records"][0]["s3"]["object"]["key"]
    filename = key.split("/")[-1]
    revision_id = key.split("/")[0]
    
    db = DbManager.get_db()
    revision = get_dataset_revision(revision_id=revision_id)
    # URL-decode the key if it has special characters
    filename = filename.replace("+", " ")
    try:
        s3_handler = S3(bucket_name=bucket)
        file_object = s3_handler.get_object(file_path=filename)
        validator = PostSchemaValidator(file_object)
        violations += validator.get_violations()
        
        post_schema_violation = PostSchemaViolationRepository(db)
        post_schema_violation.create(violations)
    except Exception as e:
        logger.error(f"Error scanning object '{key}' from bucket '{bucket}'")
        raise e
    return {
        "statusCode": 200,
        "body": f"Successfully ran the file schema check for file '{key}' from bucket '{bucket}' with {len(violations)} violations",
    }