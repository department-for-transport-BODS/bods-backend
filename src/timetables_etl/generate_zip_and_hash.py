from pathlib import Path
from tempfile import NamedTemporaryFile
from zipfile import ZIP_DEFLATED, ZipFile

from common_layer.db.repositories.dataset_revision import update_file_hash_in_db
from common_layer.json_logging import configure_logging
from common_layer.s3 import S3
from common_layer.utils import sha1sum
from structlog.stdlib import get_logger

log = get_logger()


def get_file_path_and_name(full_path_name):
    """
    Return file path and file name from full file path
    """
    file_path = Path(full_path_name)
    return file_path.parent, file_path.name


def get_files_in_s3_folder(s3_handler, s3_folder):
    """
    Get list of files in s3 folder
    """
    files = []
    for page in s3_handler.get_list_objects_v2(s3_folder):
        if "Contents" not in page:
            print(f"No files found in {s3_folder}")
            continue

        for obj in page["Contents"]:
            file_key = obj["Key"]
            if file_key.endswith("/"):  # Skip folders
                continue
            files.append(file_key)
    return files


def create_zip_archive(s3_handler, zip_filename, files):
    """
    Create zip archive in tmp folder
    """
    with NamedTemporaryFile(suffix=zip_filename, delete=False) as tmp_file:
        with ZipFile(tmp_file.name, "w", ZIP_DEFLATED) as zf:
            for file_key in files:
                file_obj = s3_handler.get_object(file_key)
                zf.writestr(file_key, file_obj.read())
        tmp_file.flush()
        return tmp_file.name


def lambda_handler(event, context):
    """
    Lambda handler to recreate zip archive
    """
    configure_logging()
    bucket = event["Bucket"]
    key = event["ObjectKey"]
    valid_files = event["ValidFiles"]

    # URL-decode the key if it has special characters
    key = key.replace("+", " ")

    try:
        # Get S3 handler
        s3_handler = S3(bucket_name=bucket)

        file_path, file_name = get_file_path_and_name(valid_files[0])
        valid_s3_folders = f"{file_path}/"
        xml_files = get_files_in_s3_folder(s3_handler, valid_s3_folders)

        msg = None
        if len(xml_files) == len(valid_files):
            log.info(f"No modified files found in {valid_s3_folders}")
            msg = f"No modified files found in {valid_s3_folders}"
        else:
            log.info(
                "Modified files found",
                valid_s3_folders=valid_s3_folders,
            )

            temp_filename = create_zip_archive(
                s3_handler, key.split("/")[-1], xml_files
            )

            # Upload the zip file directly to S3
            log.info("Uploading zip file to S3", key=key)
            with open(temp_filename, "rb") as temp_file_data:
                s3_handler.put_object(key, temp_file_data.read())

            # Hashing the file
            log.info("Hashing the file", key=key)
            stream = s3_handler.get_object(key)

            update_file_hash_in_db(
                event["ObjectKey"],
                event["DatasetRevisionId"],
                modified_file_hash=sha1sum(stream.read()),
            )
            msg = f"Modified hash is updated"
        return {"statusCode": 200, "body": msg}
    except Exception as err:
        log.error("Error while re-zipping files", exc_info=True)
        raise err
