"""
The logic for handling superceded TXC Files
If there a multiple files per service code (i.e. sharing the same revision number):

- Select the one with the latest operating_period_start_date
- Retain any files that have an operating_period_start_date earlier
    - Than the combination of (latest start date AND highest revision)

To Ensure files are kept that represent services starting at different times
Even if they have lower revision numbers

So a scenario that get filtered out:

Latest revision but start date is earlier than the latest start date
If there's more than one with the same revision id

"""

from datetime import date

from common_layer.aws.step import MapExecutionSucceeded, MapResults
from common_layer.database.models import OrganisationTXCFileAttributes
from structlog.stdlib import get_logger

from .models import ETLMapInputData

log = get_logger()


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


def find_latest_start_date_file(
    files: list[OrganisationTXCFileAttributes], revision: int
) -> OrganisationTXCFileAttributes | None:
    """
    Find file with latest start date among files with specified revision
    """
    highest_revision_files = [
        file for file in files if file.revision_number == revision
    ]

    latest_start_date = None
    latest_file = None

    for file in highest_revision_files:
        if file.operating_period_start_date is None:
            continue

        if (
            latest_start_date is None
            or file.operating_period_start_date > latest_start_date
        ):
            latest_start_date = file.operating_period_start_date
            latest_file = file

    return latest_file


def get_earlier_start_date_files(
    files: list[OrganisationTXCFileAttributes],
    reference_date: date | None,
    highest_revision: int,
) -> list[OrganisationTXCFileAttributes]:
    """
    Get files with earlier start dates and lower revisions
    """
    if reference_date is None:
        return []

    result: list[OrganisationTXCFileAttributes] = []
    for file in files:
        # Skip files with the highest revision
        if file.revision_number >= highest_revision:
            continue

        # Skip files without start dates
        if file.operating_period_start_date is None:
            continue

        # Keep files with earlier start dates
        if file.operating_period_start_date < reference_date:
            result.append(file)

    return result


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


def filter_txc_files_by_service_code(
    txc_files: list[OrganisationTXCFileAttributes],
) -> list[OrganisationTXCFileAttributes]:
    """
    Filter TXC files according to selection logic:
    - For each service code:
      - From files with highest revision, select only one with latest operating_period_start_date
      - Also retain files with lower revisions that have earlier start dates than the selected file
    """
    service_code_groups = group_files_by_service_code(txc_files)

    filtered_files: list[OrganisationTXCFileAttributes] = []

    for _service_code, files in service_code_groups.items():
        highest_revision = find_highest_revision_in_group(files)

        latest_file = find_latest_start_date_file(files, highest_revision)

        if latest_file:
            # Add the file with highest revision and latest start date
            filtered_files.append(latest_file)

            # Add files with lower revisions and earlier start dates
            earlier_start_files = get_earlier_start_date_files(
                files, latest_file.operating_period_start_date, highest_revision
            )
            filtered_files.extend(earlier_start_files)
        else:
            # If no file with highest revision and valid start date, include all files
            filtered_files.extend(files)

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
