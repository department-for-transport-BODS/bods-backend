"""
Tests for the FileAttributesEtlLambda
"""

import pytest
from common_layer.database.models.model_organisation import OrganisationDatasetRevision
from common_layer.txc.models.txc_data import TXCData

from tests.factories.database.organisation import OrganisationDatasetRevisionFactory
from tests.timetables_etl.factories.txc.factory_txc_data import (
    TXCDataFactory,
    make_test_txc_data,
)
from tests.timetables_etl.factories.txc.factory_txc_operator import TXCOperatorFactory
from tests.timetables_etl.factories.txc.factory_txc_service import TXCServiceFactory
from timetables_etl.file_attributes_etl import make_txc_file_attributes


@pytest.mark.parametrize(
    "txc_data,revision",
    [
        pytest.param(
            make_test_txc_data(),
            OrganisationDatasetRevisionFactory.create_with_id(1),
            id="Basic Valid TXC Data",
        ),
        pytest.param(
            TXCDataFactory(
                Services=[
                    TXCServiceFactory.multiple_lines(["Line 1", "Line 2"]),
                    TXCServiceFactory.multiple_lines(["Line 3"]),
                ],
                Operators=[
                    TXCOperatorFactory(
                        NationalOperatorCode="TEST123", LicenceNumber="PD9999999"
                    )
                ],
            ),
            OrganisationDatasetRevisionFactory.create_with_id(2),
            id="Multiple Services With Multiple Lines",
        ),
        pytest.param(
            TXCDataFactory(
                Services=[TXCServiceFactory.non_public_use()],
            ),
            OrganisationDatasetRevisionFactory.create_with_id(3),
            id="Non Public Use Service",
        ),
        pytest.param(
            TXCDataFactory(
                Services=[TXCServiceFactory.with_no_origin_destination()],
                Operators=[
                    TXCOperatorFactory(NationalOperatorCode="", LicenceNumber="")
                ],
            ),
            OrganisationDatasetRevisionFactory.create_with_id(4),
            id="Empty Origin Destination And Operator Codes",
        ),
        pytest.param(
            TXCDataFactory(
                Services=[
                    TXCServiceFactory.create(with_standard_line=True),
                    TXCServiceFactory.create(with_standard_line=True),
                ],
                Operators=[TXCOperatorFactory(NationalOperatorCode="FLIX")],
            ),
            OrganisationDatasetRevisionFactory.create_with_id(5),
            id="Multiple Standard Lines With London Plymouth Route",
        ),
        pytest.param(
            TXCDataFactory(
                Services=[TXCServiceFactory.create(no_lines=True)],
            ),
            OrganisationDatasetRevisionFactory.create_with_id(6),
            id="Service With No Lines",
        ),
        pytest.param(
            TXCDataFactory(
                Services=[
                    TXCServiceFactory.flexible_with_origin_destination(
                        origin="Manchester", destination="Liverpool"
                    )
                ],
            ),
            OrganisationDatasetRevisionFactory.create_with_id(7),
            id="Flexible Service With Custom Origin Destination",
        ),
        pytest.param(
            TXCDataFactory(
                Services=[
                    TXCServiceFactory.without_end_date(),
                    TXCServiceFactory.create(),
                ],
            ),
            OrganisationDatasetRevisionFactory.create_with_id(8),
            id="Mixed Services With And Without End Dates",
        ),
        pytest.param(
            TXCDataFactory(Services=[]),
            OrganisationDatasetRevisionFactory.create_with_id(9),
            id="No Services At All",
        ),
        pytest.param(
            TXCDataFactory(
                Services=[
                    TXCServiceFactory.create(
                        StandardService=None, FlexibleService=None
                    ),
                ]
            ),
            OrganisationDatasetRevisionFactory.create_with_id(10),
            id="Service Without Standard Or Flexible Service",
        ),
        pytest.param(
            TXCDataFactory(
                Operators=[
                    TXCOperatorFactory(
                        NationalOperatorCode="NOC1", LicenceNumber="LIC1"
                    ),
                    TXCOperatorFactory(
                        NationalOperatorCode="NOC2", LicenceNumber="LIC2"
                    ),
                ]
            ),
            OrganisationDatasetRevisionFactory.create_with_id(11),
            id="Multiple Operators First Used",
        ),
    ],
)
def test_make_txc_file_attributes_success(
    txc_data: TXCData,
    revision: OrganisationDatasetRevision,
) -> None:
    """Test successful cases for make_txc_file_attributes"""
    result = make_txc_file_attributes(txc_data, revision)

    assert result.revision_id == revision.id

    if txc_data.Metadata:
        assert result.schema_version == txc_data.Metadata.SchemaVersion
        assert result.modification_datetime == txc_data.Metadata.ModificationDateTime
        assert result.modification == txc_data.Metadata.Modification
        assert result.revision_number == txc_data.Metadata.RevisionNumber
        assert result.creation_datetime == txc_data.Metadata.CreationDateTime
        assert result.filename == txc_data.Metadata.FileName
        assert result.hash == (txc_data.Metadata.FileHash or "")

    if txc_data.Services:
        # Service and operator fields
        assert result.service_code == txc_data.Services[0].ServiceCode
        assert result.public_use == txc_data.Services[0].PublicUse

        # Date handling
        start_dates = [service.StartDate for service in txc_data.Services]
        end_dates = [
            service.EndDate for service in txc_data.Services if service.EndDate
        ]
        assert result.operating_period_start_date == (
            min(start_dates) if start_dates else None
        )
        assert result.operating_period_end_date == (
            max(end_dates) if end_dates else None
        )

        # Line names
        all_line_names = []
        for service in txc_data.Services:
            all_line_names.extend(line.LineName for line in service.Lines)
        assert sorted(result.line_names) == sorted(all_line_names)

        # Origin/Destination
        origins = []
        destinations = []
        for service in txc_data.Services:
            if service.StandardService:
                origins.append(service.StandardService.Origin)
                destinations.append(service.StandardService.Destination)
            elif service.FlexibleService:
                origins.append(service.FlexibleService.Origin)
                destinations.append(service.FlexibleService.Destination)

        assert result.origin == (next(iter(origins), "") if origins else "")
        assert result.destination == (
            next(iter(destinations), "") if destinations else ""
        )

    # Operator fields
    if txc_data.Operators:
        assert (
            result.national_operator_code == txc_data.Operators[0].NationalOperatorCode
        )
        assert result.licence_number == (txc_data.Operators[0].LicenceNumber or "")
    else:
        assert result.national_operator_code == ""
        assert result.licence_number == ""


@pytest.mark.parametrize(
    "txc_data,revision,expected_error",
    [
        pytest.param(
            TXCDataFactory(Metadata=None),
            OrganisationDatasetRevisionFactory.create_with_id(1),
            ValueError,
            id="Missing Metadata Should Raise Error",
        ),
        pytest.param(
            make_test_txc_data(schema_version="2.5"),
            OrganisationDatasetRevisionFactory.create_with_id(2),
            ValueError,
            id="Unsupported Schema Version (2.5)",
        ),
    ],
)
def test_make_txc_file_attributes_failure(
    txc_data: TXCData,
    revision: OrganisationDatasetRevision,
    expected_error: type[Exception],
) -> None:
    """Test failure cases for make_txc_file_attributes"""
    with pytest.raises(expected_error):
        make_txc_file_attributes(txc_data, revision)
