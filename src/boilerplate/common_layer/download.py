"""
Downloader functions
"""

from common_layer.s3 import S3
from common_layer.xml.txc.models import TXCData
from common_layer.xml.txc.parser.parser_txc import (
    TXCParserConfig,
    load_xml_data,
    parse_txc_from_element,
)
from common_layer.xml.utils.hashing import get_bytes_hash
from lxml.etree import _Element  # type: ignore
from structlog.stdlib import get_logger

log = get_logger()


def get_txc_xml(s3_bucket_name: str, s3_file_key: str) -> tuple[_Element, str]:
    """
    Download XML from S3, Calculate hash, and parse as lxml _Element
    Returns tuple of xml data and hash string
    """
    s3_client = S3(s3_bucket_name)
    file_data = s3_client.download_fileobj(s3_file_key)
    file_hash = get_bytes_hash(file_data)
    log.info("Downloaded S3 data", bucket=s3_bucket_name, key=s3_file_key)
    xml = load_xml_data(file_data)
    log.info("Parsed XML data")
    return xml, file_hash


def download_and_parse_txc(
    s3_bucket: str, s3_key: str, txc_parser_config: TXCParserConfig | None = None
) -> TXCData:
    """
    Download from S3 and return Pydantic model of TXC Data to process
    """
    xml_data, file_hash = get_txc_xml(s3_bucket, s3_key)

    txc_data = parse_txc_from_element(xml_data, txc_parser_config)
    if file_hash and txc_data.Metadata:
        txc_data.Metadata.FileHash = file_hash
    log.info("Parsed TXC XML into Pydantic Models")
    return txc_data
