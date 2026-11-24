"""
Data Quality tests
"""

from unittest.mock import MagicMock, patch

import pytest
from common_layer.database.client import SqlDB
from common_layer.database.models import DataQualityPTIObservation
from common_layer.database.repos import (
    DataQualityPTIObservationRepo,
    OrganisationDatasetRevisionRepo,
    create_violation_from_parse_error,
    format_violation_details,
)
from common_layer.database.repos.operation_decorator import SQLDBClientError
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
    assert result == []
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
        pytest.raises(SQLDBClientError),
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


AUTHORITY_NAMES = ", ".join(f"'Authority{i}'" for i in range(185))
AUTHORITY_NAME_ENUM_MESSAGE = (
    "Element '{http://www.transxchange.org.uk/}AuthorityName': "
    "[facet 'enumeration'] The value 'TransportforWales' is not an element "
    f"of the set {{{AUTHORITY_NAMES}}}."
)


@pytest.mark.parametrize(
    "message, expected",
    [
        pytest.param(
            AUTHORITY_NAME_ENUM_MESSAGE,
            "Element '{http://www.transxchange.org.uk/}AuthorityName': "
            "[facet 'enumeration'] The value 'TransportforWales' is not an element "
            "of the set of allowed values.",
            id="Enumeration allowed values removed",
        ),
        pytest.param(
            "x" * 3000,
            "x" * 1021 + "...",
            id="Long message truncated to column length",
        ),
        pytest.param(
            "Element 'Journey': This element is not expected.",
            "Element 'Journey': This element is not expected.",
            id="Short message unchanged",
        ),
    ],
)
def test_format_violation_details(message: str, expected: str):
    """
    Test schema violation details are shortened to fit the details column
    """
    result = format_violation_details(message)

    assert result == expected
    assert len(result) <= 1024


def test_create_violation_from_parse_error_truncates_long_message():
    """
    Test long parse error messages are truncated to fit the details column
    """
    exc = Exception()
    exc.msg = "x" * 3000  # type: ignore[attr-defined]
    exc.lineno = 5  # type: ignore[attr-defined]

    violation = create_violation_from_parse_error(exc, 1, "file.xml")

    assert len(violation.details) == 1024
    assert violation.line == 5
