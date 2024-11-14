"""
SQL Alchemy models for tables starting with users_
"""

from __future__ import annotations

from datetime import datetime
from typing import List, Optional

from sqlalchemy import Boolean, DateTime, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .common import BaseSQLModel
from .model_organisation import (
    OrganisationDataset,
    OrganisationDatasetrevision,
    OrganisationDatasetSubscription,
    OrganisationOrganisation,
)


class UsersUser(BaseSQLModel):
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

    organisation_dataset: Mapped[List["OrganisationDataset"]] = relationship(
        "OrganisationDataset",
        back_populates="contact",
        default_factory=list,
        kw_only=True,
    )
    publications: Mapped[list["OrganisationDatasetrevision"]] = relationship(
        "OrganisationDatasetrevision",
        back_populates="published_by",
        foreign_keys="[OrganisationDatasetrevision.published_by_id]",
        default_factory=list,
        kw_only=True,
    )

    # Modified revisions - where user is the last modifier
    modified_revisions: Mapped[list["OrganisationDatasetrevision"]] = relationship(
        "OrganisationDatasetrevision",
        back_populates="last_modified_user",
        foreign_keys="[OrganisationDatasetrevision.last_modified_user_id]",
        default_factory=list,
        kw_only=True,
    )

    organisation_organisation: Mapped["OrganisationOrganisation"] = relationship(
        "OrganisationOrganisation", uselist=False, back_populates="key_contact"
    )
    dataset_subscriptions: Mapped[List["OrganisationDatasetSubscription"]] = (
        relationship(
            "OrganisationDatasetSubscription",
            back_populates="user",
            cascade="all, delete-orphan",
            default_factory=list,
            kw_only=True,
        )
    )

    subscribed_datasets: Mapped[List["OrganisationDataset"]] = relationship(
        "OrganisationDataset",
        secondary="organisation_datasetsubscription",
        back_populates="subscribers",
        default_factory=list,
        kw_only=True,
        viewonly=True,
    )
