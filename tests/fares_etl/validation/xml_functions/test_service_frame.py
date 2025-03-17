import pytest

from fares_etl.validation.app.xml_functions.service_frame import (
    check_lines_operator_ref_present,
    check_lines_public_code_present,
    is_lines_present_in_service_frame,
    is_schedule_stop_points,
    is_service_frame_present,
)

from ..helpers import get_lxml_element


@pytest.mark.parametrize(
    (
        "type_of_frame_ref_present",
        "type_of_frame_ref_attr_present",
        "type_of_frame_ref_correct",
        "service_frame_present",
        "expected",
    ),
    [
        (True, True, True, True, ""),
        (
            False,
            False,
            False,
            False,
            [
                "3",
                "If 'ServiceFrame' is present, mandatory element 'TypeOfFrameRef' "
                "should be included and TypeOfFrameRef should include UK_PI_NETWORK",
            ],
        ),
        (
            True,
            True,
            False,
            True,
            [
                "5",
                "If 'ServiceFrame' is present, mandatory element 'TypeOfFrameRef' "
                "should be included and TypeOfFrameRef should include UK_PI_NETWORK",
            ],
        ),
        (
            True,
            False,
            False,
            True,
            [
                "4",
                "Attribute 'ref' of element 'TypeOfFrameRef' is missing",
            ],
        ),
        (True, True, True, False, ""),
    ],
)
def test_is_service_frame_present(
    type_of_frame_ref_present: bool,
    type_of_frame_ref_attr_present: bool,
    type_of_frame_ref_correct: bool,
    service_frame_present: bool,
    expected: list[str],
):
    service_frame = """
        <Description>This frame contains the stop and line definitions for the service.</Description>
        <lines>
        <Line version="1.0" id="236">
            <Name>Southdown PSV 236</Name>
            <Description>Oxted - East Grinstead</Description>
            <PublicCode>236</PublicCode>
            <PrivateCode type="txc:Line@id">SPSV:PK1007823:51:236</PrivateCode>
            <OperatorRef version="1.0" ref="noc:SPSV">noc:137709</OperatorRef>
            <LineType>local</LineType>
        </Line>
        </lines>
    """
    type_of_frame_ref_attr_correct = """
        <TypeOfFrameRef ref="fxc:UK:DFT:TypeOfFrame_UK_PI_NETWORK:FXCP" version="fxc:v1.0" />
    """
    type_of_frame_ref_attr_missing = """<TypeOfFrameRef version="fxc:v1.0" />"""
    type_of_frame_ref_attr_incorrect = """
        <TypeOfFrameRef ref="fxc:UK:DFT:TypeOfFrame_UK_PI_FARE_PRODUCT:FXCP" version="fxc:v1.0" />
    """
    service_frames = """
    <PublicationDelivery version="1.1" xsi:schemaLocation="http://www.netex.org.uk/netex http://netex.uk/netex/schema/1.09c/xsd/NeTEx_publication.xsd" xmlns="http://www.netex.org.uk/netex" xmlns:siri="http://www.siri.org.uk/siri" xmlns:gml="http://www.opengis.net/gml/3.2" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">
        <ServiceFrame version="1.0" id="epd:UK:FYOR:ServiceFrame_UK_PI_NETWORK:1_Inbound:op" dataSourceRef="data_source" responsibilitySetRef="tariffs">
            {0}
            {1}
        </ServiceFrame>
    </PublicationDelivery>"""

    if type_of_frame_ref_present:
        if type_of_frame_ref_attr_present:
            if type_of_frame_ref_correct:
                if service_frame_present:
                    xml = service_frames.format(
                        type_of_frame_ref_attr_correct, service_frame
                    )
                else:
                    xml = service_frames.format(type_of_frame_ref_attr_correct, "")
            else:
                xml = service_frames.format(
                    type_of_frame_ref_attr_incorrect, service_frame
                )
        else:
            xml = service_frames.format(type_of_frame_ref_attr_missing, service_frame)
    else:
        xml = service_frames.format("", service_frame)

    service_frames = get_lxml_element("//x:ServiceFrame", xml)
    result = is_service_frame_present(None, service_frames)
    assert result == expected


@pytest.mark.parametrize(
    (
        "service_frame_present",
        "lines_present",
        "line_present",
        "line_name_present",
        "expected",
    ),
    [
        (True, True, True, True, ""),
        (False, True, True, True, ""),
        (True, False, True, True, ""),
        (
            True,
            True,
            False,
            True,
            ["4", "Mandatory element 'Line' in ServiceFrame is missing"],
        ),
        (
            True,
            True,
            True,
            False,
            [
                "5",
                "From 'Line' element in ServiceFrame, element 'Name' is missing or empty",
            ],
        ),
    ],
)
def test_is_lines_present_in_service_frame(
    service_frame_present: bool,
    lines_present: bool,
    line_present: bool,
    line_name_present: bool,
    expected: list[str],
):
    service_frame_with_child = """
    <ServiceFrame version="1.0" id="epd:UK:FYOR:ServiceFrame_UK_PI_NETWORK:1_Inbound:op" dataSourceRef="data_source" responsibilitySetRef="tariffs">
        <lines>
            <Line version="1.0" id="236">
                <Name>Southdown PSV 236</Name>
            </Line>
        </lines>
    </ServiceFrame>
    """
    service_frame_without_line = """
    <ServiceFrame version="1.0" id="epd:UK:FYOR:ServiceFrame_UK_PI_NETWORK:1_Inbound:op" dataSourceRef="data_source" responsibilitySetRef="tariffs">
        <lines>
        </lines>
    </ServiceFrame>
    """
    service_frame_without_name = """
    <ServiceFrame version="1.0" id="epd:UK:FYOR:ServiceFrame_UK_PI_NETWORK:1_Inbound:op" dataSourceRef="data_source" responsibilitySetRef="tariffs">
        <lines>
            <Line version="1.0" id="236">
            </Line>
        </lines>
    </ServiceFrame>
    """
    service_frame_without_lines = """
    <ServiceFrame version="1.0" id="epd:UK:FYOR:ServiceFrame_UK_PI_NETWORK:1_Inbound:op" dataSourceRef="data_source" responsibilitySetRef="tariffs">
    </ServiceFrame>
    """
    service_frames = """<PublicationDelivery version="1.1" xsi:schemaLocation="http://www.netex.org.uk/netex http://netex.uk/netex/schema/1.09c/xsd/NeTEx_publication.xsd" xmlns="http://www.netex.org.uk/netex" xmlns:siri="http://www.siri.org.uk/siri" xmlns:gml="http://www.opengis.net/gml/3.2" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">
            {0}
    </PublicationDelivery>"""
    if service_frame_present:
        if lines_present:
            if line_present:
                if line_name_present:
                    xml = service_frames.format(service_frame_with_child)
                else:
                    xml = service_frames.format(service_frame_without_name)
            else:
                xml = service_frames.format(service_frame_without_line)
        else:
            xml = service_frames.format(service_frame_without_lines)
    else:
        xml = service_frames.format("")
    service_frames = get_lxml_element("//x:ServiceFrame", xml)
    result = is_lines_present_in_service_frame(None, service_frames)
    assert result == expected
    return


@pytest.mark.parametrize(
    (
        "line_present",
        "public_code_present",
        "expected",
    ),
    [
        (True, True, ""),
        (False, True, ""),
        (
            True,
            False,
            [
                "5",
                "From 'Line' element in ServiceFrame, element 'PublicCode' is missing or empty",
            ],
        ),
    ],
)
def test_check_lines_public_code_present(
    line_present: bool, public_code_present: bool, expected: list[str]
):
    service_frame_with_child = """
    <ServiceFrame version="1.0" id="epd:UK:FYOR:ServiceFrame_UK_PI_NETWORK:1_Inbound:op" dataSourceRef="data_source" responsibilitySetRef="tariffs">
        <lines>
            <Line version="1.0" id="236">
                <PublicCode>236</PublicCode>
            </Line>
        </lines>
    </ServiceFrame>
    """
    service_frame_without_line = """
    <ServiceFrame version="1.0" id="epd:UK:FYOR:ServiceFrame_UK_PI_NETWORK:1_Inbound:op" dataSourceRef="data_source" responsibilitySetRef="tariffs">
        <lines>
        </lines>
    </ServiceFrame>
    """
    service_frame_without_public_code = """
    <ServiceFrame version="1.0" id="epd:UK:FYOR:ServiceFrame_UK_PI_NETWORK:1_Inbound:op" dataSourceRef="data_source" responsibilitySetRef="tariffs">
        <lines>
            <Line version="1.0" id="236">
            </Line>
        </lines>
    </ServiceFrame>
    """
    service_frames = """<PublicationDelivery version="1.1" xsi:schemaLocation="http://www.netex.org.uk/netex http://netex.uk/netex/schema/1.09c/xsd/NeTEx_publication.xsd" xmlns="http://www.netex.org.uk/netex" xmlns:siri="http://www.siri.org.uk/siri" xmlns:gml="http://www.opengis.net/gml/3.2" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">
            {0}
    </PublicationDelivery>"""
    if line_present:
        if public_code_present:
            xml = service_frames.format(service_frame_with_child)
        else:
            xml = service_frames.format(service_frame_without_public_code)
    else:
        xml = service_frames.format(service_frame_without_line)
    line_frame = get_lxml_element("//x:ServiceFrame/x:lines/x:Line", xml)
    if line_frame:
        result = check_lines_public_code_present(None, line_frame)
        assert result == expected
        return


@pytest.mark.parametrize(
    (
        "line_present",
        "operator_ref_present",
        "expected",
    ),
    [
        (True, True, ""),
        (False, True, ""),
        (
            True,
            False,
            [
                "5",
                "From 'Line' element in ServiceFrame, element'OperatorRef' is missing",
            ],
        ),
    ],
)
def test_check_lines_operator_ref_present(
    line_present: bool, operator_ref_present: bool, expected: list[str]
):
    service_frame_with_child = """
    <ServiceFrame version="1.0" id="epd:UK:FYOR:ServiceFrame_UK_PI_NETWORK:1_Inbound:op" dataSourceRef="data_source" responsibilitySetRef="tariffs">
        <lines>
            <Line version="1.0" id="236">
                <OperatorRef version="1.0" ref="noc:SPSV">noc:137709</OperatorRef>
            </Line>
        </lines>
    </ServiceFrame>
    """
    service_frame_without_line = """
    <ServiceFrame version="1.0" id="epd:UK:FYOR:ServiceFrame_UK_PI_NETWORK:1_Inbound:op" dataSourceRef="data_source" responsibilitySetRef="tariffs">
        <lines>
        </lines>
    </ServiceFrame>
    """
    service_frame_without_operator_ref = """
    <ServiceFrame version="1.0" id="epd:UK:FYOR:ServiceFrame_UK_PI_NETWORK:1_Inbound:op" dataSourceRef="data_source" responsibilitySetRef="tariffs">
        <lines>
            <Line version="1.0" id="236">
            </Line>
        </lines>
    </ServiceFrame>
    """
    service_frames = """<PublicationDelivery version="1.1" xsi:schemaLocation="http://www.netex.org.uk/netex http://netex.uk/netex/schema/1.09c/xsd/NeTEx_publication.xsd" xmlns="http://www.netex.org.uk/netex" xmlns:siri="http://www.siri.org.uk/siri" xmlns:gml="http://www.opengis.net/gml/3.2" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">
            {0}
    </PublicationDelivery>"""
    if line_present:
        if operator_ref_present:
            xml = service_frames.format(service_frame_with_child)
        else:
            xml = service_frames.format(service_frame_without_operator_ref)
    else:
        xml = service_frames.format(service_frame_without_line)
    line_frame = get_lxml_element("//x:ServiceFrame/x:lines/x:Line", xml)
    if line_frame:
        result = check_lines_operator_ref_present(None, line_frame)
        assert result == expected
        return


@pytest.mark.parametrize(
    (
        "scheduled_stop_points_present",
        "scheduled_stop_point_present",
        "scheduled_stop_point_id_present",
        "scheduled_stop_point_id_correct",
        "scheduled_stop_point_name_present",
        "expected",
    ),
    [
        (
            True,
            True,
            True,
            True,
            False,
            [
                "11",
                "From 'scheduledStopPoints' element in ServiceFrame,"
                " element 'Name' is missing or empty",
            ],
        ),
    ],
)
def test_is_schedule_stop_points(
    scheduled_stop_points_present: bool,
    scheduled_stop_point_present: bool,
    scheduled_stop_point_id_present: bool,
    scheduled_stop_point_id_correct: bool,
    scheduled_stop_point_name_present: bool,
    expected: list[str],
):
    service_frame_with_children = """
    <ServiceFrame version="1.0" id="epd:UK:FYOR:ServiceFrame_UK_PI_NETWORK:1_Inbound:op" dataSourceRef="data_source" responsibilitySetRef="tariffs">
        <scheduledStopPoints>
            <ScheduledStopPoint version="any" id="atco:3290">
              <Name>Wigginton Mill Lane</Name>
              <TopographicPlaceView>
                <TopographicPlaceRef versionRef="nptg:2.4" ref="nptgLocality:E0053942" />
                <Name>Wigginton</Name>
              </TopographicPlaceView>
            </ScheduledStopPoint>
            <ScheduledStopPoint version="any" id="atco:3290">
              <Name>Wigginton Pond</Name>
              <TopographicPlaceView>
                <TopographicPlaceRef versionRef="nptg:2.4" ref="nptgLocality:E0053942" />
                <Name>Wigginton</Name>
              </TopographicPlaceView>
            </ScheduledStopPoint>
        </scheduledStopPoints>
    </ServiceFrame>
    """
    service_frame_without_child = """
    <ServiceFrame version="1.0" id="epd:UK:FYOR:ServiceFrame_UK_PI_NETWORK:1_Inbound:op" dataSourceRef="data_source" responsibilitySetRef="tariffs">
    </ServiceFrame>
    """
    service_frame_without_schedule_stop_point = """
    <ServiceFrame version="1.0" id="epd:UK:FYOR:ServiceFrame_UK_PI_NETWORK:1_Inbound:op" dataSourceRef="data_source" responsibilitySetRef="tariffs">
        <scheduledStopPoints>
        </scheduledStopPoints>
    </ServiceFrame>
    """
    schedule_stop_point_incorrect_format = """
   <ServiceFrame version="1.0" id="epd:UK:FYOR:ServiceFrame_UK_PI_NETWORK:1_Inbound:op" dataSourceRef="data_source" responsibilitySetRef="tariffs">
        <scheduledStopPoints>
            <ScheduledStopPoint version="any" id="xxxx:3290">
              <Name>Wigginton Mill Lane</Name>
              <TopographicPlaceView>
                <TopographicPlaceRef versionRef="nptg:2.4" ref="nptgLocality:E0053942" />
                <Name>Wigginton</Name>
              </TopographicPlaceView>
            </ScheduledStopPoint>
            <ScheduledStopPoint version="any" id="atco:3290">
              <Name>Wigginton Pond</Name>
              <TopographicPlaceView>
                <TopographicPlaceRef versionRef="nptg:2.4" ref="nptgLocality:E0053942" />
                <Name>Wigginton</Name>
              </TopographicPlaceView>
            </ScheduledStopPoint>
        </scheduledStopPoints>
    </ServiceFrame>
    """
    schedule_stop_point_missing_id = """
   <ServiceFrame version="1.0" id="epd:UK:FYOR:ServiceFrame_UK_PI_NETWORK:1_Inbound:op" dataSourceRef="data_source" responsibilitySetRef="tariffs">
        <scheduledStopPoints>
            <ScheduledStopPoint version="any">
              <Name>Wigginton Mill Lane</Name>
              <TopographicPlaceView>
                <TopographicPlaceRef versionRef="nptg:2.4" ref="nptgLocality:E0053942" />
                <Name>Wigginton</Name>
              </TopographicPlaceView>
            </ScheduledStopPoint>
            <ScheduledStopPoint version="any" id="atco:3290">
            <Name>Wigginton Pond</Name>
              <TopographicPlaceView>
                <TopographicPlaceRef versionRef="nptg:2.4" ref="nptgLocality:E0053942" />
                <Name>Wigginton</Name>
              </TopographicPlaceView>
            </ScheduledStopPoint>
        </scheduledStopPoints>
    </ServiceFrame>
    """
    schedule_stop_points_missing_name = """
       <ServiceFrame version="1.0" id="epd:UK:FYOR:ServiceFrame_UK_PI_NETWORK:1_Inbound:op" dataSourceRef="data_source" responsibilitySetRef="tariffs">
        <scheduledStopPoints>
            <ScheduledStopPoint version="any" id="atco:3290">
              <Name>Wigginton Mill Lane</Name>
              <TopographicPlaceView>
                <TopographicPlaceRef versionRef="nptg:2.4" ref="nptgLocality:E0053942" />
              </TopographicPlaceView>
            </ScheduledStopPoint>
            <ScheduledStopPoint version="any" id="atco:3290">
              <TopographicPlaceView>
                <TopographicPlaceRef versionRef="nptg:2.4" ref="nptgLocality:E0053942" />
                <Name>Wigginton</Name>
              </TopographicPlaceView>
            </ScheduledStopPoint>
        </scheduledStopPoints>
    </ServiceFrame>
    """
    service_frames = """<PublicationDelivery version="1.1" xsi:schemaLocation="http://www.netex.org.uk/netex http://netex.uk/netex/schema/1.09c/xsd/NeTEx_publication.xsd" xmlns="http://www.netex.org.uk/netex" xmlns:siri="http://www.siri.org.uk/siri" xmlns:gml="http://www.opengis.net/gml/3.2" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">
            {0}
    </PublicationDelivery>"""
    if scheduled_stop_points_present:
        if scheduled_stop_point_present:
            if scheduled_stop_point_id_present:
                if scheduled_stop_point_id_correct:
                    if scheduled_stop_point_name_present:
                        xml = service_frames.format(service_frame_with_children)
                    else:
                        xml = service_frames.format(schedule_stop_points_missing_name)
                else:
                    xml = service_frames.format(schedule_stop_point_incorrect_format)
            else:
                xml = service_frames.format(schedule_stop_point_missing_id)
        else:
            xml = service_frames.format(service_frame_without_schedule_stop_point)
    else:
        xml = service_frames.format(service_frame_without_child)
    service_frames = get_lxml_element("//x:ServiceFrame", xml)
    result = is_schedule_stop_points(None, service_frames)
    assert result == expected
    return
