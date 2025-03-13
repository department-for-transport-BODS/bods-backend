"""
Test the Filtering Logic
"""

from datetime import date, datetime

import pytest
from collate_files.app.txc_filtering import (
    deduplicate_file_attributes_by_filename,
    filter_txc_files_by_service_code,
    find_highest_revision_in_group,
    find_latest_start_date_file,
    get_earlier_start_date_files,
    group_files_by_service_code,
)
from common_layer.database.models import OrganisationTXCFileAttributes


def create_txc_file_attrs(
    attr_id: int,
    service_code: str,
    revision_number: int,
    operating_period_start_date: date | None = None,
    filename: str = "file.xml",
) -> OrganisationTXCFileAttributes:
    """Create a test TXC file with the specified attributes"""
    attr = OrganisationTXCFileAttributes(
        schema_version="1.0",
        revision_number=revision_number,
        creation_datetime=datetime.now(),
        modification_datetime=datetime.now(),
        filename=filename,
        service_code=service_code,
        revision_id=100,
        modification="TEST",
        national_operator_code="NOC123",
        licence_number="LIC123",
        operating_period_end_date=None,
        operating_period_start_date=operating_period_start_date,
        public_use=True,
        line_names=["Test Line"],
        destination="Test Destination",
        origin="Test Origin",
        hash=f"hash{attr_id}",
        service_mode="bus",
    )
    attr.id = attr_id
    return attr


@pytest.mark.parametrize(
    "files, expected_result",
    [
        pytest.param(
            [
                create_txc_file_attrs(1, "SC001", 1, date(2023, 1, 1)),
                create_txc_file_attrs(2, "SC001", 2, date(2023, 2, 1)),
                create_txc_file_attrs(3, "SC002", 1, date(2023, 1, 1)),
            ],
            {
                "SC001": [
                    create_txc_file_attrs(1, "SC001", 1, date(2023, 1, 1)),
                    create_txc_file_attrs(2, "SC001", 2, date(2023, 2, 1)),
                ],
                "SC002": [
                    create_txc_file_attrs(3, "SC002", 1, date(2023, 1, 1)),
                ],
            },
            id="Multiple service codes",
        ),
        pytest.param(
            [],
            {},
            id="Empty list",
        ),
        pytest.param(
            [
                create_txc_file_attrs(1, "SC001", 1, date(2023, 1, 1)),
                create_txc_file_attrs(2, "SC001", 2, date(2023, 2, 1)),
            ],
            {
                "SC001": [
                    create_txc_file_attrs(1, "SC001", 1, date(2023, 1, 1)),
                    create_txc_file_attrs(2, "SC001", 2, date(2023, 2, 1)),
                ],
            },
            id="Single service code",
        ),
    ],
)
def test_group_files_by_service_code(
    files: list[OrganisationTXCFileAttributes],
    expected_result: dict[str, list[OrganisationTXCFileAttributes]],
):
    """
    Test grouping files by service code
    """
    result = group_files_by_service_code(files)

    # Check structure matches
    assert set(result.keys()) == set(expected_result.keys())

    # For each service code, check the files match
    for service_code in result:
        assert len(result[service_code]) == len(expected_result[service_code])

        # Check each file has the correct service code
        for file in result[service_code]:
            assert file.service_code == service_code


@pytest.mark.parametrize(
    "files, expected_result",
    [
        pytest.param(
            [
                create_txc_file_attrs(1, "SC001", 1, date(2023, 1, 1)),
                create_txc_file_attrs(2, "SC001", 3, date(2023, 2, 1)),
                create_txc_file_attrs(3, "SC001", 2, date(2023, 3, 1)),
            ],
            3,
            id="Multiple revisions",
        ),
        pytest.param(
            [
                create_txc_file_attrs(1, "SC001", 2, date(2023, 1, 1)),
                create_txc_file_attrs(2, "SC001", 2, date(2023, 2, 1)),
            ],
            2,
            id="Same revisions",
        ),
        pytest.param(
            [
                create_txc_file_attrs(1, "SC001", 5, date(2023, 1, 1)),
            ],
            5,
            id="Single file",
        ),
    ],
)
def test_find_highest_revision_in_group(
    files: list[OrganisationTXCFileAttributes],
    expected_result: int,
):
    """
    Test finding the highest revision in a group of files
    """
    result = find_highest_revision_in_group(files)
    assert result == expected_result


@pytest.mark.parametrize(
    "files, revision_to_filter_by, expected_id",
    [
        pytest.param(
            [
                create_txc_file_attrs(1, "SC001", 2, date(2023, 1, 1)),
                create_txc_file_attrs(2, "SC001", 2, date(2023, 2, 1)),
                create_txc_file_attrs(3, "SC001", 2, date(2023, 3, 1)),
            ],
            2,
            3,
            id="Different dates",
        ),
        pytest.param(
            [
                create_txc_file_attrs(1, "SC001", 2, date(2023, 1, 1)),
                create_txc_file_attrs(2, "SC001", 2, None),
                create_txc_file_attrs(3, "SC001", 2, date(2023, 3, 1)),
            ],
            2,
            3,
            id="Mixed dates with None",
        ),
        pytest.param(
            [
                create_txc_file_attrs(1, "SC001", 2, None),
                create_txc_file_attrs(2, "SC001", 2, None),
            ],
            2,
            None,
            id="All None dates",
        ),
        pytest.param(
            [],
            2,
            None,
            id="Empty list",
        ),
    ],
)
def test_find_latest_start_date_file(
    files: list[OrganisationTXCFileAttributes],
    revision_to_filter_by: int,
    expected_id: int | None,
):
    """
    Test finding file with latest start date for various scenarios
    """
    result = find_latest_start_date_file(files, revision_to_filter_by)

    if expected_id is None:
        assert result is None
    else:
        assert result is not None
        assert result.id == expected_id


@pytest.mark.parametrize(
    "files, reference_date, highest_revision, expected_ids",
    [
        pytest.param(
            [
                # Lower revision, earlier date - should be included
                create_txc_file_attrs(1, "SC001", 1, date(2023, 1, 1)),
                # Lower revision, later date - should NOT be included
                create_txc_file_attrs(2, "SC001", 1, date(2023, 4, 1)),
                # Lower revision, no date - should NOT be included
                create_txc_file_attrs(3, "SC001", 1, None),
                # Same revision - should NOT be included regardless of date
                create_txc_file_attrs(4, "SC001", 2, date(2023, 1, 1)),
                # Higher revision - should NOT be included regardless of date
                create_txc_file_attrs(5, "SC001", 3, date(2023, 1, 1)),
            ],
            date(2023, 3, 1),
            2,
            [1],
            id="Mixed files",
        ),
        pytest.param(
            # Input: No files with earlier dates
            [
                create_txc_file_attrs(1, "SC001", 1, date(2023, 4, 1)),
                create_txc_file_attrs(2, "SC001", 1, None),
            ],
            date(2023, 3, 1),
            2,
            [],
            id="No earlier dates",
        ),
        pytest.param(
            [
                create_txc_file_attrs(1, "SC001", 1, date(2023, 1, 1)),
            ],
            None,
            2,
            [],
            id="No reference date",
        ),
    ],
)
def test_get_earlier_start_date_files(
    files: list[OrganisationTXCFileAttributes],
    reference_date: date | None,
    highest_revision: int,
    expected_ids: list[int],
):
    """
    Test getting files with earlier start dates and lower revisions
    """
    result = get_earlier_start_date_files(files, reference_date, highest_revision)

    result_ids = [file.id for file in result]
    assert sorted(result_ids) == sorted(expected_ids)


@pytest.mark.parametrize(
    "files, expected_ids",
    [
        pytest.param(
            # Input: Complex scenario
            [
                # Service Code 1 - Should keep IDs 3 (latest date of highest revision) and 1 (earlier date, lower revision)
                create_txc_file_attrs(1, "SC001", 1, date(2023, 1, 1)),
                create_txc_file_attrs(2, "SC001", 2, date(2023, 2, 1)),
                create_txc_file_attrs(3, "SC001", 2, date(2023, 3, 1)),
                # Service Code 2 - Only one file, should keep it (ID 4)
                create_txc_file_attrs(4, "SC002", 1, date(2023, 1, 1)),
                # Service Code 3 - Since highest revision (2) has NULL date, keep all files (IDs 5 and 6)
                create_txc_file_attrs(5, "SC003", 1, date(2023, 1, 1)),
                create_txc_file_attrs(6, "SC003", 2, None),
                # Service Code 4 - All null dates. Should keep all (ID 7)
                create_txc_file_attrs(7, "SC004", 1, None),
            ],
            # Expected IDs to keep - now includes ID 6
            [1, 3, 4, 5, 6, 7],
            id="Complex scenario",
        ),
        pytest.param(
            # Input: Empty list
            [],
            # Expected: Empty list
            [],
            id="Empty list",
        ),
    ],
)
def test_filter_txc_files_by_service_code(
    files: list[OrganisationTXCFileAttributes],
    expected_ids: list[int],
):
    """
    Test the main filtering function with various scenarios
    """
    result = filter_txc_files_by_service_code(files)

    # Check IDs match
    result_ids = [file.id for file in result]
    assert sorted(result_ids) == sorted(expected_ids)


@pytest.mark.parametrize(
    "files, expected_ids",
    [
        pytest.param(
            [
                create_txc_file_attrs(1, "SC001", 1, date(2023, 1, 1), "file1.xml"),
                create_txc_file_attrs(2, "SC001", 1, date(2023, 1, 1), "file1.xml"),
                create_txc_file_attrs(3, "SC002", 1, date(2023, 1, 1), "file2.xml"),
            ],
            [2, 3],
            id="Deduplicate by filename - higher id wins",
        ),
        pytest.param(
            [
                create_txc_file_attrs(1, "SC001", 1, date(2023, 1, 1), "file1.xml"),
                create_txc_file_attrs(5, "SC001", 2, date(2023, 2, 1), "file1.xml"),
                create_txc_file_attrs(3, "SC001", 3, date(2023, 3, 1), "file1.xml"),
                create_txc_file_attrs(4, "SC002", 1, date(2023, 1, 1), "file2.xml"),
            ],
            [5, 4],
            id="Multiple duplicates - highest id selected",
        ),
        pytest.param(
            [
                create_txc_file_attrs(1, "SC001", 1, date(2023, 1, 1), "file1.xml"),
                create_txc_file_attrs(2, "SC001", 2, date(2023, 2, 1), "file2.xml"),
                create_txc_file_attrs(3, "SC002", 1, date(2023, 1, 1), "file3.xml"),
            ],
            [1, 2, 3],
            id="No duplicates - return all files",
        ),
        pytest.param(
            [],
            [],
            id="Empty list - return empty list",
        ),
    ],
)
def test_deduplicate_file_attributes_by_filename(
    files: list[OrganisationTXCFileAttributes],
    expected_ids: list[int],
):
    """
    Test deduplicating file attributes by filename
    """
    result = deduplicate_file_attributes_by_filename(files)

    # Check the correct number of files was returned
    assert len(result) == len(expected_ids)

    # Check that the returned files have the expected IDs
    result_ids = [file.id for file in result]
    assert sorted(result_ids) == sorted(expected_ids)
