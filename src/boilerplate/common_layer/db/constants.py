from enum import Enum


class StepName(str, Enum):
    CLAM_AV_SCANNER = "Clam AV Scanner"
    TIMETABLE_SCHEMA_CHECK = "Timetable Schema Check"
    TIMETABLE_POST_SCHEMA_CHECK = "Timetable Post Schema Check"
    TXC_FILE_VALIDATOR = "TxC File Validator"
    TXC_ATTRIBUTE_EXTRACTION = "TxC attributes extraction"
    PTI_VALIDATION = "PTI Validation"
    DOWNLOAD_DATASET = "Download Dataset"
    ETL_PROCESS = "ETL Process"
