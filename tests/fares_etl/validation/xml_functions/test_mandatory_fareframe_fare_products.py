import pytest

from fares_etl.validation.app.xml_functions.mandatory_fareframe_fare_products import (
    check_access_right_elements,
    check_fare_product_validable_elements,
    check_fare_products,
    check_fare_products_charging_type,
    check_fare_products_type_ref,
    check_product_type,
)

from ..helpers import get_lxml_element

X_PATH_PREASSIGNED = "//x:dataObjects/x:CompositeFrame/x:frames/x:FareFrame/x:fareProducts/x:PreassignedFareProduct"
X_PATH_AMOUNT_OF_PRICE_UNIT = "//x:dataObjects/x:CompositeFrame/x:frames/x:FareFrame/x:fareProducts/x:AmountOfPriceUnitProduct"


@pytest.mark.parametrize(
    (
        "type_of_frame_ref_ref_present",
        "type_of_frame_ref_ref_valid",
        "fare_products",
        "fare_product_tag",
        "preassigned_fare_product",
        "name",
        "expected",
    ),
    [
        (True, True, True, "PreassignedFareProduct", True, True, ""),
        (
            False,
            False,
            False,
            "PreassignedFareProduct",
            False,
            False,
            "",
        ),
        (True, False, False, "PreassignedFareProduct", False, False, ""),
        (
            True,
            True,
            False,
            "PreassignedFareProduct",
            False,
            False,
            [
                "7",
                "'fareProducts' and it's child elements is missing"
                " from 'FareFrame' - UK_PI_FARE_PRODUCT",
            ],
        ),
        (
            True,
            True,
            True,
            "PreassignedFareProduct",
            False,
            False,
            [
                "9",
                "'PreassignedFareProduct' and it's child elements in"
                " 'fareProducts' for 'FareFrame' - UK_PI_FARE_PRODUCT",
            ],
        ),
        (
            True,
            True,
            True,
            "PreassignedFareProduct",
            True,
            False,
            [
                "10",
                "'Name' missing from 'PreassignedFareProduct' "
                "in 'fareProducts' for 'FareFrame' - UK_PI_FARE_PRODUCT",
            ],
        ),
        (True, True, True, "AmountOfPriceUnitProduct", True, True, ""),
        (
            False,
            False,
            False,
            "AmountOfPriceUnitProduct",
            False,
            False,
            "",
        ),
        (True, False, False, "AmountOfPriceUnitProduct", False, False, ""),
        (
            True,
            True,
            False,
            "AmountOfPriceUnitProduct",
            False,
            False,
            [
                "7",
                "'fareProducts' and it's child elements is missing"
                " from 'FareFrame' - UK_PI_FARE_PRODUCT",
            ],
        ),
        (
            True,
            True,
            True,
            "AmountOfPriceUnitProduct",
            True,
            False,
            [
                "10",
                "'Name' missing from 'AmountOfPriceUnitProduct' "
                "in 'fareProducts' for 'FareFrame' - UK_PI_FARE_PRODUCT",
            ],
        ),
    ],
)
def test_preassigned_fare_products(
    type_of_frame_ref_ref_present: bool,
    type_of_frame_ref_ref_valid: bool,
    fare_products: bool,
    fare_product_tag: str,
    preassigned_fare_product: bool,
    name: bool,
    expected: list[str],
):
    """
    Test if mandatory element 'PreassignedFareProduct' and 'AmountOfPriceUnitProduct' missing in
    fareProducts for FareFrame - UK_PI_FARE_PRODUCT
    FareFrame UK_PI_FARE_PRODUCT is mandatory
    """
    fare_product_type = "other"
    if fare_product_tag == "AmountOfPriceUnitProduct":
        fare_product_type = "tripCarnet"

    fare_frame_with_all_children_properties = f"""
    <FareFrame version="1.0" id="epd:UK:FSYO:FareFrame_UK_PI_FARE_PRODUCT:Line_9_Outbound:op" dataSourceRef="data_source" responsibilitySetRef="tariffs">
        <TypeOfFrameRef ref="fxc:UK:DFT:TypeOfFrame_UK_PI_FARE_PRODUCT:FXCP" version="fxc:v1.0" />
        <fareProducts>
            <{fare_product_tag} id="Trip@AdultSingle" version="1.0">
                <Name>Adult Single</Name>
                <ProductType>{fare_product_type}</ProductType>
            </{fare_product_tag}>
        </fareProducts>
    </FareFrame>
    """

    fare_frame_type_of_frame_ref_not_present = f"""
    <FareFrame version="1.0" id="epd:UK:FSYO:FareFrame_UK_PI_FARE_PRODUCT:Line_9_Outbound:op" dataSourceRef="data_source" responsibilitySetRef="tariffs">
        <TypeOfFrameRef />
        <fareProducts>
            <{fare_product_tag} id="Trip@AdultSingle" version="1.0">
                <Name>Adult Single</Name>
                <ProductType>{fare_product_type}</ProductType>
            </{fare_product_tag}>
        </fareProducts>
    </FareFrame>
    """

    fare_frame_type_of_frame_ref_not_valid = """
    <FareFrame version="1.0" id="epd:UK:FSYO:FareFrame_UK_PI_FARE_PRODUCT:Line_9_Outbound:op" dataSourceRef="data_source" responsibilitySetRef="tariffs">
        <TypeOfFrameRef ref="fxc:UK:DFT:TypeOfFrame_UK_NETW:FXCP" version="fxc:v1.0" />
    </FareFrame>
    """

    fare_frame_without_fare_products = """
    <FareFrame version="1.0" id="epd:UK:FSYO:FareFrame_UK_PI_FARE_PRODUCT:Line_9_Outbound:op" dataSourceRef="data_source" responsibilitySetRef="tariffs">
        <TypeOfFrameRef ref="fxc:UK:DFT:TypeOfFrame_UK_PI_FARE_PRODUCT:FXCP" version="fxc:v1.0" />
    </FareFrame>
    """

    fare_frame_without_preassigned_fare_product = """
    <FareFrame version="1.0" id="epd:UK:FSYO:FareFrame_UK_PI_FARE_PRODUCT:Line_9_Outbound:op" dataSourceRef="data_source" responsibilitySetRef="tariffs">
        <TypeOfFrameRef ref="fxc:UK:DFT:TypeOfFrame_UK_PI_FARE_PRODUCT:FXCP" version="fxc:v1.0" />
        <fareProducts>
        </fareProducts>
    </FareFrame>
    """

    fare_frame_without_name = f"""
    <FareFrame version="1.0" id="epd:UK:FSYO:FareFrame_UK_PI_FARE_PRODUCT:Line_9_Outbound:op" dataSourceRef="data_source" responsibilitySetRef="tariffs">
        <TypeOfFrameRef ref="fxc:UK:DFT:TypeOfFrame_UK_PI_FARE_PRODUCT:FXCP" version="fxc:v1.0" />
        <fareProducts>
            <{fare_product_tag} id="Trip@AdultSingle" version="1.0">
                <ProductType>{fare_product_type}</ProductType>
            </{fare_product_tag}>
        </fareProducts>
    </FareFrame>
    """

    frames = """
    <PublicationDelivery version="1.1" xsi:schemaLocation="http://www.netex.org.uk/netex http://netex.uk/netex/schema/1.09c/xsd/NeTEx_publication.xsd" xmlns="http://www.netex.org.uk/netex" xmlns:siri="http://www.siri.org.uk/siri" xmlns:gml="http://www.opengis.net/gml/3.2" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">
        <dataObjects>
            <CompositeFrame id="epd:UK:FYOR:CompositeFrame_UK_PI_LINE_FARE_OFFER:Trip@Line_1_Inbound:op">
                <frames>
                    {0}
                </frames>
            </CompositeFrame>
        </dataObjects>
    </PublicationDelivery>
    """

    if type_of_frame_ref_ref_present:
        if type_of_frame_ref_ref_valid:
            if fare_products:
                if preassigned_fare_product:
                    if name:
                        xml = frames.format(fare_frame_with_all_children_properties)
                    else:
                        xml = frames.format(fare_frame_without_name)
                else:
                    xml = frames.format(fare_frame_without_preassigned_fare_product)
            else:
                xml = frames.format(fare_frame_without_fare_products)
        else:
            xml = frames.format(fare_frame_type_of_frame_ref_not_valid)
    else:
        xml = frames.format(fare_frame_type_of_frame_ref_not_present)

    xpath = "//x:dataObjects/x:CompositeFrame/x:frames/x:FareFrame"
    fare_frames = get_lxml_element(xpath, xml)
    response = check_fare_products(None, fare_frames)
    assert response == expected


@pytest.mark.parametrize(
    (
        "type_of_frame_ref_ref_present",
        "type_of_frame_ref_ref_valid",
        "type_of_fare_product",
        "expected",
    ),
    [
        (True, True, True, ""),
        (
            False,
            False,
            False,
            "",
        ),
        (True, False, False, ""),
        (
            True,
            True,
            False,
            [
                "10",
                "'TypeOfFareProductRef' missing from 'PreassignedFareProduct' "
                "in 'fareProducts' for 'FareFrame' - UK_PI_FARE_PRODUCT",
            ],
        ),
    ],
)
def test_preassigned_fare_products_type_ref(
    type_of_frame_ref_ref_present: bool,
    type_of_frame_ref_ref_valid: bool,
    type_of_fare_product: bool,
    expected: list[str],
):
    """
    Test if mandatory element is 'TypeOfFareProductRef' present
    in PreassignedFareProduct for FareFrame - UK_PI_FARE_PRODUCT
    FareFrame UK_PI_FARE_PRODUCT is mandatory
    """
    fare_frame_with_all_children_properties = """
    <FareFrame version="1.0" id="epd:UK:FSYO:FareFrame_UK_PI_FARE_PRODUCT:Line_9_Outbound:op" dataSourceRef="data_source" responsibilitySetRef="tariffs">
        <TypeOfFrameRef ref="fxc:UK:DFT:TypeOfFrame_UK_PI_FARE_PRODUCT:FXCP" version="fxc:v1.0" />
        <fareProducts>
            <PreassignedFareProduct id="Trip@AdultSingle" version="1.0">
                <TypeOfFareProductRef version="1.0" ref="fxc:standard_product@trip@single"/>
            </PreassignedFareProduct>
        </fareProducts>
    </FareFrame>
    """

    fare_frame_type_of_frame_ref_not_present = """
    <FareFrame version="1.0" id="epd:UK:FSYO:FareFrame_UK_PI_FARE_PRODUCT:Line_9_Outbound:op" dataSourceRef="data_source" responsibilitySetRef="tariffs">
        <TypeOfFrameRef />
        <fareProducts>
            <PreassignedFareProduct id="Trip@AdultSingle" version="1.0">
                <TypeOfFareProductRef version="1.0" ref="fxc:standard_product@trip@single"/>
            </PreassignedFareProduct>
        </fareProducts>
    </FareFrame>
    """

    fare_frame_type_of_frame_ref_not_valid = """
    <FareFrame version="1.0" id="epd:UK:FSYO:FareFrame_UK_PI_FARE_PRODUCT:Line_9_Outbound:op" dataSourceRef="data_source" responsibilitySetRef="tariffs">
        <TypeOfFrameRef ref="fxc:UK:DFT:TypeOfFrame_UK_NETW:FXCP" version="fxc:v1.0" />
        <fareProducts>
            <PreassignedFareProduct id="Trip@AdultSingle" version="1.0">
            </PreassignedFareProduct>
        </fareProducts>
    </FareFrame>
    """

    fare_frame_without_type_of_fare_product_ref = """
    <FareFrame version="1.0" id="epd:UK:FSYO:FareFrame_UK_PI_FARE_PRODUCT:Line_9_Outbound:op" dataSourceRef="data_source" responsibilitySetRef="tariffs">
        <TypeOfFrameRef ref="fxc:UK:DFT:TypeOfFrame_UK_PI_FARE_PRODUCT:FXCP" version="fxc:v1.0" />
        <fareProducts>
            <PreassignedFareProduct id="Trip@AdultSingle" version="1.0">
            </PreassignedFareProduct>
        </fareProducts>
    </FareFrame>
    """

    frames = """
    <PublicationDelivery version="1.1" xsi:schemaLocation="http://www.netex.org.uk/netex http://netex.uk/netex/schema/1.09c/xsd/NeTEx_publication.xsd" xmlns="http://www.netex.org.uk/netex" xmlns:siri="http://www.siri.org.uk/siri" xmlns:gml="http://www.opengis.net/gml/3.2" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">
        <dataObjects>
            <CompositeFrame id="epd:UK:FYOR:CompositeFrame_UK_PI_LINE_FARE_OFFER:Trip@Line_1_Inbound:op">
                <frames>
                    {0}
                </frames>
            </CompositeFrame>
        </dataObjects>
    </PublicationDelivery>
    """

    if type_of_frame_ref_ref_present:
        if type_of_frame_ref_ref_valid:
            if type_of_fare_product:
                xml = frames.format(fare_frame_with_all_children_properties)
            else:
                xml = frames.format(fare_frame_without_type_of_fare_product_ref)
        else:
            xml = frames.format(fare_frame_type_of_frame_ref_not_valid)
    else:
        xml = frames.format(fare_frame_type_of_frame_ref_not_present)

    preassigned_fare_products = get_lxml_element(X_PATH_PREASSIGNED, xml)
    response = check_fare_products_type_ref(None, preassigned_fare_products)
    assert response == expected


@pytest.mark.parametrize(
    (
        "type_of_frame_ref_ref_present",
        "type_of_frame_ref_ref_valid",
        "type_of_fare_product",
        "expected",
    ),
    [
        (True, True, True, ""),
        (
            False,
            False,
            False,
            "",
        ),
        (True, False, False, ""),
        (
            True,
            True,
            False,
            [
                "10",
                "'TypeOfFareProductRef' missing from 'AmountOfPriceUnitProduct' "
                "in 'fareProducts' for 'FareFrame' - UK_PI_FARE_PRODUCT",
            ],
        ),
    ],
)
def test_amountofpriceunit_fare_products_type_ref(
    type_of_frame_ref_ref_present: bool,
    type_of_frame_ref_ref_valid: bool,
    type_of_fare_product: bool,
    expected: list[str],
):
    """
    Test if mandatory element is 'TypeOfFareProductRef' present
    in AmountOfPriceUnitProduct for FareFrame - UK_PI_FARE_PRODUCT
    FareFrame UK_PI_FARE_PRODUCT is mandatory
    """
    fare_frame_with_all_children_properties = """
    <FareFrame version="1.0" id="epd:UK:FSYO:FareFrame_UK_PI_FARE_PRODUCT:Line_9_Outbound:op" dataSourceRef="data_source" responsibilitySetRef="tariffs">
        <TypeOfFrameRef ref="fxc:UK:DFT:TypeOfFrame_UK_PI_FARE_PRODUCT:FXCP" version="fxc:v1.0" />
        <fareProducts>
            <AmountOfPriceUnitProduct id="Trip@AdultSingle" version="1.0">
                <TypeOfFareProductRef version="1.0" ref="fxc:standard_product@trip@single"/>
            </AmountOfPriceUnitProduct>
        </fareProducts>
    </FareFrame>
    """

    fare_frame_type_of_frame_ref_not_present = """
    <FareFrame version="1.0" id="epd:UK:FSYO:FareFrame_UK_PI_FARE_PRODUCT:Line_9_Outbound:op" dataSourceRef="data_source" responsibilitySetRef="tariffs">
        <TypeOfFrameRef />
        <fareProducts>
            <AmountOfPriceUnitProduct id="Trip@AdultSingle" version="1.0">
                <TypeOfFareProductRef version="1.0" ref="fxc:standard_product@trip@single"/>
            </AmountOfPriceUnitProduct>
        </fareProducts>
    </FareFrame>
    """

    fare_frame_type_of_frame_ref_not_valid = """
    <FareFrame version="1.0" id="epd:UK:FSYO:FareFrame_UK_PI_FARE_PRODUCT:Line_9_Outbound:op" dataSourceRef="data_source" responsibilitySetRef="tariffs">
        <TypeOfFrameRef ref="fxc:UK:DFT:TypeOfFrame_UK_NETW:FXCP" version="fxc:v1.0" />
        <fareProducts>
            <AmountOfPriceUnitProduct id="Trip@AdultSingle" version="1.0">
            </AmountOfPriceUnitProduct>
        </fareProducts>
    </FareFrame>
    """

    fare_frame_without_type_of_fare_product_ref = """
    <FareFrame version="1.0" id="epd:UK:FSYO:FareFrame_UK_PI_FARE_PRODUCT:Line_9_Outbound:op" dataSourceRef="data_source" responsibilitySetRef="tariffs">
        <TypeOfFrameRef ref="fxc:UK:DFT:TypeOfFrame_UK_PI_FARE_PRODUCT:FXCP" version="fxc:v1.0" />
        <fareProducts>
            <AmountOfPriceUnitProduct id="Trip@AdultSingle" version="1.0">
            </AmountOfPriceUnitProduct>
        </fareProducts>
    </FareFrame>
    """

    frames = """
    <PublicationDelivery version="1.1" xsi:schemaLocation="http://www.netex.org.uk/netex http://netex.uk/netex/schema/1.09c/xsd/NeTEx_publication.xsd" xmlns="http://www.netex.org.uk/netex" xmlns:siri="http://www.siri.org.uk/siri" xmlns:gml="http://www.opengis.net/gml/3.2" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">
        <dataObjects>
            <CompositeFrame id="epd:UK:FYOR:CompositeFrame_UK_PI_LINE_FARE_OFFER:Trip@Line_1_Inbound:op">
                <frames>
                    {0}
                </frames>
            </CompositeFrame>
        </dataObjects>
    </PublicationDelivery>
    """

    if type_of_frame_ref_ref_present:
        if type_of_frame_ref_ref_valid:
            if type_of_fare_product:
                xml = frames.format(fare_frame_with_all_children_properties)
            else:
                xml = frames.format(fare_frame_without_type_of_fare_product_ref)
        else:
            xml = frames.format(fare_frame_type_of_frame_ref_not_valid)
    else:
        xml = frames.format(fare_frame_type_of_frame_ref_not_present)

    fare_products = get_lxml_element(X_PATH_AMOUNT_OF_PRICE_UNIT, xml)
    response = check_fare_products_type_ref(None, fare_products)
    assert response == expected


@pytest.mark.parametrize(
    (
        "type_of_frame_ref_ref_present",
        "type_of_frame_ref_ref_valid",
        "charging_moment_type",
        "expected",
    ),
    [
        (True, True, True, ""),
        (
            False,
            False,
            False,
            "",
        ),
        (True, False, False, ""),
        (
            True,
            True,
            False,
            [
                "10",
                "'ChargingMomentType' missing from 'PreassignedFareProduct'"
                " in 'fareProducts' for 'FareFrame' - UK_PI_FARE_PRODUCT",
            ],
        ),
    ],
)
def test_preassigned_fare_products_charging_type(
    type_of_frame_ref_ref_present: bool,
    type_of_frame_ref_ref_valid: bool,
    charging_moment_type: bool,
    expected: list[str],
):
    """
    Test if mandatory element is 'ChargingMomentType' present in
    PreassignedFareProduct for FareFrame - UK_PI_FARE_PRODUCT
    FareFrame UK_PI_FARE_PRODUCT is mandatory
    """
    fare_frame_with_all_children_properties = """
    <FareFrame version="1.0" id="epd:UK:FSYO:FareFrame_UK_PI_FARE_PRODUCT:Line_9_Outbound:op" dataSourceRef="data_source" responsibilitySetRef="tariffs">
        <TypeOfFrameRef ref="fxc:UK:DFT:TypeOfFrame_UK_PI_FARE_PRODUCT:FXCP" version="fxc:v1.0" />
        <fareProducts>
            <PreassignedFareProduct id="Trip@AdultSingle" version="1.0">
                <ChargingMomentType>beforeTravel</ChargingMomentType>
            </PreassignedFareProduct>
        </fareProducts>
    </FareFrame>
    """

    fare_frame_type_of_frame_ref_not_present = """
    <FareFrame version="1.0" id="epd:UK:FSYO:FareFrame_UK_PI_FARE_PRODUCT:Line_9_Outbound:op" dataSourceRef="data_source" responsibilitySetRef="tariffs">
        <TypeOfFrameRef />
        <fareProducts>
            <PreassignedFareProduct id="Trip@AdultSingle" version="1.0">
                <ChargingMomentType>beforeTravel</ChargingMomentType>
            </PreassignedFareProduct>
        </fareProducts>
    </FareFrame>
    """

    fare_frame_type_of_frame_ref_not_valid = """
    <FareFrame version="1.0" id="epd:UK:FSYO:FareFrame_UK_PI_FARE_PRODUCT:Line_9_Outbound:op" dataSourceRef="data_source" responsibilitySetRef="tariffs">
        <TypeOfFrameRef ref="fxc:UK:DFT:TypeOfFrame_UK_NETW:FXCP" version="fxc:v1.0" />
        <fareProducts>
            <PreassignedFareProduct id="Trip@AdultSingle" version="1.0">
            </PreassignedFareProduct>
        </fareProducts>
    </FareFrame>
    """

    fare_frame_without_charging_moment_type = """
    <FareFrame version="1.0" id="epd:UK:FSYO:FareFrame_UK_PI_FARE_PRODUCT:Line_9_Outbound:op" dataSourceRef="data_source" responsibilitySetRef="tariffs">
        <TypeOfFrameRef ref="fxc:UK:DFT:TypeOfFrame_UK_PI_FARE_PRODUCT:FXCP" version="fxc:v1.0" />
        <fareProducts>
            <PreassignedFareProduct id="Trip@AdultSingle" version="1.0">
            </PreassignedFareProduct>
        </fareProducts>
    </FareFrame>
    """

    frames = """
    <PublicationDelivery version="1.1" xsi:schemaLocation="http://www.netex.org.uk/netex http://netex.uk/netex/schema/1.09c/xsd/NeTEx_publication.xsd" xmlns="http://www.netex.org.uk/netex" xmlns:siri="http://www.siri.org.uk/siri" xmlns:gml="http://www.opengis.net/gml/3.2" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">
        <dataObjects>
            <CompositeFrame id="epd:UK:FYOR:CompositeFrame_UK_PI_LINE_FARE_OFFER:Trip@Line_1_Inbound:op">
                <frames>
                    {0}
                </frames>
            </CompositeFrame>
        </dataObjects>
    </PublicationDelivery>
    """

    if type_of_frame_ref_ref_present:
        if type_of_frame_ref_ref_valid:
            if charging_moment_type:
                xml = frames.format(fare_frame_with_all_children_properties)
            else:
                xml = frames.format(fare_frame_without_charging_moment_type)
        else:
            xml = frames.format(fare_frame_type_of_frame_ref_not_valid)
    else:
        xml = frames.format(fare_frame_type_of_frame_ref_not_present)

    preassigned_fare_products = get_lxml_element(X_PATH_PREASSIGNED, xml)
    response = check_fare_products_charging_type(None, preassigned_fare_products)
    assert response == expected


@pytest.mark.parametrize(
    (
        "type_of_frame_ref_ref_present",
        "type_of_frame_ref_ref_valid",
        "charging_moment_type",
        "expected",
    ),
    [
        (True, True, True, ""),
        (
            False,
            False,
            False,
            "",
        ),
        (True, False, False, ""),
        (
            True,
            True,
            False,
            [
                "10",
                "'ChargingMomentType' missing from 'AmountOfPriceUnitProduct'"
                " in 'fareProducts' for 'FareFrame' - UK_PI_FARE_PRODUCT",
            ],
        ),
    ],
)
def test_amountofpriceunit_fare_products_charging_type(
    type_of_frame_ref_ref_present: bool,
    type_of_frame_ref_ref_valid: bool,
    charging_moment_type: bool,
    expected: list[str],
):
    """
    Test if mandatory element is 'ChargingMomentType' present in
    AmountOfPriceUnitProduct for FareFrame - UK_PI_FARE_PRODUCT
    FareFrame UK_PI_FARE_PRODUCT is mandatory
    """
    fare_frame_with_all_children_properties = """
    <FareFrame version="1.0" id="epd:UK:FSYO:FareFrame_UK_PI_FARE_PRODUCT:Line_9_Outbound:op" dataSourceRef="data_source" responsibilitySetRef="tariffs">
        <TypeOfFrameRef ref="fxc:UK:DFT:TypeOfFrame_UK_PI_FARE_PRODUCT:FXCP" version="fxc:v1.0" />
        <fareProducts>
            <AmountOfPriceUnitProduct id="Trip@AdultSingle" version="1.0">
                <ChargingMomentType>beforeTravel</ChargingMomentType>
            </AmountOfPriceUnitProduct>
        </fareProducts>
    </FareFrame>
    """

    fare_frame_type_of_frame_ref_not_present = """
    <FareFrame version="1.0" id="epd:UK:FSYO:FareFrame_UK_PI_FARE_PRODUCT:Line_9_Outbound:op" dataSourceRef="data_source" responsibilitySetRef="tariffs">
        <TypeOfFrameRef />
        <fareProducts>
            <AmountOfPriceUnitProduct id="Trip@AdultSingle" version="1.0">
                <ChargingMomentType>beforeTravel</ChargingMomentType>
            </AmountOfPriceUnitProduct>
        </fareProducts>
    </FareFrame>
    """

    fare_frame_type_of_frame_ref_not_valid = """
    <FareFrame version="1.0" id="epd:UK:FSYO:FareFrame_UK_PI_FARE_PRODUCT:Line_9_Outbound:op" dataSourceRef="data_source" responsibilitySetRef="tariffs">
        <TypeOfFrameRef ref="fxc:UK:DFT:TypeOfFrame_UK_NETW:FXCP" version="fxc:v1.0" />
        <fareProducts>
            <AmountOfPriceUnitProduct id="Trip@AdultSingle" version="1.0">
            </AmountOfPriceUnitProduct>
        </fareProducts>
    </FareFrame>
    """

    fare_frame_without_charging_moment_type = """
    <FareFrame version="1.0" id="epd:UK:FSYO:FareFrame_UK_PI_FARE_PRODUCT:Line_9_Outbound:op" dataSourceRef="data_source" responsibilitySetRef="tariffs">
        <TypeOfFrameRef ref="fxc:UK:DFT:TypeOfFrame_UK_PI_FARE_PRODUCT:FXCP" version="fxc:v1.0" />
        <fareProducts>
            <AmountOfPriceUnitProduct id="Trip@AdultSingle" version="1.0">
            </AmountOfPriceUnitProduct>
        </fareProducts>
    </FareFrame>
    """

    frames = """
    <PublicationDelivery version="1.1" xsi:schemaLocation="http://www.netex.org.uk/netex http://netex.uk/netex/schema/1.09c/xsd/NeTEx_publication.xsd" xmlns="http://www.netex.org.uk/netex" xmlns:siri="http://www.siri.org.uk/siri" xmlns:gml="http://www.opengis.net/gml/3.2" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">
        <dataObjects>
            <CompositeFrame id="epd:UK:FYOR:CompositeFrame_UK_PI_LINE_FARE_OFFER:Trip@Line_1_Inbound:op">
                <frames>
                    {0}
                </frames>
            </CompositeFrame>
        </dataObjects>
    </PublicationDelivery>
    """

    if type_of_frame_ref_ref_present:
        if type_of_frame_ref_ref_valid:
            if charging_moment_type:
                xml = frames.format(fare_frame_with_all_children_properties)
            else:
                xml = frames.format(fare_frame_without_charging_moment_type)
        else:
            xml = frames.format(fare_frame_type_of_frame_ref_not_valid)
    else:
        xml = frames.format(fare_frame_type_of_frame_ref_not_present)

    fare_products = get_lxml_element(X_PATH_AMOUNT_OF_PRICE_UNIT, xml)
    response = check_fare_products_charging_type(None, fare_products)
    assert response == expected


@pytest.mark.parametrize(
    (
        "type_of_frame_ref_ref_present",
        "type_of_frame_ref_ref_valid",
        "validable_elements",
        "validable_element",
        "fare_structure_elements",
        "fare_structure_element_ref",
        "expected",
    ),
    [
        (True, True, True, True, True, True, ""),
        (
            False,
            False,
            False,
            False,
            False,
            False,
            "",
        ),
        (True, False, False, False, False, False, ""),
        (
            True,
            True,
            False,
            False,
            False,
            False,
            [
                "10",
                "'validableElements' and it's child elements missing from "
                "'PreassignedFareProduct' in 'fareProducts' for 'FareFrame' - UK_PI_FARE_PRODUCT",
            ],
        ),
        (
            True,
            True,
            True,
            False,
            False,
            False,
            [
                "11",
                "'ValidableElement' missing from 'PreassignedFareProduct'"
                " in 'fareProducts' for 'FareFrame' - UK_PI_FARE_PRODUCT",
            ],
        ),
        (
            True,
            True,
            True,
            True,
            False,
            False,
            [
                "12",
                "'fareStructureElements' and it's child elements missing from "
                "'PreassignedFareProduct' in 'fareProducts' for 'FareFrame' - UK_PI_FARE_PRODUCT",
            ],
        ),
        (
            True,
            True,
            True,
            True,
            True,
            False,
            [
                "14",
                "'FareStructureElementRef' missing from 'PreassignedFareProduct' "
                "in 'fareProducts' for 'FareFrame' - UK_PI_FARE_PRODUCT",
            ],
        ),
    ],
)
def test_preassigned_validable_elements(
    type_of_frame_ref_ref_present: bool,
    type_of_frame_ref_ref_valid: bool,
    validable_elements: bool,
    validable_element: bool,
    fare_structure_elements: bool,
    fare_structure_element_ref: bool,
    expected: list[str],
):
    """
    Test if element 'validableElements' or it's children missing in
    fareProducts.PreassignedFareProduct for FareFrame - UK_PI_FARE_PRODUCT
    FareFrame UK_PI_FARE_PRODUCT is mandatory
    """
    fare_frame_with_all_children_properties = """
    <FareFrame version="1.0" id="epd:UK:FSYO:FareFrame_UK_PI_FARE_PRODUCT:Line_9_Outbound:op" dataSourceRef="data_source" responsibilitySetRef="tariffs">
        <TypeOfFrameRef ref="fxc:UK:DFT:TypeOfFrame_UK_PI_FARE_PRODUCT:FXCP" version="fxc:v1.0" />
        <fareProducts>
            <PreassignedFareProduct id="Trip@AdultSingle" version="1.0">
                <validableElements>
                    <ValidableElement id="Trip@AdultSingle@travel" version="1.0">
                    <Name>Adult Single</Name>
                    <fareStructureElements>
                        <FareStructureElementRef version="1.0" ref="Tariff@AdultSingle@access" />
                        <FareStructureElementRef version="1.0" ref="Tariff@AdultSingle@conditions_of_travel" />
                        <FareStructureElementRef version="1.0" ref="Tariff@AdultSingle@access_when" />
                    </fareStructureElements>
                    </ValidableElement>
                </validableElements>
            </PreassignedFareProduct>
        </fareProducts>
    </FareFrame>
    """

    fare_frame_type_of_frame_ref_not_present = """
    <FareFrame version="1.0" id="epd:UK:FSYO:FareFrame_UK_PI_FARE_PRODUCT:Line_9_Outbound:op" dataSourceRef="data_source" responsibilitySetRef="tariffs">
        <TypeOfFrameRef />
        <fareProducts>
            <PreassignedFareProduct id="Trip@AdultSingle" version="1.0">
                <validableElements>
                    <ValidableElement id="Trip@AdultSingle@travel" version="1.0">
                        <Name>Adult Single</Name>
                        <fareStructureElements>
                            <FareStructureElementRef version="1.0" ref="Tariff@AdultSingle@access" />
                            <FareStructureElementRef version="1.0" ref="Tariff@AdultSingle@conditions_of_travel" />
                            <FareStructureElementRef version="1.0" ref="Tariff@AdultSingle@access_when" />
                        </fareStructureElements>
                    </ValidableElement>
                </validableElements>
            </PreassignedFareProduct>
        </fareProducts>
    </FareFrame>
    """

    fare_frame_type_of_frame_ref_not_valid = """
    <FareFrame version="1.0" id="epd:UK:FSYO:FareFrame_UK_PI_FARE_PRODUCT:Line_9_Outbound:op" dataSourceRef="data_source" responsibilitySetRef="tariffs">
        <TypeOfFrameRef ref="fxc:UK:DFT:TypeOfFrame_UK_NETW:FXCP" version="fxc:v1.0" />
        <fareProducts>
            <PreassignedFareProduct id="Trip@AdultSingle" version="1.0">
            </PreassignedFareProduct>
        </fareProducts>
    </FareFrame>
    """

    fare_frame_without_validable_elements = """
    <FareFrame version="1.0" id="epd:UK:FSYO:FareFrame_UK_PI_FARE_PRODUCT:Line_9_Outbound:op" dataSourceRef="data_source" responsibilitySetRef="tariffs">
        <TypeOfFrameRef ref="fxc:UK:DFT:TypeOfFrame_UK_PI_FARE_PRODUCT:FXCP" version="fxc:v1.0" />
        <fareProducts>
            <PreassignedFareProduct id="Trip@AdultSingle" version="1.0">
            </PreassignedFareProduct>
        </fareProducts>
    </FareFrame>
    """

    fare_frame_without_validable_element = """
    <FareFrame version="1.0" id="epd:UK:FSYO:FareFrame_UK_PI_FARE_PRODUCT:Line_9_Outbound:op" dataSourceRef="data_source" responsibilitySetRef="tariffs">
        <TypeOfFrameRef ref="fxc:UK:DFT:TypeOfFrame_UK_PI_FARE_PRODUCT:FXCP" version="fxc:v1.0" />
        <fareProducts>
            <PreassignedFareProduct id="Trip@AdultSingle" version="1.0">
                <validableElements>
                </validableElements>
            </PreassignedFareProduct>
        </fareProducts>
    </FareFrame>
    """

    fare_frame_without_fare_structure_elements = """
    <FareFrame version="1.0" id="epd:UK:FSYO:FareFrame_UK_PI_FARE_PRODUCT:Line_9_Outbound:op" dataSourceRef="data_source" responsibilitySetRef="tariffs">
        <TypeOfFrameRef ref="fxc:UK:DFT:TypeOfFrame_UK_PI_FARE_PRODUCT:FXCP" version="fxc:v1.0" />
        <fareProducts>
            <PreassignedFareProduct id="Trip@AdultSingle" version="1.0">
                <validableElements>
                    <ValidableElement id="Trip@AdultSingle@travel" version="1.0">
                    <Name>Adult Single</Name>
                    </ValidableElement>
                </validableElements>
            </PreassignedFareProduct>
        </fareProducts>
    </FareFrame>
    """

    fare_frame_without_fare_structure_element_ref = """
    <FareFrame version="1.0" id="epd:UK:FSYO:FareFrame_UK_PI_FARE_PRODUCT:Line_9_Outbound:op" dataSourceRef="data_source" responsibilitySetRef="tariffs">
        <TypeOfFrameRef ref="fxc:UK:DFT:TypeOfFrame_UK_PI_FARE_PRODUCT:FXCP" version="fxc:v1.0" />
        <fareProducts>
            <PreassignedFareProduct id="Trip@AdultSingle" version="1.0">
                <validableElements>
                    <ValidableElement id="Trip@AdultSingle@travel" version="1.0">
                    <Name>Adult Single</Name>
                    <fareStructureElements>
                    </fareStructureElements>
                    </ValidableElement>
                </validableElements>
            </PreassignedFareProduct>
        </fareProducts>
    </FareFrame>
    """

    frames = """
    <PublicationDelivery version="1.1" xsi:schemaLocation="http://www.netex.org.uk/netex http://netex.uk/netex/schema/1.09c/xsd/NeTEx_publication.xsd" xmlns="http://www.netex.org.uk/netex" xmlns:siri="http://www.siri.org.uk/siri" xmlns:gml="http://www.opengis.net/gml/3.2" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">
        <dataObjects>
            <CompositeFrame id="epd:UK:FYOR:CompositeFrame_UK_PI_LINE_FARE_OFFER:Trip@Line_1_Inbound:op">
                <frames>
                    {0}
                </frames>
            </CompositeFrame>
        </dataObjects>
    </PublicationDelivery>
    """

    if type_of_frame_ref_ref_present:
        if type_of_frame_ref_ref_valid:
            if validable_elements:
                if validable_element:
                    if fare_structure_elements:
                        if fare_structure_element_ref:
                            xml = frames.format(fare_frame_with_all_children_properties)
                        else:
                            xml = frames.format(
                                fare_frame_without_fare_structure_element_ref
                            )
                    else:
                        xml = frames.format(fare_frame_without_fare_structure_elements)
                else:
                    xml = frames.format(fare_frame_without_validable_element)
            else:
                xml = frames.format(fare_frame_without_validable_elements)
        else:
            xml = frames.format(fare_frame_type_of_frame_ref_not_valid)
    else:
        xml = frames.format(fare_frame_type_of_frame_ref_not_present)

    preassigned_fare_products = get_lxml_element(X_PATH_PREASSIGNED, xml)
    response = check_fare_product_validable_elements(None, preassigned_fare_products)
    assert response == expected


@pytest.mark.parametrize(
    (
        "type_of_frame_ref_ref_present",
        "type_of_frame_ref_ref_valid",
        "validable_elements",
        "validable_element",
        "fare_structure_elements",
        "fare_structure_element_ref",
        "expected",
    ),
    [
        (True, True, True, True, True, True, ""),
        (
            False,
            False,
            False,
            False,
            False,
            False,
            "",
        ),
        (True, False, False, False, False, False, ""),
        (
            True,
            True,
            False,
            False,
            False,
            False,
            [
                "10",
                "'validableElements' and it's child elements missing from "
                "'AmountOfPriceUnitProduct' in 'fareProducts' for 'FareFrame' - UK_PI_FARE_PRODUCT",
            ],
        ),
        (
            True,
            True,
            True,
            False,
            False,
            False,
            [
                "11",
                "'ValidableElement' missing from 'AmountOfPriceUnitProduct'"
                " in 'fareProducts' for 'FareFrame' - UK_PI_FARE_PRODUCT",
            ],
        ),
        (
            True,
            True,
            True,
            True,
            False,
            False,
            [
                "12",
                "'fareStructureElements' and it's child elements missing from "
                "'AmountOfPriceUnitProduct' in 'fareProducts' for 'FareFrame' - UK_PI_FARE_PRODUCT",
            ],
        ),
        (
            True,
            True,
            True,
            True,
            True,
            False,
            [
                "14",
                "'FareStructureElementRef' missing from 'AmountOfPriceUnitProduct' "
                "in 'fareProducts' for 'FareFrame' - UK_PI_FARE_PRODUCT",
            ],
        ),
    ],
)
def test_amountofpriceunit_validable_elements(
    type_of_frame_ref_ref_present: bool,
    type_of_frame_ref_ref_valid: bool,
    validable_elements: bool,
    validable_element: bool,
    fare_structure_elements: bool,
    fare_structure_element_ref: bool,
    expected: list[str],
):
    """
    Test if element 'validableElements' or it's children missing in
    fareProducts.AmountOfPriceUnitProduct for FareFrame - UK_PI_FARE_PRODUCT
    FareFrame UK_PI_FARE_PRODUCT is mandatory
    """
    fare_frame_with_all_children_properties = """
    <FareFrame version="1.0" id="epd:UK:FSYO:FareFrame_UK_PI_FARE_PRODUCT:Line_9_Outbound:op" dataSourceRef="data_source" responsibilitySetRef="tariffs">
        <TypeOfFrameRef ref="fxc:UK:DFT:TypeOfFrame_UK_PI_FARE_PRODUCT:FXCP" version="fxc:v1.0" />
        <fareProducts>
            <AmountOfPriceUnitProduct id="Trip@AdultSingle" version="1.0">
                <validableElements>
                    <ValidableElement id="Trip@AdultSingle@travel" version="1.0">
                    <Name>Adult Single</Name>
                    <fareStructureElements>
                        <FareStructureElementRef version="1.0" ref="Tariff@AdultSingle@access" />
                        <FareStructureElementRef version="1.0" ref="Tariff@AdultSingle@conditions_of_travel" />
                        <FareStructureElementRef version="1.0" ref="Tariff@AdultSingle@access_when" />
                    </fareStructureElements>
                    </ValidableElement>
                </validableElements>
            </AmountOfPriceUnitProduct>
        </fareProducts>
    </FareFrame>
    """

    fare_frame_type_of_frame_ref_not_present = """
    <FareFrame version="1.0" id="epd:UK:FSYO:FareFrame_UK_PI_FARE_PRODUCT:Line_9_Outbound:op" dataSourceRef="data_source" responsibilitySetRef="tariffs">
        <TypeOfFrameRef />
        <fareProducts>
            <AmountOfPriceUnitProduct id="Trip@AdultSingle" version="1.0">
                <validableElements>
                    <ValidableElement id="Trip@AdultSingle@travel" version="1.0">
                        <Name>Adult Single</Name>
                        <fareStructureElements>
                            <FareStructureElementRef version="1.0" ref="Tariff@AdultSingle@access" />
                            <FareStructureElementRef version="1.0" ref="Tariff@AdultSingle@conditions_of_travel" />
                            <FareStructureElementRef version="1.0" ref="Tariff@AdultSingle@access_when" />
                        </fareStructureElements>
                    </ValidableElement>
                </validableElements>
            </AmountOfPriceUnitProduct>
        </fareProducts>
    </FareFrame>
    """

    fare_frame_type_of_frame_ref_not_valid = """
    <FareFrame version="1.0" id="epd:UK:FSYO:FareFrame_UK_PI_FARE_PRODUCT:Line_9_Outbound:op" dataSourceRef="data_source" responsibilitySetRef="tariffs">
        <TypeOfFrameRef ref="fxc:UK:DFT:TypeOfFrame_UK_NETW:FXCP" version="fxc:v1.0" />
        <fareProducts>
            <AmountOfPriceUnitProduct id="Trip@AdultSingle" version="1.0">
            </AmountOfPriceUnitProduct>
        </fareProducts>
    </FareFrame>
    """

    fare_frame_without_validable_elements = """
    <FareFrame version="1.0" id="epd:UK:FSYO:FareFrame_UK_PI_FARE_PRODUCT:Line_9_Outbound:op" dataSourceRef="data_source" responsibilitySetRef="tariffs">
        <TypeOfFrameRef ref="fxc:UK:DFT:TypeOfFrame_UK_PI_FARE_PRODUCT:FXCP" version="fxc:v1.0" />
        <fareProducts>
            <AmountOfPriceUnitProduct id="Trip@AdultSingle" version="1.0">
            </AmountOfPriceUnitProduct>
        </fareProducts>
    </FareFrame>
    """

    fare_frame_without_validable_element = """
    <FareFrame version="1.0" id="epd:UK:FSYO:FareFrame_UK_PI_FARE_PRODUCT:Line_9_Outbound:op" dataSourceRef="data_source" responsibilitySetRef="tariffs">
        <TypeOfFrameRef ref="fxc:UK:DFT:TypeOfFrame_UK_PI_FARE_PRODUCT:FXCP" version="fxc:v1.0" />
        <fareProducts>
            <AmountOfPriceUnitProduct id="Trip@AdultSingle" version="1.0">
                <validableElements>
                </validableElements>
            </AmountOfPriceUnitProduct>
        </fareProducts>
    </FareFrame>
    """

    fare_frame_without_fare_structure_elements = """
    <FareFrame version="1.0" id="epd:UK:FSYO:FareFrame_UK_PI_FARE_PRODUCT:Line_9_Outbound:op" dataSourceRef="data_source" responsibilitySetRef="tariffs">
        <TypeOfFrameRef ref="fxc:UK:DFT:TypeOfFrame_UK_PI_FARE_PRODUCT:FXCP" version="fxc:v1.0" />
        <fareProducts>
            <AmountOfPriceUnitProduct id="Trip@AdultSingle" version="1.0">
                <validableElements>
                    <ValidableElement id="Trip@AdultSingle@travel" version="1.0">
                    <Name>Adult Single</Name>
                    </ValidableElement>
                </validableElements>
            </AmountOfPriceUnitProduct>
        </fareProducts>
    </FareFrame>
    """

    fare_frame_without_fare_structure_element_ref = """
    <FareFrame version="1.0" id="epd:UK:FSYO:FareFrame_UK_PI_FARE_PRODUCT:Line_9_Outbound:op" dataSourceRef="data_source" responsibilitySetRef="tariffs">
        <TypeOfFrameRef ref="fxc:UK:DFT:TypeOfFrame_UK_PI_FARE_PRODUCT:FXCP" version="fxc:v1.0" />
        <fareProducts>
            <AmountOfPriceUnitProduct id="Trip@AdultSingle" version="1.0">
                <validableElements>
                    <ValidableElement id="Trip@AdultSingle@travel" version="1.0">
                    <Name>Adult Single</Name>
                    <fareStructureElements>
                    </fareStructureElements>
                    </ValidableElement>
                </validableElements>
            </AmountOfPriceUnitProduct>
        </fareProducts>
    </FareFrame>
    """

    frames = """
    <PublicationDelivery version="1.1" xsi:schemaLocation="http://www.netex.org.uk/netex http://netex.uk/netex/schema/1.09c/xsd/NeTEx_publication.xsd" xmlns="http://www.netex.org.uk/netex" xmlns:siri="http://www.siri.org.uk/siri" xmlns:gml="http://www.opengis.net/gml/3.2" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">
        <dataObjects>
            <CompositeFrame id="epd:UK:FYOR:CompositeFrame_UK_PI_LINE_FARE_OFFER:Trip@Line_1_Inbound:op">
                <frames>
                    {0}
                </frames>
            </CompositeFrame>
        </dataObjects>
    </PublicationDelivery>
    """

    if type_of_frame_ref_ref_present:
        if type_of_frame_ref_ref_valid:
            if validable_elements:
                if validable_element:
                    if fare_structure_elements:
                        if fare_structure_element_ref:
                            xml = frames.format(fare_frame_with_all_children_properties)
                        else:
                            xml = frames.format(
                                fare_frame_without_fare_structure_element_ref
                            )
                    else:
                        xml = frames.format(fare_frame_without_fare_structure_elements)
                else:
                    xml = frames.format(fare_frame_without_validable_element)
            else:
                xml = frames.format(fare_frame_without_validable_elements)
        else:
            xml = frames.format(fare_frame_type_of_frame_ref_not_valid)
    else:
        xml = frames.format(fare_frame_type_of_frame_ref_not_present)

    fare_products = get_lxml_element(X_PATH_AMOUNT_OF_PRICE_UNIT, xml)
    response = check_fare_product_validable_elements(None, fare_products)
    assert response == expected


@pytest.mark.parametrize(
    (
        "type_of_frame_ref_ref_present",
        "type_of_frame_ref_ref_valid",
        "access_right",
        "validable_element_ref",
        "expected",
    ),
    [
        (True, True, True, True, ""),
        (
            False,
            False,
            False,
            False,
            "",
        ),
        (True, False, False, False, ""),
        (
            True,
            True,
            False,
            False,
            [
                "10",
                "'accessRightsInProduct' missing from 'PreassignedFareProduct' in "
                "'fareProducts' for 'FareFrame' - UK_PI_FARE_PRODUCT",
            ],
        ),
        (
            True,
            True,
            True,
            False,
            [
                "12",
                "'ValidableElementRef' missing from 'accessRightsInProduct' in "
                "'fareProducts' for 'FareFrame' - UK_PI_FARE_PRODUCT",
            ],
        ),
    ],
)
def test_preassigned_access_right_elements(
    type_of_frame_ref_ref_present: bool,
    type_of_frame_ref_ref_valid: bool,
    access_right: bool,
    validable_element_ref: bool,
    expected: list[str],
):
    """
    Test if mandatory element 'AccessRightInProduct' or it's children missing in
    fareProducts.PreassignedFareProduct for FareFrame - UK_PI_FARE_PRODUCT
    FareFrame UK_PI_FARE_PRODUCT is mandatory
    """
    fare_frame_with_all_children_properties = """
    <FareFrame version="1.0" id="epd:UK:FSYO:FareFrame_UK_PI_FARE_PRODUCT:Line_9_Outbound:op" dataSourceRef="data_source" responsibilitySetRef="tariffs">
        <TypeOfFrameRef ref="fxc:UK:DFT:TypeOfFrame_UK_PI_FARE_PRODUCT:FXCP" version="fxc:v1.0" />
        <fareProducts>
            <PreassignedFareProduct id="Trip@AdultSingle" version="1.0">
                <accessRightsInProduct>
                    <AccessRightInProduct id="Trip@AdultSingle@travel@accessRight" version="1.0" order="1">
                        <ValidableElementRef version="1.0" ref="Trip@AdultSingle@travel" />
                    </AccessRightInProduct>
                </accessRightsInProduct>
            </PreassignedFareProduct>
        </fareProducts>
    </FareFrame>
    """

    fare_frame_type_of_frame_ref_not_present = """
    <FareFrame version="1.0" id="epd:UK:FSYO:FareFrame_UK_PI_FARE_PRODUCT:Line_9_Outbound:op" dataSourceRef="data_source" responsibilitySetRef="tariffs">
        <TypeOfFrameRef />
        <fareProducts>
            <PreassignedFareProduct id="Trip@AdultSingle" version="1.0">
                <accessRightsInProduct>
                    <AccessRightInProduct id="Trip@AdultSingle@travel@accessRight" version="1.0" order="1">
                        <ValidableElementRef version="1.0" ref="Trip@AdultSingle@travel" />
                    </AccessRightInProduct>
                </accessRightsInProduct>
            </PreassignedFareProduct>
        </fareProducts>
    </FareFrame>
    """

    fare_frame_type_of_frame_ref_not_valid = """
    <FareFrame version="1.0" id="epd:UK:FSYO:FareFrame_UK_PI_FARE_PRODUCT:Line_9_Outbound:op" dataSourceRef="data_source" responsibilitySetRef="tariffs">
        <TypeOfFrameRef ref="fxc:UK:DFT:TypeOfFrame_UK_NETW:FXCP" version="fxc:v1.0" />
        <fareProducts>
            <PreassignedFareProduct id="Trip@AdultSingle" version="1.0">
            </PreassignedFareProduct>
        </fareProducts>
    </FareFrame>
    """

    fare_frame_without_access_rights_in_product = """
    <FareFrame version="1.0" id="epd:UK:FSYO:FareFrame_UK_PI_FARE_PRODUCT:Line_9_Outbound:op" dataSourceRef="data_source" responsibilitySetRef="tariffs">
        <TypeOfFrameRef ref="fxc:UK:DFT:TypeOfFrame_UK_PI_FARE_PRODUCT:FXCP" version="fxc:v1.0" />
        <fareProducts>
            <PreassignedFareProduct id="Trip@AdultSingle" version="1.0">
            </PreassignedFareProduct>
        </fareProducts>
    </FareFrame>
    """

    fare_frame_without_validable_element_ref = """
    <FareFrame version="1.0" id="epd:UK:FSYO:FareFrame_UK_PI_FARE_PRODUCT:Line_9_Outbound:op" dataSourceRef="data_source" responsibilitySetRef="tariffs">
        <TypeOfFrameRef ref="fxc:UK:DFT:TypeOfFrame_UK_PI_FARE_PRODUCT:FXCP" version="fxc:v1.0" />
        <fareProducts>
            <PreassignedFareProduct id="Trip@AdultSingle" version="1.0">
                <accessRightsInProduct>
                    <AccessRightInProduct id="Trip@AdultSingle@travel@accessRight" version="1.0" order="1">
                    </AccessRightInProduct>
                </accessRightsInProduct>
            </PreassignedFareProduct>
        </fareProducts>
    </FareFrame>
    """

    frames = """
    <PublicationDelivery version="1.1" xsi:schemaLocation="http://www.netex.org.uk/netex http://netex.uk/netex/schema/1.09c/xsd/NeTEx_publication.xsd" xmlns="http://www.netex.org.uk/netex" xmlns:siri="http://www.siri.org.uk/siri" xmlns:gml="http://www.opengis.net/gml/3.2" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">
        <dataObjects>
            <CompositeFrame id="epd:UK:FYOR:CompositeFrame_UK_PI_LINE_FARE_OFFER:Trip@Line_1_Inbound:op">
                <frames>
                    {0}
                </frames>
            </CompositeFrame>
        </dataObjects>
    </PublicationDelivery>
    """

    if type_of_frame_ref_ref_present:
        if type_of_frame_ref_ref_valid:
            if access_right:
                if validable_element_ref:
                    xml = frames.format(fare_frame_with_all_children_properties)
                else:
                    xml = frames.format(fare_frame_without_validable_element_ref)
            else:
                xml = frames.format(fare_frame_without_access_rights_in_product)
        else:
            xml = frames.format(fare_frame_type_of_frame_ref_not_valid)
    else:
        xml = frames.format(fare_frame_type_of_frame_ref_not_present)

    preassigned_fare_products = get_lxml_element(X_PATH_PREASSIGNED, xml)
    response = check_access_right_elements(None, preassigned_fare_products)
    assert response == expected


@pytest.mark.parametrize(
    (
        "type_of_frame_ref_ref_present",
        "type_of_frame_ref_ref_valid",
        "access_right",
        "validable_element_ref",
        "expected",
    ),
    [
        (True, True, True, True, ""),
        (
            False,
            False,
            False,
            False,
            "",
        ),
        (True, False, False, False, ""),
        (
            True,
            True,
            False,
            False,
            [
                "10",
                "'accessRightsInProduct' missing from 'AmountOfPriceUnitProduct' in "
                "'fareProducts' for 'FareFrame' - UK_PI_FARE_PRODUCT",
            ],
        ),
        (
            True,
            True,
            True,
            False,
            [
                "12",
                "'ValidableElementRef' missing from 'accessRightsInProduct' in "
                "'fareProducts' for 'FareFrame' - UK_PI_FARE_PRODUCT",
            ],
        ),
    ],
)
def test_amountofpriceunit_access_right_elements(
    type_of_frame_ref_ref_present: bool,
    type_of_frame_ref_ref_valid: bool,
    access_right: bool,
    validable_element_ref: bool,
    expected: list[str],
):
    """
    Test if mandatory element 'AccessRightInProduct' or it's children missing in
    fareProducts.AmountOfPriceUnitProduct for FareFrame - UK_PI_FARE_PRODUCT
    FareFrame UK_PI_FARE_PRODUCT is mandatory
    """
    fare_frame_with_all_children_properties = """
    <FareFrame version="1.0" id="epd:UK:FSYO:FareFrame_UK_PI_FARE_PRODUCT:Line_9_Outbound:op" dataSourceRef="data_source" responsibilitySetRef="tariffs">
        <TypeOfFrameRef ref="fxc:UK:DFT:TypeOfFrame_UK_PI_FARE_PRODUCT:FXCP" version="fxc:v1.0" />
        <fareProducts>
            <AmountOfPriceUnitProduct id="Trip@AdultSingle" version="1.0">
                <accessRightsInProduct>
                    <AccessRightInProduct id="Trip@AdultSingle@travel@accessRight" version="1.0" order="1">
                        <ValidableElementRef version="1.0" ref="Trip@AdultSingle@travel" />
                    </AccessRightInProduct>
                </accessRightsInProduct>
            </AmountOfPriceUnitProduct>
        </fareProducts>
    </FareFrame>
    """

    fare_frame_type_of_frame_ref_not_present = """
    <FareFrame version="1.0" id="epd:UK:FSYO:FareFrame_UK_PI_FARE_PRODUCT:Line_9_Outbound:op" dataSourceRef="data_source" responsibilitySetRef="tariffs">
        <TypeOfFrameRef />
        <fareProducts>
            <AmountOfPriceUnitProduct id="Trip@AdultSingle" version="1.0">
                <accessRightsInProduct>
                    <AccessRightInProduct id="Trip@AdultSingle@travel@accessRight" version="1.0" order="1">
                        <ValidableElementRef version="1.0" ref="Trip@AdultSingle@travel" />
                    </AccessRightInProduct>
                </accessRightsInProduct>
            </AmountOfPriceUnitProduct>
        </fareProducts>
    </FareFrame>
    """

    fare_frame_type_of_frame_ref_not_valid = """
    <FareFrame version="1.0" id="epd:UK:FSYO:FareFrame_UK_PI_FARE_PRODUCT:Line_9_Outbound:op" dataSourceRef="data_source" responsibilitySetRef="tariffs">
        <TypeOfFrameRef ref="fxc:UK:DFT:TypeOfFrame_UK_NETW:FXCP" version="fxc:v1.0" />
        <fareProducts>
            <AmountOfPriceUnitProduct id="Trip@AdultSingle" version="1.0">
            </AmountOfPriceUnitProduct>
        </fareProducts>
    </FareFrame>
    """

    fare_frame_without_access_rights_in_product = """
    <FareFrame version="1.0" id="epd:UK:FSYO:FareFrame_UK_PI_FARE_PRODUCT:Line_9_Outbound:op" dataSourceRef="data_source" responsibilitySetRef="tariffs">
        <TypeOfFrameRef ref="fxc:UK:DFT:TypeOfFrame_UK_PI_FARE_PRODUCT:FXCP" version="fxc:v1.0" />
        <fareProducts>
            <AmountOfPriceUnitProduct id="Trip@AdultSingle" version="1.0">
            </AmountOfPriceUnitProduct>
        </fareProducts>
    </FareFrame>
    """

    fare_frame_without_validable_element_ref = """
    <FareFrame version="1.0" id="epd:UK:FSYO:FareFrame_UK_PI_FARE_PRODUCT:Line_9_Outbound:op" dataSourceRef="data_source" responsibilitySetRef="tariffs">
        <TypeOfFrameRef ref="fxc:UK:DFT:TypeOfFrame_UK_PI_FARE_PRODUCT:FXCP" version="fxc:v1.0" />
        <fareProducts>
            <AmountOfPriceUnitProduct id="Trip@AdultSingle" version="1.0">
                <accessRightsInProduct>
                    <AccessRightInProduct id="Trip@AdultSingle@travel@accessRight" version="1.0" order="1">
                    </AccessRightInProduct>
                </accessRightsInProduct>
            </AmountOfPriceUnitProduct>
        </fareProducts>
    </FareFrame>
    """

    frames = """
    <PublicationDelivery version="1.1" xsi:schemaLocation="http://www.netex.org.uk/netex http://netex.uk/netex/schema/1.09c/xsd/NeTEx_publication.xsd" xmlns="http://www.netex.org.uk/netex" xmlns:siri="http://www.siri.org.uk/siri" xmlns:gml="http://www.opengis.net/gml/3.2" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">
        <dataObjects>
            <CompositeFrame id="epd:UK:FYOR:CompositeFrame_UK_PI_LINE_FARE_OFFER:Trip@Line_1_Inbound:op">
                <frames>
                    {0}
                </frames>
            </CompositeFrame>
        </dataObjects>
    </PublicationDelivery>
    """

    if type_of_frame_ref_ref_present:
        if type_of_frame_ref_ref_valid:
            if access_right:
                if validable_element_ref:
                    xml = frames.format(fare_frame_with_all_children_properties)
                else:
                    xml = frames.format(fare_frame_without_validable_element_ref)
            else:
                xml = frames.format(fare_frame_without_access_rights_in_product)
        else:
            xml = frames.format(fare_frame_type_of_frame_ref_not_valid)
    else:
        xml = frames.format(fare_frame_type_of_frame_ref_not_present)

    fare_products = get_lxml_element(X_PATH_AMOUNT_OF_PRICE_UNIT, xml)
    response = check_access_right_elements(None, fare_products)
    assert response == expected


@pytest.mark.parametrize(
    (
        "type_of_frame_ref_ref_present",
        "type_of_frame_ref_ref_valid",
        "product_type",
        "expected",
    ),
    [
        (True, True, True, ""),
        (
            False,
            False,
            False,
            "",
        ),
        (True, False, False, ""),
        (
            True,
            True,
            False,
            [
                "10",
                "'ProductType' missing or empty from 'PreassignedFareProduct' in "
                "'fareProducts' for 'FareFrame' - UK_PI_FARE_PRODUCT",
            ],
        ),
    ],
)
def test_preassigned_product_type(
    type_of_frame_ref_ref_present: bool,
    type_of_frame_ref_ref_valid: bool,
    product_type: bool,
    expected: list[str],
):
    """
    Test if mandatory element 'ProductType'is missing in
    fareProducts.PreassignedFareProduct for FareFrame - UK_PI_FARE_PRODUCT
    FareFrame UK_PI_FARE_PRODUCT is mandatory
    """
    fare_frame_with_all_children_properties = """
    <FareFrame version="1.0" id="epd:UK:FSYO:FareFrame_UK_PI_FARE_PRODUCT:Line_9_Outbound:op" dataSourceRef="data_source" responsibilitySetRef="tariffs">
        <TypeOfFrameRef ref="fxc:UK:DFT:TypeOfFrame_UK_PI_FARE_PRODUCT:FXCP" version="fxc:v1.0" />
        <fareProducts>
            <PreassignedFareProduct id="Trip@AdultSingle" version="1.0">
                <ProductType>dayPass</ProductType>
            </PreassignedFareProduct>
        </fareProducts>
    </FareFrame>
    """

    fare_frame_type_of_frame_ref_not_present = """
    <FareFrame version="1.0" id="epd:UK:FSYO:FareFrame_UK_PI_FARE_PRODUCT:Line_9_Outbound:op" dataSourceRef="data_source" responsibilitySetRef="tariffs">
        <TypeOfFrameRef />
        <fareProducts>
            <PreassignedFareProduct id="Trip@AdultSingle" version="1.0">
                <ProductType>dayPass</ProductType>
            </PreassignedFareProduct>
        </fareProducts>
    </FareFrame>
    """

    fare_frame_type_of_frame_ref_not_valid = """
    <FareFrame version="1.0" id="epd:UK:FSYO:FareFrame_UK_PI_FARE_PRODUCT:Line_9_Outbound:op" dataSourceRef="data_source" responsibilitySetRef="tariffs">
        <TypeOfFrameRef ref="fxc:UK:DFT:TypeOfFrame_UK_NETW:FXCP" version="fxc:v1.0" />
        <fareProducts>
            <PreassignedFareProduct id="Trip@AdultSingle" version="1.0">
            </PreassignedFareProduct>
        </fareProducts>
    </FareFrame>
    """

    fare_frame_without_product_type = """
    <FareFrame version="1.0" id="epd:UK:FSYO:FareFrame_UK_PI_FARE_PRODUCT:Line_9_Outbound:op" dataSourceRef="data_source" responsibilitySetRef="tariffs">
        <TypeOfFrameRef ref="fxc:UK:DFT:TypeOfFrame_UK_PI_FARE_PRODUCT:FXCP" version="fxc:v1.0" />
        <fareProducts>
            <PreassignedFareProduct id="Trip@AdultSingle" version="1.0">
            </PreassignedFareProduct>
        </fareProducts>
    </FareFrame>
    """

    frames = """
    <PublicationDelivery version="1.1" xsi:schemaLocation="http://www.netex.org.uk/netex http://netex.uk/netex/schema/1.09c/xsd/NeTEx_publication.xsd" xmlns="http://www.netex.org.uk/netex" xmlns:siri="http://www.siri.org.uk/siri" xmlns:gml="http://www.opengis.net/gml/3.2" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">
        <dataObjects>
            <CompositeFrame id="epd:UK:FYOR:CompositeFrame_UK_PI_LINE_FARE_OFFER:Trip@Line_1_Inbound:op">
                <frames>
                    {0}
                </frames>
            </CompositeFrame>
        </dataObjects>
    </PublicationDelivery>
    """

    if type_of_frame_ref_ref_present:
        if type_of_frame_ref_ref_valid:
            if product_type:
                xml = frames.format(fare_frame_with_all_children_properties)
            else:
                xml = frames.format(fare_frame_without_product_type)
        else:
            xml = frames.format(fare_frame_type_of_frame_ref_not_valid)
    else:
        xml = frames.format(fare_frame_type_of_frame_ref_not_present)

    preassigned_fare_products = get_lxml_element(X_PATH_PREASSIGNED, xml)
    response = check_product_type(None, preassigned_fare_products)
    assert response == expected


@pytest.mark.parametrize(
    (
        "type_of_frame_ref_ref_present",
        "type_of_frame_ref_ref_valid",
        "product_type",
        "wrong_product_type",
        "expected",
    ),
    [
        (True, True, True, False, ""),
        (
            False,
            False,
            False,
            False,
            "",
        ),
        (True, False, False, False, ""),
        (
            True,
            True,
            False,
            False,
            [
                "10",
                "'ProductType' missing or empty from 'AmountOfPriceUnitProduct' in "
                "'fareProducts' for 'FareFrame' - UK_PI_FARE_PRODUCT",
            ],
        ),
        (
            True,
            True,
            True,
            True,
            [
                "10",
                "'ProductType' for 'AmountOfPriceUnitProduct' in 'fareProducts' must be tripCarnet or passCarnet"
                "",
            ],
        ),
    ],
)
def test_amountofpriceunit_product_type(
    type_of_frame_ref_ref_present: bool,
    type_of_frame_ref_ref_valid: bool,
    product_type: bool,
    wrong_product_type: bool,
    expected: list[str],
):
    """
    Test if mandatory element 'ProductType'is missing in
    fareProducts.AmountOfPriceUnitProduct for FareFrame - UK_PI_FARE_PRODUCT
    FareFrame UK_PI_FARE_PRODUCT is mandatory
    """
    fare_frame_with_all_children_properties = """
    <FareFrame version="1.0" id="epd:UK:FSYO:FareFrame_UK_PI_FARE_PRODUCT:Line_9_Outbound:op" dataSourceRef="data_source" responsibilitySetRef="tariffs">
        <TypeOfFrameRef ref="fxc:UK:DFT:TypeOfFrame_UK_PI_FARE_PRODUCT:FXCP" version="fxc:v1.0" />
        <fareProducts>
            <AmountOfPriceUnitProduct id="Trip@AdultSingle" version="1.0">
                <ProductType>passCarnet</ProductType>
            </AmountOfPriceUnitProduct>
        </fareProducts>
    </FareFrame>
    """

    fare_frame_with_wrong_product_type = """
    <FareFrame version="1.0" id="epd:UK:FSYO:FareFrame_UK_PI_FARE_PRODUCT:Line_9_Outbound:op" dataSourceRef="data_source" responsibilitySetRef="tariffs">
        <TypeOfFrameRef ref="fxc:UK:DFT:TypeOfFrame_UK_PI_FARE_PRODUCT:FXCP" version="fxc:v1.0" />
        <fareProducts>
            <AmountOfPriceUnitProduct id="Trip@AdultSingle" version="1.0">
                <ProductType>dayPass</ProductType>
            </AmountOfPriceUnitProduct>
        </fareProducts>
    </FareFrame>
    """

    fare_frame_type_of_frame_ref_not_present = """
    <FareFrame version="1.0" id="epd:UK:FSYO:FareFrame_UK_PI_FARE_PRODUCT:Line_9_Outbound:op" dataSourceRef="data_source" responsibilitySetRef="tariffs">
        <TypeOfFrameRef />
        <fareProducts>
            <AmountOfPriceUnitProduct id="Trip@AdultSingle" version="1.0">
                <ProductType>passCarnet</ProductType>
            </AmountOfPriceUnitProduct>
        </fareProducts>
    </FareFrame>
    """

    fare_frame_type_of_frame_ref_not_valid = """
    <FareFrame version="1.0" id="epd:UK:FSYO:FareFrame_UK_PI_FARE_PRODUCT:Line_9_Outbound:op" dataSourceRef="data_source" responsibilitySetRef="tariffs">
        <TypeOfFrameRef ref="fxc:UK:DFT:TypeOfFrame_UK_NETW:FXCP" version="fxc:v1.0" />
        <fareProducts>
            <AmountOfPriceUnitProduct id="Trip@AdultSingle" version="1.0">
            </AmountOfPriceUnitProduct>
        </fareProducts>
    </FareFrame>
    """

    fare_frame_without_product_type = """
    <FareFrame version="1.0" id="epd:UK:FSYO:FareFrame_UK_PI_FARE_PRODUCT:Line_9_Outbound:op" dataSourceRef="data_source" responsibilitySetRef="tariffs">
        <TypeOfFrameRef ref="fxc:UK:DFT:TypeOfFrame_UK_PI_FARE_PRODUCT:FXCP" version="fxc:v1.0" />
        <fareProducts>
            <AmountOfPriceUnitProduct id="Trip@AdultSingle" version="1.0">
            </AmountOfPriceUnitProduct>
        </fareProducts>
    </FareFrame>
    """

    frames = """
    <PublicationDelivery version="1.1" xsi:schemaLocation="http://www.netex.org.uk/netex http://netex.uk/netex/schema/1.09c/xsd/NeTEx_publication.xsd" xmlns="http://www.netex.org.uk/netex" xmlns:siri="http://www.siri.org.uk/siri" xmlns:gml="http://www.opengis.net/gml/3.2" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">
        <dataObjects>
            <CompositeFrame id="epd:UK:FYOR:CompositeFrame_UK_PI_LINE_FARE_OFFER:Trip@Line_1_Inbound:op">
                <frames>
                    {0}
                </frames>
            </CompositeFrame>
        </dataObjects>
    </PublicationDelivery>
    """

    if type_of_frame_ref_ref_present:
        if type_of_frame_ref_ref_valid:
            if product_type:
                if wrong_product_type:
                    xml = frames.format(fare_frame_with_wrong_product_type)
                else:
                    xml = frames.format(fare_frame_with_all_children_properties)
            else:
                xml = frames.format(fare_frame_without_product_type)
        else:
            xml = frames.format(fare_frame_type_of_frame_ref_not_valid)
    else:
        xml = frames.format(fare_frame_type_of_frame_ref_not_present)

    fare_products = get_lxml_element(X_PATH_AMOUNT_OF_PRICE_UNIT, xml)
    response = check_product_type(None, fare_products)
    assert response == expected
