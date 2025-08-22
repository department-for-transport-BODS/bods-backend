"""
Exceptions related to missing DB Data for the ETL Processes
Rather than faults with the DB Models / Repos etc
"""

from ...exceptions import ETLException
from ..models import ETLErrorCode


class OrganisationDatasetNotFound(ETLException):
    """
    Step Requiring the OrganisationDataset failed to find the referenced one
    """

    code = ETLErrorCode.ORGANISATION_DATASET_NOT_FOUND


class OrganisationDatasetRevisionNotFound(ETLException):
    """
    Step Requiring the OrganisationDatasetRevision failed to find the referenced one
    """

    code = ETLErrorCode.ORGANISATION_DATASET_REVISION_NOT_FOUND


class OrganisationTXCFileAttributesNotFound(ETLException):
    """
    Step Requiring the OrganisationDatasetRevision failed to find the referenced one
    """

    code = ETLErrorCode.ORGANISATION_TXC_FILE_ATTRIBUTES_NOT_FOUND


class PipelinesDatasetETLTaskResultNotFound(ETLException):
    """
    Step Requiring the OrganisationDatasetRevision failed to find the referenced one
    """

    code = ETLErrorCode.PIPELINES_DATASET_ETL_TASK_RESULT_NOT_FOUND
