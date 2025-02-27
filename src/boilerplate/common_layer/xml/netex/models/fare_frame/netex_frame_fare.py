"""
Fare Frame
"""

from __future__ import annotations

from typing import Annotated

from common_layer.xml.netex.models.fare_frame.netex_fare_zone import FareZone
from common_layer.xml.netex.models.fare_frame.netex_price_group import PriceGroup
from common_layer.xml.netex.models.fare_frame.netex_sales_offer_package import (
    SalesOfferPackage,
)
from pydantic import BaseModel, Field

from ..data_objects.netex_data_object_profiles import UserProfile
from ..netex_utility import MultilingualString, VersionedRef
from .netex_fare_preassigned import PreassignedFareProduct
from .netex_fare_table import FareTable
from .netex_fare_tariff import Tariff
from .netex_frame_defaults import FrameDefaultsStructure


class DistributionAssignment(BaseModel):
    """Definition of a distribution assignment"""

    id: Annotated[str, Field(description="Assignment identifier")]
    version: Annotated[str, Field(description="Version")]
    order: Annotated[str, Field(description="Order")]
    DistributionChannelRef: Annotated[
        VersionedRef, Field(description="Reference to distribution channel")
    ]
    DistributionChannelType: Annotated[
        str, Field(description="Type of distribution channel")
    ]
    PaymentMethods: Annotated[str, Field(description="Allowed payment methods")]


class PriceUnit(BaseModel):
    """Definition of a price unit (currency)"""

    id: Annotated[str, Field(description="Price unit identifier")]
    version: Annotated[str, Field(description="Version")]
    Name: Annotated[
        MultilingualString | None, Field(description="Name of the price unit")
    ]
    PrivateCode: Annotated[str | None, Field(description="Currency symbol")]
    Precision: Annotated[int | None, Field(description="Decimal precision")]


class PricingParameterSet(BaseModel):
    """Set of pricing parameters"""

    id: Annotated[str, Field(description="Parameter set identifier")]
    version: Annotated[str, Field(description="Version")]
    priceUnits: Annotated[list[PriceUnit], Field(description="list of price units")]


class GeographicalUnit(BaseModel):
    """Definition of a geographical unit"""

    id: Annotated[str, Field(description="Unit identifier")]
    version: Annotated[str, Field(description="Version")]
    Name: Annotated[MultilingualString | str, Field(description="Name of the unit")]


class AlternativeName(BaseModel):
    """Alternative name in different language"""

    id: Annotated[str, Field(description="Name identifier")]
    version: Annotated[str, Field(description="Version")]
    order: Annotated[str, Field(description="Order")]
    Name: Annotated[
        MultilingualString | str, Field(description="Name in specific language")
    ]


class DistributionChannel(BaseModel):
    """Definition of a distribution channel"""

    id: Annotated[str, Field(description="Channel identifier")]
    version: Annotated[str, Field(description="Version")]
    ShortName: Annotated[MultilingualString | str, Field(description="Short name")]
    alternativeNames: Annotated[
        list[AlternativeName] | None,
        Field(description="list of alternative names", default=None),
    ]
    DistributionChannelType: Annotated[str, Field(description="Type of channel")]
    IsObligatory: Annotated[
        bool | None, Field(description="Whether channel is obligatory", default=None)
    ]


class FulfilmentMethod(BaseModel):
    """Definition of a fulfilment method"""

    id: Annotated[str, Field(description="Method identifier")]
    version: Annotated[str, Field(description="Version")]
    Name: Annotated[MultilingualString | str, Field(description="Name of the method")]
    FulfilmentMethodType: Annotated[str, Field(description="Type of fulfilment")]
    RequiresBookingReference: Annotated[
        bool | None,
        Field(description="Whether booking reference is required", default=None),
    ]
    typesOfTravelDocument: Annotated[
        list[VersionedRef], Field(description="References to travel document types")
    ]


class TypeOfTravelDocument(BaseModel):
    """Definition of a travel document type"""

    id: Annotated[str, Field(description="Document type identifier")]
    version: Annotated[str, Field(description="Version")]
    Name: Annotated[
        MultilingualString | str | None,
        Field(description="Name of document type", default=None),
    ]
    MediaType: Annotated[str, Field(description="Type of media")]
    MachineReadable: Annotated[
        str | None, Field(description="Machine readability type", default=None)
    ]


class FareFrame(BaseModel):
    """
    A frame containing fare-related definitions. Can contain various combinations
    of components depending on the frame type.
    """

    # Required attributes
    id: Annotated[str, Field(description="Frame identifier")]
    version: Annotated[str, Field(description="Version")]
    responsibilitySetRef: Annotated[
        str | None, Field(description="Responsibility set reference")
    ]

    # Optional core attributes
    Name: Annotated[
        MultilingualString | str | None,
        Field(description="Name of the frame", default=None),
    ]
    Description: Annotated[
        MultilingualString | str | None,
        Field(description="Description of the frame", default=None),
    ]
    TypeOfFrameRef: Annotated[
        VersionedRef | None, Field(description="Reference to frame type", default=None)
    ]
    dataSourceRef: Annotated[
        str | None, Field(description="Reference to data source", default=None)
    ]

    # Optional components based on frame type
    FrameDefaults: Annotated[
        FrameDefaultsStructure | None,
        Field(description="Default values for the frame", default=None),
    ]
    PricingParameterSet: Annotated[
        PricingParameterSet | None,
        Field(description="Pricing parameters", default=None),
    ]
    geographicalUnits: Annotated[
        list[GeographicalUnit] | None,
        Field(description="list of geographical units", default=None),
    ]
    usageParameters: Annotated[
        list[UserProfile] | None,
        Field(description="list of user profiles", default=None),
    ]
    distributionChannels: Annotated[
        list[DistributionChannel] | None,
        Field(description="list of distribution channels", default=None),
    ]
    fulfilmentMethods: Annotated[
        list[FulfilmentMethod] | None,
        Field(description="list of fulfilment methods", default=None),
    ]
    typesOfTravelDocuments: Annotated[
        list[TypeOfTravelDocument] | None,
        Field(description="list of travel document types", default=None),
    ]
    fareZones: Annotated[
        list[FareZone] | None, Field(description="list of fare zones", default=None)
    ]
    tariffs: Annotated[
        list[Tariff] | None, Field(description="list of tariffs", default=None)
    ]
    fareProducts: Annotated[
        list[PreassignedFareProduct] | None,
        Field(description="list of fare products", default=None),
    ]
    priceGroups: Annotated[
        list[PriceGroup] | None, Field(description="list of price groups", default=None)
    ]
    fareTables: Annotated[
        list[FareTable] | None, Field(description="list of fare tables", default=None)
    ]
    salesOfferPackages: Annotated[
        list[SalesOfferPackage] | None,
        Field(description="list of sales offer packages", default=None),
    ]
