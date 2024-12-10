"""
Transmodel Factories
"""

from datetime import date, datetime, timedelta
from typing import Literal

import factory
from common_layer.database.models import (
    TransmodelBookingArrangements,
    TransmodelService,
    TransmodelVehicleJourney,
)


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


class TransmodelServiceFactory(factory.Factory):
    """Factory for TransmodelService with consistent test data generation"""

    class Meta:  # type: ignore[misc]
        model = TransmodelService

    # Default field values
    service_code = factory.Sequence(lambda n: f"TEST{n:04d}")
    name = factory.Sequence(lambda n: f"Service {n}")
    other_names = factory.List([])
    start_date = factory.LazyFunction(lambda: date.today())
    service_type: Literal["standard", "flexible"] = "standard"
    end_date = factory.LazyFunction(lambda: date.today() + timedelta(days=365))
    revision_id = None
    txcfileattributes_id = None

    @classmethod
    def create_standard_service(
        cls, id_number: int, service_code: str | None = None
    ) -> TransmodelService:
        """Creates a standard service with default values"""
        return cls.create_with_id(
            id_number=id_number,
            service_code=service_code or f"STD{id_number:04d}",
            service_type="standard",
        )

    @classmethod
    def create_flexible_service(
        cls, id_number: int, service_code: str | None = None
    ) -> TransmodelService:
        """Creates a flexible service with default values"""
        return cls.create_with_id(
            id_number=id_number,
            service_code=service_code or f"FLX{id_number:04d}",
            service_type="flexible",
        )

    @classmethod
    def create_with_id(cls, id_number: int, **kwargs) -> TransmodelService:
        """Creates a TransmodelService with a specific ID"""
        service = cls.create(**kwargs)
        service.id = id_number
        return service

    @classmethod
    def create_batch_with_ids(
        cls, starting_id: int, count: int, **kwargs
    ) -> list[TransmodelService]:
        """Creates multiple services with sequential IDs"""
        return [
            cls.create_with_id(id_number=starting_id + i, **kwargs)
            for i in range(count)
        ]


class TransmodelBookingArrangementsFactory(factory.Factory):
    """Factory for TransmodelBookingArrangements"""

    class Meta:  # type: ignore[misc]
        model = TransmodelBookingArrangements

    description = factory.Sequence(lambda n: f"Booking Arrangement {n}")
    email = None
    phone_number = None
    web_address = None
    created = factory.LazyFunction(lambda: datetime.now())
    last_updated = factory.LazyFunction(lambda: datetime.now())
    service_id = factory.Sequence(lambda n: n)

    @classmethod
    def create_with_id(cls, id_number: int, **kwargs) -> TransmodelBookingArrangements:
        """Creates a TransmodelBookingArrangements with a specific ID"""
        arrangement = cls.create(**kwargs)
        arrangement.id = id_number
        return arrangement

    @classmethod
    def phone_only(
        cls, service_id: int, description: str, phone: str
    ) -> TransmodelBookingArrangements:
        """Creates a phone-only booking arrangement"""
        return cls.create(
            description=description,
            phone_number=phone,
            service_id=service_id,
        )

    @classmethod
    def online_only(
        cls,
        service_id: int,
        description: str,
        email: str | None = None,
        web_address: str | None = None,
    ) -> TransmodelBookingArrangements:
        """Creates an online-only booking arrangement"""
        return cls.create(
            description=description,
            email=email,
            web_address=web_address,
            service_id=service_id,
        )

    @classmethod
    def all_methods(
        cls,
        service_id: int,
        description: str,
        phone: str,
        email: str,
        web_address: str,
    ) -> TransmodelBookingArrangements:
        """Creates a booking arrangement with all contact methods"""
        return cls.create(
            description=description,
            phone_number=phone,
            email=email,
            web_address=web_address,
            service_id=service_id,
        )
