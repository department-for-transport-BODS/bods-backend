"""
SQL Alchemy models for tables starting with users_
"""

from __future__ import annotations

from sqlalchemy import ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from .common import BaseSQLModel


class AgentUserInvite(BaseSQLModel):
    """
    BODs Agent user invite Table
    """

    __tablename__ = "users_agentuserinvite"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    agent_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("users_user.id", ondelete="CASCADE"),
        nullable=False,
        kw_only=True,
    )
    organisation_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("organisation_organisation.id"), nullable=False
    )
    invitation_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("users_invitation.id"),
        nullable=True,
    )

    inviter_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("users_user.id", ondelete="CASCADE"),
        nullable=False,
        unique=True,
    )
    status: Mapped[str] = mapped_column(String(20), nullable=False)
