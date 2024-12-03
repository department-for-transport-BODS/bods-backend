import pytest
from sqlalchemy.exc import SQLAlchemyError
from unittest.mock import MagicMock
from db.repositories.pti_observation import PTIObservationRepository
from exceptions.pipeline_exceptions import PipelineException
from pti_common.models import Observation, Rule, Violation
from tests.mock_db import MockedDB


@pytest.fixture
def violations():
    """
    Create sample violations for testing.
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
        Violation(line=10, filename="file1.xml", name="Element1", observation=observation_1),
        Violation(line=20, filename="file2.xml", name="Element2", observation=observation_2),
    ]


def test_create(violations):
    mock_db = MockedDB()

    revision_id = 123

    repo = PTIObservationRepository(mock_db)

    result = repo.create(revision_id=revision_id, violations=violations)

    assert result is True
    with mock_db.session as session:
        observations = (
            session.query(mock_db.classes.data_quality_ptiobservation).filter_by(revision_id=revision_id).all()
        )
        assert len(observations) == len(violations), "new records created"

        for record, violation in zip(observations, violations):
            assert record.revision_id == revision_id
            assert record.line == violation.line
            assert record.filename == violation.filename
            assert record.element == violation.name
            assert record.details == violation.observation.details
            assert record.category == violation.observation.category
            assert record.reference == violation.observation.reference


def test_create_handles_empty_violations():
    mock_db = MockedDB()
    revision_id = 456

    repo = PTIObservationRepository(mock_db)
    result = repo.create(revision_id=revision_id, violations=[])

    assert result is True
    with mock_db.session as session:
        records = session.query(mock_db.classes.data_quality_ptiobservation).filter_by(revision_id=revision_id).all()
        assert len(records) == 0


def test_create_rollback_on_error(violations):
    mock_db = MockedDB()
    repo = PTIObservationRepository(mock_db)

    revision_id = 789
    with pytest.raises(PipelineException, match="Failed to add re-create PTIObservations for revision 789"):
        with mock_db.session as session:
            session.add = MagicMock(side_effect=SQLAlchemyError("Test exception"))
            repo.create(revision_id=revision_id, violations=violations)

    # Check no records are added (rollback)
    with mock_db.session as session:
        records = session.query(mock_db.classes.data_quality_ptiobservation).filter_by(revision_id=revision_id).all()
        assert len(records) == 0
