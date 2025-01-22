"""
Factoryboy Factories for PTI Models
"""

import factory
from common_layer.pti.models import Header, Schema
from factory import Factory, SubFactory


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
        model = Schema

    header = SubFactory(HeaderFactory)
    observations = []
