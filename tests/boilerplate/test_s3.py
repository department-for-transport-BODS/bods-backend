from io import BytesIO
import unittest
from unittest.mock import patch, MagicMock
from src.boilerplate.s3 import S3


class TestS3(unittest.TestCase):
    @patch("src.boilerplate.s3.boto3.client")
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
                         "http://localstack:4566")

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


if __name__ == "__main__":
    unittest.main()