"""
SQLAlchemy Models for tables prepended ui_ 
"""

from common_layer.database.models.common import BaseSQLModel
from sqlalchemy import Integer, Text
from sqlalchemy.orm import Mapped, mapped_column


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
