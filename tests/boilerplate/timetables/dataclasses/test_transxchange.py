from pathlib import Path
import unittest
from common_layer.timetables.transxchange import TransXChangeDocument
from common_layer.timetables.dataclasses import transxchange


class TestTransXChangeZip(unittest.TestCase):
    def setUp(self):
        xml_path = Path(__file__).parent.parent.parent.parent.resolve() / "data" / "sample.xml"
        xml_content = open(xml_path, "rb")
        self.document = TransXChangeDocument(xml_content)

    def test_from_txc_document(self):
        buf = transxchange.TXCFile.from_txc_document(self.document,
                                                     True)
        self.assertEqual(buf.header.filename, "sample.xml")
        self.assertEqual(buf.header.schema_version, "2.4")
        self.assertEqual(buf.service.service_code, "UZ000FLIX:UKN603")
        self.assertEqual(buf.operator.national_operator_code, "FLIX")
        self.assertEqual(buf.service_code, "UZ000FLIX:UKN603")
        self.assertEqual(buf.hash, "ca6a517e77b727d34a05de63938777f5199bb1f6")



