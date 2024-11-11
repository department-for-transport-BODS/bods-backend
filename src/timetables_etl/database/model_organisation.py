"""
SQL Models whose tables are prefixed organisation_
"""

from __future__ import annotations

from datetime import datetime
from enum import Enum, IntEnum
from typing import TYPE_CHECKING, List, Optional

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String, UniqueConstraint
from sqlalchemy import Enum as SQLEnum
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .common import BaseSQLModel, TimeStampedMixin

if TYPE_CHECKING:
    from .model_pipelines import DatasetETLTaskResult


class User(BaseSQLModel):
    __tablename__ = "users_user"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    password: Mapped[str] = mapped_column(String(128))
    is_superuser: Mapped[bool] = mapped_column(Boolean)
    username: Mapped[str] = mapped_column(String(150))
    first_name: Mapped[str] = mapped_column(String(150))
    last_name: Mapped[str] = mapped_column(String(150))
    is_staff: Mapped[bool] = mapped_column(Boolean)
    is_active: Mapped[bool] = mapped_column(Boolean)
    date_joined: Mapped[datetime] = mapped_column(DateTime(True))
    account_type: Mapped[int] = mapped_column(Integer)
    name: Mapped[str] = mapped_column(String(255))
    email: Mapped[str] = mapped_column(String(254))
    description: Mapped[str] = mapped_column(String(400))
    dev_organisation: Mapped[str] = mapped_column(String(60))
    agent_organisation: Mapped[str] = mapped_column(String(60))
    notes: Mapped[str] = mapped_column(String(150))
    last_login: Mapped[Optional[datetime]] = mapped_column(DateTime(True))

    organisation_dataset: Mapped[List["Dataset"]] = relationship(
        "Dataset", back_populates="contact", default_factory=list, kw_only=True
    )
    publications: Mapped[List["DatasetRevision"]] = relationship(
        "DatasetRevision",
        back_populates="published_by",
        foreign_keys="[DatasetRevision.published_by_id]",
        default_factory=list,
        kw_only=True,
    )

    # Modified revisions - where user is the last modifier
    modified_revisions: Mapped[List["DatasetRevision"]] = relationship(
        "DatasetRevision",
        back_populates="last_modified_user",
        foreign_keys="[DatasetRevision.last_modified_user_id]",
        default_factory=list,
        kw_only=True,
    )

    organisation_organisation: Mapped["Organisation"] = relationship(
        "Organisation", uselist=False, back_populates="key_contact"
    )
    dataset_subscriptions: Mapped[List["DatasetSubscription"]] = relationship(
        "DatasetSubscription",
        back_populates="user",
        cascade="all, delete-orphan",
        default_factory=list,
        kw_only=True,
    )

    subscribed_datasets: Mapped[List["Dataset"]] = relationship(
        "Dataset",
        secondary="organisation_datasetsubscription",
        back_populates="subscribers",
        default_factory=list,
        kw_only=True,
        viewonly=True,
    )


class ChoiceEnum(Enum):
    @classmethod
    def choices(cls):
        return sorted([(key.value, key.name) for key in cls], key=lambda c: c[0])


class DatasetType(IntEnum):
    """Dataset types enumeration"""

    TIMETABLE = 1
    AVL = 2
    FARES = 3
    DISRUPTIONS = 4

    @classmethod
    def choices(cls) -> list[tuple[int, str]]:
        """Get choices for forms/validation"""
        return [(member.value, member.name) for member in cls]


class AVLFeedStatus(ChoiceEnum):
    LIVE = "FEED_UP"
    INACTIVE = "FEED_DOWN"
    ERROR = "SYSTEM_ERROR"


class Dataset(BaseSQLModel):
    __tablename__ = "organisation_dataset"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    created: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    modified: Mapped[datetime] = mapped_column(DateTime(timezone=True))

    # Foreign Keys
    organisation_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("organisation_organisation.id", ondelete="CASCADE"),
        nullable=False,
        kw_only=True,
        doc="Bus portal organisation",
    )

    contact_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("users_user.id", ondelete="CASCADE"),
        nullable=False,
        kw_only=True,
        doc="This user will receive all notifications",
    )

    live_revision_id: Mapped[Optional[int]] = mapped_column(
        Integer,
        ForeignKey("organisation_datasetrevision.id", ondelete="SET NULL"),
        nullable=True,
        kw_only=True,
    )

    dataset_type: Mapped[DatasetType] = mapped_column(
        Integer,
        nullable=False,
        default=DatasetType.TIMETABLE,
        server_default=str(DatasetType.TIMETABLE.value),
        kw_only=True,
    )
    avl_feed_status: Mapped[AVLFeedStatus] = mapped_column(
        SQLEnum(AVLFeedStatus),
        nullable=False,
        default=AVLFeedStatus.INACTIVE,
        server_default=AVLFeedStatus.INACTIVE.value,
        kw_only=True,
    )

    is_dummy: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=False, server_default="false", kw_only=True
    )

    avl_feed_last_checked: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        kw_only=True,
        doc="The time when the AVL feed status was last checked",
    )

    # Relationships
    contact: Mapped["User"] = relationship(
        "User",
        back_populates="organisation_dataset",
        default=None,
        kw_only=True,
    )

    live_revision: Mapped[Optional["DatasetRevision"]] = relationship(
        "DatasetRevision",
        foreign_keys=[live_revision_id],
        back_populates="live_revision_dataset",
        uselist=False,
        default=None,
        kw_only=True,
    )
    organisation: Mapped["Organisation"] = relationship(
        "Organisation",
        back_populates="organisation_dataset",
        default=None,
        kw_only=True,
    )

    revisions: Mapped[List["DatasetRevision"]] = relationship(
        "DatasetRevision",
        back_populates="dataset",
        foreign_keys="[DatasetRevision.dataset_id]",
        default_factory=list,
        kw_only=True,
    )
    subscriptions: Mapped[List["DatasetSubscription"]] = relationship(
        "DatasetSubscription",
        back_populates="dataset",
        cascade="all, delete-orphan",
        default_factory=list,
        kw_only=True,
    )

    subscribers: Mapped[List["User"]] = relationship(
        "User",
        secondary="organisation_datasetsubscription",
        back_populates="subscribed_datasets",
        default_factory=list,
        kw_only=True,
        viewonly=True,
    )


class DatasetRevision(TimeStampedMixin, BaseSQLModel):
    """
    SQLAlchemy model for Dataset Revision that mirrors the Django model.
    """

    __tablename__ = "organisation_datasetrevision"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, init=False)

    # Foreign Keys
    dataset_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("organisation_dataset.id", ondelete="CASCADE"),
        nullable=False,
        kw_only=True,
        doc="The parent dataset",
    )

    published_by_id: Mapped[Optional[int]] = mapped_column(
        Integer,
        ForeignKey("users_user.id", ondelete="PROTECT"),
        nullable=True,
        kw_only=True,
    )

    last_modified_user_id: Mapped[Optional[int]] = mapped_column(
        Integer,
        ForeignKey("users_user.id", ondelete="DO_NOTHING"),
        nullable=True,
        kw_only=True,
    )

    # Basic fields
    name: Mapped[str] = mapped_column(
        String(255), unique=True, nullable=False, kw_only=True, doc="Feed name"
    )

    description: Mapped[str] = mapped_column(
        String(255), nullable=False, kw_only=True, doc="Any description for the feed"
    )

    short_description: Mapped[str] = mapped_column(
        String(30), nullable=False, kw_only=True, doc="Short description for the feed"
    )

    comment: Mapped[str] = mapped_column(
        String(255),
        default="",
        server_default="",
        kw_only=True,
        doc="Any comments for the feed",
    )

    url_link: Mapped[str] = mapped_column(
        String(500),
        default="",
        server_default="",
        kw_only=True,
        doc="URL link to feed, if any",
    )

    is_published: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        server_default="false",
        nullable=False,
        kw_only=True,
        doc="Whether the feed is published or not",
    )

    published_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        kw_only=True,
        doc="The time when this change was published",
    )

    username: Mapped[str] = mapped_column(
        String(255),
        default="",
        server_default="",
        kw_only=True,
        doc="Username required to access the resource, if any",
    )

    password: Mapped[str] = mapped_column(
        String(255),
        default="",
        server_default="",
        kw_only=True,
        doc="Password required to access the resource, if any",
    )

    requestor_ref: Mapped[str] = mapped_column(
        String(255),
        default="",
        server_default="",
        kw_only=True,
        doc="Requestor ref to access the resource, if any",
    )

    # Relationships
    dataset: Mapped["Dataset"] = relationship(
        "Dataset",
        foreign_keys=[dataset_id],
        back_populates="revisions",
        default=None,
        kw_only=True,
    )
    live_revision_dataset: Mapped[Optional["Dataset"]] = relationship(
        "Dataset",
        back_populates="live_revision",
        foreign_keys="[Dataset.live_revision_id]",
        uselist=False,
        default=None,
        kw_only=True,
    )
    published_by: Mapped[Optional["User"]] = relationship(
        "User",
        foreign_keys=[published_by_id],
        back_populates="publications",
        default=None,
        kw_only=True,
    )

    last_modified_user: Mapped[Optional["User"]] = relationship(
        "User",
        foreign_keys=[last_modified_user_id],
        back_populates="modified_revisions",
        default=None,
        kw_only=True,
    )

    etl_results: Mapped[List["DatasetETLTaskResult"]] = relationship(
        "DatasetETLTaskResult",
        back_populates="revision",
        cascade="all, delete-orphan",
        default_factory=list,
        kw_only=True,
    )


class Organisation(BaseSQLModel):
    __tablename__ = "organisation_organisation"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    created: Mapped[datetime] = mapped_column(DateTime(True))
    modified: Mapped[datetime] = mapped_column(DateTime(True))
    name: Mapped[str] = mapped_column(String(255))
    short_name: Mapped[str] = mapped_column(String(255))
    is_active: Mapped[bool] = mapped_column(Boolean)
    is_abods_global_viewer: Mapped[bool] = mapped_column(Boolean)
    key_contact_id: Mapped[Optional[int]] = mapped_column(
        Integer, ForeignKey("users_user.id"), nullable=True, kw_only=True
    )

    licence_required: Mapped[Optional[bool]] = mapped_column(Boolean)

    organisation_dataset: Mapped[List["Dataset"]] = relationship(
        "Dataset", back_populates="organisation"
    )
    key_contact: Mapped["User"] = relationship(
        "User", back_populates="organisation_organisation"
    )


class DatasetSubscription(TimeStampedMixin, BaseSQLModel):
    """
    SQLAlchemy model for Dataset Subscription that mirrors the Django model.
    Maintains a unique constraint between dataset and user.
    """

    __tablename__ = "organisation_datasetsubscription"
    __table_args__ = (
        UniqueConstraint("dataset_id", "user_id", name="uq_dataset_user"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, init=False)

    # Foreign Keys
    dataset_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("organisation_dataset.id", ondelete="CASCADE"),
        nullable=False,
        kw_only=True,
    )

    user_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("users_user.id", ondelete="CASCADE"),
        nullable=False,
        kw_only=True,
    )

    dataset: Mapped["Dataset"] = relationship(
        "Dataset",
        back_populates="subscriptions",
        default=None,
        kw_only=True,
        overlaps="subscribers,subscribed_datasets",
    )

    user: Mapped["User"] = relationship(
        "User",
        back_populates="dataset_subscriptions",
        default=None,
        kw_only=True,
        overlaps="subscribers,subscribed_datasets",
    )
