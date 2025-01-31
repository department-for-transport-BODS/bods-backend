"""
Task Data from real data
"""

from common_layer.database.client import SqlDB
from common_layer.database.repos.repo_organisation import (
    OrganisationDatasetRevisionRepo,
    OrganisationTXCFileAttributesRepo,
)
from common_layer.txc.models.txc_data import TXCData
from structlog.stdlib import get_logger

from src.timetables_etl.file_attributes_etl.app.process_txc import (
    make_txc_file_attributes,
)
from tests.factories.database.organisation import OrganisationDatasetRevisionFactory
from tests.factories.database.pipelines import DatasetETLTaskResultFactory
from timetables_etl.etl.app.etl_process import get_task_data
from timetables_etl.etl.app.models import ETLInputData, TaskData
from tools.local_etl.mock_task_data import create_mocked_task_data

log = get_logger()


def create_task_data_from_inputs(
    txc: TXCData,
    task_id: int | None = None,
    file_attributes_id: int | None = None,
    revision_id: int | None = None,
    db: SqlDB | None = None,
) -> TaskData:
    """
    Create TaskData based on available inputs.
    If db is provided, will attempt to fetch real data for provided IDs.
    Falls back to mock data when needed.
    """
    if task_id and file_attributes_id and db:
        log.info("Fetching task data from database using provided IDs")
        input_data = ETLInputData(
            DatasetEtlTaskResultId=task_id,
            fileAttributesId=file_attributes_id,
            Bucket="test",
            ObjectKey="test",
        )
        return get_task_data(input_data, db)

    if revision_id and file_attributes_id:
        log.info("Creating mock task with provided revision_id and file_attributes_id")
        # If db provided, try to get real revision and file attributes
        if db:
            revision = OrganisationDatasetRevisionRepo(db).get_by_id(revision_id)
            file_attributes = OrganisationTXCFileAttributesRepo(db).get_by_id(
                file_attributes_id
            )
        else:
            revision = None
            file_attributes = None

        if not revision:
            revision = OrganisationDatasetRevisionFactory.create_with_id(123)

        if not file_attributes:
            file_attributes = make_txc_file_attributes(txc, revision)
            file_attributes.id = file_attributes_id

        mock_task = DatasetETLTaskResultFactory.create_with_id(
            id_number=999,  # Mock task ID
            revision_id=revision_id,
            progress=0,
            task_name_failed=None,
            error_code=None,
            additional_info=None,
        )

        return TaskData(
            etl_task=mock_task,
            revision=revision,
            file_attributes=file_attributes,
            input_data=ETLInputData(
                DatasetEtlTaskResultId=mock_task.id,
                fileAttributesId=file_attributes_id,
                Bucket="test",
                ObjectKey="test",
            ),
        )

    log.info("Creating complete mock task data")
    return create_mocked_task_data(txc)
