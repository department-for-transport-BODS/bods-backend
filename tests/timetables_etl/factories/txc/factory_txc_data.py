"""
TXC Data Factory
"""

from datetime import date
from typing import Optional

import factory
from common_layer.xml.txc.models.txc_data import TXCData

from tests.timetables_etl.factories.txc.factory_txc_metadata import TXCMetadataFactory
from tests.timetables_etl.factories.txc.factory_txc_operator import TXCOperatorFactory
from tests.timetables_etl.factories.txc.factory_txc_service import (
    TXCLineFactory,
    TXCServiceFactory,
    TXCStandardServiceFactory,
)


class TXCDataFactory(factory.Factory):
    """
    Factory to create TXC Data
    """

    class Meta:  # type: ignore[misc]
        model = TXCData

    Metadata = factory.SubFactory(TXCMetadataFactory)
    Operators = factory.List([factory.SubFactory(TXCOperatorFactory)])
    Services = factory.List([factory.SubFactory(TXCServiceFactory)])


def make_test_txc_data(
    *,
    schema_version: Optional[str] = None,
    modification: Optional[str] = None,
    operator_code: Optional[str] = None,
    licence_number: Optional[str] = None,
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    service_code: Optional[str] = None,
    public_use: Optional[bool] = None,
    line_names: Optional[list[str]] = None,
    origin: Optional[str] = None,
    destination: Optional[str] = None
) -> TXCData:
    """Helper function to create TXCData with customizable fields"""
    metadata_kwargs = {}
    if schema_version:
        metadata_kwargs["SchemaVersion"] = schema_version
    if modification:
        metadata_kwargs["Modification"] = modification

    operator_kwargs = {}
    if operator_code:
        operator_kwargs["NationalOperatorCode"] = operator_code
    if licence_number:
        operator_kwargs["LicenceNumber"] = licence_number

    service_kwargs = {}
    if start_date:
        service_kwargs["StartDate"] = start_date
    if end_date:
        service_kwargs["EndDate"] = end_date
    if service_code:
        service_kwargs["ServiceCode"] = service_code
    if public_use is not None:
        service_kwargs["PublicUse"] = public_use

    standard_service_kwargs = {}
    if origin:
        standard_service_kwargs["Origin"] = origin
    if destination:
        standard_service_kwargs["Destination"] = destination

    lines = []
    if line_names:
        lines = [TXCLineFactory(LineName=name) for name in line_names]

    if standard_service_kwargs:
        service_kwargs["StandardService"] = TXCStandardServiceFactory(
            **standard_service_kwargs
        )
    if lines:
        service_kwargs["Lines"] = lines

    return TXCDataFactory(
        Metadata=TXCMetadataFactory(**metadata_kwargs),
        Operators=[TXCOperatorFactory(**operator_kwargs)],
        Services=[TXCServiceFactory(**service_kwargs)],
    )
