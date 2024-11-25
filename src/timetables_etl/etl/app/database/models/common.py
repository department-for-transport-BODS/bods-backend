"""
Common
"""

from datetime import UTC, datetime

from sqlalchemy import DateTime
from sqlalchemy.ext.declarative import declared_attr
from sqlalchemy.orm import DeclarativeBase, Mapped, MappedAsDataclass, mapped_column


class BaseSQLModel(MappedAsDataclass, DeclarativeBase):
    """
    Base Class for SQL Models enabling Declarative declaration and usage as python dataclass
    """


class TimeStampedMixin:
    """
    A mixin that adds self-managed created and modified fields.
    All timestamps are stored in UTC.
    """

    @declared_attr.directive
    @classmethod
    def created(cls) -> Mapped[datetime]:
        """
        Generate the created timestamp
        """
        return mapped_column(
            DateTime(timezone=True),
            default=lambda: datetime.now(UTC),
            nullable=False,
            kw_only=True,
        )

    @declared_attr.directive
    @classmethod
    def modified(cls) -> Mapped[datetime]:
        """
        Generates the modified field when model is being updated
        """
        return mapped_column(
            DateTime(timezone=True),
            default=lambda: datetime.now(UTC),
            onupdate=lambda: datetime.now(UTC),
            nullable=False,
            kw_only=True,
        )
