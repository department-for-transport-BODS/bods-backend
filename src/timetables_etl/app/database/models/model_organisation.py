"""
Tables prefixed organisation_
SQLAlchemy Models
"""

from __future__ import annotations

from datetime import date, datetime

from sqlalchemy import (
    ARRAY,
    Boolean,
    Date,
    DateTime,
    ForeignKey,
    Integer,
    String,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column

from .common import BaseSQLModel, TimeStampedMixin


class OrganisationDataset(TimeStampedMixin, BaseSQLModel):
    __tablename__ = "organisation_dataset"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, init=False)
    live_revision_id: Mapped[int | None] = mapped_column(
        Integer,
        ForeignKey("organisation_datasetrevision.id"),
        nullable=True,
        unique=True,
    )
    organisation_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("organisation_organisation.id"), nullable=False
    )
    contact_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("users_user.id"), nullable=False
    )
    dataset_type: Mapped[int] = mapped_column(Integer, nullable=False)
    avl_feed_status: Mapped[str] = mapped_column(String(20), nullable=False)
    avl_feed_last_checked: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    is_dummy: Mapped[bool] = mapped_column(Boolean, nullable=False)


class OrganisationDatasetrevision(TimeStampedMixin, BaseSQLModel):
    """
    Revision data
    """

    __tablename__ = "organisation_datasetrevision"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, init=False)
    upload_file: Mapped[str | None] = mapped_column(String(100), nullable=True)
    status: Mapped[str] = mapped_column(String(20), nullable=False)
    name: Mapped[str] = mapped_column(String(255), nullable=False, unique=True)
    description: Mapped[str] = mapped_column(String(255), nullable=False)
    comment: Mapped[str] = mapped_column(String(255), nullable=False)
    is_published: Mapped[bool] = mapped_column(Boolean, nullable=False)
    url_link: Mapped[str] = mapped_column(String(500), nullable=False)
    num_of_lines: Mapped[int | None] = mapped_column(Integer, nullable=True)
    num_of_operators: Mapped[int | None] = mapped_column(Integer, nullable=True)
    transxchange_version: Mapped[str] = mapped_column(String(8), nullable=False)
    imported: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    bounding_box: Mapped[str | None] = mapped_column(String(8096), nullable=True)
    publisher_creation_datetime: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    publisher_modified_datetime: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    first_expiring_service: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    last_expiring_service: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    first_service_start: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    num_of_bus_stops: Mapped[int | None] = mapped_column(Integer, nullable=True)
    dataset_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("organisation_dataset.id"), nullable=False
    )
    last_modified_user_id: Mapped[int | None] = mapped_column(
        Integer, ForeignKey("users_user.id"), nullable=True
    )
    published_by_id: Mapped[int | None] = mapped_column(
        Integer, ForeignKey("users_user.id"), nullable=True
    )
    published_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    password: Mapped[str] = mapped_column(String(255), nullable=False)
    requestor_ref: Mapped[str] = mapped_column(String(255), nullable=False)
    username: Mapped[str] = mapped_column(String(255), nullable=False)
    short_description: Mapped[str] = mapped_column(String(30), nullable=False)
    num_of_timing_points: Mapped[int | None] = mapped_column(Integer, nullable=True)


class OrganisationOrganisation(TimeStampedMixin, BaseSQLModel):
    __tablename__ = "organisation_organisation"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, init=False)
    name: Mapped[str] = mapped_column(String(255), nullable=False, unique=True)
    short_name: Mapped[str] = mapped_column(String(255), nullable=False)
    key_contact_id: Mapped[int | None] = mapped_column(
        Integer, ForeignKey("users_user.id"), nullable=True, unique=True
    )
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False)
    licence_required: Mapped[bool | None] = mapped_column(Boolean, nullable=True)
    is_abods_global_viewer: Mapped[bool] = mapped_column(Boolean, nullable=False)


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


class OrganisationTXCFileAttributes(BaseSQLModel):
    """Organisation TXC File Attributes Table"""

    __tablename__ = "organisation_txcfileattributes"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, init=False)
    schema_version: Mapped[str] = mapped_column(String(10), nullable=False)
    revision_number: Mapped[int] = mapped_column(Integer, nullable=False)
    creation_datetime: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False
    )
    modification_datetime: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False
    )
    filename: Mapped[str] = mapped_column(String(512), nullable=False)
    service_code: Mapped[str] = mapped_column(String(100), nullable=False)
    revision_id: Mapped[int] = mapped_column(Integer, nullable=False)
    modification: Mapped[str] = mapped_column(String(28), nullable=False)
    national_operator_code: Mapped[str] = mapped_column(String(100), nullable=False)
    licence_number: Mapped[str] = mapped_column(String(56), nullable=False)
    operating_period_end_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    operating_period_start_date: Mapped[date | None] = mapped_column(
        Date, nullable=True
    )
    public_use: Mapped[bool] = mapped_column(Boolean, nullable=False)
    line_names: Mapped[list[str]] = mapped_column(ARRAY(String), nullable=False)
    destination: Mapped[str] = mapped_column(String(512), nullable=False)
    origin: Mapped[str] = mapped_column(String(512), nullable=False)
    hash: Mapped[str] = mapped_column(String(40), nullable=False)
