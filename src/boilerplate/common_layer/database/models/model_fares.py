"""
SQL Alchemy models for tables starting with fares_
"""

from __future__ import annotations

from datetime import date, datetime

from common_layer.xml.netex.models.netex_types import (
    PreassignedFareProductTypeT,
    TariffBasisT,
    UserTypeT,
)
from sqlalchemy import (
    ARRAY,
    BigInteger,
    CheckConstraint,
    Date,
    DateTime,
    ForeignKey,
    Integer,
    String,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column

from .common import BaseSQLModel, CreatedTimeStampMixin


class FaresMetadata(BaseSQLModel):
    """Fares Metadata Table"""

    __tablename__ = "fares_faresmetadata"

    datasetmetadata_ptr_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("organisation_datasetmetadata.id"),
        primary_key=True,
        init=False,
        autoincrement=False,
    )
    num_of_fare_zones: Mapped[int] = mapped_column(
        Integer, CheckConstraint("num_of_fare_zones >= 0"), nullable=False
    )
    num_of_lines: Mapped[int] = mapped_column(
        Integer, CheckConstraint("num_of_lines >= 0"), nullable=False
    )
    num_of_sales_offer_packages: Mapped[int] = mapped_column(
        Integer, CheckConstraint("num_of_sales_offer_packages >= 0"), nullable=False
    )
    num_of_fare_products: Mapped[int] = mapped_column(
        Integer, CheckConstraint("num_of_fare_products >= 0"), nullable=False
    )
    num_of_user_profiles: Mapped[int] = mapped_column(
        Integer, CheckConstraint("num_of_user_profiles >= 0"), nullable=False
    )
    valid_from: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    valid_to: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    num_of_pass_products: Mapped[int | None] = mapped_column(
        Integer, CheckConstraint("num_of_pass_products >= 0"), nullable=True
    )
    num_of_trip_products: Mapped[int | None] = mapped_column(
        Integer, CheckConstraint("num_of_trip_products >= 0"), nullable=True
    )


class FaresMetadataStop(BaseSQLModel):
    """Fares Metadata Stops Table"""

    __tablename__ = "fares_faresmetadata_stops"
    __table_args__ = (
        UniqueConstraint(
            "faresmetadata_id", "stoppoint_id", name="uq_faresmetadata_stoppoint"
        ),
    )

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        init=False,
    )
    faresmetadata_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("fares_faresmetadata.datasetmetadata_ptr_id"),
        nullable=False,
        index=True,
    )
    stoppoint_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("naptan_stoppoint.id"), nullable=False, index=True
    )


class FaresDataCatalogueMetadata(BaseSQLModel):
    """Fares Data Catalogue Metadata Table"""

    __tablename__ = "fares_datacataloguemetadata"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        init=False,
    )
    xml_file_name: Mapped[str] = mapped_column(String(255), nullable=False)
    valid_from: Mapped[date | None] = mapped_column(Date, nullable=True)
    valid_to: Mapped[date | None] = mapped_column(Date, nullable=True)
    national_operator_code: Mapped[list[str]] = mapped_column(
        ARRAY(String(255)), nullable=True
    )
    line_id: Mapped[list[str] | None] = mapped_column(ARRAY(String(100)), nullable=True)
    line_name: Mapped[list[str] | None] = mapped_column(
        ARRAY(String(100)), nullable=True
    )
    atco_area: Mapped[list[int] | None] = mapped_column(ARRAY(Integer), nullable=True)
    tariff_basis: Mapped[list[TariffBasisT] | None] = mapped_column(
        ARRAY(String(100)), nullable=True
    )
    product_type: Mapped[list[PreassignedFareProductTypeT] | None] = mapped_column(
        ARRAY(String(100)), nullable=True
    )
    product_name: Mapped[list[str] | None] = mapped_column(
        ARRAY(String(100)), nullable=True
    )
    user_type: Mapped[list[UserTypeT] | None] = mapped_column(
        ARRAY(String(100)), nullable=True
    )
    fares_metadata_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("fares_faresmetadata.datasetmetadata_ptr_id"),
        nullable=False,
        index=True,
        init=False,
    )


class FaresValidation(BaseSQLModel):
    """Fares Validation Table"""

    __tablename__ = "fares_validator_faresvalidation"

    id: Mapped[int] = mapped_column(
        BigInteger,
        primary_key=True,
        init=False,
    )
    file_name: Mapped[str] = mapped_column(String(256), nullable=False)
    error_line_no: Mapped[int] = mapped_column(Integer, nullable=False)
    type_of_observation: Mapped[str] = mapped_column(String(1024), nullable=False)
    category: Mapped[str] = mapped_column(String(1024), nullable=False)
    error: Mapped[str] = mapped_column(String(2000), nullable=False)
    reference: Mapped[str] = mapped_column(String(1024), nullable=False)
    important_note: Mapped[str] = mapped_column(String(2000), nullable=False)
    organisation_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("organisation_organisation.id"),
        nullable=False,
        index=True,
    )
    revision_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("organisation_datasetrevision.id"),
        nullable=False,
        index=True,
    )


class FaresValidationResult(CreatedTimeStampMixin, BaseSQLModel):
    """Fares Validation Result Table"""

    __tablename__ = "fares_validator_faresvalidationresult"

    id: Mapped[int] = mapped_column(
        BigInteger,
        primary_key=True,
        init=False,
    )
    count: Mapped[int] = mapped_column(Integer, nullable=False)
    report_file_name: Mapped[str] = mapped_column(String(256), nullable=False)
    organisation_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("organisation_organisation.id"),
        nullable=False,
        index=True,
    )
    revision_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("organisation_datasetrevision.id"),
        nullable=False,
        unique=True,
    )
