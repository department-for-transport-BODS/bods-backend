"""
Common
"""

from datetime import UTC, date, datetime

from sqlalchemy import DateTime
from sqlalchemy.ext.declarative import declared_attr
from sqlalchemy.orm import DeclarativeBase, Mapped, MappedAsDataclass, mapped_column


class BaseSQLModel(MappedAsDataclass, DeclarativeBase):
    """
    Base Class for SQL Models enabling Declarative declaration and usage as python dataclass
    """

    def as_dict(self):
        def serialize_value(value):
            if isinstance(value, (date, datetime)):
                return value.isoformat()
            return value

        return {
            column.name: serialize_value(getattr(self, column.name))
            for column in self.__table__.columns
        }


class CreatedTimeStampMixin(MappedAsDataclass):
    """
    A mixin that adds a self-managed created field.
    Timestamp is stored in UTC.
    """

    include_created = True

    @declared_attr.directive
    @classmethod
    def created(cls) -> Mapped[datetime] | None:
        """
        Generate the created timestamp when inserting
        """
        if cls.include_created:
            return mapped_column(
                DateTime(timezone=True),
                insert_default=datetime.now(UTC),
                default_factory=datetime.now,
                nullable=False,
                kw_only=True,
            )
        return None


class TimeStampedMixin(CreatedTimeStampMixin):
    """
    A mixin that adds self-managed created and modified fields.
    All timestamps are stored in UTC.
    """

    include_last_updated = False
    include_modified = True

    @declared_attr.directive
    @classmethod
    def last_updated(cls) -> Mapped[datetime] | None:
        """
        Generates the modified field when model is being updated
        """
        if cls.include_last_updated:
            return mapped_column(
                DateTime(timezone=True),
                insert_default=datetime.now(UTC),
                default_factory=datetime.now,
                onupdate=datetime.now(UTC),
                nullable=False,
                kw_only=True,
            )
        return None

    @declared_attr.directive
    @classmethod
    def modified(cls) -> Mapped[datetime] | None:
        """
        Generates the modified field when model is being updated
        """
        if cls.include_modified:
            return mapped_column(
                DateTime(timezone=True),
                insert_default=datetime.now(UTC),
                default_factory=datetime.now,
                onupdate=datetime.now(UTC),
                nullable=False,
                kw_only=True,
            )
        return None
