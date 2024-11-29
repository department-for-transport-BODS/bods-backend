


from common import DbManager
from db.repositories.otc_service import OtcServiceRepository
from tests.mock_db import MockedDB, naptan_adminarea, otc_localauthority, otc_localauthority_registration_numbers, otc_service, ui_lta


def test_otc_service():
    db = DbManager.get_db()
    repo = OtcServiceRepository(db)
    result = repo.get_service_with_traveline_region("PH0005857/241")
    assert result


# TODO: Add test covering weca vs otc
def test_get_service_by_registration_number():
    db = MockedDB()

    service = otc_service(id=123, registration_number="1234", api_type="WECA", atco_code="ATC001")
    ui_lta_record = ui_lta(id=567, name="LTA1")
    admin_area = naptan_adminarea(id=234, atco_code="ATC001", traveline_region_id="Region1", ui_lta_id=ui_lta_record.id)
    localauthority = otc_localauthority(id=890, ui_lta_id=ui_lta_record.id)
    registration = otc_localauthority_registration_numbers(service_id=service.id, localauthority_id=localauthority.id)

    with db.session as session:
        session.add_all([service, admin_area, ui_lta_record, localauthority, registration])
        session.commit()

    repo = OtcServiceRepository(db)
    result_service, result_traveline_region = repo.get_service_with_traveline_region("1234")

    assert result_service is not None
    assert result_traveline_region is not None

    # TODO: The returned region is delimited.. R|e|g|i|o|n|1
    assert result_service.registration_number == "1234"
    assert result_traveline_region == "Region1"