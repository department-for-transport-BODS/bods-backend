from datetime import datetime
import unittest
import uuid
from unittest.mock import patch, MagicMock
from sqlalchemy.exc import SQLAlchemyError, NoResultFound
from boilerplate.db.file_processing_result import (
    PipelineFileProcessingResult,
    get_file_processing_result_obj,
    write_processing_step,
    get_file_processing_error_code,
    file_processing_result_to_db,
    txc_file_attributes_to_db,
)
from tests.mock_db import MockedDB, pipeline_processing_step as step_


class TestFileProcessingResult(unittest.TestCase):
    def test_create_result(self):
        mock_db = MockedDB()
        result_data = mock_db.classes.pipelines_fileprocessingresult()
        test_obj = PipelineFileProcessingResult(mock_db)
        result = test_obj.create(result_data)
        self.assertTrue(result,
                        "File processing entity created successfully!")

    def test_read_result(self):
        mock_db = MockedDB()
        params = dict(
            task_id=str(uuid.uuid4()),
            status="READY",
            pipeline_processing_step_id=1,
            revision_id=3467,
        )
        result_data = mock_db.classes.pipelines_fileprocessingresult(**params)
        test_obj = PipelineFileProcessingResult(mock_db)
        result = test_obj.create(result_data)
        self.assertTrue(result,
                        "File processing entity created successfully!")
        ret_obj = test_obj.read(revision_id=3467)
        self.assertTrue(
            params,
            dict(
                task_id=ret_obj.task_id,
                status=ret_obj.status,
                pipeline_processing_ste_id=ret_obj.pipeline_processing_step_id,
                revision_id=ret_obj.revision_id,
            ),
        )

    def test_update_result(self):
        mock_db = MockedDB()
        task_id = str(uuid.uuid4())
        params = dict(
            task_id=task_id,
            status="READY",
            pipeline_processing_step_id=1,
            revision_id=3467,
        )
        result_data = mock_db.classes.pipelines_fileprocessingresult(**params)
        test_obj = PipelineFileProcessingResult(mock_db)
        result = test_obj.create(result_data)
        self.assertTrue(result,
                        "File processing entity created successfully!")
        update_params = dict(
            status="UPDATED",
            completed=datetime.now(),
            error_message="DATASET_EXPIRED",
        )
        result = test_obj.update(task_id, **update_params)
        self.assertTrue(result,
                        "File processing result updated successfully!")

        ret_obj = test_obj.read(revision_id=3467)
        self.assertTrue(task_id, ret_obj.task_id)

    def test_create_raises_exception(self):
        mock_db = MockedDB()
        mock_db.session = MagicMock()
        mock_db.session.__enter__.return_value.add.side_effect = (
            SQLAlchemyError("Add failed")
        )
        params = dict(
            task_id=str(uuid.uuid4()),
            status="READY",
            pipeline_processing_step_id=1,
            revision_id=3467,
        )
        result_data = mock_db.classes.pipelines_fileprocessingresult(**params)
        test_obj = PipelineFileProcessingResult(mock_db)
        with self.assertRaises(SQLAlchemyError) as _context:
            test_obj.create(result_data)

        self.assertEqual(str(_context.exception), "Add failed")

        mock_db.session.__enter__.return_value.rollback.assert_called_once()

    def test_read_raises_exception(self):
        mock_db = MockedDB()
        mock_db.session = MagicMock()
        mock_db.session.__enter__.return_value.query.side_effect = (
            NoResultFound("No record found")
        )
        test_obj = PipelineFileProcessingResult(mock_db)
        with self.assertRaises(NoResultFound) as _context:
            test_obj.read(1234)

        self.assertEqual(str(_context.exception), "No record found")
        mock_db.session.__enter__.return_value.query.assert_called_once()

    def test_update_raises_exception(self):
        mock_db = MockedDB()
        mock_db.session = MagicMock()
        mock_db.session.__enter__.return_value.add.side_effect = Exception(
            "Update failed"
        )
        test_obj = PipelineFileProcessingResult(mock_db)
        data = {"a": "Test"}
        with self.assertRaises(Exception) as _context:
            test_obj.update(3467, **data)

        self.assertEqual(str(_context.exception), "Update failed")

        mock_db.session.__enter__.return_value.rollback.assert_called_once()

    def test_get_file_processing_result_obj(self):
        mock_db = MockedDB()
        params = dict(
            task_id="4f52d7f5-cc5c-457a-8227-8e4d02ce8840",
            status="PENDING",
            filename="test.zip",
            pipeline_processing_step_id=1,
            revision_id=3467,
        )
        ret_instance = get_file_processing_result_obj(mock_db, **params)
        self.assertTrue(
            isinstance(
                ret_instance, mock_db.classes.pipelines_fileprocessingresult
            ),
            True,
        )

    def test_write_processing_step(self):
        mock_db = MockedDB()
        with mock_db.session as session:
            session.add(step_(name="Test Scanner",
                              category="FARES"))
            session.commit()

        result_data = write_processing_step(
            mock_db, name="Test Scanner", category="FARES"
        )

        self.assertTrue(result_data, 1)

    def test_get_file_processing_error_code(self):
        error_status = "NO_DATA_FOUND"
        mock_db = MockedDB()
        result_data = mock_db.classes.pipelines_pipelineerrorcode(status=error_status)
        mock_db.session.add(result_data)
        mock_db.session.commit()

        buf_ = get_file_processing_error_code(mock_db, error_status)
        self.assertTrue(buf_.id, 1)

    def test_write_processing_step_exception(self):
        mock_db = MockedDB()
        mock_db.session = MagicMock()
        mock_db.session.__enter__.return_value.query.side_effect = (
            SQLAlchemyError("Query failed")
        )
        with self.assertRaises(SQLAlchemyError) as _context:
            write_processing_step(
                mock_db, name="Test Scanner", category="FARES"
            )

        self.assertEqual(str(_context.exception), "Query failed")
        mock_db.session.__enter__.return_value.query.assert_called_once()

    def test_get_file_processing_error_code_exception(self):
        error_status = "NO_DATA_FOUND"
        mock_db = MockedDB()
        mock_db.session = MagicMock()
        mock_db.session.__enter__.return_value.query.side_effect = (
            NoResultFound("No record found")
        )
        test_obj = PipelineFileProcessingResult(mock_db)
        with self.assertRaises(NoResultFound) as _context:
            get_file_processing_error_code(mock_db, error_status)

        self.assertEqual(str(_context.exception), "No record found")
        mock_db.session.__enter__.return_value.query.assert_called_once()

    @patch("boilerplate.db.file_processing_result.BodsDB")
    @patch(
        "boilerplate.db.file_processing_result.get_file_processing_result_obj"
    )
    @patch("boilerplate.db.file_processing_result.PipelineFileProcessingResult")
    @patch("boilerplate.db.file_processing_result.write_error_to_db")
    def test_file_processing_result_to_db_success(
        self,
        mock_write_error_to_db,
        mock_file_proc_result,
        mock_get_file_processing_result_obj,
        mock_bods_db,
    ):
        # Configure mocks
        mock_db_instance = mock_bods_db.return_value
        mock_result_obj = MagicMock()
        mock_get_file_processing_result_obj.return_value = mock_result_obj
        mock_pipeline_result_instance = mock_file_proc_result.return_value

        # Create a sample event and context
        event = {
            "Bucket": "test-bucket",
            "ObjectKey": "test-key",
            "DatasetRevisionId": 123,
            "DatasetType": "timetables"
        }

        context = {}

        # Define a simple lambda handler to use with the decorator
        @file_processing_result_to_db(step_name="Clam AV Scanner")
        def lambda_handler(event, context):
            return "Handler executed successfully"

        # Execute the lambda handler with the decorator
        result = lambda_handler(event, context)

        # Assert expected result
        self.assertEqual(result, "Handler executed successfully")

        # Assert create and update methods were called on
        # PipelineFileProcessingResult
        mock_pipeline_result_instance.create.assert_called_once_with(
            mock_result_obj
        )
        mock_pipeline_result_instance.update.assert_called_once()

        # Assert write_error_to_db was not called
        mock_write_error_to_db.assert_not_called()

    @patch("boilerplate.db.file_processing_result.BodsDB")
    @patch(
        "boilerplate.db.file_processing_result."
        "get_file_processing_result_obj"
    )
    @patch("boilerplate.db.file_processing_result.PipelineFileProcessingResult")
    @patch("boilerplate.db.file_processing_result.write_error_to_db")
    def test_file_processing_result_to_db_failure(
        self,
        mock_write_error_to_db,
        mock_file_proc_result,
        mock_get_file_processing_result_obj,
        mock_bods_db,
    ):
        # Configure mocks
        mock_db_instance = mock_bods_db.return_value
        mock_result_obj = MagicMock()
        mock_get_file_processing_result_obj.return_value = mock_result_obj
        mock_pipeline_result_instance = mock_file_proc_result.return_value

        # Create a sample event and context
        event = {
            "Bucket": "test-bucket",
            "ObjectKey": "test-key",
            "DatasetRevisionId": 123,
            "DatasetType": "timetables"
        }
        context = {}

        # Define a lambda handler that raises an exception to trigger the error
        # path
        @file_processing_result_to_db(step_name="TIMETABLES")
        def lambda_handler(event, context):
            raise ValueError("An error occurred")

        # Run the lambda handler and assert it raises an exception
        with self.assertRaises(ValueError):
            lambda_handler(event, context)

        # Assert write_error_to_db was called with the correct arguments
        mock_write_error_to_db.assert_called_once()

        # Assert create was called, but update was not (due to the exception)
        mock_pipeline_result_instance.create.assert_called_once_with(
            mock_result_obj
        )
        mock_pipeline_result_instance.update.assert_not_called()

    @patch("boilerplate.db.file_processing_result.BodsDB")
    def test_txc_file_attributes_to_db(self, mock_bods_db):
        mock_db_instance = mock_bods_db.return_value

        # Mock the session context manager
        mock_session = MagicMock()
        mock_db_instance.session.__enter__.return_value = mock_session
        mock_db_instance.session.__exit__.return_value = (
            None  # Ensure context manager exits cleanly
        )

        # Mock the organisation_txcfileattributes class
        mock_class = MagicMock()
        mock_db_instance.classes.organisation_txcfileattributes = mock_class

        # Create a mock TXCFile attribute
        date_time_ = datetime.now()
        mock_attribute = MagicMock()
        mock_attribute.header.schema_version = "1.0"
        mock_attribute.header.modification = "new"
        mock_attribute.header.revision_number = "2"
        mock_attribute.header.creation_datetime = date_time_
        mock_attribute.header.modification_datetime = date_time_
        mock_attribute.header.filename = "file.xml"
        mock_attribute.operator.national_operator_code = "ABC123"
        mock_attribute.operator.licence_number = "LIC123"
        mock_attribute.service.service_code = "SERV123"
        mock_attribute.service.origin = "Origin"
        mock_attribute.service.destination = "Destination"
        mock_attribute.service.operating_period_start_date = date_time_.date()
        mock_attribute.service.operating_period_end_date = date_time_.date()
        mock_attribute.service.public_use = True
        mock_attribute.service.lines = [
            MagicMock(line_name="Line1"),
            MagicMock(line_name="Line2"),
        ]
        mock_attribute.hash = "hash123"

        # Call the function with mock data
        txc_file_attributes_to_db(revision_id=1, attributes=[mock_attribute])

        # Check that the db class constructor was called correctly
        mock_class.assert_called_with(
            revision_id=1,
            schema_version="1.0",
            modification="new",
            revision_number="2",
            creation_datetime=date_time_,
            modification_datetime=date_time_,
            filename="file.xml",
            national_operator_code="ABC123",
            licence_number="LIC123",
            service_code="SERV123",
            origin="Origin",
            destination="Destination",
            operating_period_start_date=date_time_.date(),
            operating_period_end_date=date_time_.date(),
            public_use=True,
            line_names=["Line1", "Line2"],
            hash="hash123",
        )

        # Check that bulk_save_objects and commit were called
        mock_session.bulk_save_objects.assert_called_once()
        mock_session.commit.assert_called_once()

    @patch("boilerplate.db.file_processing_result.BodsDB")
    def test_txc_file_attributes_to_db_exception(self, mock_bods_db):
        mock_db_instance = mock_bods_db.return_value

        # Mock the session context manager
        mock_session = MagicMock()
        mock_db_instance.session.__enter__.return_value.bulk_save_objects.\
            side_effect = Exception("An error occurred")

        # Mock the organisation_txcfileattributes class
        mock_class = MagicMock()
        mock_db_instance.classes.organisation_txcfileattributes = mock_class

        # Create a mock TXCFile attribute
        date_time_ = datetime.now()
        mock_attribute = MagicMock()
        mock_attribute.header.schema_version = "1.0"
        mock_attribute.header.modification = "new"
        mock_attribute.header.revision_number = "2"
        mock_attribute.header.creation_datetime = date_time_
        mock_attribute.header.modification_datetime = date_time_
        mock_attribute.header.filename = "file.xml"
        mock_attribute.operator.national_operator_code = "ABC123"
        mock_attribute.operator.licence_number = "LIC123"
        mock_attribute.service.service_code = "SERV123"
        mock_attribute.service.origin = "Origin"
        mock_attribute.service.destination = "Destination"
        mock_attribute.service.operating_period_start_date = date_time_.date()
        mock_attribute.service.operating_period_end_date = date_time_.date()
        mock_attribute.service.public_use = True
        mock_attribute.service.lines = [
            MagicMock(line_name="Line1"),
            MagicMock(line_name="Line2"),
        ]
        mock_attribute.hash = "hash123"

        # Call the function with mock data
        # txc_file_attributes_to_db(revision_id=1, attributes=[mock_attribute])

        # Check that bulk_save_objects and commit were called
        # mock_session.bulk_save_objects.assert_called_once()
        # mock_session.commit.assert_called_once()
        with self.assertRaises(Exception) as _context:
            txc_file_attributes_to_db(
                revision_id=1, attributes=[mock_attribute]
            )

        self.assertEqual(str(_context.exception), "An error occurred")
        mock_db_instance.session.__enter__.return_value.\
            bulk_save_objects.assert_called_once()


if __name__ == "__main__":
    unittest.main()
