"""
Models for Many to Many Relationhip Tables
AKA: Associative Entity, Junction Tables, Jump Tables
"""

from sqlalchemy import Integer
from sqlalchemy.orm import Mapped, mapped_column

from .common import BaseSQLModel


class TransmodelServiceServicePattern(BaseSQLModel):
    """Association table between Services and ServicePatterns"""

    __tablename__ = "transmodel_service_service_patterns"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, init=False)
    service_id: Mapped[int] = mapped_column(Integer, nullable=False)
    servicepattern_id: Mapped[int] = mapped_column(Integer, nullable=False)
