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
    file_processing_result_to_db
)
from tests.mock_db import MockedDB


class TestFileProcessingResult(unittest.TestCase):
    def test_create_result(self):
        mock_db = MockedDB()
        result_data = mock_db.classes.pipelines_fileprocessingresult()
        test_obj = PipelineFileProcessingResult(mock_db)
        result = test_obj.create(result_data)
        self.assertTrue(result, "File processing entity created successfully!")

    def test_read_result(self):
        mock_db = MockedDB()
        params = dict(task_id=str(uuid.uuid4()),
                      status="READY",
                      pipeline_processing_step_id=1,
                      revision_id=3467)
        result_data = mock_db.classes.pipelines_fileprocessingresult(**params)
        test_obj = PipelineFileProcessingResult(mock_db)
        result = test_obj.create(result_data)
        self.assertTrue(result, "File processing entity created successfully!")
        ret_obj = test_obj.read(revision_id=3467)
        self.assertTrue(params, dict(task_id=ret_obj.task_id,
                                     status=ret_obj.status,
                                     pipeline_processing_ste_id=ret_obj.pipeline_processing_step_id,
                                     revision_id=ret_obj.revision_id))

    def test_update_result(self):
        mock_db = MockedDB()
        task_id = str(uuid.uuid4())
        params = dict(task_id=task_id,
                      status="READY",
                      pipeline_processing_step_id=1,
                      revision_id=3467)
        result_data = mock_db.classes.pipelines_fileprocessingresult(**params)
        test_obj = PipelineFileProcessingResult(mock_db)
        result = test_obj.create(result_data)
        self.assertTrue(result, "File processing entity created successfully!")
        update_params = dict(status="UPDATED",
                             completed=datetime.now(),
                             error_message="DATASET_EXPIRED")
        result = test_obj.update(task_id, **update_params)
        self.assertTrue(result, "File processing result updated successfully!")

        ret_obj = test_obj.read(revision_id=3467)
        self.assertTrue(task_id, ret_obj.task_id)

    def test_create_raises_exception(self):
        mock_db = MockedDB()
        mock_db.session = MagicMock()
        mock_db.session.__enter__.return_value.add.side_effect = SQLAlchemyError("Add failed")
        params = dict(task_id=str(uuid.uuid4()),
                      status="READY",
                      pipeline_processing_step_id=1,
                      revision_id=3467)
        result_data = mock_db.classes.pipelines_fileprocessingresult(**params)
        test_obj = PipelineFileProcessingResult(mock_db)
        with self.assertRaises(SQLAlchemyError) as _context:
            test_obj.create(result_data)

        self.assertEqual(str(_context.exception), "Add failed")

        mock_db.session.__enter__.return_value.rollback.assert_called_once()

    def test_read_raises_exception(self):
        mock_db = MockedDB()
        mock_db.session = MagicMock()
        mock_db.session.__enter__.return_value.query.side_effect = \
            NoResultFound("No record found")
        test_obj = PipelineFileProcessingResult(mock_db)
        with self.assertRaises(NoResultFound) as _context:
            test_obj.read(1234)

        self.assertEqual(str(_context.exception), "No record found")
        mock_db.session.__enter__.return_value.query.assert_called_once()

    def test_update_raises_exception(self):
        mock_db = MockedDB()
        mock_db.session = MagicMock()
        mock_db.session.__enter__.return_value.add.side_effect = Exception("Update failed")
        test_obj = PipelineFileProcessingResult(mock_db)
        data = {'a': "Test"}
        with self.assertRaises(Exception) as _context:
            test_obj.update(3467, **data)

        self.assertEqual(str(_context.exception), "Update failed")

        mock_db.session.__enter__.return_value.rollback.assert_called_once()

    def test_get_file_processing_result_obj(self):
        mock_db = MockedDB()
        params = dict(task_id="4f52d7f5-cc5c-457a-8227-8e4d02ce8840",
                      status="PENDING",
                      filename="test.zip",
                      pipeline_processing_step_id=1,
                      revision_id=3467)
        ret_instance = get_file_processing_result_obj(mock_db, **params)
        self.assertTrue(isinstance(ret_instance,
                                   mock_db.classes.pipelines_fileprocessingresult),
                        True)

    def test_write_processing_step(self):
        mock_db = MockedDB()
        result_data = write_processing_step(mock_db,
                                            name="Test Scanner",
                                            category="FARES")

        self.assertTrue(result_data, 1)

    def test_get_file_processing_error_code(self):
        error_status = "NO_DATA_FOUND"
        mock_db = MockedDB()
        result_data = mock_db.classes.pipeline_error_code(status=error_status)
        mock_db.session.add(result_data)
        mock_db.session.commit()

        buf_ = get_file_processing_error_code(mock_db, error_status)
        self.assertTrue(buf_.id, 1)

    def test_write_processing_step_exception(self):
        mock_db = MockedDB()
        mock_db.session = MagicMock()
        mock_db.session.__enter__.return_value.add.side_effect = \
            SQLAlchemyError("Add failed")
        with self.assertRaises(SQLAlchemyError) as _context:
            write_processing_step(mock_db,
                                  name="Test Scanner",
                                  category="FARES")

        self.assertEqual(str(_context.exception), "Add failed")
        mock_db.session.__enter__.return_value.add.assert_called_once()

    def test_get_file_processing_error_code_exception(self):
        error_status = "NO_DATA_FOUND"
        mock_db = MockedDB()
        mock_db.session = MagicMock()
        mock_db.session.__enter__.return_value.query.side_effect = \
            NoResultFound("No record found")
        test_obj = PipelineFileProcessingResult(mock_db)
        with self.assertRaises(NoResultFound) as _context:
            get_file_processing_error_code(mock_db, error_status)

        self.assertEqual(str(_context.exception), "No record found")
        mock_db.session.__enter__.return_value.query.assert_called_once()

    @patch("boilerplate.db.file_processing_result.BodsDB")
    @patch("boilerplate.db.file_processing_result.get_file_processing_result_obj")
    @patch("boilerplate.db.file_processing_result.PipelineFileProcessingResult")
    @patch("boilerplate.db.file_processing_result.write_error_to_db")
    def test_file_processing_result_to_db_success(
            self, mock_write_error_to_db, mock_file_proc_result,
            mock_get_file_processing_result_obj, mock_bods_db
    ):
        # Configure mocks
        mock_db_instance = mock_bods_db.return_value
        mock_result_obj = MagicMock()
        mock_get_file_processing_result_obj.return_value = mock_result_obj
        mock_pipeline_result_instance = mock_file_proc_result.return_value

        # Create a sample event and context
        event = {"Records": [{"s3": {"object": {"key": "3456/test_file.zip"}}}]}
        context = {}

        # Define a simple lambda handler to use with the decorator
        @file_processing_result_to_db(step_name="Clam AV Scanner")
        def lambda_handler(event, context):
            return "Handler executed successfully"

        # Execute the lambda handler with the decorator
        result = lambda_handler(event, context)

        # Assert expected result
        self.assertEqual(result, "Handler executed successfully")

        # Assert create and update methods were called on PipelineFileProcessingResult
        mock_pipeline_result_instance.create.assert_called_once_with(mock_result_obj)
        mock_pipeline_result_instance.update.assert_called_once()

        # Assert write_error_to_db was not called
        mock_write_error_to_db.assert_not_called()

    @patch("boilerplate.db.file_processing_result.BodsDB")
    @patch("boilerplate.db.file_processing_result.get_file_processing_result_obj")
    @patch("boilerplate.db.file_processing_result.PipelineFileProcessingResult")
    @patch("boilerplate.db.file_processing_result.write_error_to_db")
    def test_file_processing_result_to_db_failure(
            self, mock_write_error_to_db, mock_file_proc_result,
            mock_get_file_processing_result_obj, mock_bods_db
    ):
        # Configure mocks
        mock_db_instance = mock_bods_db.return_value
        mock_result_obj = MagicMock()
        mock_get_file_processing_result_obj.return_value = mock_result_obj
        mock_pipeline_result_instance = mock_file_proc_result.return_value

        # Create a sample event and context
        event = {"Records": [{"s3": {"object": {"key": "revision/test_file.zip"}}}]}
        context = {}

        # Define a lambda handler that raises an exception to trigger the error path
        @file_processing_result_to_db(step_name="TIMETABLES")
        def lambda_handler(event, context):
            raise ValueError("An error occurred")

        # Run the lambda handler and assert it raises an exception
        with self.assertRaises(ValueError):
            lambda_handler(event, context)

        # Assert write_error_to_db was called with the correct arguments
        mock_write_error_to_db.assert_called_once()

        # Assert create was called, but update was not (due to the exception)
        mock_pipeline_result_instance.create.assert_called_once_with(mock_result_obj)
        mock_pipeline_result_instance.update.assert_not_called()


if __name__ == "__main__":
    unittest.main()
