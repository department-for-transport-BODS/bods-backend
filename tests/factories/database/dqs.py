from datetime import datetime
from typing import TYPE_CHECKING

import factory
from common_layer.database.models.model_dqs import DQSReport, DQSTaskResults
from factory.fuzzy import FuzzyChoice, FuzzyInteger
from pytz import UTC


class DQSReportFactory(factory.Factory):
    """
    Factory for creating DQSReport instances using the repository pattern.
    """

    class Meta:  # type: ignore[misc]
        model = DQSReport

    created = factory.LazyFunction(lambda: datetime.now(UTC))
    file_name = factory.Faker("file_name")
    status = FuzzyChoice(["PENDING", "SUCCESS", "FAILED"])
    revision_id = None


class DQSTaskResultsFactory(factory.Factory):
    """
    Factory for creating DQSTaskResults instances using the repository pattern.
    """

    class Meta:  # type: ignore[misc]
        """Factory configuration."""

        model = DQSTaskResults

    created = factory.LazyFunction(lambda: datetime.now(UTC))
    modified = factory.LazyFunction(lambda: datetime.now(UTC))
    status = FuzzyChoice(["PENDING", "SUCCESS", "FAILED"])
    message = factory.Faker("sentence")

    transmodel_txcfileattributes_id = None
    transmodel_txcfileattributes = None

    dataquality_report_id = None
    dataquality_report = None

    @classmethod
    def create_with_id(cls, id_number: int, **kwargs) -> DQSTaskResults:
        """Creates a DQSTaskResults instance with a specific ID"""
        attrs = cls.create(**kwargs)
        attrs.id = id_number
        return attrs
