"""
Handle Getting the correct operating profile
"""

import pytest
from common_layer.xml.txc.models.txc_operating_profile import TXCOperatingProfile
from common_layer.xml.txc.models.txc_service import TXCService
from common_layer.xml.txc.models.txc_vehicle_journey import TXCVehicleJourney

from tests.timetables_etl.factories.txc.factory_txc_service import TXCServiceFactory
from tests.timetables_etl.factories.txc.factory_vehicle_journey import (
    TXCOperatingProfileFactory,
    TXCVehicleJourneyFactory,
)
from timetables_etl.etl.app.transform.vehicle_journey_operations import (
    get_operating_profile,
)


@pytest.mark.parametrize(
    "txc_vj,txc_services,expected",
    [
        pytest.param(
            TXCVehicleJourneyFactory.create(
                VehicleJourneyCode="VJ1",
                OperatingProfile=TXCOperatingProfileFactory.create(),
            ),
            [],
            TXCOperatingProfileFactory.create(),
            id="Valid: VJ has OperatingProfile",
        ),
        pytest.param(
            TXCVehicleJourneyFactory.create(
                VehicleJourneyCode="VJ2",
                OperatingProfile=None,
            ),
            [
                TXCServiceFactory.create(
                    ServiceCode="SVC1",
                    OperatingProfile=TXCOperatingProfileFactory.create(),
                )
            ],
            TXCOperatingProfileFactory.create(),
            id="Valid: Service has OperatingProfile when VJ doesn't",
        ),
        pytest.param(
            TXCVehicleJourneyFactory.create(
                VehicleJourneyCode="VJ3",
                OperatingProfile=None,
            ),
            [
                TXCServiceFactory.create(
                    ServiceCode="SVC2",
                    OperatingProfile=None,
                ),
                TXCServiceFactory.create(
                    ServiceCode="SVC3",
                    OperatingProfile=TXCOperatingProfileFactory.create(),
                ),
            ],
            TXCOperatingProfileFactory.create(),
            id="Valid: Second Service has OperatingProfile",
        ),
        pytest.param(
            TXCVehicleJourneyFactory.create(
                VehicleJourneyCode="VJ4",
                OperatingProfile=None,
            ),
            [
                TXCServiceFactory.create(
                    ServiceCode="SVC4",
                    OperatingProfile=None,
                ),
            ],
            None,
            id="Missing: No OperatingProfile in VJ or Services",
        ),
        pytest.param(
            TXCVehicleJourneyFactory.create(
                VehicleJourneyCode="VJ5",
                OperatingProfile=None,
            ),
            [],
            None,
            id="Missing: No OperatingProfile and Empty Services",
        ),
    ],
)
def test_get_operating_profile(
    txc_vj: TXCVehicleJourney,
    txc_services: list[TXCService],
    expected: TXCOperatingProfile | None,
) -> None:
    """
    Test getting OperatingProfile following priority order:
        1. Vehicle Journey OperatingProfile
        2. Service OperatingProfile
    """
    result = get_operating_profile(txc_vj, txc_services)
    assert result == expected
