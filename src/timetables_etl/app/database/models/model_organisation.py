"""
Tables prefixed organisation_
SQLAlchemy Models
"""

from __future__ import annotations

from datetime import date, datetime
from typing import Optional

from sqlalchemy import (
    ARRAY,
    Boolean,
    Date,
    DateTime,
    ForeignKey,
    ForeignKeyConstraint,
    Integer,
    PrimaryKeyConstraint,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy import Enum as SQLEnum
from sqlalchemy.orm import Mapped, mapped_column

from .common import BaseSQLModel, TimeStampedMixin
from .db_enums import AVLFeedStatus, DatasetType


class OrganisationDataset(BaseSQLModel):
    __tablename__ = "organisation_dataset"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    created: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    modified: Mapped[datetime] = mapped_column(DateTime(timezone=True))
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
    avl_feed_status: Mapped[str] = mapped_column(
        Text, nullable=False, unique=True, kw_only=True
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


class OrganisationDatasetrevision(TimeStampedMixin, BaseSQLModel):
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


class OrganisationOrganisation(BaseSQLModel):
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


class OrganisationDatasetSubscription(TimeStampedMixin, BaseSQLModel):
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


class OrganisationTxcFileAttributes(BaseSQLModel):
    __tablename__ = "organisation_txcfileattributes"
    __table_args__ = (
        ForeignKeyConstraint(
            ["revision_id"],
            ["public.organisation_datasetrevision.id"],
            deferrable=True,
            initially="DEFERRED",
            name="organisation_txcfile_revision_id_ddb2f841_fk_organisat",
        ),
        PrimaryKeyConstraint("id", name="organisation_txcfileattributes_pkey"),
        {"schema": "public"},
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    schema_version: Mapped[str] = mapped_column(String(10))
    revision_number: Mapped[int] = mapped_column(Integer)
    creation_datetime: Mapped[datetime] = mapped_column(DateTime(True))
    modification_datetime: Mapped[datetime] = mapped_column(DateTime(True))
    filename: Mapped[str] = mapped_column(String(512))
    service_code: Mapped[str] = mapped_column(String(100))
    revision_id: Mapped[int] = mapped_column(Integer)
    modification: Mapped[str] = mapped_column(String(28))
    national_operator_code: Mapped[str] = mapped_column(String(100))
    licence_number: Mapped[str] = mapped_column(String(56))
    public_use: Mapped[bool] = mapped_column(Boolean)
    line_names: Mapped[list] = mapped_column(ARRAY(String(length=255)))
    destination: Mapped[str] = mapped_column(String(512))
    origin: Mapped[str] = mapped_column(String(512))
    hash: Mapped[str] = mapped_column(String(40))
    operating_period_end_date: Mapped[Optional[date]] = mapped_column(Date)
    operating_period_start_date: Mapped[Optional[date]] = mapped_column(Date)
