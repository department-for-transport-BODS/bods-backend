"""
TXC StopPoints to Pydantic models
"""

from lxml.etree import _Element  # type: ignore
from structlog.stdlib import get_logger

from ....utils import (
    find_section,
    get_element_bool,
    get_element_datetime,
    get_element_int,
    get_element_text,
    get_element_texts,
)
from ...models import AnnotatedStopPointRef, DescriptorStructure, TXCStopPoint
from .parse_stop_point_classification import parse_stop_classification_structure
from .parse_stop_point_location import parse_place_structure

log = get_logger()


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


def parse_descriptor_structure(descriptor_xml: _Element) -> DescriptorStructure | None:
    """
    StopPoints -> SpotPoint -> Descriptor
    """
    common_name = get_element_text(descriptor_xml, "CommonName")
    if common_name is None:
        log.info(
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
        log.error(
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
        log.error(
            "Missing Stop Point information",
            atco_code=atco_code,
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
