from datetime import datetime
import unittest
import uuid
from unittest.mock import patch, MagicMock
from sqlalchemy.exc import SQLAlchemyError, NoResultFound
from boilerplate.db.file_processing_result import (
    PipelineFileProcessingResult,
    get_file_processing_result_obj,
    get_file_processing_step,
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

        buf_ = mock_db.classes.pipeline_processing_step
        result = mock_db.session.query(buf_).filter(buf_.name == "FARES").one()
        self.assertTrue(result.id, 1)

    def test_get_file_processing_error_code(self):
        error_status = "NO_DATA_FOUND"
        mock_db = MockedDB()
        result_data = mock_db.classes.pipeline_error_code(status=error_status)
        mock_db.session.add(result_data)
        mock_db.session.commit()

        buf_ = mock_db.classes.pipeline_error_code
        result = mock_db.session.query(buf_).filter(buf_.status == error_status).one()
        self.assertTrue(result.id, 1)


if __name__ == "__main__":
    unittest.main()
