from common_layer.database.models.common import BaseSQLModel
from sqlalchemy import Identity, Integer, Text
from sqlalchemy.orm import Mapped, mapped_column


class UiLta(BaseSQLModel):
    __tablename__ = "ui_lta"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, init=False)
    name: Mapped[str] = mapped_column(Text)
