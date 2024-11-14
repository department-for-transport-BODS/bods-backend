import unittest
from unittest.mock import patch, mock_open
from io import BytesIO
from zipfile import ZipFile, ZIP_DEFLATED
from boilerplate.zip import ZippedValidator
from exceptions.zip_file_exceptions import (
    NestedZipForbidden,
    ZipTooLarge,
    NoDataFound,
    ZipValidationException
)


class TestZippedValidator(unittest.TestCase):
    def create_zip_file(self, files, file_sizes=None):
        """Helper function to create an in-memory zip file."""
        zip_in_memory = BytesIO()
        with ZipFile(zip_in_memory, 'w', ZIP_DEFLATED) as zf:
            for i, file_name in enumerate(files):
                file_content = b"A" * file_sizes[i] if file_sizes else b"Test content"
                zf.writestr(file_name, file_content)
        zip_in_memory.seek(0)
        zip_in_memory.name = "sample.zip"
        return zip_in_memory

    def test_is_too_large(self):
        """Test that ZipTooLarge is raised if the file size exceeds the max size."""
        large_zip = self.create_zip_file(["file1.xml"],
                                         file_sizes=[int(1e10) + 1])  # Larger than 1e10 bytes
        validator = ZippedValidator(large_zip, max_file_size=1e10)

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
        valid_zip = self.create_zip_file(["file1.xml", "file2.xml"], file_sizes=[100, 200])
        validator = ZippedValidator(valid_zip, max_file_size=1e10)

        self.assertTrue(validator.is_valid())

    def test_exceeds_uncompressed_size(self):
        """Test that ZipTooLarge is raised if the sum of uncompressed files exceeds max_file_size."""
        oversized_zip = self.create_zip_file(["file1.xml", "file2.xml"],
                                             file_sizes=[int(5e7), int(5e7)])  # Total > 1e10 bytes
        validator = ZippedValidator(oversized_zip, max_file_size=5e6)

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

    @patch("boilerplate.utils.get_file_size", return_value=500)
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

    @patch("boilerplate.utils.get_file_size", return_value=500)
    @patch("boilerplate.zip.ZipFile")
    def test_is_valid_with_exception(self, mock_zipfile, mock_get_file_size):
        mock_file = mock_open(read_data=b"dummy data")
        with mock_file() as file:
            validator = ZippedValidator(file)
            # Mock the validate method to raise a ZipValidationException
            with patch.object(validator, "validate",
                              side_effect=ZipValidationException("abc.xml")):
                self.assertFalse(validator.is_valid())


if __name__ == "__main__":
    unittest.main()
