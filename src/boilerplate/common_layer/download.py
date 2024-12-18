"""
Downloader functions
"""

from common_layer.s3 import S3
from common_layer.txc.models.txc_data import TXCData
from common_layer.txc.parser.parser_txc import load_xml_data, parse_txc_from_element
from lxml.etree import _Element
from structlog.stdlib import get_logger

log = get_logger()


def get_txc_xml(s3_bucket_name: str, s3_file_key: str) -> _Element:
    """
    Get the TXC XML Data from S3
    """
    s3_client = S3(s3_bucket_name)
    file_data = s3_client.download_fileobj(s3_file_key)
    log.info("Downloaded S3 data", bucket=s3_bucket_name, key=s3_file_key)
    xml = load_xml_data(file_data)
    log.info("Parsed XML data")
    return xml


def download_and_parse_txc(s3_bucket: str, s3_key: str) -> TXCData:
    """
    Download from S3 and return Pydantic model of TXC Data to process
    """
    xml = get_txc_xml(s3_bucket, s3_key)

    txc_data = parse_txc_from_element(xml)
    log.info("Parsed TXC XML into Pydantic Models")
    return txc_data
