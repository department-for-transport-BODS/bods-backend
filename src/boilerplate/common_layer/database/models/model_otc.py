import datetime
from datetime import date, datetime

from common_layer.database.models.common import BaseSQLModel
from sqlalchemy import Boolean, Date, DateTime, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column


class OtcService(BaseSQLModel):

    __tablename__ = "otc_service"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, init=False)
    registration_number: Mapped[str] = mapped_column(String(25))
    variation_number: Mapped[int] = mapped_column(Integer)
    service_number: Mapped[str] = mapped_column(String(1000))
    current_traffic_area: Mapped[str] = mapped_column(String(1))
    start_point: Mapped[str] = mapped_column(Text)
    finish_point: Mapped[str] = mapped_column(Text)
    via: Mapped[str] = mapped_column(Text)
    service_type_other_details: Mapped[str] = mapped_column(Text)
    description: Mapped[str] = mapped_column(String(25))
    registration_status: Mapped[str] = mapped_column(String(20))
    public_text: Mapped[str] = mapped_column(Text)
    service_type_description: Mapped[str] = mapped_column(String(1000))
    subsidies_description: Mapped[str] = mapped_column(String(7))
    subsidies_details: Mapped[str] = mapped_column(Text)
    effective_date: Mapped[date | None] = mapped_column(Date)
    received_date: Mapped[date | None] = mapped_column(Date)
    end_date: Mapped[date | None] = mapped_column(Date)
    registration_code: Mapped[int | None] = mapped_column(Integer)
    short_notice: Mapped[bool | None] = mapped_column(Boolean)
    licence_id: Mapped[int | None] = mapped_column(Integer)
    operator_id: Mapped[int | None] = mapped_column(Integer)
    last_modified: Mapped[datetime | None] = mapped_column(DateTime(True))
    api_type: Mapped[str | None] = mapped_column(Text)
    atco_code: Mapped[str | None] = mapped_column(Text)


class OtcLocalAuthorityRegistrationNumbers(BaseSQLModel):
    __tablename__ = "otc_localauthority_registration_numbers"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        init=False,
    )
    localauthority_id: Mapped[int] = mapped_column(Integer)
    service_id: Mapped[int] = mapped_column(Integer)


class OtcLocalAuthority(BaseSQLModel):
    __tablename__ = "otc_localauthority"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, init=False)
    name: Mapped[str] = mapped_column(Text)
    ui_lta_id: Mapped[int | None] = mapped_column(Integer)
