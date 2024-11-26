from factory import Factory, SubFactory
from pti.models import Header, Schema


class HeaderFactory(Factory):
    class Meta:
        model = Header

    namespaces = {"x": "http://www.transxchange.org.uk/"}
    version = "1.0.0"
    guidance_document = "https://pti.org.uk/system/files/files/" "TransXChange%20UK%20PTI%20Profile%20v1.1.pdf"
    notes = ""


class SchemaFactory(Factory):
    class Meta:
        model = Schema

    header = SubFactory(HeaderFactory)
    observations = []
