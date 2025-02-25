from common_layer.database.models import FaresMetadata
from common_layer.database.models.model_fares import (
    FaresDataCatalogueMetadata,
    FaresMetadataStop,
)
from common_layer.database.repos.repo_fares import (
    FaresDataCatalogueMetadataRepo,
    FaresMetadataRepo,
    FaresMetadataStopsRepo,
)


def test_fares_metadata_delete_by_metadata_id(test_db):
    """
    Test deleting fares metadata by id
    """
    repo = FaresMetadataRepo(test_db)

    record = FaresMetadata(
        datasetmetadata_ptr_id=999,
        num_of_fare_products=2,
        num_of_fare_zones=1,
        num_of_lines=1,
        num_of_pass_products=4,
        num_of_sales_offer_packages=2,
        num_of_trip_products=2,
        num_of_user_profiles=2,
        valid_from=None,
        valid_to=None,
    )
    inserted_record = repo.insert(record)

    with test_db.session_scope() as session:
        record_in_db = (
            session.query(FaresMetadata)
            .filter_by(datasetmetadata_ptr_id=inserted_record.datasetmetadata_ptr_id)
            .one_or_none()
        )
        assert (
            record_in_db is not None
        ), "Record should exist before calling delete_by_id"

    repo.delete_by_metadata_id(inserted_record.datasetmetadata_ptr_id)

    # Verify record no longer exists directly
    with test_db.session_scope() as session:
        record_after_deletion = (
            session.query(FaresMetadata)
            .filter_by(datasetmetadata_ptr_id=inserted_record.datasetmetadata_ptr_id)
            .one_or_none()
        )
        assert (
            record_after_deletion is None
        ), "Record should not exist after calling delete_by_id"


def test_fares_metadata_stops_delete_by_metadata_id(test_db):
    """
    Test deleting fares metadata stop by id
    """
    repo = FaresMetadataStopsRepo(test_db)

    metadata_id = 12

    record = FaresMetadataStop(
        faresmetadata_id=metadata_id,
        stoppoint_id=1234,
    )
    inserted_record = repo.insert(record)

    with test_db.session_scope() as session:
        record_in_db = (
            session.query(FaresMetadataStop)
            .filter_by(id=inserted_record.id)
            .one_or_none()
        )
        assert (
            record_in_db is not None
        ), "Record should exist before calling delete_by_id"

    repo.delete_by_metadata_id(metadata_id)

    # Verify record no longer exists directly
    with test_db.session_scope() as session:
        record_after_deletion = (
            session.query(FaresMetadataStop)
            .filter_by(id=inserted_record.id)
            .one_or_none()
        )
        assert (
            record_after_deletion is None
        ), "Record should not exist after calling delete_by_id"


def test_fares_data_catalogue_metadata_delete_by_metadata_id(test_db):
    """
    Test deleting fares data catalogue metadata by metadata id
    """
    repo = FaresDataCatalogueMetadataRepo(test_db)

    metadata_id = 123

    record = FaresDataCatalogueMetadata(
        atco_area=[1],
        line_id=["test"],
        line_name=["line"],
        national_operator_code=["TEST"],
        product_name=["product1"],
        product_type=["singleTrip"],
        tariff_basis=["flat"],
        user_type=["adult"],
        valid_from=None,
        valid_to=None,
        xml_file_name="test.xml",
        fares_metadata_id=metadata_id,
    )
    inserted_record = repo.insert(record)

    with test_db.session_scope() as session:
        record_in_db = (
            session.query(FaresDataCatalogueMetadata)
            .filter_by(id=inserted_record.id)
            .one_or_none()
        )
        assert (
            record_in_db is not None
        ), "Record should exist before calling delete_by_id"

    repo.delete_by_metadata_id(metadata_id)

    # Verify record no longer exists directly
    with test_db.session_scope() as session:
        record_after_deletion = (
            session.query(FaresDataCatalogueMetadata)
            .filter_by(id=inserted_record.id)
            .one_or_none()
        )
        assert (
            record_after_deletion is None
        ), "Record should not exist after calling delete_by_id"
