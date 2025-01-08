from io import BytesIO
from zipfile import is_zipfile

from common_layer.db.constants import StepName
from common_layer.db.file_processing_result import file_processing_result_to_db
from common_layer.exceptions.xml_file_exceptions import XMLValidationException
from common_layer.exceptions.zip_file_exceptions import ZipValidationException
from common_layer.json_logging import configure_logging
from common_layer.s3 import S3
from common_layer.xml_validator import FileValidator, XMLValidator
from common_layer.zip import ZippedValidator
from structlog.stdlib import get_logger

log = get_logger()


class TimetableFileValidator:
    def __init__(self, event):
        self._s3_obj = S3(event["Bucket"])
        self._key = event["ObjectKey"]

    @property
    def is_zip(self):
        with BytesIO(self._s3_obj.get_object(self._key).read()) as file_object:
            return is_zipfile(file_object)

    @property
    def file(self):
        byte_stream = BytesIO(self._s3_obj.get_object(self._key).read())
        byte_stream.name = self._key
        return byte_stream

    def validate(self):
        """Validates a Timetable DatasetRevision.

        Raises:
            FileTooLarge: if file size is greater than max_file_size.

            DangerousXML: if DefusedXmlException is raised during parsing.
            XMLSyntaxError: if the file cannot be parsed.

            NestedZipForbidden: if zip file contains another zip file.
            ZipTooLarge: if zip file or sum of uncompressed files are
                greater than max_file_size.
            NoDataFound: if zip file contains no files with data_file_ext extension.
        """
        FileValidator(self.file).is_too_large()
        if self.is_zip:
            with ZippedValidator(self.file) as zv:
                zv.validate()
                for name in zv.get_files():
                    with zv.open(name) as f:
                        XMLValidator(f).dangerous_xml_check()
        else:
            XMLValidator(self.file).dangerous_xml_check()


@file_processing_result_to_db(step_name=StepName.TXC_FILE_VALIDATOR)
def lambda_handler(event, context):
    configure_logging()
    bucket = event["Bucket"]
    key = event["ObjectKey"]
    try:
        validator = TimetableFileValidator(event)
        validator.validate()
    except ZipValidationException as exc:
        message = exc.message
        log.error(message, exc_info=True)
        raise exc
    except XMLValidationException as exc:
        message = exc.message
        log.error(message, exc_info=True)
        raise exc
    except Exception as exc:
        raise exc
    return {
        "statusCode": 200,
        "body": f"File validation completed '{key}' from bucket '{bucket}'",
    }
