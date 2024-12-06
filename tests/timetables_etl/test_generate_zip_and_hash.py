from pathlib import Path
import unittest
from unittest.mock import MagicMock, patch
from io import BytesIO
from timetables_etl.generate_zip_and_hash import (
    lambda_handler,
    create_zip_archive,
    get_file_path_and_name,
    get_files_in_s3_folder
)

PREFIX = "timetables_etl.generate_zip_and_hash"


class TestLambdaHandler(unittest.TestCase):
    @patch(f"{PREFIX}.S3")
    @patch(f"{PREFIX}.update_file_hash_in_db")
    @patch(f"{PREFIX}.sha1sum")
    def test_lambda_handler_no_zip(self,
                                   mock_sha1sum,
                                   mock_update_file_hash,
                                   mock_s3):
        # Setup mock S3
        mock_s3_handler = MagicMock()
        mock_s3.return_value = mock_s3_handler

        mock_update_file_hash.return_value = True

        # Mock S3 get_list_objects_v2
        mock_s3_handler.get_list_objects_v2.return_value = [
            {"Contents": [{"Key": "folder/file1.xml"},
                          {"Key": "folder/file2.xml"}]}
        ]

        # Mock S3 get_object
        mock_s3_handler.get_object.return_value = BytesIO(b"file content")

        # Mock S3 put_object
        mock_s3_handler.put_object.return_value = None

        # Mock sha1sum
        mock_sha1sum.return_value = "fakehash123"

        # Prepare event
        event = {
            "Bucket": "test-bucket",
            "ObjectKey": "output/zipfile.zip",
            "ValidFiles": ["folder/file1.xml", "folder/file2.xml"],
            "DatasetRevisionId": 123,
        }

        # Call lambda_handler
        response = lambda_handler(event, None)

        # Assertions
        self.assertEqual(response["statusCode"], 200)
        self.assertEqual(response["body"],
                         "No modified files found in folder/")

    @patch(f"{PREFIX}.S3")
    @patch(f"{PREFIX}.update_file_hash_in_db")
    @patch(f"{PREFIX}.sha1sum")
    def test_lambda_handler_zip_creation(self,
                                         mock_sha1sum,
                                         mock_dataset_revision_repo,
                                         mock_s3):
        # Setup mock S3
        mock_s3_handler = MagicMock()
        mock_s3.return_value = mock_s3_handler

        # Mock S3 get_list_objects_v2
        mock_s3_handler.get_list_objects_v2.return_value = [
            {"Contents": [{"Key": "folder/file1.xml"},
                          {"Key": "folder/file2.xml"}]}
        ]

        # Mock S3 get_object
        mock_s3_handler.get_object.return_value = BytesIO(b"file content")

        # Mock S3 put_object
        mock_s3_handler.put_object.return_value = None

        # Mock sha1sum
        mock_sha1sum.return_value = "fakehash123"

        mock_dataset_revision_repo.return_value = True

        # Prepare event
        event = {
            "Bucket": "test-bucket",
            "ObjectKey": "output/zipfile.zip",
            "ValidFiles": ["folder/file1.xml"],
            "DatasetRevisionId": 123,
        }

        # Call lambda_handler
        lambda_handler(event, None)

        # Assert S3 interactions
        mock_s3_handler.get_list_objects_v2.assert_called_once_with("folder/")
        self.assertEqual(mock_s3_handler.get_object.call_count, 3)
        mock_s3_handler.put_object.assert_called_once()


    @patch(f"{PREFIX}.S3")
    def test_create_zip_archive(self, mock_s3):
        # Setup mock S3
        mock_s3_handler = MagicMock()
        mock_s3.return_value = mock_s3_handler
        mock_s3_handler.get_object.return_value = BytesIO(b"file content")

        # Prepare inputs
        s3_handler = mock_s3_handler
        zip_filename = "test.zip"
        files = ["folder/file1.xml", "folder/file2.xml"]

        # Test create_zip_archive
        temp_file_path = create_zip_archive(s3_handler, zip_filename, files)

        # Verify temp file creation
        self.assertTrue(temp_file_path.endswith(".zip"))

    def test_get_file_path_and_name(self):
        full_path_name = "folder/file1.xml"
        file_path, file_name = get_file_path_and_name(full_path_name)

        # Verify results
        self.assertEqual(file_path, Path("folder"))
        self.assertEqual(file_name, "file1.xml")

    @patch(f"{PREFIX}.S3")
    def test_get_files_in_s3_folder(self, mock_s3):
        # Setup mock S3
        mock_s3_handler = MagicMock()
        mock_s3.return_value = mock_s3_handler

        # Mock S3 get_list_objects_v2
        mock_s3_handler.get_list_objects_v2.return_value = [
            {"Contents": [{"Key": "folder/file1.xml"},
                          {"Key": "folder/file2.xml"}]}
        ]

        # Test get_files_in_s3_folder
        files = get_files_in_s3_folder(mock_s3_handler, "folder/")

        # Verify results
        self.assertEqual(files, ["folder/file1.xml", "folder/file2.xml"])


if __name__ == "__main__":
    unittest.main()