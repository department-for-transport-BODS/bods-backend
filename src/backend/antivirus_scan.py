from logger import logger
from file_scanner import FileScanner # to be imported from lambda layer
from s3 import S3


def lambda_handler(event, context):
    zip_file_location = event.get('zip_file_path', None)
    try:
        if zip_file_location is None:
            raise Exception
        # read zip file from s3 location
        s3_file = read_s3_file(zip_file_location)
        scanner = FileScanner(settings.CLAMAV_HOST, settings.CLAMAV_PORT)
        scanner.scan(s3_file)
        # instaitae Filescanner object
        # call the required method to scan the file and get the response
    except Exception as e:
        logger.error(f"GTFSRT zip task failed due to {e}")
    return