from datetime import date

import factory
from common_layer.database.models.model_otc import (
    OtcLocalAuthority,
    OtcLocalAuthorityRegistrationNumbers,
    OtcService,
)
from factory import LazyFunction
from factory.fuzzy import FuzzyChoice, FuzzyInteger


class OtcServiceFactory(factory.Factory):
    """
    Factory for creating OtcService instances using the repository pattern.
    """

    class Meta:  # type: ignore[misc]
        """Factory configuration."""

        model = OtcService

    registration_number = factory.Sequence(lambda n: f"PH0006633/0{n}")
    variation_number = FuzzyInteger(1, 10)
    service_number = factory.Sequence(lambda n: f"SERVICE_{n}")
    current_traffic_area = ""
    start_point = "Bristol Bus Station (01000053209)"
    finish_point = "Clevedon, Six Ways (0190NSC30808)"
    via = "Tickenham"
    service_type_other_details = ""
    description = ""
    registration_status = ""
    public_text = ""
    service_type_description = ""
    subsidies_description = ""
    subsidies_details = ""

    effective_date = LazyFunction(lambda: date(2024, 12, 31))
    received_date = None
    end_date = None

    registration_code = None
    short_notice = False
    licence_id = None
    operator_id = None
    last_modified = None
    api_type = FuzzyChoice(choices=["WECA", "EP", None])
    atco_code = factory.Sequence(lambda n: f"ATC00{n}")

    @classmethod
    def create_with_id(cls, id_number: int, **kwargs) -> OtcService:
        """Creates file attributes with a specific ID"""
        attrs = cls.create(id=id_number, **kwargs)
        return attrs


class OtcLocalAuthorityFactory(factory.Factory):
    """
    Factory for creating OtcLocalAuthority instances using the repository pattern.
    """

    class Meta:  # type: ignore[misc]
        """Factory configuration."""

        model = OtcLocalAuthority

    name = "local-authority-name"
    ui_lta_id = None


class OtcLocalAuthorityRegistrationNumbersFactory(factory.Factory):
    """
    Factory for creating OtcLocalAuthorityRegistrationNumbers instances using the repository pattern.
    """

    class Meta:  # type: ignore[misc]
        """Factory configuration."""

        model = OtcLocalAuthorityRegistrationNumbers
