"""
Shared Constants
"""

from enum import Enum


class StepName(str, Enum):
    """
    Enumeration representing various steps or processes in a workflow.
    """

    CLAM_AV_SCANNER = "Clam AV Scanner"
    TIMETABLE_SCHEMA_CHECK = "Timetable Schema Check"
    TIMETABLE_POST_SCHEMA_CHECK = "Timetable Post Schema Check"
    TXC_FILE_VALIDATOR = "TxC File Validator"
    NETEX_FILE_VALIDATOR = "NeTEx File Validator"
    TXC_ATTRIBUTE_EXTRACTION = "TxC attributes extraction"
    PTI_VALIDATION = "PTI Validation"
    DOWNLOAD_DATASET = "Download Dataset"
    ETL_PROCESS = "ETL Process"
    GENERATE_OUTPUT_ZIP = "Final Output Zip Generation"
