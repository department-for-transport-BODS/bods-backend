from unittest.mock import MagicMock, patch

import pytest
from common_layer.database.models.model_data_quality import DataQualityPTIObservation
from common_layer.database.repos.operation_decorator import RepositoryError
from common_layer.database.repos.repo_data_quality import DataQualityPTIObservationRepo
from common_layer.database.repos.repo_organisation import (
    OrganisationDatasetRevisionRepo,
)
from common_layer.exceptions.pipeline_exceptions import PipelineException
from common_layer.pti.models import Observation, Rule, Violation
from sqlalchemy.exc import SQLAlchemyError

from tests.factories.database.organisation import OrganisationDatasetRevisionFactory


@pytest.fixture
def pti_violations():
    """
    Create sample PTI violations for testing.
    """
    rule_1 = Rule(test="some_test_1")
    rule_2 = Rule(test="some_test_2")

    observation_1 = Observation(
        details="Violation 1",
        category="A",
        service_type="Type1",
        reference="Ref1",
        context="Context1",
        number=101,
        rules=[rule_1, rule_2],
    )

    observation_2 = Observation(
        details="Violation 2",
        category="B",
        service_type="Type2",
        reference="Ref2",
        context="Context2",
        number=102,
        rules=[rule_1],
    )

    return [
        Violation(
            line=10, filename="file1.xml", name="Element1", observation=observation_1
        ),
        Violation(
            line=20, filename="file2.xml", name="Element2", observation=observation_2
        ),
    ]


def test_pti_observation_repo_create_from_violations(pti_violations, test_db):

    dataset_revision = OrganisationDatasetRevisionFactory.create()
    inserted_revision = OrganisationDatasetRevisionRepo(test_db).insert(
        dataset_revision
    )
    revision_id = inserted_revision.id

    repo = DataQualityPTIObservationRepo(test_db)

    result = repo.create_from_violations(
        revision_id=revision_id, violations=pti_violations
    )

    assert result is True
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


def test_pti_observation_repo_create_from_violations_handles_empty_violations(test_db):
    revision_id = 456

    repo = DataQualityPTIObservationRepo(test_db)
    result = repo.create_from_violations(revision_id=revision_id, violations=[])

    assert result is True
    with test_db.session_scope() as session:
        records = (
            session.query(DataQualityPTIObservation)
            .filter_by(revision_id=revision_id)
            .all()
        )
        assert len(records) == 0


def test_create_from_violations_rollback_on_error(pti_violations, test_db):
    repo = DataQualityPTIObservationRepo(test_db)

    revision_id = 789

    m_session = MagicMock()
    m_session.return_value.__enter__.return_value.add = MagicMock(
        side_effect=SQLAlchemyError("Test exception")
    )

    with patch.object(test_db, "session_scope", m_session):
        with pytest.raises(RepositoryError):
            repo.create_from_violations(
                revision_id=revision_id, violations=pti_violations
            )

    # Check no records are added (rollback)
    with test_db.session_scope() as session:
        records = (
            session.query(DataQualityPTIObservation)
            .filter_by(revision_id=revision_id)
            .all()
        )
        assert len(records) == 0
