"""
Mock Data
"""

from datetime import UTC, datetime

from common_layer.database.models import (
    DatasetETLTaskResult,
    ETLErrorCode,
    OrganisationDatasetRevision,
)
from common_layer.xml.txc.models import TXCData

from src.timetables_etl.file_attributes_etl.app.process_txc import (
    make_txc_file_attributes,
)
from timetables_etl.etl.app.models import ETLInputData, TaskData


def create_mocked_task_data(
    txc: TXCData,
) -> TaskData:
    """Create task data for testing"""
    revision = OrganisationDatasetRevision(
        upload_file="FLIX-FlixBus-UK045-London-Plymouth.xml",
        status="pending",
        name="Test",
        description="Jon 18th November 2024 Upload Testing data upload with a single xml",
        comment="First publication",
        is_published=False,
        url_link="",
        num_of_lines=1,
        num_of_operators=None,
        transxchange_version="2.4",
        imported=None,
        bounding_box=None,
        publisher_creation_datetime=datetime(2024, 11, 14, 10, 54, 47, tzinfo=UTC),
        publisher_modified_datetime=datetime(2024, 11, 14, 11, 4, 47, tzinfo=UTC),
        first_expiring_service=datetime(2025, 1, 5, 23, 59, 0, tzinfo=UTC),
        last_expiring_service=datetime(2025, 1, 5, 23, 59, 0, tzinfo=UTC),
        first_service_start=datetime(2024, 11, 11, 0, 0, 0, tzinfo=UTC),
        num_of_bus_stops=7,
        dataset_id=3013,
        last_modified_user_id=272,
        published_by_id=None,
        published_at=None,
        password="",
        requestor_ref="",
        username="",
        short_description="Jon Test SingleXML Upload",
        num_of_timing_points=40,
        modified_file_hash="123",
        original_file_hash="123",
    )
    file_attributes = make_txc_file_attributes(txc, revision)
    file_attributes.id = 123
    return TaskData(
        etl_task=DatasetETLTaskResult(
            revision_id=revision.id,
            progress=10,
            task_name_failed="123",
            error_code=ETLErrorCode.AV_SCAN_FAILED,
            additional_info="123",
        ),
        revision=revision,
        file_attributes=file_attributes,
        input_data=ETLInputData(
            task_id=123,
            file_attributes_id=file_attributes.id,
            s3_bucket_name="test",
            s3_file_key="test",
            superseded_timetable=False,
        ),
    )
