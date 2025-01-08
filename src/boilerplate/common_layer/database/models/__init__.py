# pylint: disable=too-few-public-methods
"""
Export models for DB queries
"""

from .model_avl import AvlCavlDataArchive
from .model_data_quality import (
    DataQualityPostSchemaViolation,
    DataQualityPTIObservation,
    DataQualitySchemaViolation,
)
from .model_junction import (
    TransmodelServicePatternAdminAreas,
    TransmodelServicePatternLocality,
    TransmodelServiceServicePattern,
    TransmodelTracksVehicleJourney,
)
from .model_naptan import NaptanAdminArea, NaptanLocality, NaptanStopPoint
from .model_organisation import (
    OrganisationDataset,
    OrganisationDatasetRevision,
    OrganisationOrganisation,
    OrganisationTXCFileAttributes,
)
from .model_otc import (
    OtcLocalAuthority,
    OtcLocalAuthorityRegistrationNumbers,
    OtcService,
)
from .model_pipelines import (
    DatasetETLTaskResult,
    ETLErrorCode,
    FileProcessingResult,
    PipelineErrorCode,
    PipelineProcessingStep,
)
from .model_transmodel import (
    TransmodelBankHolidays,
    TransmodelService,
    TransmodelServicePattern,
    TransmodelServicePatternStop,
    TransmodelStopActivity,
    TransmodelTracks,
)
from .model_transmodel_flexible import (
    TransmodelBookingArrangements,
    TransmodelFlexibleServiceOperationPeriod,
)
from .model_transmodel_serviced_organisations import (
    TransmodelServicedOrganisations,
    TransmodelServicedOrganisationVehicleJourney,
    TransmodelServicedOrganisationWorkingDays,
)
from .model_transmodel_vehicle_journey import (
    TMDayOfWeek,
    TransmodelNonOperatingDatesExceptions,
    TransmodelOperatingDatesExceptions,
    TransmodelOperatingProfile,
    TransmodelVehicleJourney,
)
from .model_ui import UiLta
from .model_users import UsersUser

__all__ = [
    # Enums
    "TMDayOfWeek",
    "ETLErrorCode",
    # Database Models
    "AvlCavlDataArchive",
    "NaptanAdminArea",
    "NaptanLocality",
    "NaptanStopPoint",
    # Organisation
    "OrganisationDataset",
    "OrganisationDatasetRevision",
    "OrganisationOrganisation",
    "OrganisationTXCFileAttributes",
    # Transmodel
    "TransmodelBankHolidays",
    "TransmodelBookingArrangements",
    "TransmodelFlexibleServiceOperationPeriod",
    "TransmodelNonOperatingDatesExceptions",
    "TransmodelOperatingDatesExceptions",
    "TransmodelOperatingProfile",
    "TransmodelService",
    "TransmodelServicedOrganisations",
    "TransmodelServicedOrganisationVehicleJourney",
    "TransmodelServicedOrganisationWorkingDays",
    "TransmodelServicePattern",
    "TransmodelServicePatternAdminAreas",
    "TransmodelServicePatternLocality",
    "TransmodelServicePatternStop",
    "TransmodelServiceServicePattern",
    "TransmodelStopActivity",
    "TransmodelTracks",
    "TransmodelTracksVehicleJourney",
    "TransmodelVehicleJourney",
    # Users
    "UsersUser",
    # OTC Models
    "OtcLocalAuthority",
    "OtcLocalAuthorityRegistrationNumbers",
    "OtcService",
    # Ui Models
    "UiLta",
    # Pipelines
    "FileProcessingResult",
    "DatasetETLTaskResult",
    "PipelineErrorCode",
    "PipelineProcessingStep",
    # Data Quality
    "DataQualitySchemaViolation",
    "DataQualityPostSchemaViolation",
    "DataQualityPTIObservation",
]
