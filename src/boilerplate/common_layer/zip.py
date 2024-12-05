from io import BytesIO
from zipfile import ZipFile, is_zipfile, BadZipFile
from common_layer.exceptions.zip_file_exceptions import (
    NestedZipForbidden,
    ZipValidationException,
    ZipTooLarge,
    NoDataFound,
)
from common_layer.utils import get_file_size
from common_layer.logger import logger


def unzip(s3_client, file_path: str, prefix='') -> str:
    try:
        zip_content = BytesIO(s3_client.get_object(file_path).read())
        split_path = file_path.split('/')
        zip_name = split_path[-1].split('.')[0]
        base_dir = f"{'/'.join(split_path[:-1])}"
        folder_name = f"{base_dir}/{prefix}_{zip_name}/" if base_dir else \
            f"{prefix}_{zip_name}/"
        with ZipFile(zip_content) as zipObj:
            for filename in zipObj.namelist():
                file_content = zipObj.read(filename)
                new_key = f"{folder_name}{filename}"
                s3_client.put_object(new_key, file_content)
        return folder_name
    except BadZipFile as e:
        logger.error(f"{file_path} is not a valid zip file: {e}")
        raise e
    except Exception as e:
        print(f"Unexpected error: {e}")
        raise e


class ZippedValidator:
    """Class for validating a transxchange zip file.

    Args:
        file (File): a zip file that requires validation.
        max_file_size (int): maximum size a file can be and pass validation.

    Examples:
        # Use the validator to basic validation, e.g. file size, nesting
        >>> f = open("path/to/zip/file.zip", "rb")
        >>> validator = ZippedValidator(f)
        >>> validator.validate()
        >>> f.close()
    """

    def __init__(self, file, max_file_size=1e10, data_file_ext=".xml"):
        self.file = file
        self.file.seek(0)
        self.max_file_size = max_file_size
        self.data_file_ext = data_file_ext
        self.zip_file = ZipFile(self.file)

    def __enter__(self):
        self.zip_file = ZipFile(self.file)
        return self

    def __exit__(self, *args):
        self.zip_file.close()

    def is_valid(self):
        try:
            self.validate()
        except ZipValidationException:
            return False

        return True

    def validate(self):
        """Validates a zip file and raises an exception if file is invalid.

        Raises:
            NestedZipForbidden: if zip file contains another zip file.
            ZipTooLarge: if zip file or sum of uncompressed files are
            greater than max_file_size.
            NoDataFound: if zip file contains no files with data_file_ext extension.
        """
        if self.is_nested_zip():
            raise NestedZipForbidden(self.file.name)

        if self.is_too_large() or self.exceeds_uncompressed_size():
            raise ZipTooLarge(self.file.name)

        if not self.has_data():
            raise NoDataFound(self.file.name)

    def is_too_large(self):
        """Returns True if zip file is greater than max_file_size."""
        return get_file_size(self.file) > self.max_file_size

    def is_nested_zip(self):
        """Returns True if zip file contains another zip file."""
        names = self.get_files(extension=".zip")
        # explicity check is_zipfile not just the extension
        for name in names:
            with self.open(name) as m:
                if name.endswith(".zip") or is_zipfile(m):
                    return True
        return False

    def has_data(self):
        """Returns True if zip file contains a file with an data_file_ext extension."""
        return len(self.get_files(extension=self.data_file_ext)) > 0

    def exceeds_uncompressed_size(self):
        """Returns True if the sum of the uncompressed files exceeds max_file_size."""
        total = sum([zinfo.file_size for zinfo in self.zip_file.filelist])
        return total > self.max_file_size

    def open(self, name):
        """Opens zip_file."""
        return self.zip_file.open(name, "r")

    def get_files(self, extension=".xml"):
        """Returns a list of the full paths to the files in zip file.

        Args:
            extension (str): The extension to filter the files on.

        """
        return [name for name in self.zip_file.namelist() if name.endswith(extension)]
