"""
AVL Models
SQLAlchemy Models
"""

from sqlalchemy import Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from .common import BaseSQLModel, TimeStampedMixin


class AvlCavlDataArchive(TimeStampedMixin, BaseSQLModel):
    """AVL CAVL Data Archive Table"""

    include_created = True
    include_last_updated = True
    include_modified = False

    __tablename__ = "avl_cavldataarchive"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, init=False)
    data: Mapped[str] = mapped_column(String(100), nullable=False)
    data_format: Mapped[str] = mapped_column(String(2), nullable=False)
