"""
Factoryboy Factories for PTI Models
"""

import factory
from factory import Factory, SubFactory
from pti.app.models.models_pti import Header, PtiJsonSchema


class HeaderFactory(Factory):
    class Meta:  # type: ignore[misc]
        model = Header

    namespaces = {"x": "http://www.transxchange.org.uk/"}
    version = "1.0.0"
    guidance_document = (
        "https://pti.org.uk/system/files/files/"
        "TransXChange%20UK%20PTI%20Profile%20v1.1.pdf"
    )
    notes = ""


class SchemaFactory(factory.DictFactory):
    class Meta:  # type: ignore[misc]
        model = PtiJsonSchema

    header = SubFactory(HeaderFactory)
    observations = []
