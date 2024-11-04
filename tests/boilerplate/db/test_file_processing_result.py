from datetime import datetime
import unittest
import uuid
from unittest.mock import patch, MagicMock
from sqlalchemy.exc import SQLAlchemyError, NoResultFound
from boilerplate.db.file_processing_result import (
    PipelineFileProcessingResult,
    get_file_processing_result_obj,
    get_file_processing_step,
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
                      pipeline_processing_step="TIMETABLES",
                      revision=3467)
        result_data = mock_db.classes.pipelines_fileprocessingresult(**params)
        test_obj = PipelineFileProcessingResult(mock_db)
        result = test_obj.create(result_data)
        self.assertTrue(result, "File processing entity created successfully!")
        ret_obj = test_obj.read(revision_id=3467)
        self.assertTrue(params, dict(task_id=ret_obj.task_id,
                                     status=ret_obj.status,
                                     pipeline_processing_step=ret_obj.pipeline_processing_step,
                                     revision=ret_obj.revision))

    def test_update_result(self):
        mock_db = MockedDB()
        task_id = str(uuid.uuid4())
        params = dict(task_id=task_id,
                      status="READY",
                      pipeline_processing_step="TIMETABLES",
                      revision=3467)
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
                      pipeline_processing_step="TIMETABLES",
                      revision=3467)
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
                      pipeline_processing_step="PENDING",
                      revision=3467)
        ret_instance = get_file_processing_result_obj(mock_db, **params)
        self.assertTrue(isinstance(ret_instance,
                                   mock_db.classes.pipelines_fileprocessingresult),
                        True)

    def test_get_file_processing_step(self):
        mock_db = MockedDB()
        result_data = mock_db.classes.pipeline_processing_step(name="FARES")
        mock_db.session.add(result_data)
        mock_db.session.commit()

        buf_ = get_file_processing_step(mock_db, name="FARES")
        self.assertTrue(buf_.id, 1)

    def test_get_file_processing_error_code(self):
        error_status = "NO_DATA_FOUND"
        mock_db = MockedDB()
        result_data = mock_db.classes.pipeline_error_code(status=error_status)
        mock_db.session.add(result_data)
        mock_db.session.commit()

        buf_ = get_file_processing_error_code(mock_db, error_status)
        self.assertTrue(buf_.id, 1)

    def test_get_file_processing_step_exception(self):
        mock_db = MockedDB()
        mock_db.session = MagicMock()
        mock_db.session.__enter__.return_value.query.side_effect = \
            NoResultFound("No record found")
        test_obj = PipelineFileProcessingResult(mock_db)
        with self.assertRaises(NoResultFound) as _context:
            get_file_processing_step(mock_db, name="FARES")

        self.assertEqual(str(_context.exception), "No record found")
        mock_db.session.__enter__.return_value.query.assert_called_once()

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

    @patch('boilerplate.db.file_processing_result.BodsDB')
    def test_file_processing_result_to_db(self, mock_db):
        def test_lambda(event, context):
            return True

        event = {
            "Records": [
                {
                    "s3": {
                        "bucket": {
                            "name": "bodds-dev",
                        },
                        "object": {"key": "3657/16012023095023.zip"},
                    },
                }
            ]
        }

        step = MagicMock()
        step.id = 1
        error_code = MagicMock()
        error_code.id = 1
        step_patch = patch('boilerplate.db.file_processing_result.get_file_processing_step')
        step_patch.return_value = step
        error_code_patch = patch('boilerplate.db.file_processing_result.get_file_processing_error_code')
        error_code_patch.return_value = error_code

        get_file_processing_step.return_value = MagicMock()
        get_file_processing_step.return_value.id = 1
        decrator_obj = file_processing_result_to_db(test_lambda)
        result = decrator_obj(event, None)
        self.assertTrue(result)

    @patch('boilerplate.db.file_processing_result.BodsDB')
    @patch('boilerplate.db.file_processing_result.get_file_processing_step')
    def test_file_processing_result_to_db_exception(self, mock_step, mock_db):
        def test_lambda(event, context):
            return True

        event = {
            "Records": [
                {
                    "s3": {
                        "bucket": {
                            "name": "bodds-dev",
                        },
                        "object": {"key": "3675/16012023095023.zip"},
                    },
                }
            ]
        }
        mock_step.side_effect = Exception("Test exception")
        mock_step.side_effect.status = "500"
        mock_step.side_effect.error_status = "edf"
        decrator_obj = file_processing_result_to_db(test_lambda)
        result = decrator_obj(event, None)
        self.assertTrue(str(result), 'Test exception')


if __name__ == "__main__":
    unittest.main()
