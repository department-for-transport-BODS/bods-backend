"""
The logic for handling superceded TXC Files
"""

from datetime import date

from common_layer.aws.step import MapExecutionSucceeded, MapResults
from common_layer.database.models import OrganisationTXCFileAttributes
from structlog.stdlib import get_logger

from .models import ETLMapInputData

log = get_logger()


def deduplicate_file_attributes_by_filename(
    file_attributes: list[OrganisationTXCFileAttributes],
) -> list[OrganisationTXCFileAttributes]:
    """
    Deduplicate file attributes by filename, keeping the one with the highest id
    for each unique filename.
    This scenario should only happen when developing / testing
    When calling the State Machine directly multiple times against a revision
    """
    # Group file attributes by filename
    filename_groups: dict[str, list[OrganisationTXCFileAttributes]] = {}
    for file in file_attributes:
        if file.filename not in filename_groups:
            filename_groups[file.filename] = []
        filename_groups[file.filename].append(file)

    # For each group, select the file attribute with the highest id
    deduplicated_files: list[OrganisationTXCFileAttributes] = []

    for filename, files in filename_groups.items():
        if len(files) > 1:
            # Multiple files with the same filename found
            file_ids = [file.id for file in files]
            files_sorted_by_id = sorted(files, key=lambda x: x.id, reverse=True)
            selected_file = files_sorted_by_id[0]

            log.info(
                "Multiple OrganisationTXCFileAttributes found for filename",
                filename=filename,
                file_attribute_ids=file_ids,
                selected_id=selected_file.id,
                total_duplicates=len(files),
            )

            deduplicated_files.append(selected_file)
        else:
            # Only one file with this filename
            deduplicated_files.append(files[0])

    if len(file_attributes) != len(deduplicated_files):
        log.info(
            "File Attributes Deduplicated",
            original_count=len(file_attributes),
            deduplicated_count=len(deduplicated_files),
            duplicate_count=len(file_attributes) - len(deduplicated_files),
        )

    return deduplicated_files


def group_files_by_service_code(
    txc_files: list[OrganisationTXCFileAttributes],
) -> dict[str, list[OrganisationTXCFileAttributes]]:
    """
    Group files by service code
    """
    service_code_groups: dict[str, list[OrganisationTXCFileAttributes]] = {}
    for file in txc_files:
        if file.service_code not in service_code_groups:
            service_code_groups[file.service_code] = []
        service_code_groups[file.service_code].append(file)
    return service_code_groups


def find_highest_revision_in_group(files: list[OrganisationTXCFileAttributes]) -> int:
    """
    Find the highest revision number in a group of files
    """
    return max(file.revision_number for file in files)


def get_max_start_date(files: list[OrganisationTXCFileAttributes]) -> date | None:
    """
    Get the latest operating_period_start_date from a group of files
    """
    return max(
        (
            file.operating_period_start_date
            for file in files
            if file.operating_period_start_date
        ),
        default=None,
    )


def get_earlier_start_date_files(
    files: list[OrganisationTXCFileAttributes],
    reference_date: date | None,
    highest_revision: int,
) -> list[OrganisationTXCFileAttributes]:
    """
    Get files with earlier start dates and lower revisions
    """
    if not reference_date:
        # Edge case: We don't expect this to happen in production, since
        # StartDate is mandatory in the TransXChange XSD
        return [file for file in files if file.revision_number < highest_revision]

    return [
        file
        for file in files
        if file.revision_number < highest_revision
        and file.operating_period_start_date
        and file.operating_period_start_date < reference_date
    ]


def filter_txc_files_by_service_code(
    txc_files: list[OrganisationTXCFileAttributes],
) -> list[OrganisationTXCFileAttributes]:
    """
    Filter TXC files according to selection logic:
    - For each service code:
      - Select all files from the highest revision
      - Also retain files with lower revisions that have earlier start dates than the selected file

    With this logic, we filter out any files from previous revisions that have been superceded
    """
    service_code_groups = group_files_by_service_code(txc_files)

    filtered_files: list[OrganisationTXCFileAttributes] = []

    for _service_code, files in service_code_groups.items():
        highest_revision = find_highest_revision_in_group(files)

        # Include all files from the highest revision
        highest_revision_files = [
            file for file in files if file.revision_number == highest_revision
        ]
        filtered_files.extend(highest_revision_files)

        # Find the max start date within the highest revision group
        max_start_date = get_max_start_date(highest_revision_files)

        # Include files with earlier start dates from lower revisions
        earlier_start_files = get_earlier_start_date_files(
            files, max_start_date, highest_revision
        )
        filtered_files.extend(earlier_start_files)

    return filtered_files


def build_filename_map(
    map_results: MapResults,
) -> dict[str, MapExecutionSucceeded]:
    """
    Build a  Dictionary mapping filenames to successful map executions
    """
    filename_to_map_result: dict[str, MapExecutionSucceeded] = {}

    for result in map_results.succeeded:
        if result.parsed_input and result.parsed_input.Key:
            # Extract filename from the S3 key
            filename = result.parsed_input.Key.split("/")[-1]
            filename_to_map_result[filename] = result

    return filename_to_map_result


def create_etl_map_inputs(
    all_files: list[OrganisationTXCFileAttributes],
    filtered_files: list[OrganisationTXCFileAttributes],
    filename_map: dict[str, MapExecutionSucceeded],
) -> list[ETLMapInputData]:
    """
    Create S3FileReference objects for files,
    marking those not in filtered_files as superceded
    """
    filtered_file_ids = {file.id for file in filtered_files}

    s3_references: list[ETLMapInputData] = []

    for file in all_files:
        # Determine if this file was filtered out (superseded)
        is_superceded = file.id not in filtered_file_ids

        map_result = filename_map.get(file.filename)

        if map_result and map_result.parsed_input:
            # Only create reference if we have valid bucket and key
            if map_result.parsed_input.Bucket and map_result.parsed_input.Key:
                s3_reference = ETLMapInputData(
                    s3_bucket_name=map_result.parsed_input.Bucket,
                    s3_file_key=map_result.parsed_input.Key,
                    superseded_timetable=is_superceded,
                    file_attributes_id=file.id,
                )

                s3_references.append(s3_reference)

    return s3_references


def create_etl_inputs_from_map_results(
    all_files: list[OrganisationTXCFileAttributes],
    filtered_files: list[OrganisationTXCFileAttributes],
    map_results: MapResults,
) -> list[ETLMapInputData]:
    """
    For each successful file build a list of Map inputs checking whether to supercede
    """
    filename_map = build_filename_map(map_results)

    return create_etl_map_inputs(all_files, filtered_files, filename_map)
