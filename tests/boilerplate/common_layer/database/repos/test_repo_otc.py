from unittest.mock import MagicMock

import pytest
from common_layer.database.models.model_otc import OtcLocalAuthorityRegistrationNumbers
from common_layer.database.repos.repo_otc import OtcServiceRepo
from common_layer.exceptions.pipeline_exceptions import PipelineException

from tests.factories.database.naptan import NaptanAdminAreaFactory
from tests.factories.database.otc import OtcLocalAuthorityFactory, OtcServiceFactory
from tests.factories.database.ui import UiLtaFactory


def test_get_service_by_registration_number_weca(test_db):

    registration_number = "PH0006633/01010001"
    api_type = "WECA"
    traveline_region_id = "SW"

    service = OtcServiceFactory.create(
        registration_number=registration_number,
        api_type=api_type,
    )

    admin_area = NaptanAdminAreaFactory.create(
        traveline_region_id=traveline_region_id, ui_lta_id=None
    )

    with test_db.session_scope() as session:
        session.add_all([service, admin_area])
        session.commit()

    # Run the query
    repo = OtcServiceRepo(test_db)
    service_with_region = repo.get_service_with_traveline_region(registration_number)

    # Assertions
    assert service_with_region is not None
    assert service_with_region.service.registration_number == registration_number
    assert service_with_region.traveline_region == traveline_region_id


def test_get_service_by_registration_number_otc(test_db):

    registration_number = "PC0004417/343"
    api_type = None

    with test_db.session_scope() as session:
        # Create and insert the initial records
        service = OtcServiceFactory.create(
            registration_number=registration_number,
            api_type=api_type,
            atco_code="ATC001",
        )
        ui_lta_record = UiLtaFactory.create()
        session.add_all([service, ui_lta_record])
        session.commit()

        # Use the generated IDs for dependent records
        admin_area = NaptanAdminAreaFactory.create(
            atco_code="ATC001",
            traveline_region_id="N",
            ui_lta_id=ui_lta_record.id,  # Use the generated ID
        )
        localauthority = OtcLocalAuthorityFactory.create(
            ui_lta_id=ui_lta_record.id  # Use the generated ID
        )
        session.add_all([admin_area, localauthority])
        session.commit()

        # Use the localauthority ID for the registration record
        registration = OtcLocalAuthorityRegistrationNumbers(
            service_id=service.id, localauthority_id=localauthority.id
        )
        session.add(registration)
        session.commit()  # Final commit

    repo = OtcServiceRepo(test_db)
    service_with_region = repo.get_service_with_traveline_region(registration_number)

    assert service_with_region is not None
    assert service_with_region.service.registration_number == registration_number
    assert service_with_region.traveline_region == "N"


def test_get_service_with_multiple_traveline_regions(test_db):

    api_type = None
    registration_number = "PH0005857/241"

    with test_db.session_scope() as session:
        service = OtcServiceFactory.create(
            registration_number=registration_number,
            api_type=api_type,
        )
        ui_lta_record = UiLtaFactory.create(name="LTA2")
        session.add_all([service, ui_lta_record])
        session.commit()

        admin_area_1 = NaptanAdminAreaFactory.create(
            traveline_region_id="NE", ui_lta_id=ui_lta_record.id
        )
        admin_area_2 = NaptanAdminAreaFactory.create(
            traveline_region_id="SW", ui_lta_id=ui_lta_record.id
        )
        localauthority = OtcLocalAuthorityFactory.create(ui_lta_id=ui_lta_record.id)
        session.add_all([admin_area_1, admin_area_2, localauthority])
        session.commit()

        registration = OtcLocalAuthorityRegistrationNumbers(
            service_id=service.id, localauthority_id=localauthority.id
        )
        session.add(registration)
        session.commit()

    repo = OtcServiceRepo(test_db)
    service_with_region = repo.get_service_with_traveline_region(registration_number)

    assert service_with_region is not None
    assert service_with_region.service.registration_number == registration_number
    assert (
        service_with_region.traveline_region == "NE|SW"
        or service_with_region.traveline_region == "SW|NE"
    ), "regions should be concatenated and delimited with |"


def test_get_service_with_traveline_region_not_found(test_db):
    repo = OtcServiceRepo(test_db)
    service_with_region = repo.get_service_with_traveline_region("9999")
    assert service_with_region is None


def test_get_service_with_traveline_region_exception(test_db):
    m_session = MagicMock()
    m_session.return_value.__enter__.return_value.query.side_effect = Exception(
        "DB Exception"
    )
    test_db.session_scope = m_session

    repo = OtcServiceRepo(test_db)
    with pytest.raises(
        PipelineException,
        match="Error retrieving service with traveline region with registration number 9999.",
    ):
        repo.get_service_with_traveline_region("9999")


def test_get_service_with_distinct_traveline_regions(test_db):
    """
    Ensure that distinct is applied in the subqueries to avoid duplicate
    traveline_region_id values in the result.
    """
    api_type = None
    registration_number = "PH0005857/241"

    with test_db.session_scope() as session:
        # Create a service
        service = OtcServiceFactory.create(
            registration_number=registration_number,
            api_type=api_type,
        )
        ui_lta_record = UiLtaFactory.create(name="LTA2")
        session.add_all([service, ui_lta_record])
        session.commit()

        # Create admin areas with duplicate traveline_region_id for the same ui_lta_id
        admin_area_1 = NaptanAdminAreaFactory.create(
            traveline_region_id="NE", ui_lta_id=ui_lta_record.id
        )
        admin_area_2 = NaptanAdminAreaFactory.create(
            traveline_region_id="NE", ui_lta_id=ui_lta_record.id
        )
        admin_area_3 = NaptanAdminAreaFactory.create(
            traveline_region_id="SW", ui_lta_id=ui_lta_record.id
        )
        localauthority = OtcLocalAuthorityFactory.create(ui_lta_id=ui_lta_record.id)
        session.add_all([admin_area_1, admin_area_2, admin_area_3, localauthority])
        session.commit()

        # Create the registration linking the Service and LocalAuthority
        registration = OtcLocalAuthorityRegistrationNumbers(
            service_id=service.id, localauthority_id=localauthority.id
        )
        session.add(registration)
        session.commit()

    # Query using the repository
    repo = OtcServiceRepo(test_db)
    service_with_region = repo.get_service_with_traveline_region(registration_number)

    assert service_with_region is not None
    assert service_with_region.service.registration_number == registration_number
    assert (
        service_with_region.traveline_region == "NE|SW"
        or service_with_region.traveline_region == "SW|NE"
    ), "regions should be concatenated without duplicates and delimited with |"
