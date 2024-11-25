"""
Pytest Fixtures
"""

from datetime import UTC, datetime

import pytest

from timetables_etl.etl.app.database.models.model_organisation import (
    OrganisationDatasetRevision,
)


def create_revision(
    db_id: int = 3941,
    name: str = "Dev Org_Three Mile Cross_UK045_20241111",
    status: str = "success",
) -> OrganisationDatasetRevision:
    """
    Create a mock revision
    """
    revision = OrganisationDatasetRevision(
        upload_file="FLIX-FlixBus-UK045-London-Plymouth.xml",
        status=status,
        name=name,
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
    )

    created_time = datetime(2024, 11, 18, 10, 19, 3, 410000, tzinfo=UTC)
    modified_time = datetime(2024, 11, 18, 10, 19, 8, 673000, tzinfo=UTC)

    revision.id = db_id
    revision.created = created_time
    revision.modified = modified_time

    return revision


@pytest.fixture
def mock_revision() -> OrganisationDatasetRevision:
    """A single mock revision with default values."""
    return create_revision()


@pytest.fixture
def mock_revisions() -> list[OrganisationDatasetRevision]:
    """Multiple mock revisions with sequential IDs."""
    return [create_revision(db_id=i) for i in range(1, 4)]
