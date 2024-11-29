from unittest.mock import MagicMock
import pytest
from common import DbManager
from db.repositories.otc_service import OtcServiceRepository

from exceptions.pipeline_exceptions import PipelineException
from tests.mock_db import (
    MockedDB,
    naptan_adminarea,
    otc_localauthority,
    otc_localauthority_registration_numbers,
    otc_service,
    ui_lta,
)

def test_get_service_by_registration_number_weca():
    db = MockedDB()
    # Set up data
    registration_number = "PH0006633/01010001"
    api_type = "WECA"
    service = otc_service(id=1, registration_number=registration_number, api_type=api_type, atco_code="ATC001")
    admin_area = naptan_adminarea(id=1, atco_code="ATC001", traveline_region_id="SW", ui_lta_id=None)

    with db.session as session:
        session.add_all([service, admin_area])
        session.commit()

    # Run the query
    repo = OtcServiceRepository(db)
    service_with_region = repo.get_service_with_traveline_region(registration_number)

    # Assertions
    assert service_with_region is not None
    assert service_with_region.service.registration_number == registration_number
    assert service_with_region.traveline_region == "SW"


def test_get_service_by_registration_number_otc():
    db = MockedDB()

    registration_number = "PC0004417/343"
    api_type = None
    service = otc_service(id=123, registration_number=registration_number, api_type=api_type, atco_code="ATC001")
    ui_lta_record = ui_lta(id=567, name="LTA1")
    admin_area = naptan_adminarea(id=234, atco_code="ATC001", traveline_region_id="N", ui_lta_id=ui_lta_record.id)
    localauthority = otc_localauthority(id=890, ui_lta_id=ui_lta_record.id)
    registration = otc_localauthority_registration_numbers(service_id=service.id, localauthority_id=localauthority.id)

    with db.session as session:
        session.add_all([service, admin_area, ui_lta_record, localauthority, registration])
        session.commit()

    repo = OtcServiceRepository(db)
    service_with_region = repo.get_service_with_traveline_region(registration_number)

    assert service_with_region is not None
    assert service_with_region.service.registration_number == registration_number
    assert service_with_region.traveline_region == "N"


def test_get_service_with_multiple_traveline_regions():
    db = MockedDB()

    # Set up data
    api_type = None
    registration_number = "PH0005857/241"
    service = otc_service(id=3, registration_number=registration_number, api_type=None, atco_code="ATC003")
    ui_lta_record = ui_lta(id=3, name="LTA2")
    admin_area_1 = naptan_adminarea(id=3, atco_code="ATC003", traveline_region_id="NE", ui_lta_id=ui_lta_record.id)
    admin_area_2 = naptan_adminarea(id=4, atco_code="ATC003", traveline_region_id="SW", ui_lta_id=ui_lta_record.id)
    localauthority = otc_localauthority(id=4, ui_lta_id=ui_lta_record.id)
    registration = otc_localauthority_registration_numbers(service_id=service.id, localauthority_id=localauthority.id)

    with db.session as session:
        session.add_all([service, ui_lta_record, admin_area_1, admin_area_2, localauthority, registration])
        session.commit()

    repo = OtcServiceRepository(db)
    service_with_region = repo.get_service_with_traveline_region(registration_number)

    assert service_with_region is not None
    assert service_with_region.service.registration_number == registration_number
    assert (
        service_with_region.traveline_region == "NE|SW" or service_with_region.traveline_region == "SW|NE"
    ), "regions should be concatenated and delimited with |"


def test_get_service_with_traveline_region_not_found():
    db = MockedDB()

    repo = OtcServiceRepository(db)
    service_with_region = repo.get_service_with_traveline_region("9999")

    assert service_with_region is None


def test_get_service_with_traveline_region_exception():
    db = MockedDB()
    m_session = MagicMock()
    m_session.__enter__.return_value.query.side_effect = Exception("DB Exception")
    db.session = m_session

    repo = OtcServiceRepository(db)
    with pytest.raises(
        PipelineException, match="Error retrieving service with traveline region with registration number 9999."
    ):
        repo.get_service_with_traveline_region("9999")
