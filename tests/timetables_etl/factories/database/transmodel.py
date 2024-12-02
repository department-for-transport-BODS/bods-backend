"""
Transmodel Factories
"""

import factory

from timetables_etl.etl.app.database.models import TransmodelVehicleJourney


class TransmodelVehicleJourneyFactory(factory.Factory):
    """
    Factory for TransmodelVehicleJourney
    """

    class Meta:  # type: ignore[misc]
        model = TransmodelVehicleJourney

    start_time = None
    direction = None
    journey_code = None
    line_ref = None
    departure_day_shift = False
    service_pattern_id = None
    block_number = None

    @classmethod
    def create_with_id(cls, id_number: int) -> TransmodelVehicleJourney:
        """Creates a TransmodelVehicleJourney with a specific ID"""
        journey = cls.create()
        journey.id = id_number
        return journey
