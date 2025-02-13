"""
Fare Frame
"""

from typing import Annotated

from common_layer.xml.netex.models.data_objects.netex_fare_tariff_fare_structure import (
    DistanceMatrixElement,
)
from pydantic import BaseModel, Field

from ..netex_utility import FromToDate, MultilingualString, VersionedRef
from .netex_data_object_profiles import UserProfile


class ScheduledStopPointRef(VersionedRef):
    """Reference to a scheduled stop point with optional content"""

    content: Annotated[
        str | None,
        Field(
            description="Optional description or name of the stop point", default=None
        ),
    ]


class FareZone(BaseModel):
    """Definition of a fare zone"""

    id: Annotated[str, Field(description="Fare zone identifier")]
    version: Annotated[str, Field(description="Version of the fare zone")]
    Name: Annotated[
        MultilingualString | str, Field(description="Name of the fare zone")
    ]
    members: Annotated[
        list[ScheduledStopPointRef],
        Field(description="list of scheduled stop points in this fare zone"),
    ]


class RoundTrip(BaseModel):
    """Definition of round trip parameters"""

    id: Annotated[str, Field(description="Round trip identifier")]
    version: Annotated[str, Field(description="Version")]
    TripType: Annotated[str, Field(description="Type of trip")]


class FrequencyOfUse(BaseModel):
    """Definition of frequency of use parameters"""

    id: Annotated[str, Field(description="Frequency identifier")]
    version: Annotated[str, Field(description="Version")]
    FrequencyOfUseType: Annotated[str, Field(description="Type of frequency")]


class UsageValidityPeriod(BaseModel):
    """Definition of usage validity period"""

    id: Annotated[str, Field(description="Usage validity period identifier")]
    version: Annotated[str, Field(description="Version")]
    UsageTrigger: Annotated[str, Field(description="Trigger for usage")]
    UsageEnd: Annotated[str, Field(description="End condition")]
    ActivationMeans: Annotated[str, Field(description="Means of activation")]


class GenericParameterAssignment(BaseModel):
    """Definition of generic parameter assignment"""

    id: Annotated[str, Field(description="Parameter assignment identifier")]
    version: Annotated[str, Field(description="Version")]
    order: Annotated[str, Field(description="Order of assignment")]
    TypeOfAccessRightAssignmentRef: Annotated[
        VersionedRef, Field(description="Reference to access right type")
    ]
    ValidityParameterAssignmentType: Annotated[
        str | None,
        Field(description="Type of validity parameter assignment", default=None),
    ]
    LimitationGroupingType: Annotated[
        str | None, Field(description="Type of limitation grouping", default=None)
    ]
    validityParameters: Annotated[
        list[BaseModel] | None,
        Field(description="list of validity parameters", default=None),
    ]
    limitations: Annotated[
        list[UserProfile | RoundTrip | FrequencyOfUse | UsageValidityPeriod] | None,
        Field(description="list of limitations", default=None),
    ]


class FareStructureElement(BaseModel):
    """Definition of a fare structure element"""

    id: Annotated[str, Field(description="Fare structure element identifier")]
    version: Annotated[str, Field(description="Version")]
    Name: Annotated[MultilingualString | str, Field(description="Name of the element")]
    TypeOfFareStructureElementRef: Annotated[
        VersionedRef, Field(description="Reference to element type")
    ]
    distanceMatrixElements: Annotated[
        list[DistanceMatrixElement] | None,
        Field(description="list of distance matrix elements", default=None),
    ]
    GenericParameterAssignment: Annotated[
        GenericParameterAssignment | None,
        Field(description="Parameter assignment", default=None),
    ]


class ValidableElement(BaseModel):
    """Definition of a validable element"""

    id: Annotated[str, Field(description="Validable element identifier")]
    version: Annotated[str, Field(description="Version")]
    Name: Annotated[MultilingualString | str, Field(description="Name of the element")]
    fareStructureElements: Annotated[
        list[VersionedRef], Field(description="References to fare structure elements")
    ]


class AccessRightInProduct(BaseModel):
    """Definition of an access right in product"""

    id: Annotated[str, Field(description="Access right identifier")]
    version: Annotated[str, Field(description="Version")]
    order: Annotated[str, Field(description="Order")]
    ValidableElementRef: Annotated[
        VersionedRef, Field(description="Reference to validable element")
    ]


class ConditionSummary(BaseModel):
    """Summary of fare conditions"""

    FareStructureType: Annotated[str, Field(description="Type of fare structure")]
    TariffBasis: Annotated[str, Field(description="Basis of tariff")]
    IsPersonal: Annotated[bool, Field(description="Whether the fare is personal")]


class PreassignedFareProduct(BaseModel):
    """Definition of a preassigned fare product"""

    id: Annotated[str, Field(description="Product identifier")]
    version: Annotated[str, Field(description="Version")]
    Name: Annotated[MultilingualString | str, Field(description="Name of the product")]
    ChargingMomentRef: Annotated[
        VersionedRef, Field(description="Reference to charging moment")
    ]
    ChargingMomentType: Annotated[str, Field(description="Type of charging moment")]
    TypeOfFareProductRef: Annotated[
        VersionedRef, Field(description="Reference to product type")
    ]
    OperatorRef: Annotated[VersionedRef, Field(description="Reference to operator")]
    ConditionSummary: Annotated[
        ConditionSummary, Field(description="Summary of conditions")
    ]
    validableElements: Annotated[
        list[ValidableElement], Field(description="list of validable elements")
    ]
    accessRightsInProduct: Annotated[
        list[AccessRightInProduct], Field(description="list of access rights")
    ]
    ProductType: Annotated[str, Field(description="Type of product")]


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


class GeographicalIntervalPrice(BaseModel):
    """Definition of a geographical interval price"""

    id: Annotated[str, Field(description="Price identifier")]
    version: Annotated[str, Field(description="Version")]
    Amount: Annotated[float, Field(description="Price amount")]


class PriceGroup(BaseModel):
    """Definition of a price group"""

    id: Annotated[str, Field(description="Price group identifier")]
    version: Annotated[str, Field(description="Version")]
    members: Annotated[
        list[GeographicalIntervalPrice],
        Field(description="list of prices in this group"),
    ]


class FareTableColumn(BaseModel):
    """Definition of a fare table column"""

    id: Annotated[str, Field(description="Column identifier")]
    version: Annotated[str, Field(description="Version")]
    order: Annotated[str, Field(description="Column order")]
    Name: Annotated[MultilingualString | str, Field(description="Column name")]
    representing: Annotated[
        dict[str, VersionedRef],
        Field(description="References for what this column represents"),
    ]


class FareTableRow(BaseModel):
    """Definition of a fare table row"""

    id: Annotated[str, Field(description="Row identifier")]
    version: Annotated[str, Field(description="Version")]
    order: Annotated[str, Field(description="Row order")]
    Name: Annotated[MultilingualString | str, Field(description="Row name")]


class DistanceMatrixElementPrice(BaseModel):
    """Definition of a distance matrix element price"""

    id: Annotated[str, Field(description="Price identifier")]
    version: Annotated[str, Field(description="Version")]
    GeographicalIntervalPriceRef: Annotated[
        VersionedRef, Field(description="Reference to geographical interval price")
    ]
    DistanceMatrixElementRef: Annotated[
        VersionedRef, Field(description="Reference to distance matrix element")
    ]


class Cell(BaseModel):
    """Definition of a fare table cell"""

    id: Annotated[str, Field(description="Cell identifier")]
    version: Annotated[str, Field(description="Version")]
    order: Annotated[str, Field(description="Cell order")]
    DistanceMatrixElementPrice: Annotated[
        DistanceMatrixElementPrice, Field(description="Price for this cell")
    ]
    ColumnRef: Annotated[VersionedRef, Field(description="Reference to column")]
    RowRef: Annotated[VersionedRef, Field(description="Reference to row")]


class NestedFareTable(BaseModel):
    """Definition of a nested fare table"""

    id: Annotated[str, Field(description="Table identifier")]
    version: Annotated[str, Field(description="Version")]
    Name: Annotated[MultilingualString | str, Field(description="Table name")]
    Description: Annotated[
        MultilingualString | str | None,
        Field(description="Table description", default=None),
    ]
    cells: Annotated[list[Cell], Field(description="list of cells in this table")]


class FareTable(BaseModel):
    """Definition of a fare table"""

    id: Annotated[str, Field(description="Table identifier")]
    version: Annotated[str, Field(description="Version")]
    Name: Annotated[MultilingualString | str, Field(description="Table name")]
    Description: Annotated[
        MultilingualString | str | None,
        Field(description="Table description", default=None),
    ]
    pricesFor: Annotated[
        dict[str, VersionedRef],
        Field(description="References for what these prices are for"),
    ]
    usedIn: Annotated[
        dict[str, VersionedRef],
        Field(description="References for where these prices are used"),
    ]
    specifics: Annotated[
        dict[str, VersionedRef], Field(description="Specific references for this table")
    ]
    columns: Annotated[
        list[FareTableColumn], Field(description="list of columns in this table")
    ]
    rows: Annotated[list[FareTableRow], Field(description="list of rows in this table")]
    includes: Annotated[
        list[NestedFareTable], Field(description="list of nested fare tables")
    ]


class PriceUnit(BaseModel):
    """Definition of a price unit (currency)"""

    id: Annotated[str, Field(description="Price unit identifier")]
    version: Annotated[str, Field(description="Version")]
    Name: Annotated[
        MultilingualString | str, Field(description="Name of the price unit")
    ]
    PrivateCode: Annotated[str, Field(description="Currency symbol")]
    Precision: Annotated[int, Field(description="Decimal precision")]


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


class FrameDefaults(BaseModel):
    """Default values for the frame"""

    DefaultCodespaceRef: Annotated[
        VersionedRef, Field(description="Default codespace reference")
    ]
    DefaultDataSourceRef: Annotated[
        VersionedRef, Field(description="Default data source reference")
    ]
    DefaultResponsibilitySetRef: Annotated[
        VersionedRef, Field(description="Default responsibility set reference")
    ]


class Tariff(BaseModel):
    """Definition of a tariff"""

    id: Annotated[str, Field(description="Tariff identifier")]
    version: Annotated[str, Field(description="Version")]
    validityConditions: Annotated[
        list[FromToDate], Field(description="Validity conditions")
    ]
    Name: Annotated[MultilingualString | str, Field(description="Name of the tariff")]
    OperatorRef: Annotated[VersionedRef, Field(description="Reference to operator")]
    LineRef: Annotated[VersionedRef, Field(description="Reference to line")]
    TypeOfTariffRef: Annotated[
        VersionedRef, Field(description="Reference to tariff type")
    ]
    TariffBasis: Annotated[str, Field(description="Basis of tariff")]
    fareStructureElements: Annotated[
        list[FareStructureElement], Field(description="list of fare structure elements")
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
        str, Field(description="Responsibility set reference")
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
        FrameDefaults | None,
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
