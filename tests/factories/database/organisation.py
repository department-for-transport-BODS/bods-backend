"""
Organisation Database Model Factories
"""

from datetime import UTC, date, datetime, timedelta

import factory
from common_layer.database.models import (
    OrganisationDataset,
    OrganisationDatasetRevision,
    OrganisationTXCFileAttributes,
)
from common_layer.database.models.db_enums import AVLFeedStatus
from factory import LazyFunction
from factory.fuzzy import FuzzyChoice, FuzzyInteger


class OrganisationDatasetFactory(factory.Factory):
    """
    Factory for OrganisationDataset
    """

    class Meta:  # type: ignore[misc]
        """Factory configuration."""

        model = OrganisationDataset

    live_revision_id = FuzzyInteger(1000, 5000)
    organisation_id = FuzzyInteger(1000, 5000)
    contact_id = FuzzyInteger(1000, 5000)
    dataset_type = FuzzyChoice([0, 1])

    avl_feed_status = AVLFeedStatus.LIVE.value
    avl_feed_last_checked = LazyFunction(
        lambda: datetime.now(tz=UTC) - timedelta(minutes=10)
    )
    is_dummy = False

    @classmethod
    def create_with_id(cls, id_number: int, **kwargs) -> OrganisationDataset:
        """Creates a revision with a specific ID"""
        dataset = cls.create(**kwargs)
        dataset.id = id_number
        return dataset


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
    modified_file_hash = factory.Faker("sha1")
    original_file_hash = factory.Faker("sha1")
    modified_before_reprocessing = None
    status_before_reprocessing = ""

    @classmethod
    def create_with_id(cls, id_number: int, **kwargs) -> OrganisationDatasetRevision:
        """Creates a revision with a specific ID"""
        revision = cls.create(**kwargs)
        revision.id = id_number
        return revision

    @classmethod
    def published(cls, **kwargs) -> OrganisationDatasetRevision:
        """Creates a published revision"""
        return cls.create(
            is_published=True,
            published_at=datetime.now(UTC),
            published_by_id=FuzzyInteger(1, 1000).fuzz(),
            **kwargs,
        )

    @classmethod
    def with_dates(
        cls, start_date: date, end_date: date, **kwargs
    ) -> OrganisationDatasetRevision:
        """Creates a revision with specific service dates"""
        return cls.create(
            first_service_start=datetime.combine(start_date, datetime.min.time(), UTC),
            first_expiring_service=datetime.combine(end_date, datetime.max.time(), UTC),
            last_expiring_service=datetime.combine(end_date, datetime.max.time(), UTC),
            **kwargs,
        )


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
    service_mode = "bus"

    @classmethod
    def create_with_id(cls, id_number: int, **kwargs) -> OrganisationTXCFileAttributes:
        """Creates file attributes with a specific ID"""
        attrs = cls.create(**kwargs)
        attrs.id = id_number
        return attrs

    @classmethod
    def with_service_details(
        cls, origin: str, destination: str, line_names: list[str], **kwargs
    ) -> OrganisationTXCFileAttributes:
        """Creates file attributes with specific service details"""
        return cls.create(
            origin=origin, destination=destination, line_names=line_names, **kwargs
        )

    @classmethod
    def with_operating_period(
        cls, start_date: date, end_date: date, **kwargs
    ) -> OrganisationTXCFileAttributes:
        """Creates file attributes with specific operating period"""
        return cls.create(
            operating_period_start_date=start_date,
            operating_period_end_date=end_date,
            **kwargs,
        )
