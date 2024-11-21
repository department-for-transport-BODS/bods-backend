from pathlib import Path
import unittest
from unittest.mock import Mock, patch, MagicMock
from io import BytesIO

import boilerplate.timetables.transxchange
from boilerplate.timetables.transxchange import (
    TransXChangeDocument,
    TransXChangeZip,
    TransXChangeDatasetParser,
    BaseSchemaViolation,
    TXCPostSchemaViolation
)


class TestTransXChangeDocument(unittest.TestCase):
    def setUp(self):
        # Mock XML content for testing purposes
        xml_path = Path(__file__).parent.parent.parent.resolve() / "data" / "sample.xml"
        xml_content = open(xml_path, "rb").read()
        self.document = TransXChangeDocument(BytesIO(xml_content))

    def test_get_transxchange_version(self):
        self.assertEqual(self.document.get_transxchange_version(), "2.4")

    def test_get_creation_date_time(self):
        self.assertEqual(self.document.get_creation_date_time(), "2024-06-18T13:05:55")

    def test_get_modification_date_time(self):
        self.assertEqual(self.document.get_modification_date_time(), "2024-06-18T13:15:55")

    def test_get_revision_number(self):
        self.assertEqual(self.document.get_revision_number(), "1")

    def test_stop_points(self):
        stops = self.document.get_stop_points()
        self.assertEqual(len(stops), 11)

    def test_get_location_system(self):
        stops = self.document.get_stop_points()
        result = self.document.get_location_system(stops[0])
        self.assertEqual(result, "Grid")

    def test_get_services(self):
        services = self.document.get_services()
        self.assertEqual(len(services), 1)
        self.assertEqual(services[0]["RevisionNumber"], "0")

    def test_get_all_line_names(self):
        line_names = self.document.get_all_line_names()
        self.assertEqual(line_names, ["UKN603"])

    def test_get_file_name(self):
        file_name = self.document.get_file_name()
        self.assertEqual(file_name, "sample.xml")

    def test_get_modification(self):
        modification = self.document.get_modification()
        self.assertEqual(modification, "revise")

    def test_get_service_codes(self):
        service_codes = self.document.get_service_codes()
        self.assertEqual(service_codes[0].text, "UZ000FLIX:UKN603")

    def test_get_lines(self):
        lines = self.document.get_lines()
        self.assertEqual(len(lines), 1)

    def test_get_annotated_stop_point_refs(self):
        annotated_stop_point_refs = self.document.get_annotated_stop_point_refs()
        self.assertEqual(len(annotated_stop_point_refs), 3)

    def test_get_flexible_service(self):
        flexible_service = self.document.get_flexible_service()
        self.assertEqual(len(flexible_service), 0)

    def test_has_latitude(self):
        stops = self.document.get_stop_points()
        self.assertTrue(any((self.document.has_latitude(stop)
                             for stop in stops)))

    def test_get_journey_pattern_sections(self):
        journey_pattern_sections = self.document.get_journey_pattern_sections()
        self.assertEqual(len(journey_pattern_sections), 14)

    def test_get_all_vehicle_journeys(self):
        journeys = self.document.get_all_vehicle_journeys("VehicleJourney")
        self.assertEqual(len(journeys), 54)

    def test_get_all_vehicle_journeys_allow_none_true(self):
        journeys = self.document.get_all_vehicle_journeys("VehicleJourney",
                                                          allow_none=True)
        self.assertEqual(len(journeys), 54)

    def test_get_all_operating_profiles_vehicle_journeys(self):
        operating_profiles = self.document.get_all_operating_profiles("VehicleJourneys")
        self.assertEqual(len(operating_profiles), 54)

    def test_get_all_operating_profiles_services(self):
        operating_profiles = self.document.get_all_operating_profiles("Services")
        self.assertEqual(len(operating_profiles), 1)

    def test_get_all_operating_profiles_vehicle_journeys_allow_none_true(self):
        operating_profiles = self.document.get_all_operating_profiles("VehicleJourneys",
                                                                      allow_none=True)
        self.assertEqual(len(operating_profiles), 54)

    def test_get_all_serviced_organisations(self):
        serviced_organisations = self.document.get_all_serviced_organisations()
        self.assertEqual(len(serviced_organisations), 1)

    def test_get_operators(self):
        operators = self.document.get_operators()
        self.assertEqual(len(operators), 1)

    def test_get_licensed_operators(self):
        licensed_operators = self.document.get_licensed_operators()
        self.assertEqual(len(licensed_operators), 0)

    def test_get_nocs(self):
        nocs = self.document.get_nocs()
        self.assertEqual(nocs, ["FLIX"])

    def test_get_principal_timing_points(self):
        principal_timing_points = self.document.get_principal_timing_points()
        self.assertEqual(len(principal_timing_points), 171)

    def test_get_operating_period_start_date(self):
        start_date = self.document.get_operating_period_start_date()
        self.assertEqual(start_date[0].text, "2024-06-10")

    def test_get_operating_period_end_date(self):
        end_date = self.document.get_operating_period_end_date()
        self.assertEqual(end_date[0].text, "2024-07-10")

    def test_get_public_use(self):
        public_use = self.document.get_public_use()
        self.assertEqual(public_use[0].text, "true")

    def test_get_service_origin(self):
        service_origin = self.document.get_service_origin()
        self.assertEqual(service_origin, "Manchester")

    def test_get_service_destination(self):
        service_destination = self.document.get_service_destination()
        self.assertEqual(service_destination, "Paris")

    def test_get_vehicle_journeys(self):
        vehicle_journeys = self.document.get_vehicle_journeys()
        self.assertEqual(len(vehicle_journeys), 54)

    def test_get_serviced_organisations(self):
        serviced_organisations = self.document.get_serviced_organisations()
        self.assertEqual(len(serviced_organisations), 1)


class TestTransXChangeZip(unittest.TestCase):
    @patch("boilerplate.timetables.transxchange.TransXChangeDocument")
    @patch("boilerplate.timetables.transxchange.ZippedValidator.get_files")
    @patch.object(boilerplate.timetables.transxchange.ZippedValidator,
                  "__init__", return_value=None)
    @patch.object(TransXChangeZip, "get_doc_from_name", return_value="sample")
    def test_get_transxchange_docs(self, mock_txc, mock_super_init, mock_get_files, mock_txc_doc):
        # Set up mocks
        mock_get_files.return_value = ["file1.xml", "file2.xml"]  # Mocked list of filenames
        mock_doc = mock_txc_doc.return_value
        mock_super_init.return_value = MagicMock()
        with patch("boilerplate.timetables.transxchange.open",
                   MagicMock()) as mock_open:
            mock_open.return_value = BytesIO(b"sample zip file")
            zip_instance = TransXChangeZip(source="dummy.zip")

            # Call the get_transxchange_docs method
            docs = zip_instance.get_transxchange_docs(validate=False)

            # Assertions
            self.assertEqual(len(docs), 2)
            mock_get_files.assert_called_once()
            self.assertEqual(mock_txc.call_count, 2)

    @patch("boilerplate.timetables.transxchange.TransXChangeZip.get_files",
           return_value=["doc1.xml", "doc2.xml"])
    @patch("boilerplate.timetables.transxchange.TransXChangeZip.get_doc_from_name")
    @patch.object(boilerplate.timetables.transxchange.ZippedValidator,
                  "__init__", return_value=None)
    def test_iter_doc(self, mock_super_init, mock_get_doc_from_name, mock_get_files):
        # Mocked TransXChangeDocument instances for each file
        mock_doc1 = MagicMock(name="TransXChangeDocument1")
        mock_doc2 = MagicMock(name="TransXChangeDocument2")
        mock_get_doc_from_name.side_effect = [mock_doc1, mock_doc2]

        # Initialize TransXChangeZip with mocked file
        with patch("boilerplate.timetables.transxchange.open",
                   MagicMock()) as mock_open:
            mock_open.return_value = BytesIO(b"sample zip file")
            txc_zip = TransXChangeZip("dummy.zip")

            # Convert iterator to list for testing
            docs = list(txc_zip.iter_doc())

            # Assertions
            self.assertEqual(len(docs), 2)
            self.assertIn(mock_doc1, docs)
            self.assertIn(mock_doc2, docs)
            mock_get_files.assert_called_once()

    @patch.object(boilerplate.timetables.transxchange.ZippedValidator,
                  "__init__", return_value=None)
    @patch.object(boilerplate.timetables.transxchange.ZippedValidator,
                  "open", return_value=None)
    def test_get_doc_from_name(self, mock_open_zip, mock_super_init):
        mock_open_zip.return_value = BytesIO(b"sample zip file")
        with patch("boilerplate.timetables.transxchange.open",
                   MagicMock()) as mock_open:
            mock_open.return_value = BytesIO(b"sample zip file")
            with patch("boilerplate.timetables.transxchange.TransXChangeDocument", MagicMock()) as mock_txc_doc:
                mock_doc = mock_txc_doc.return_value
                txc_zip = TransXChangeZip("dummy.zip")

                # Test get_doc_from_name
                doc = txc_zip.get_doc_from_name("doc1.xml")

                # Assertions
                mock_open_zip.assert_called_once_with("doc1.xml")
                self.assertEqual(mock_txc_doc.call_count, 1)
                self.assertEqual(doc, mock_doc)

    @patch("boilerplate.timetables.transxchange.TransXChangeZip.get_files",
           return_value=["doc1.xml", "doc2.xml"])
    @patch("boilerplate.timetables.transxchange.TransXChangeZip.get_doc_from_name")
    @patch("boilerplate.timetables.transxchange.logger.info")
    @patch.object(boilerplate.timetables.transxchange.ZippedValidator,
                  "__init__", return_value=None)
    def test_validate_contents(self, mock_super_init,
                               mock_logger_info,
                               mock_get_doc_from_name,
                               mock_get_files):
        with patch("boilerplate.timetables.transxchange.open",
                   MagicMock()) as mock_open:
            mock_open.return_value = BytesIO(b"sample zip file")
            txc_zip = TransXChangeZip("dummy.zip")

            # Run validate_contents method
            txc_zip.validate_contents()

            # Assertions
            mock_get_files.assert_called_once()
            self.assertEqual(mock_get_doc_from_name.call_count, 2)
            mock_logger_info.assert_any_call("[TransXChange] Validating 2 files.")
            mock_logger_info.assert_any_call("[TransXChange] => Validating doc1.xml file 1 of 2.")

    @patch("boilerplate.timetables.transxchange.TransXChangeZip.validate_contents")
    @patch("boilerplate.timetables.transxchange.ZippedValidator.validate")
    @patch.object(boilerplate.timetables.transxchange.ZippedValidator,
                  "__init__", return_value=None)
    def test_validate(self, mock_super_init, mock_super_validate, mock_validate_contents):
        with patch("boilerplate.timetables.transxchange.open",
                   MagicMock()) as mock_open:
            mock_open.return_value = BytesIO(b"sample zip file")
            txc_zip = TransXChangeZip("dummy.zip")

            # Run validate method
            txc_zip.validate()

            # Assertions
            mock_super_validate.assert_called_once()
            mock_validate_contents.assert_called_once()


class TestTransXChangeDatasetParser(unittest.TestCase):
    PTH_ = "boilerplate.timetables.transxchange"
    @patch(f"{PTH_}.TransXChangeDatasetParser.is_zipfile", return_value=True)
    @patch(f"{PTH_}.TransXChangeZip")
    def test_get_documents_zipfile(self, mock_transxchange_zip, mock_is_zipfile):
        # Mock the iterator returned by TransXChangeZip.iter_doc
        mock_doc1 = MagicMock(name="TransXChangeDocument1")
        mock_doc2 = MagicMock(name="TransXChangeDocument2")
        mock_transxchange_zip.return_value.__enter__.return_value.iter_doc.return_value = iter([mock_doc1, mock_doc2])

        parser = TransXChangeDatasetParser(BytesIO())

        # Collect documents
        docs = list(parser.get_documents())

        # Assertions
        self.assertEqual(len(docs), 2)
        self.assertIn(mock_doc1, docs)
        self.assertIn(mock_doc2, docs)

    @patch(f"{PTH_}.TransXChangeDatasetParser.is_zipfile", return_value=False)
    @patch(f"{PTH_}.TransXChangeDocument")
    def test_get_documents_single_file(self, mock_transxchange_document, mock_is_zipfile):
        mock_doc = mock_transxchange_document.return_value

        parser = TransXChangeDatasetParser(BytesIO())

        # Collect documents
        docs = list(parser.get_documents())

        # Assertions
        self.assertEqual(len(docs), 1)
        self.assertIn(mock_doc, docs)

    @patch(f"{PTH_}.TransXChangeDatasetParser.get_documents")
    def test_get_transxchange_versions(self, mock_get_documents):
        mock_doc = MagicMock()
        mock_doc.get_transxchange_version.return_value = "2.1"
        mock_get_documents.return_value = [mock_doc, mock_doc]

        parser = TransXChangeDatasetParser(BytesIO())
        versions = parser.get_transxchange_versions()

        self.assertEqual(versions, ["2.1", "2.1"])
        mock_doc.get_transxchange_version.assert_called()

    @patch(f"{PTH_}.TransXChangeDatasetParser.get_documents")
    def test_get_file_names(self, mock_get_documents):
        mock_doc = MagicMock()
        mock_doc.get_file_name.return_value = "file.xml"
        mock_get_documents.return_value = [mock_doc, mock_doc]

        parser = TransXChangeDatasetParser(BytesIO())
        file_names = parser.get_file_names()

        self.assertEqual(file_names, ["file.xml", "file.xml"])
        mock_doc.get_file_name.assert_called()

    @patch(f"{PTH_}.TransXChangeDatasetParser.get_documents")
    def test_get_stop_points(self, mock_get_documents):
        mock_doc = MagicMock()
        mock_doc.get_stop_points.return_value = ["Stop1", "Stop2"]
        mock_get_documents.return_value = [mock_doc, mock_doc]

        parser = TransXChangeDatasetParser(BytesIO())
        stops = parser.get_stop_points()

        self.assertEqual(stops, ["Stop1", "Stop2", "Stop1", "Stop2"])
        mock_doc.get_stop_points.assert_called()

    @patch(f"{PTH_}.TransXChangeDatasetParser.get_documents")
    def test_get_annotated_stop_point_refs(self, mock_get_documents):
        mock_doc = MagicMock()
        mock_doc.get_annotated_stop_point_refs.return_value = ["Ref1", "Ref2"]
        mock_get_documents.return_value = [mock_doc, mock_doc]

        parser = TransXChangeDatasetParser(BytesIO())
        annotated_refs = parser.get_annotated_stop_point_refs()

        self.assertEqual(annotated_refs, ["Ref1", "Ref2", "Ref1", "Ref2"])
        mock_doc.get_annotated_stop_point_refs.assert_called()

    @patch(f"{PTH_}.TransXChangeDatasetParser.get_documents")
    def test_get_principal_timing_points(self, mock_get_documents):
        mock_doc = MagicMock()
        mock_doc.get_principal_timing_points.return_value = ["TimePoint1", "TimePoint2"]
        mock_get_documents.return_value = [mock_doc, mock_doc]

        parser = TransXChangeDatasetParser(BytesIO())
        timing_points = parser.get_principal_timing_points()

        self.assertEqual(timing_points, ["TimePoint1", "TimePoint2", "TimePoint1", "TimePoint2"])
        mock_doc.get_principal_timing_points.assert_called()

    @patch(f"{PTH_}.TransXChangeDatasetParser.get_documents")
    def test_get_nocs(self, mock_get_documents):
        mock_doc = MagicMock()
        mock_doc.get_nocs.return_value = ["NOC1", "NOC2"]
        mock_get_documents.return_value = [mock_doc, mock_doc]

        parser = TransXChangeDatasetParser(BytesIO())
        nocs = parser.get_nocs()

        self.assertEqual(nocs, ["NOC1", "NOC2", "NOC1", "NOC2"])
        mock_doc.get_nocs.assert_called()

    @patch(f"{PTH_}.TransXChangeDatasetParser.get_documents")
    def test_get_line_names(self, mock_get_documents):
        mock_doc = MagicMock()
        mock_doc.get_all_line_names.return_value = ["Line1", "Line2"]
        mock_get_documents.return_value = [mock_doc, mock_doc]

        parser = TransXChangeDatasetParser(BytesIO())
        line_names = parser.get_line_names()

        self.assertEqual(line_names, ["Line1", "Line2", "Line1", "Line2"])
        mock_doc.get_all_line_names.assert_called()

    @patch(f"{PTH_}.TransXChangeZip")
    @patch(f"{PTH_}.TransXChangeDocument")
    def test_iter_docs_with_zipfile(self, mock_document, mock_zip):
        """
        Test _iter_docs when the source is a zip file.
        """
        # Mock source and zip file behavior
        mock_source = "mock_source.zip"
        mock_zip_instance = MagicMock()
        mock_zip_instance.iter_doc.return_value = ["doc1", "doc2"]
        mock_zip.return_value.__enter__.return_value = mock_zip_instance

        # Instance of the class to test
        instance = TransXChangeDatasetParser(mock_source)
        instance.is_zipfile = MagicMock(
            return_value=True)  # Mock is_zipfile to return True

        # Collect documents
        docs = list(instance._iter_docs())

        # Assertions
        assert docs == ["doc1", "doc2"]
        instance.is_zipfile.assert_called_once()
        mock_zip.assert_called_once_with(mock_source)
        mock_zip_instance.iter_doc.assert_called_once()

    @patch(f"{PTH_}.TransXChangeDocument")
    def test_iter_docs_without_zipfile(self, mock_document):
        """
        Test _iter_docs when the source is not a zip file.
        """
        # Mock source and document behavior
        mock_source = "mock_source.xml"
        mock_document_instance = MagicMock()
        mock_document.return_value = mock_document_instance

        # Instance of the class to test
        instance = TransXChangeDatasetParser(mock_source)
        instance.is_zipfile = MagicMock(
            return_value=False)  # Mock is_zipfile to return False

        # Collect documents
        docs = list(instance._iter_docs())

        # Assertions
        assert docs == [mock_document_instance]
        instance.is_zipfile.assert_called_once()
        mock_document.assert_called_once_with(mock_source)

    @patch(f"{PTH_}.zipfile.is_zipfile")
    def test_is_zipfile_true(self, mock_is_zipfile):
        """
        Test is_zipfile returns True when the source is a valid zip file.
        """
        # Mock zipfile.is_zipfile to return True
        mock_is_zipfile.return_value = True

        # Instance of the class to test
        instance = TransXChangeDatasetParser("mock_source.zip")

        # Call the method
        result = instance.is_zipfile()

        # Assertions
        assert result is True
        mock_is_zipfile.assert_called_once_with("mock_source.zip")


class TestBaseSchemaViolation(unittest.TestCase):

    def test_from_error(self):
        """
        Test BaseSchemaViolation.from_error correctly initializes the
        object from an error.
        """
        # Mock the error object
        mock_error = MagicMock()
        mock_error.filename = "/path/to/test_file.xml"
        mock_error.line = 42
        mock_error.message = "An error occurred."

        # Call the method
        violation = BaseSchemaViolation.from_error(mock_error)

        # Assertions
        self.assertEqual(violation.filename, "test_file.xml")
        self.assertEqual(violation.line, 42)
        self.assertEqual(violation.details, "An error occurred.")

    def test_from_error_with_no_path(self):
        """
        Test BaseSchemaViolation.from_error when the filename has
        no directory path.
        """
        # Mock the error object
        mock_error = MagicMock()
        mock_error.filename = "simple_file.xml"
        mock_error.line = 99
        mock_error.message = "Another error occurred."

        # Call the method
        violation = BaseSchemaViolation.from_error(mock_error)

        # Assertions
        self.assertEqual(violation.filename, "simple_file.xml")
        self.assertEqual(violation.line, 99)
        self.assertEqual(violation.details, "Another error occurred.")


class TestTXCPostSchemaViolation(unittest.TestCase):

    def test_from_error(self):
        """
        Test TXCPostSchemaViolation.from_error correctly initializes the object
        from an error.
        """
        # Mock the error object
        mock_error = MagicMock()
        mock_error.filename = "/path/to/test_file.xml"
        mock_error.message = "Schema violation occurred."

        # Call the method
        violation = TXCPostSchemaViolation.from_error(mock_error)

        # Assertions
        self.assertEqual(violation.filename, "test_file.xml")
        self.assertEqual(violation.details, "Schema violation occurred.")

    def test_from_error_with_no_path(self):
        """
        Test TXCPostSchemaViolation.from_error when the filename has no
        directory path.
        """
        # Mock the error object
        mock_error = MagicMock()
        mock_error.filename = "simple_file.xml"
        mock_error.message = "Another schema violation."

        # Call the method
        violation = TXCPostSchemaViolation.from_error(mock_error)

        # Assertions
        self.assertEqual(violation.filename, "simple_file.xml")
        self.assertEqual(violation.details, "Another schema violation.")


if __name__ == "__main__":
    unittest.main()