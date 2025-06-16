"""
Exported repos
"""

from .repo_avl import AvlCavlDataArchiveRepo
from .repo_data_quality import (
    DataQualityPostSchemaViolationRepo,
    DataQualityPTIObservationRepo,
    DataQualitySchemaViolationRepo,
)
from .repo_etl_task import (
    ETLTaskResultRepo,
    FileProcessingResultRepo,
    PipelineErrorCodeRepository,
    PipelineProcessingStepRepository,
)
from .repo_fares import (
    FaresDataCatalogueMetadataRepo,
    FaresMetadataRepo,
    FaresMetadataStopsRepo,
    FaresValidationRepo,
    FaresValidationResultRepo,
)
from .repo_junction import (
    OrganisationDatasetRevisionAdminAreasRepo,
    OrganisationDatasetRevisionLocalitiesRepo,
    TransmodelServicePatternAdminAreaRepo,
    TransmodelServicePatternLocalityRepo,
    TransmodelServicePatternTracksRepo,
    TransmodelServiceServicePatternRepo,
    TransmodelTracksVehicleJourneyRepo,
)
from .repo_naptan import NaptanAdminAreaRepo, NaptanLocalityRepo, NaptanStopPointRepo
from .repo_organisation import (
    OrganisationDatasetMetdataRepo,
    OrganisationDatasetRepo,
    OrganisationDatasetRevisionRepo,
    OrganisationOrganisationRepo,
    OrganisationTXCFileAttributesRepo,
)
from .repo_otc import OtcServiceRepo
from .repo_transmodel import (
    TransmodelBankHolidaysRepo,
    TransmodelServicePatternDistanceRepo,
    TransmodelServicePatternRepo,
    TransmodelServicePatternStopRepo,
    TransmodelServiceRepo,
    TransmodelStopActivityRepo,
    TransmodelTrackRepo,
)
from .repo_transmodel_flexible import (
    TransmodelBookingArrangementsRepo,
    TransmodelFlexibleServiceOperationPeriodRepo,
)
from .repo_transmodel_serviced_organisations import (
    TransmodelServicedOrganisationsRepo,
    TransmodelServicedOrganisationVehicleJourneyRepo,
    TransmodelServicedOrganisationWorkingDaysRepo,
)
from .repo_transmodel_vehicle_journey import (
    TransmodelNonOperatingDatesExceptionsRepo,
    TransmodelOperatingDatesExceptionsRepo,
    TransmodelOperatingProfileRepo,
    TransmodelVehicleJourneyRepo,
)

__all__ = [
    # AVL
    "AvlCavlDataArchiveRepo",
    # Data Quality
    "DataQualitySchemaViolationRepo",
    "DataQualityPostSchemaViolationRepo",
    "DataQualityPTIObservationRepo",
    # ETL Task
    "ETLTaskResultRepo",
    "FileProcessingResultRepo",
    "PipelineProcessingStepRepository",
    "PipelineErrorCodeRepository",
    # Fares,
    "FaresDataCatalogueMetadataRepo",
    "FaresMetadataRepo",
    "FaresMetadataStopsRepo",
    "FaresValidationRepo",
    "FaresValidationResultRepo",
    # Junction
    "TransmodelServiceServicePatternRepo",
    "TransmodelServiceServicePatternRepo",
    "OrganisationDatasetRevisionAdminAreasRepo",
    "TransmodelServicePatternAdminAreaRepo",
    "OrganisationDatasetRevisionLocalitiesRepo",
    "TransmodelServicePatternLocalityRepo",
    # Naptan
    "NaptanAdminAreaRepo",
    "NaptanStopPointRepo",
    "NaptanLocalityRepo",
    # Organisation
    "OrganisationDatasetRepo",
    "OrganisationDatasetRevisionRepo",
    "OrganisationOrganisationRepo",
    "OrganisationTXCFileAttributesRepo",
    "OrganisationDatasetMetdataRepo",
    # Otc
    "OtcServiceRepo",
    # Transmodel
    "TransmodelBankHolidaysRepo",
    "TransmodelServicePatternRepo",
    "TransmodelServicePatternDistanceRepo",
    "TransmodelServicePatternStopRepo",
    "TransmodelServiceRepo",
    "TransmodelStopActivityRepo",
    "TransmodelTracksVehicleJourneyRepo",
    "TransmodelTrackRepo",
    # Transmodel Flexible
    "TransmodelBookingArrangementsRepo",
    "TransmodelFlexibleServiceOperationPeriodRepo",
    # Transmodel Serviced Organisations
    "TransmodelServicedOrganisationsRepo",
    "TransmodelServicedOrganisationVehicleJourneyRepo",
    "TransmodelServicedOrganisationWorkingDaysRepo",
    # Transmodel Vehicle Journey
    "TransmodelNonOperatingDatesExceptionsRepo",
    "TransmodelOperatingDatesExceptionsRepo",
    "TransmodelOperatingProfileRepo",
    "TransmodelVehicleJourneyRepo",
    "TransmodelServicePatternTracksRepo",
]
