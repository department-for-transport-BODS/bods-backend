import unittest
from io import BytesIO
from boilerplate.utils import get_file_size, sha1sum
import tempfile
import os


class TestGetFileSize(unittest.TestCase):
    def test_get_file_size_with_bytesio(self):
        """Test with an in-memory file using BytesIO."""
        # Create an in-memory file with BytesIO
        in_memory_file = BytesIO(b"testing file size")

        # Expected size is the length of the string in bytes
        expected_size = len(b"testing file size")

        # Assert that get_file_size returns the correct size
        self.assertEqual(get_file_size(in_memory_file), expected_size)

    def test_get_file_size_with_empty_file(self):
        """Test with an empty in-memory file."""
        # Create an empty in-memory file
        empty_file = BytesIO(b"")

        # Expected size is 0 for an empty file
        expected_size = 0

        # Assert that get_file_size returns the correct size
        self.assertEqual(get_file_size(empty_file), expected_size)

    def test_get_file_size_with_real_file(self):
        """Test with a real file on the filesystem."""
        # Use tempfile to create a temporary file
        with tempfile.NamedTemporaryFile(delete=False) as temp_file:
            try:
                # Write some content to the file
                content = b"Testing file size"
                temp_file.write(content)
                temp_file.seek(0)  # Go back to the start of the file for reading

                # Expected size is the length of the content in bytes
                expected_size = len(content)

                # Assert that get_file_size returns the correct size
                self.assertEqual(get_file_size(temp_file), expected_size)
            finally:
                # Clean up by deleting the temporary file
                os.remove(temp_file.name)

    def test_sha1sum(self):
        text = "Hash Test"
        result = sha1sum(text.encode("utf-8"))
        self.assertEqual(result, "b42616bc4884db35e6f24a5803b3c65333fd4bd5")


if __name__ == '__main__':
    unittest.main()
