"""
Test TXCFileAttributes Serialisation
"""

from datetime import UTC, datetime
from typing import Any

import pytest
from common_layer.dynamodb.models import TXCFileAttributes
from common_layer.dynamodb.utils import dataclass_to_dict
from freezegun import freeze_time

from tests.factories.database.organisation import OrganisationTXCFileAttributesFactory


@pytest.mark.parametrize(
    "factory_kwargs,expected_modifications",
    [
        pytest.param({}, {}, id="Default Factory Values"),
        pytest.param(
            {"line_names": ["Route 66", "Golden Line"], "service_code": "EXPRESS_101"},
            {"line_names": ["Route 66", "Golden Line"], "service_code": "EXPRESS_101"},
            id="Custom Route Names And Service",
        ),
        pytest.param(
            {
                "revision_number": 42,
            },
            {
                "revision_number": 42,
            },
            id="Revised Service Between Cities",
        ),
    ],
)
@freeze_time("2024-02-04 12:00:00")
def test_dataclass_to_dict_serialization(
    factory_kwargs: dict[str, Any], expected_modifications: dict[str, Any]
) -> None:
    """
    Test the serialization of TXCFileAttributes instances to dictionaries.

    Tests various combinations of input data including default values and custom modifications.
    Verifies that all fields are correctly serialized and modified fields maintain their values.
    """
    # Create the ORM object using the factory
    orm_obj = OrganisationTXCFileAttributesFactory.create(**factory_kwargs)

    # Convert to PTI model
    pti_obj = TXCFileAttributes.from_orm(orm_obj)

    # Serialize using our utility function
    serialized = dataclass_to_dict(pti_obj)

    # Expected base values (common across all test cases)
    frozen_timestamp = int(datetime(2024, 2, 4, 12, 0, tzinfo=UTC).timestamp())

    expected_base = {
        "id": orm_obj.id,
        "revision_number": orm_obj.revision_number,
        "service_code": orm_obj.service_code,
        "line_names": orm_obj.line_names,
        "modification_datetime": frozen_timestamp,
        "hash": orm_obj.hash,
        "filename": orm_obj.filename,
    }

    # Update base expectations with case-specific modifications
    expected = {**expected_base, **expected_modifications}

    assert serialized == expected


@pytest.mark.parametrize(
    "invalid_input",
    [
        pytest.param(None, id="None Value"),
        pytest.param({}, id="Empty Dict"),
        pytest.param([], id="Empty List"),
        pytest.param("string", id="String Value"),
        pytest.param(123, id="Integer Value"),
    ],
)
def test_dataclass_to_dict_invalid_inputs(invalid_input: Any) -> None:
    """
    Test error handling for invalid inputs to dataclass_to_dict.

    Verifies that appropriate TypeError is raised when non-dataclass instances
    are passed to the serialization function.

    """
    with pytest.raises(TypeError):
        dataclass_to_dict(invalid_input)


@pytest.mark.parametrize(
    "modification_datetime,expected_timestamp",
    [
        pytest.param(
            datetime(2024, 1, 1, 0, 0, tzinfo=UTC), 1704067200, id="New Years Day 2024"
        ),
        pytest.param(
            datetime(2024, 12, 31, 23, 59, 59, tzinfo=UTC),
            1735689599,
            id="New Years Eve 2024",
        ),
    ],
)
def test_dataclass_to_dict_datetime_serialization(
    modification_datetime: datetime, expected_timestamp: int
) -> None:
    """
    Test datetime field serialization in TXCFileAttributes.

    Verifies that datetime fields are correctly converted to Unix timestamps
    during serialization.

    """
    # Create the ORM object with specific datetime
    orm_obj = OrganisationTXCFileAttributesFactory.create(
        modification_datetime=modification_datetime
    )

    # Convert to PTI model
    pti_obj = TXCFileAttributes.from_orm(orm_obj)

    # Serialize
    serialized = dataclass_to_dict(pti_obj)

    assert serialized["modification_datetime"] == expected_timestamp
