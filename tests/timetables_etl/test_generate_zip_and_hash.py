import unittest
from unittest.mock import MagicMock, patch
from io import BytesIO
from timetables_etl.generate_zip_and_hash import lambda_handler

PREFIX = "timetables_etl.generate_zip_and_hash"


class TestLambdaHandler(unittest.TestCase):
    @patch(f"{PREFIX}.S3")
    @patch(f"{PREFIX}.DatasetRevisionRepository")
    @patch(f"{PREFIX}.DbManager")
    @patch(f"{PREFIX}.sha1sum")
    def test_lambda_handler_no_zip(self,
                                   mock_sha1sum,
                                   mock_db_manager,
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

        # Mock database
        mock_db_instance = MagicMock()
        mock_db_manager.get_db.return_value = mock_db_instance
        mock_dataset_revision_repo_instance = MagicMock()
        mock_dataset_revision_repo.return_value = (
            mock_dataset_revision_repo_instance)
        mock_revision = MagicMock()
        mock_dataset_revision_repo_instance.get_by_id.return_value = (
            mock_revision)

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
    @patch(f"{PREFIX}.DatasetRevisionRepository")
    @patch(f"{PREFIX}.DbManager")
    @patch(f"{PREFIX}.sha1sum")
    def test_lambda_handler_zip_creation(self,
                                         mock_sha1sum,
                                         mock_db_manager,
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

        # Mock database
        mock_db_instance = MagicMock()
        mock_db_manager.get_db.return_value = mock_db_instance
        mock_dataset_revision_repo_instance = MagicMock()
        mock_dataset_revision_repo.return_value = (
            mock_dataset_revision_repo_instance)
        mock_revision = MagicMock()
        mock_dataset_revision_repo_instance.get_by_id.return_value = (
            mock_revision)

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
        self.assertEqual(mock_s3_handler.get_object.call_count, 2)
        mock_s3_handler.put_object.assert_called_once()

        # Assert database interactions
        mock_dataset_revision_repo_instance.get_by_id.assert_called_once_with(
            123)
        self.assertEqual(mock_revision.modified_file_hash, "fakehash123")
        mock_dataset_revision_repo_instance.update.assert_called_once_with(
            mock_revision)


if __name__ == "__main__":
    unittest.main()