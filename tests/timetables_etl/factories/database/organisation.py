"""
Organisation Database Model Factories
"""

from datetime import UTC, date, datetime

import factory
from factory import LazyFunction
from factory.fuzzy import FuzzyChoice, FuzzyInteger

from timetables_etl.etl.app.database.models.model_organisation import (
    OrganisationDatasetRevision,
    OrganisationTXCFileAttributes,
)


class OrganisationDatasetRevisionFactory(factory.Factory):
    """
    Factory for OrganisationDatasetRevision
    """

    class Meta:  # type: ignore[misc]
        """Factory configuration."""

        model = OrganisationDatasetRevision

    upload_file = "FLIX-FlixBus-UK045-London-Plymouth.xml"
    status = "success"
    name = factory.Sequence(lambda n: f"Dev Org_Test Upload_{n}")
    description = "Test data upload with a single xml"
    comment = "Test publication"
    is_published = False
    url_link = "http://example.com"
    num_of_lines = 1
    num_of_operators = None
    transxchange_version = "2.4"
    imported = None
    bounding_box = None
    publisher_creation_datetime = LazyFunction(
        lambda: datetime(2024, 11, 14, 10, 54, 47, tzinfo=UTC)
    )
    publisher_modified_datetime = LazyFunction(
        lambda: datetime(2024, 11, 14, 11, 4, 47, tzinfo=UTC)
    )
    first_expiring_service = LazyFunction(
        lambda: datetime(2025, 1, 5, 23, 59, 0, tzinfo=UTC)
    )
    last_expiring_service = LazyFunction(
        lambda: datetime(2025, 1, 5, 23, 59, 0, tzinfo=UTC)
    )
    first_service_start = LazyFunction(
        lambda: datetime(2024, 11, 11, 0, 0, 0, tzinfo=UTC)
    )
    num_of_bus_stops = 7
    dataset_id = FuzzyInteger(1000, 5000)
    last_modified_user_id = FuzzyInteger(1, 1000)
    published_by_id = None
    published_at = None
    password = ""
    requestor_ref = ""
    username = ""
    short_description = "Test SingleXML Upload"
    num_of_timing_points = 40
    created = LazyFunction(lambda: datetime.now(UTC))
    modified = LazyFunction(lambda: datetime.now(UTC))


class OrganisationTXCFileAttributesFactory(factory.Factory):
    """
    Factory for creating OrganisationTXCFileAttributes instances using the repository pattern.
    """

    class Meta:  # type: ignore[misc]
        """Factory configuration."""

        model = OrganisationTXCFileAttributes

    schema_version = "2.4"
    revision_number = FuzzyInteger(1, 10)
    creation_datetime = LazyFunction(lambda: datetime.now(UTC))
    modification_datetime = LazyFunction(lambda: datetime.now(UTC))
    filename = factory.Sequence(lambda n: f"test_file_{n}.xml")
    service_code = factory.Sequence(lambda n: f"SERVICE_{n}")
    revision_id = FuzzyInteger(1000, 5000)
    modification = FuzzyChoice(["new", "revise", "delete"])
    national_operator_code = "NOC"
    licence_number = factory.Sequence(lambda n: f"PD{n}")
    operating_period_end_date = LazyFunction(lambda: date(2025, 12, 31))
    operating_period_start_date = LazyFunction(lambda: date(2024, 1, 1))
    public_use = True
    line_names = ["Line 1", "Line 2"]
    destination = "Plymouth"
    origin = "London"
    hash = factory.Faker("sha1")
