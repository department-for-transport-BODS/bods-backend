import unittest
from unittest.mock import patch, mock_open, MagicMock
from io import BytesIO
from zipfile import ZipFile, ZIP_DEFLATED, BadZipFile
from boilerplate.zip import ZippedValidator, unzip
from exceptions.zip_file_exceptions import (
    NestedZipForbidden,
    ZipTooLarge,
    NoDataFound,
    ZipValidationException,
)


class TestZippedValidator(unittest.TestCase):
    def create_zip_file(self, files, file_sizes=None):
        """Helper function to create an in-memory zip file."""
        zip_in_memory = BytesIO()
        with ZipFile(zip_in_memory, "w", ZIP_DEFLATED) as zf:
            for i, file_name in enumerate(files):
                file_content = b"A" * file_sizes[i] if file_sizes else b"Test content"
                zf.writestr(file_name, file_content)
        zip_in_memory.seek(0)
        zip_in_memory.name = "sample.zip"
        return zip_in_memory

    def test_is_too_large(self):
        """Test that ZipTooLarge is raised if the file size exceeds the max size."""
        large_zip = self.create_zip_file(
            ["file1.xml"], file_sizes=[int(2)]
        )  # Larger than max_file_size
        validator = ZippedValidator(large_zip, max_file_size=int(1))

        with self.assertRaises(ZipTooLarge):
            validator.validate()

    def test_is_nested_zip(self):
        """Test that NestedZipForbidden is raised if there is a nested zip."""
        nested_zip = self.create_zip_file(["nested.zip", "file1.xml"])
        validator = ZippedValidator(nested_zip)

        with self.assertRaises(NestedZipForbidden):
            validator.validate()

    def test_has_data(self):
        """Test that NoDataFound is raised if there is no file with the data_file_ext extension."""
        zip_without_xml = self.create_zip_file(["file1.txt", "file2.csv"])
        validator = ZippedValidator(zip_without_xml, data_file_ext=".xml")

        with self.assertRaises(NoDataFound):
            validator.validate()

    def test_valid_zip(self):
        """Test that a valid zip file passes validation."""
        valid_zip = self.create_zip_file(
            ["file1.xml", "file2.xml"], file_sizes=[100, 200]
        )
        validator = ZippedValidator(valid_zip, max_file_size=1e10)

        self.assertTrue(validator.is_valid())

    def test_exceeds_uncompressed_size(self):
        """Test that ZipTooLarge is raised if the sum of uncompressed files exceeds max_file_size."""
        oversized_zip = self.create_zip_file(
            ["file1.xml", "file2.xml"], file_sizes=[int(2), int(2)]
        )  # Total > max_file_size
        validator = ZippedValidator(oversized_zip, max_file_size=int(3))

        with self.assertRaises(ZipTooLarge):
            validator.validate()

    def test_get_files_with_extension(self):
        """Test that get_files returns only files with the specified extension."""
        mixed_zip = self.create_zip_file(["file1.xml", "file2.txt", "file3.xml"])
        validator = ZippedValidator(mixed_zip, data_file_ext=".xml")

        files = validator.get_files(extension=".xml")
        self.assertEqual(files, ["file1.xml", "file3.xml"])

    def test_open_file_in_zip(self):
        """Test that open can correctly open a file within the zip."""
        zip_file = self.create_zip_file(["file1.xml"])
        validator = ZippedValidator(zip_file)

        with validator.open("file1.xml") as f:
            content = f.read()
            self.assertEqual(content, b"Test content")

    @patch("boilerplate.bods_utils.get_file_size", return_value=500)
    @patch("boilerplate.zip.ZipFile")
    def test_context_manager(self, mock_zipfile, mock_get_file_size):
        # Create a dummy zip file using mock_open
        mock_file = mock_open(read_data=b"dummy data")
        with mock_file() as file:
            # Test __enter__ and __exit__ with context manager
            with ZippedValidator(file) as validator:
                self.assertTrue(mock_zipfile.call_count == 2)
            # Ensure zip_file was closed on __exit__
            mock_zipfile.return_value.close.assert_called_once()

    @patch("boilerplate.bods_utils.get_file_size", return_value=500)
    @patch("boilerplate.zip.ZipFile")
    def test_is_valid_with_exception(self, mock_zipfile, mock_get_file_size):
        mock_file = mock_open(read_data=b"dummy data")
        with mock_file() as file:
            validator = ZippedValidator(file)
            # Mock the validate method to raise a ZipValidationException
            with patch.object(
                validator, "validate", side_effect=ZipValidationException("abc.xml")
            ):
                self.assertFalse(validator.is_valid())

    def test_unzip_valid_zip(self):
        s3_client = MagicMock()
        # Arrange
        file_path = 'test-folder/test.zip'
        prefix = 'unzipped'

        # Create a valid zip file in memory
        zip_buffer = BytesIO()
        with ZipFile(zip_buffer, 'w') as zip_file:
            zip_file.writestr('file1.txt', 'Hello, world!')
            zip_file.writestr('file2.txt', 'Python is awesome!')
        zip_buffer.seek(0)

        # Mock the S3 client to return the zip file for get_object
        s3_client.get_object.return_value = zip_buffer

        # Mock the put_object method
        s3_client.put_object = MagicMock()

        # Act
        result = unzip(s3_client, file_path, prefix)

        # Assert
        expected_folder = 'test-folder/unzipped_test/'
        self.assertEqual(result, expected_folder)

        # Verify that files are uploaded to S3
        s3_client.put_object.assert_any_call(
            f"{expected_folder}file1.txt", b'Hello, world!'
        )
        s3_client.put_object.assert_any_call(
            f"{expected_folder}file2.txt", b'Python is awesome!'
        )

    def test_unzip_invalid_zip(self):
        s3_client = MagicMock()
        # Arrange
        file_path = 'test-folder/invalid.zip'

        # Mock the S3 client to return invalid zip content
        s3_client.get_object.return_value = BytesIO(b'Not a zip file')

        # Act & Assert
        with self.assertRaises(BadZipFile):
            unzip(s3_client, file_path)


if __name__ == "__main__":
    unittest.main()
