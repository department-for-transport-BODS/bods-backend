from io import BytesIO
from pathlib import Path
from zipfile import ZipFile, ZIP_DEFLATED
from common import DbManager
from db.repositories.dataset_revision import DatasetRevisionRepository
from logger import logger
from s3 import S3
from bods_utils import sha1sum


def get_file_path_and_name(full_path_name):
    """
    Return file path and file name from full file path
    """
    file_path = Path(full_path_name)
    return file_path.parent, file_path.name


def lambda_handler(event, context):
    # Extract the bucket name and object key from the S3 event
    bucket = event["Bucket"]
    key = event["ObjectKey"]
    valid_files = event["ValidFiles"]

    # URL-decode the key if it has special characters
    key = key.replace("+", " ")

    try:
        # Get S3 handler
        s3_handler = S3(bucket_name=bucket)
        xml_files = []
        file_path, file_name = get_file_path_and_name(valid_files[0])
        valid_s3_folders = f"{file_path}/"
        for page in s3_handler.get_list_objects_v2(valid_s3_folders):
            if 'Contents' not in page:
                print(f"No files found in {valid_s3_folders}")
                continue

            for obj in page['Contents']:
                file_key = obj['Key']
                if file_key.endswith('/'):  # Skip folders
                    continue
                xml_files.append(file_key)
        msg = None
        if len(xml_files) == len(valid_files):
            logger.info(f"No modified files found in {valid_s3_folders}")
            msg = f"No modified files found in {valid_s3_folders}"
        else:
            logger.info(f"Modified files found in {valid_s3_folders}")
            # Create an in-memory zip file
            zip_buffer = BytesIO()
            with (ZipFile(zip_buffer, 'w', ZIP_DEFLATED) as zf):
                # Download file content from S3
                for file_key in valid_files:
                    file_obj = s3_handler.get_object(file_key)
                    zf.writestr(f"{file_path.parent}",
                                file_obj.read())
            # Reset buffer pointer
            zip_buffer.seek(0)

            # Upload the zip file back to S3
            logger.info(f"Zip file created")
            s3_handler.put_object(key, zip_buffer.getvalue())

            # Hashing the file
            logger.info(f"Hashing the file {key}")
            stream = s3_handler.get_object(key)
            hash_value = sha1sum(stream.read())

            # update modified hash to db
            logger.info(f"Updating the hash of {key} to db")
            dataset_revision = DatasetRevisionRepository(DbManager.get_db())
            revision = dataset_revision.get_by_id(event["DatasetRevisionId"])
            revision.modified_file_hash = hash_value
            dataset_revision.update(revision)
            msg = f"Modified hash is updated"
        return {
            "statusCode": 200,
            "body": msg
        }
    except Exception as err:
        logger.error("Error while re-zipping files")
        raise err
