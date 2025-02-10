"""
TXC MetaData Factories
"""

from datetime import UTC, datetime

from common_layer.xml.txc.models.txc_metadata import TXCMetadata
from factory import Factory, LazyFunction, Sequence


class TXCMetadataFactory(Factory):
    """
    Factory for TXC Metadata
    """

    class Meta:  # type: ignore[misc]
        model = TXCMetadata

    SchemaVersion = "2.4"
    ModificationDateTime = LazyFunction(lambda: datetime.now(UTC))
    Modification = "new"
    RevisionNumber = Sequence(lambda n: n)
    CreationDateTime = LazyFunction(lambda: datetime.now(UTC))
    FileName = "test.xml"
    FileHash = "abc123"
