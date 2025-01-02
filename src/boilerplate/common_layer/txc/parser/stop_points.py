"""
TXC StopPoints to Pydantic models
"""

from typing import cast, get_args

from lxml.etree import _Element
from structlog.stdlib import get_logger

from ..models.txc_data import AnnotatedStopPointRef
from ..models.txc_stoppoint import (
    BearingStructure,
    BusStopStructure,
    DescriptorStructure,
    LocationStructure,
    MarkedPointStructure,
    OnStreetStructure,
    PlaceStructure,
    StopClassificationStructure,
    TXCStopPoint,
)
from ..models.txc_types import BusStopTypeT, CompassPointT, TimingStatusT, TXCStopTypeT
from .utils import find_section
from .utils_tags import (
    get_element_bool,
    get_element_datetime,
    get_element_int,
    get_element_text,
    get_element_texts,
)

log = get_logger()


TIMING_STATUS_MAPPING = {
    # Map 3 letters to the new full names
    # TXC has had versions with spelling mistakes that map onto new names
    "PPT": "principalPoint",
    "principalPoint": "principalPoint",
    "principlePoint": "principalPoint",  # Deprecated spelling mistake
    "TIP": "timeInfoPoint",
    "timeInfoPoint": "timeInfoPoint",
    "PTP": "principalTimingPoint",
    "principalTimingPoint": "principalTimingPoint",
    "principleTimingPoint": "principalTimingPoint",  # Deprecated spelling mistake
    "OTH": "otherPoint",
    "otherPoint": "otherPoint",
}


def parse_annotated_stop_point_ref(stop_xml: _Element) -> AnnotatedStopPointRef:
    """
    Parses StopPoints -> AnnotatedStopPointRef
    """
    point_ref = get_element_text(stop_xml, "StopPointRef")
    common_name = get_element_text(stop_xml, "CommonName")
    if not point_ref or not common_name:
        log.warning(
            "AnnotatedStopPointRef missing required fields. Skipping.",
            StopPointRef=point_ref,
            CommonName=common_name,
        )
        raise ValueError("AnnotatedStopPointRef missing required fields.")

    return AnnotatedStopPointRef(
        StopPointRef=point_ref,
        CommonName=common_name,
        Indicator=get_element_text(stop_xml, "Indicator"),
        LocalityName=get_element_text(stop_xml, "LocalityName"),
        LocalityQualifier=get_element_text(stop_xml, "LocalityQualifier"),
    )


def parse_bearing_structure(bearing_xml: _Element) -> BearingStructure | None:
    """
    StopPoints -> StopPoint -> StopClassification -> OnStreet -> Bus -> MarkedPoint -> Bearing
    """
    compass_point = get_element_text(bearing_xml, "CompassPoint")
    if compass_point and compass_point in get_args(CompassPointT):
        return BearingStructure(CompassPoint=cast(CompassPointT, compass_point))
    log.warning("Incorrect Compass Point")
    return None


def parse_marked_point_structure(
    marked_point_xml: _Element,
) -> MarkedPointStructure | None:
    """
    StopPoints -> StopPoint -> StopClassification -> OnStreet -> Bus -> MarkedPoint
    """
    bearing_xml = marked_point_xml.find("Bearing")
    if bearing_xml is None:
        return None
    bearing = parse_bearing_structure(bearing_xml)
    return MarkedPointStructure(Bearing=bearing) if bearing else None


def parse_bus_stop_structure(bus_xml: _Element) -> BusStopStructure | None:
    """
    Parse the Bus structure within the OnStreet section.

    StopPoints -> StopPoint -> StopClassification -> OnStreet -> Bus
    """
    marked_point_xml = bus_xml.find("MarkedPoint")
    marked_point = (
        parse_marked_point_structure(marked_point_xml)
        if marked_point_xml is not None
        else None
    )

    bus_stop_type = get_element_text(bus_xml, "BusStopType")
    timing_status_code = get_element_text(bus_xml, "TimingStatus")

    if timing_status_code is not None:
        timing_status = TIMING_STATUS_MAPPING.get(timing_status_code)
    else:
        timing_status = None
    if (
        bus_stop_type is None
        or timing_status is None
        or marked_point is None
        or bus_stop_type not in get_args(BusStopTypeT)
        or timing_status not in get_args(TimingStatusT)
    ):
        log.warning(
            "Missing Bus Stop Structure Data Returning None",
            bus_stop_type=bus_stop_type,
            timing_status=timing_status,
            marked_point=marked_point,
        )
        return None

    return BusStopStructure(
        BusStopType=cast(BusStopTypeT, bus_stop_type),
        TimingStatus=cast(TimingStatusT, timing_status),
        MarkedPoint=marked_point,
    )


def parse_on_street_structure(on_street_xml: _Element) -> OnStreetStructure | None:
    """
    Parse the OnStreet structure within the StopClassification section.

    StopPoints -> StopPoint -> StopClassification -> OnStreet
    """
    bus_xml = on_street_xml.find("Bus")
    if bus_xml is None:
        log.warning(
            "Bus XML Missing. Perhaps other implemented data",
            on_street_xml=on_street_xml,
        )
        return None

    bus = parse_bus_stop_structure(bus_xml)

    if bus:
        return OnStreetStructure(Bus=bus)
    return None


def parse_stop_classification_structure(
    stop_classification_xml: _Element,
) -> StopClassificationStructure | None:
    """
    StopPoints -> StopPoint -> StopClassification
    """
    on_street_xml = stop_classification_xml.find("OnStreet")
    if on_street_xml is None:
        log.warning(
            "Missing OnStreet Section, OffStreet Not implemented",
            stop_classification_xml=stop_classification_xml,
        )
        return None
    on_street = parse_on_street_structure(on_street_xml)
    stop_type = get_element_text(stop_classification_xml, "StopType")
    if on_street and stop_type:
        return StopClassificationStructure(
            StopType=cast(TXCStopTypeT, stop_type),
            OnStreet=on_street,
        )

    return None


def parse_location_structure(location_xml: _Element) -> LocationStructure | None:
    """
    StopPoints -> StopPoint -> Place -> Location
    """
    translation_xml = location_xml.find("Translation")
    if translation_xml is not None:
        return LocationStructure(
            Longitude=get_element_text(translation_xml, "Longitude"),
            Latitude=get_element_text(translation_xml, "Latitude"),
            Easting=get_element_text(translation_xml, "Easting"),
            Northing=get_element_text(translation_xml, "Northing"),
        )
    else:
        return LocationStructure(
            Longitude=get_element_text(location_xml, "Longitude"),
            Latitude=get_element_text(location_xml, "Latitude"),
            Easting=get_element_text(location_xml, "Easting"),
            Northing=get_element_text(location_xml, "Northing"),
        )


def parse_place_structure(place_xml: _Element) -> PlaceStructure | None:
    """
    StopPoints -> StopPoint -> Place
    """
    location_xml = place_xml.find("Location")
    location = (
        parse_location_structure(location_xml) if location_xml is not None else None
    )
    locality_ref = get_element_text(place_xml, "NptgLocalityRef")
    if not locality_ref or not location:
        log.warning(
            "Missing Place Structure Required Field",
            locality_ref=locality_ref,
            location=location,
        )
        return None
    return PlaceStructure(
        NptgLocalityRef=locality_ref,
        LocalityName=get_element_text(place_xml, "LocalityName"),
        Location=location,
    )


def parse_descriptor_structure(descriptor_xml: _Element) -> DescriptorStructure | None:
    """
    StopPoints -> SpotPoint -> Descriptor
    """
    common_name = get_element_text(descriptor_xml, "CommonName")
    if common_name is None:
        log.warning(
            "Descriptor Structure Missing required CommonName", data=descriptor_xml
        )
        return None
    return DescriptorStructure(
        CommonName=common_name,
        ShortCommonName=get_element_text(descriptor_xml, "ShortCommonName"),
        Landmark=get_element_text(descriptor_xml, "Landmark"),
        Street=get_element_text(descriptor_xml, "Street"),
        Crossing=get_element_text(descriptor_xml, "Crossing"),
        Indicator=get_element_text(descriptor_xml, "Indicator"),
    )


def parse_txc_stop_point(stop_xml: _Element) -> TXCStopPoint | None:
    """
    StopPoints -> StopPoint
    """
    atco_code = get_element_text(stop_xml, "AtcoCode")
    if not atco_code:
        log.warning(
            "TXCStopPoint missing required fields. Skipping.",
            AtcoCode=atco_code,
            stop_data=stop_xml,
        )
        return None

    descriptor_xml = stop_xml.find("Descriptor")
    descriptor = (
        parse_descriptor_structure(descriptor_xml)
        if descriptor_xml is not None
        else None
    )

    place_xml = stop_xml.find("Place")
    place = parse_place_structure(place_xml) if place_xml is not None else None

    stop_classification_xml = stop_xml.find("StopClassification")
    stop_classification = (
        parse_stop_classification_structure(stop_classification_xml)
        if stop_classification_xml is not None
        else None
    )
    admin_area_ref = get_element_text(stop_xml, "AdministrativeAreaRef")
    if not descriptor or not place or not stop_classification or not admin_area_ref:
        log.warning(
            "Missing Stop Point information",
            admin_area_ref=admin_area_ref,
            place=place,
            stop_classification=stop_classification,
            descriptor=descriptor,
        )
        return None
    stop_areas = get_element_texts(stop_xml, "StopAreas") or None

    txc_stop_point = TXCStopPoint(
        AtcoCode=atco_code,
        NaptanCode=get_element_text(stop_xml, "NaptanCode"),
        PlateCode=get_element_text(stop_xml, "PlateCode"),
        PrivateCode=get_element_text(stop_xml, "PrivateCode"),
        CleardownCode=get_element_int(stop_xml, "CleardownCode"),
        FormerStopPointRef=get_element_text(stop_xml, "FormerStopPointRef"),
        Descriptor=descriptor,
        Place=place,
        StopClassification=stop_classification,
        StopAreas=stop_areas,
        AdministrativeAreaRef=admin_area_ref,
        Notes=get_element_text(stop_xml, "Notes"),
        Public=get_element_bool(stop_xml, "Public"),
        CreationDateTime=get_element_datetime(stop_xml, "CreationDateTime"),
        ModificationDateTime=get_element_datetime(stop_xml, "ModificationDateTime"),
        Modification=get_element_text(stop_xml, "Modification"),
        RevisionNumber=get_element_text(stop_xml, "RevisionNumber"),
        Status=get_element_text(stop_xml, "Status"),
    )

    return txc_stop_point


def parse_stop_points(xml_data: _Element) -> list[AnnotatedStopPointRef | TXCStopPoint]:
    """
    Convert StopPoints XML into Pydantic Models
    """
    try:
        section = find_section(xml_data, "StopPoints")
    except ValueError:
        return []
    stop_points: list[AnnotatedStopPointRef | TXCStopPoint] = []
    stops_xml = section.findall("*")

    for stop_xml in stops_xml:
        try:
            if stop_xml.tag == "AnnotatedStopPointRef":
                stop_points.append(parse_annotated_stop_point_ref(stop_xml))
            elif stop_xml.tag == "StopPoint":
                stop_point = parse_txc_stop_point(stop_xml)
                if stop_point:

                    stop_points.append(stop_point)
            else:
                log.warning("Unknown stop point type. Skipping.", tag=stop_xml.tag)
        except ValueError:
            log.error("Error Processing Stop Point", exc_info=True)
            continue
    annotated_stop_point_ref_count = sum(
        isinstance(stop, AnnotatedStopPointRef) for stop in stop_points
    )
    txc_stop_point_count = sum(isinstance(stop, TXCStopPoint) for stop in stop_points)

    log.info(
        "Parsed TXC StopPoints",
        AnnotatedStopPointRef=annotated_stop_point_ref_count,
        StopPoint=txc_stop_point_count,
    )
    return stop_points
