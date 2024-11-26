from io import BytesIO
import unittest
from zipfile import ZipFile
from unittest.mock import patch, MagicMock
from botocore.exceptions import (
    ClientError,
    BotoCoreError)
from boilerplate.s3 import S3


class TestS3(unittest.TestCase):
    @patch("boilerplate.s3.boto3.client")
    def setUp(self, mock_boto_client):
        self.mock_s3_client = MagicMock()
        mock_boto_client.return_value = self.mock_s3_client
        self._bucket = 'test_bucket'
        self.s3 = S3(bucket_name=self._bucket) # noqa

    def test_s3_client_local_stack(self):
        import os
        os.environ["PROJECT_ENV"] = "local"
        self.s3 = S3(bucket_name=self._bucket)
        self.assertEqual(self.s3._client.meta.endpoint_url,
                         "http://127.0.0.1:4566")

    def test_bucket_name(self):
        self.s3 = S3(bucket_name=self._bucket)
        self.assertEqual(self.s3.bucket_name, self._bucket)

    def test_put_object(self):
        self.mock_s3_client.put_object.return_value = None  # No exception = success
        file_content_map = {".zip": "application/zip",
                            ".xml": "application/xml",
                            ".csv": "text/csv",
                            ".txt": "text/plain"}
        for key, val in file_content_map.items():
            result = self.s3.put_object(f"test_file{key}", b"test string")
            self.assertTrue(result)
        self.assertEqual(self.mock_s3_client.put_object.call_count, len(file_content_map))

    def test_download_fileobj(self): # noqa
        file_obj = BytesIO()
        self.mock_s3_client.download_fileobj.return_value = None
        result = self.s3.download_fileobj("test_file.txt")
        self.mock_s3_client.download_fileobj.assert_called_once()
        self.assertTrue(result)

    def test_get_object(self):
        mock_body = b"This is a test file content"
        self.mock_s3_client.get_object.return_value = {"Body": mock_body}
        content = self.s3.get_object("test_file.txt")
        self.mock_s3_client.get_object.assert_called_once_with(Bucket=self._bucket,
                                                               Key="test_file.txt")
        self.assertEqual(content, b'This is a test file content')

    def test_put_object_exception(self):
        error_response = {
            'Error': {
                'Code': 'NoSuchKey',
                'Message': 'Put object failed'
            }
        }
        self.mock_s3_client.put_object.side_effect = ClientError(error_response,
                                                                 "PutObject")
        with self.assertRaises(ClientError) as context:
            self.s3.put_object(f"test_file.zip", b"test string")
        self.assertIn("Put object failed", str(context.exception))

    def test_get_object_exception(self):
        error_response = {
            'Error': {
                'Code': 'NoSuchKey',
                'Message': 'Get object failed'
            }
        }
        self.mock_s3_client.get_object.side_effect = ClientError(error_response,
                                                                 "GetObject")
        with self.assertRaises(ClientError) as context:
            self.s3.get_object("test_file.txt")
        self.assertIn("Get object failed", str(context.exception))

    def test_download_fileobj_exception(self):
        error_response = {
            'Error': {
                'Code': 'NoSuchKey',
                'Message': 'Get object failed'
            }
        }
        self.mock_s3_client.download_fileobj.side_effect = ClientError(error_response,
                                                                       "GetObject")
        with self.assertRaises(ClientError) as context:
            self.s3.download_fileobj("test_file.txt")
        self.assertIn("Get object failed", str(context.exception))

    def test_unzip(self):
        # Mock the zip file content
        zip_buffer = BytesIO()
        with ZipFile(zip_buffer, 'w') as zf:
            zf.writestr("file1.txt", "content of file1")
            zf.writestr("file2.txt", "content of file2")
        zip_buffer.seek(0)

        # Mock the response for get_object
        self.mock_s3_client.get_object.return_value = {"Body":
                                                BytesIO(zip_buffer.getvalue())}

        # Mock the put_object method
        self.s3.put_object = MagicMock()

        # Call the unzip method
        result_folder = self.s3.unzip("path/to/test.zip", prefix="unzipped")

        # Assert folder name
        self.assertEqual(result_folder, "path/to/unzipped_test")

        # Assert put_object was called for each file
        calls = [
            ((f"path/to/unzipped_test/file1.txt", b"content of file1"),),
            ((f"path/to/unzipped_test/file2.txt", b"content of file2"),)
        ]
        self.s3.put_object.assert_has_calls(calls, any_order=True)

        # Ensure no unexpected calls
        self.assertEqual(self.s3.put_object.call_count, 2)


if __name__ == "__main__":
    unittest.main()