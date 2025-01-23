"""
Data Quality tests
"""

from unittest.mock import MagicMock, patch

import pytest
from common_layer.database.client import SqlDB
from common_layer.database.models.model_data_quality import DataQualityPTIObservation
from common_layer.database.repos.operation_decorator import RepositoryError
from common_layer.database.repos.repo_data_quality import DataQualityPTIObservationRepo
from common_layer.database.repos.repo_organisation import (
    OrganisationDatasetRevisionRepo,
)
from pti.app.models.models_pti import PtiObservation, PtiRule, PtiViolation
from sqlalchemy.exc import SQLAlchemyError

from tests.factories.database.organisation import OrganisationDatasetRevisionFactory


@pytest.fixture(name="pti_violations")
def pti_violation_test_data() -> list[PtiViolation]:
    """
    Create sample PTI violations for testing.
    """
    rule_1 = PtiRule(test="some_test_1")
    rule_2 = PtiRule(test="some_test_2")

    observation_1 = PtiObservation(
        details="Violation 1",
        category="A",
        service_type="Type1",
        reference="Ref1",
        context="Context1",
        number=101,
        rules=[rule_1, rule_2],
    )

    observation_2 = PtiObservation(
        details="Violation 2",
        category="B",
        service_type="Type2",
        reference="Ref2",
        context="Context2",
        number=102,
        rules=[rule_1],
    )

    return [
        PtiViolation(
            line=10, filename="file1.xml", name="Element1", observation=observation_1
        ),
        PtiViolation(
            line=20, filename="file2.xml", name="Element2", observation=observation_2
        ),
    ]


def test_pti_observation_repo_create_from_violations(
    pti_violations: list[PtiViolation], test_db: SqlDB
):
    """
    Test inserting observations from Violations
    """

    dataset_revision = OrganisationDatasetRevisionFactory.create()
    inserted_revision = OrganisationDatasetRevisionRepo(test_db).insert(
        dataset_revision
    )
    revision_id = inserted_revision.id

    repo = DataQualityPTIObservationRepo(test_db)

    observations = [
        PtiViolation.make_observation(revision_id, violation)
        for violation in pti_violations
    ]
    result = repo.bulk_insert(observations)
    assert len(result) == len(pti_violations)
    with test_db.session_scope() as session:
        observations = (
            session.query(DataQualityPTIObservation)
            .filter_by(revision_id=revision_id)
            .all()
        )
        assert len(observations) == len(pti_violations), "new records created"

        for record, violation in zip(observations, pti_violations):
            assert record.revision_id == revision_id
            assert record.line == violation.line
            assert record.filename == violation.filename
            assert record.element == violation.name
            assert record.details == violation.observation.details
            assert record.category == violation.observation.category
            assert record.reference == violation.observation.reference


def test_pti_observation_repo_create_from_violations_handles_empty_violations(
    test_db: SqlDB,
):
    """
    Test Handling Empty Violations
    """
    revision_id = 456

    repo = DataQualityPTIObservationRepo(test_db)
    observations = [
        PtiViolation.make_observation(revision_id, violation) for violation in []
    ]
    result = repo.bulk_insert(observations)
    assert result is []
    with test_db.session_scope() as session:
        records = (
            session.query(DataQualityPTIObservation)
            .filter_by(revision_id=revision_id)
            .all()
        )
        assert len(records) == 0


def test_create_observations_handles_error(
    pti_violations: list[PtiViolation], test_db: SqlDB
):
    """Tests error handling during PTI observation creation."""
    repo = DataQualityPTIObservationRepo(test_db)
    mock_session = MagicMock()
    mock_session.return_value.__enter__.return_value.add.side_effect = SQLAlchemyError(
        "Test error"
    )

    with (
        patch.object(test_db, "session_scope", mock_session),
        pytest.raises(RepositoryError),
    ):
        observations = [
            PtiViolation.make_observation(789, violation)
            for violation in pti_violations
        ]
        repo.bulk_insert(observations)

    # Verify rollback occurred
    with test_db.session_scope() as session:
        record_count = (
            session.query(DataQualityPTIObservation).filter_by(revision_id=789).count()
        )
        assert record_count == 0
