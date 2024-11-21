"""
Models for Many to Many Relationhip Tables
AKA: Associative Entity, Junction Tables, Jump Tables
"""

from sqlalchemy import Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from .common import BaseSQLModel


class TransmodelServiceServicePattern(BaseSQLModel):
    """
    Association table between:
        - transmodel_service (TransmodelService)
        - transmodel_servicepattern (TransmodelServicePattern)
    """

    __tablename__ = "transmodel_service_service_patterns"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, init=False)
    service_id: Mapped[int] = mapped_column(Integer, nullable=False)
    servicepattern_id: Mapped[int] = mapped_column(Integer, nullable=False)


class TransmodelServicePatternLocality(BaseSQLModel):
    """
    Association table between:
        - transmodel_servicepattern (TransmodelServicePattern)
        - naptan_locality (NaptanLocality)
    """

    __tablename__ = "transmodel_servicepattern_localities"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, init=False)
    servicepattern_id: Mapped[int] = mapped_column(Integer, nullable=False)
    locality_id: Mapped[str] = mapped_column(String(8), nullable=False)


class TransmodelServicePatternAdminAreas(BaseSQLModel):
    """
    Association Table between:
        - transmodel_servicepattern (TransmodelServicePattern)
        - naptan_adminarea (NaptanAdminArea)
    """

    __tablename__ = "transmodel_servicepattern_admin_areas"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, init=False)
    servicepattern_id: Mapped[int] = mapped_column(Integer, nullable=False)
    adminarea_id: Mapped[int] = mapped_column(Integer, nullable=False)
