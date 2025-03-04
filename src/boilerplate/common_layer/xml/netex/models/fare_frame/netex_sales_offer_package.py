"""
Sales Offer Package
"""

from typing import Annotated

from pydantic import BaseModel, Field


class SalesOfferPackage(BaseModel):
    """Definition of a sales offer package"""

    id: Annotated[str, Field(description="Sales offer package identifier")]
    version: Annotated[str, Field(description="Version")]
