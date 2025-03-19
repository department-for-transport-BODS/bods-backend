"""
SQLAlchemy Models for tables prepended ui_
"""

from sqlalchemy import Integer, Text
from sqlalchemy.orm import Mapped, mapped_column

from .common import BaseSQLModel


class UiLta(BaseSQLModel):
    """
    Stores the mapping of local authorities to a local authority name
    Local Authorities from the registration data
    This supports the ability to group local authorities into a combined authorities view.
    It is displayed on the BODS UI.
    This relationship is manually created using Django.
    """

    __tablename__ = "ui_lta"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, init=False)
    name: Mapped[str] = mapped_column(Text)
