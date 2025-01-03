import unittest
import uuid
from datetime import datetime
from unittest.mock import MagicMock

from common_layer.db.constants import StepName
from common_layer.db.file_processing_result import (
    file_processing_result_to_db,
    get_file_processing_error_code,
)
from sqlalchemy.exc import NoResultFound, SQLAlchemyError

from tests.mock_db import MockedDB

PipelineFileProcessingResult = MagicMock()


class TestFileProcessingResult(unittest.TestCase):
    def test_create_result(self):
        mock_db = MockedDB()
        result_data = {
            "status": "STARTED",
            "filename": "sample.txt",
            "pipeline_processing_step_id": 1,
            "revision_id": 1,
            "created": datetime.now(),
            "modified": datetime.now(),
        }
        result = PipelineFileProcessingResult(mock_db).create(result_data)
        self.assertTrue(result, "File processing entity created successfully!")

    def test_read_result(self):
        mock_db = MockedDB()
        params = dict(
            status="READY",
            pipeline_processing_step_id=1,
            revision_id=3467,
        )
        result = PipelineFileProcessingResult(mock_db).create(params)
        self.assertTrue(result, "File processing entity created successfully!")
        ret_obj = PipelineFileProcessingResult(mock_db).read(revision_id=3467)
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
        result = PipelineFileProcessingResult(mock_db).create(params)
        self.assertTrue(result, "File processing entity created successfully!")
        update_params = dict(
            status="UPDATED",
            completed=datetime.now(),
            error_message="DATASET_EXPIRED",
        )
        result = PipelineFileProcessingResult(mock_db).update(task_id, **update_params)
        self.assertTrue(result, "File processing result updated successfully!")

        ret_obj = PipelineFileProcessingResult(mock_db).read(revision_id=3467)
        self.assertTrue(task_id, ret_obj.task_id)

    def test_create_raises_exception(self):
        mock_db = MockedDB()
        mock_db.session = MagicMock()
        mock_db.session.__enter__.return_value.add.side_effect = SQLAlchemyError(
            "Add failed"
        )
        params = dict(
            task_id=str(uuid.uuid4()),
            status="READY",
            pipeline_processing_step_id=1,
            revision_id=3467,
        )
        with self.assertRaises(SQLAlchemyError) as _context:
            PipelineFileProcessingResult(mock_db).create(params)

        self.assertEqual(str(_context.exception), "Add failed")

        mock_db.session.__enter__.return_value.rollback.assert_called_once()

    def test_read_raises_exception(self):
        mock_db = MockedDB()
        mock_db.session = MagicMock()
        mock_db.session.__enter__.return_value.query.side_effect = NoResultFound(
            "No record found"
        )
        with self.assertRaises(NoResultFound) as _context:
            PipelineFileProcessingResult(mock_db).read(1234)

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

    def test_get_file_processing_error_code(self):
        error_status = "NO_DATA_FOUND"
        mock_db = MockedDB()
        result_data = mock_db.classes.pipelines_pipelineerrorcode(error=error_status)
        mock_db.session.add(result_data)
        mock_db.session.commit()

        buf_ = get_file_processing_error_code(mock_db, error_status)
        self.assertTrue(buf_.id, 1)

    def test_get_file_processing_error_code_exception(self):
        error_status = "NO_DATA_FOUND"
        mock_db = MockedDB()
        mock_db.session = MagicMock()
        mock_db.session.__enter__.return_value.query.side_effect = NoResultFound(
            "No record found"
        )
        test_obj = PipelineFileProcessingResult(mock_db)
        with self.assertRaises(NoResultFound) as _context:
            get_file_processing_error_code(mock_db, error_status)

        self.assertEqual(str(_context.exception), "No record found")
        mock_db.session.__enter__.return_value.query.assert_called_once()

    def test_file_processing_result_to_db_success(
        self,
        mock_write_error_to_db,
        mock_file_proc_result,
        mock_db_manager,
    ):
        # Configure mocks
        mock_result_obj = MagicMock()
        mock_pipeline_result_instance = mock_file_proc_result.return_value

        # Create a sample event and context
        event = {
            "Bucket": "test-bucket",
            "ObjectKey": "test-key",
            "DatasetRevisionId": 123,
            "DatasetType": "timetables",
        }

        context = {}

        # Define a simple lambda handler to use with the decorator
        @file_processing_result_to_db(step_name=StepName.CLAM_AV_SCANNER)
        def lambda_handler(event, context):
            return "Handler executed successfully"

        # Execute the lambda handler with the decorator
        result = lambda_handler(event, context)

        # Assert expected result
        self.assertEqual(result, "Handler executed successfully")

        # Assert create and update methods were called on
        mock_pipeline_result_instance.update.assert_called_once()

        # Assert write_error_to_db was not called
        mock_write_error_to_db.assert_not_called()

    def test_file_processing_result_to_db_failure(
        self,
        mock_write_error_to_db,
        mock_file_proc_result,
        mock_db_manager,
    ):
        # Configure mocks
        mock_db_instance = mock_db_manager.get_db.return_value
        mock_result_obj = MagicMock()
        mock_pipeline_result_instance = mock_file_proc_result.return_value

        # Create a sample event and context
        event = {
            "Bucket": "test-bucket",
            "ObjectKey": "test-key",
            "DatasetRevisionId": 123,
            "DatasetType": "timetables",
        }
        context = {}

        # Define a lambda handler that raises an exception to trigger the error
        # path
        @file_processing_result_to_db(step_name=StepName.TIMETABLE_SCHEMA_CHECK)
        def lambda_handler(event, context):
            raise ValueError("An error occurred")

        # Run the lambda handler and assert it raises an exception
        with self.assertRaises(ValueError):
            lambda_handler(event, context)

        # Assert write_error_to_db was called with the correct arguments
        mock_write_error_to_db.assert_called_once()

        # Assert create was called, but update was not (due to the exception)
        mock_pipeline_result_instance.update.assert_not_called()


if __name__ == "__main__":
    unittest.main()
