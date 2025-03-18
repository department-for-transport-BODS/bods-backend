"""
Exceptions related to missing DB Data for the ETL Processes
Rather than faults with the DB Models / Repos etc
"""

from ..models import ETLErrorCode


class OrganisationDatasetRevisionNotFound(Exception):
    """
    Step Requiring the OrganisationDatasetRevision failed to find the referenced one
    """

    code = ETLErrorCode.ORGANISATION_DATASET_REVISION_NOT_FOUND


class OrganisationTXCFileAttributesNotFound(Exception):
    """
    Step Requiring the OrganisationDatasetRevision failed to find the referenced one
    """

    code = ETLErrorCode.ORGANISATION_DATASET_REVISION_NOT_FOUND
