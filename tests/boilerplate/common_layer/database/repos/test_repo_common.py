from common_layer.database.models import NaptanAdminArea
from common_layer.database.models.common import BaseSQLModel
from common_layer.database.repos.repo_common import BaseRepositoryWithId
from sqlalchemy import delete


def assert_attributes(expected_attributes: dict, record: BaseSQLModel):
    """
    Assert that every expected attribute is present
    """
    for attr_name, expected_value in expected_attributes.items():
        assert getattr(record, attr_name) == expected_value


def test_insert(test_db):
    model = NaptanAdminArea
    repo = BaseRepositoryWithId(test_db, model=model)

    expected_attributes = {
        "name": "AdminArea1",
        "traveline_region_id": "NE",
        "atco_code": "ATCO999",
        "ui_lta_id": None,
    }
    record = NaptanAdminArea(**expected_attributes)

    inserted_record = repo.insert(record)
    assert inserted_record.id is not None, "Inserted record returned with ID"
    assert_attributes(expected_attributes, inserted_record)

    # Check returned record exists in DB with expected attributes
    with test_db.session_scope() as session:
        fetched_record = (
            session.query(model).filter_by(id=inserted_record.id).one_or_none()
        )
        assert fetched_record is not None
        assert_attributes(expected_attributes, fetched_record)
        repo.delete_by_id(fetched_record.id)


def test_delete_by_id(test_db):
    model = NaptanAdminArea
    repo = BaseRepositoryWithId(test_db, model=model)

    record = NaptanAdminArea(
        name="AdminArea2",
        traveline_region_id="NE",
        atco_code="ATCO9876",
        ui_lta_id=None,
    )
    inserted_record = repo.insert(record)

    with test_db.session_scope() as session:
        record_in_db = (
            session.query(model).filter_by(id=inserted_record.id).one_or_none()
        )
        assert (
            record_in_db is not None
        ), "Record should exist before calling delete_by_id"

    repo.delete_by_id(inserted_record.id)

    # Verify record no longer exists directly
    with test_db.session_scope() as session:
        record_after_deletion = (
            session.query(model).filter_by(id=inserted_record.id).one_or_none()
        )
        assert (
            record_after_deletion is None
        ), "Record should not exist after calling delete_by_id"


def test_delete_all(test_db):
    """
    Test that _delete_all deletes all records satisfying the given delete statement from the db
    """
    model = NaptanAdminArea
    repo = BaseRepositoryWithId(test_db, model=model)

    record_count = 3
    records = [
        NaptanAdminArea(
            name=f"AdminArea{i}",
            traveline_region_id="NE",
            atco_code=f"ATCO{i}",
            ui_lta_id=None,
        )
        for i in range(0, record_count)
    ]
    repo.bulk_insert(records)

    with test_db.session_scope() as session:
        records_in_db = (
            session.query(model).where(model.traveline_region_id == "NE").all()
        )
        assert len(records_in_db) == record_count

    stmt = delete(model).where(model.traveline_region_id == "NE")
    result = repo._delete_all(stmt)

    assert result == record_count, "Number of deleted rows returned"

    # Verify records longer exist directly
    with test_db.session_scope() as session:
        records_after_deletion = (
            session.query(model).where(model.traveline_region_id == "NE").all()
        )
        assert (
            len(records_after_deletion) == 0
        ), "Records should not exist after calling _delete_all"


def test_delete_all_no_records(test_db):
    """
    Test that _delete_all works as expected if no records are found
    """
    model = NaptanAdminArea
    repo = BaseRepositoryWithId(test_db, model=model)
    stmt = delete(model).where(model.atco_code == "ATC001")
    result = repo._delete_all(stmt)
    assert result == 0
