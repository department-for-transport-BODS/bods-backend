"""
DownloadDatasetLambda lambda function
"""

from datetime import UTC, datetime
from pathlib import Path
from typing import Any
from urllib.parse import unquote

import common_layer.aws.datadog.tracing  # type: ignore # pylint: disable=unused-import
from aws_lambda_powertools.utilities.typing import LambdaContext
from common_layer.database import SqlDB
from common_layer.database.models import OrganisationDatasetRevision
from common_layer.database.repos import (
    ETLTaskResultRepo,
    OrganisationDatasetRevisionRepo,
)
from common_layer.db.constants import StepName
from common_layer.db.file_processing_result import file_processing_result_to_db
from common_layer.s3 import S3
from structlog.stdlib import get_logger

from .db_operations import DT_FORMAT, update_dataset_revision
from .file_download import download_file
from .models import DownloadDatasetInputData, FileType

log = get_logger()


def upload_file_to_s3(file_to_upload: Path, bucket_name: str, object_name: str) -> None:
    """
    Upload the file to s3 bucket
    """
    s3_handler = S3(bucket_name=bucket_name)
    with open(file_to_upload, "rb") as temp_file_data:
        s3_handler.put_object(object_name, temp_file_data.read())


def make_remote_file_name(
    revision: OrganisationDatasetRevision,
    filetype: FileType,
) -> str:
    """
    Create the name for the remote file using the current date and timestamp
    """
    now = datetime.now(UTC).strftime(DT_FORMAT)
    url_path = Path(revision.url_link)

    if url_path.suffix in (".zip", ".xml"):
        file_name = unquote(url_path.name)
        name = f"{revision.dataset_id}_{revision.id}_{now}_{file_name}"
    else:
        name = f"{revision.dataset_id}_{revision.id}_{now}.{filetype}"

    return name


def cleanup_temp_folder(path: Path, url: str):
    """Clean up temporary file on error."""
    log.error(
        "Upload to S3 complete, removing temp file for cleanup.", url=url, exc_info=True
    )
    if path.exists():
        path.unlink()


def download_and_upload_dataset(db: SqlDB, input_data: DownloadDatasetInputData) -> str:
    """
    Template function to download the dataset, upload to S3 and update the database.
    This function downloads the file, uploads it to S3, and updates the revision in the DB.
    """
    revision = OrganisationDatasetRevisionRepo(db).require_by_id(input_data.revision_id)

    result = download_file(input_data.remote_dataset_url_link)
    s3_object_path = make_remote_file_name(revision, result.filetype)

    upload_file_to_s3(result.path, input_data.s3_bucket_name, s3_object_path)
    cleanup_temp_folder(result.path, str(input_data.remote_dataset_url_link))
    update_dataset_revision(db, revision, s3_object_path)
    return s3_object_path


@file_processing_result_to_db(step_name=StepName.DOWNLOAD_DATASET)
def lambda_handler(event: dict[str, Any], _context: LambdaContext) -> dict[str, Any]:
    """
    Lambda Handler for DownloadDatasetLambda
    Downloads a Zip or TransXchange file from a specified URL
    """
    log.debug("Input Data", data=event)
    input_data = DownloadDatasetInputData(**event)
    db = SqlDB()
    s3_object_path = download_and_upload_dataset(db, input_data)
    ETLTaskResultRepo(db).update_progress(input_data.dataset_etl_task_result_id, 20)
    return {"s3": {"bucket": input_data.s3_bucket_name, "object": s3_object_path}}
