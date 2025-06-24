from common_layer.database.client import SqlDB
from common_layer.database.models import NaptanAdminArea
from common_layer.database.models.common import BaseSQLModel
from common_layer.database.repos.repo_common import BaseRepositoryWithId


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


def test_bulk_delete_by_ids(test_db: SqlDB) -> None:
    model = NaptanAdminArea
    repo = BaseRepositoryWithId(test_db, model=model)

    record_1 = NaptanAdminArea(
        name="AdminArea1",
        traveline_region_id="NE",
        atco_code="ATCO1111",
        ui_lta_id=None,
    )
    record_2 = NaptanAdminArea(
        name="AdminArea2",
        traveline_region_id="NE",
        atco_code="ATCO2222",
        ui_lta_id=None,
    )

    with test_db.session_scope() as session:
        session.add_all([record_1, record_2])
        session.flush()
        id_1 = record_1.id
        id_2 = record_2.id

    # Ensure both records exist
    with test_db.session_scope() as session:
        records = session.query(model).filter(model.id.in_([id_1, id_2])).all()
        assert len(records) == 2, "Both records should exist before deletion"

    repo.bulk_delete_by_ids([id_1, id_2])

    # Ensure both records are deleted
    with test_db.session_scope() as session:
        remaining = session.query(model).filter(model.id.in_([id_1, id_2])).all()
        assert len(remaining) == 0, "Both records should be deleted"
