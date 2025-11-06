"""
SQL Alchemy models for tables starting with users_
"""

from __future__ import annotations

from datetime import datetime
from typing import Optional

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from .common import BaseSQLModel


class UsersUser(BaseSQLModel):
    """
    BODs User Table
    """

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


class UserSettings(BaseSQLModel):
    """
    BODs User settings Table
    """

    __tablename__ = "users_usersettings"
    user_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("users_user.id", ondelete="CASCADE"),
        nullable=False,
        primary_key=True,
    )
    regional_areas: Mapped[str] = mapped_column(String(60), nullable=True)
    mute_all_dataset_notifications: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=False
    )
    notify_invitation_accepted: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=False
    )
    opt_in_user_research: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=False
    )
    share_app_usage: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=False
    )
    notify_avl_unavailable: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=False
    )
    daily_compliance_check_alert: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=False
    )
    national_interest: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=False
    )
    intended_use: Mapped[int] = mapped_column(Integer, nullable=True, default="App")
