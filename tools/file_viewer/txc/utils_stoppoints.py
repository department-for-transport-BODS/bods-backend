"""
Stop Point Utils
"""

from dataclasses import dataclass

from common_layer.xml.txc.models.txc_stoppoint import (
    AnnotatedStopPointRef,
    TXCStopPoint,
)


@dataclass
class StopPointDetails:
    """
    Displayable datatable for stoppoint details
    """

    type: str
    StopPointRef: str
    CommonName: str
    Indicator: str | None
    LocalityName: str | None
    LocalityQualifier: str | None


def get_stop_point_details(
    stop_points: list[AnnotatedStopPointRef | TXCStopPoint], stop_point_ref: str
) -> StopPointDetails | None:
    """
    Helper function to get stop point details
    """
    for stop_point in stop_points:
        if (
            isinstance(stop_point, AnnotatedStopPointRef)
            and stop_point.StopPointRef == stop_point_ref
        ):
            return StopPointDetails(
                type="Naptan",
                StopPointRef=stop_point.StopPointRef,
                CommonName=stop_point.CommonName,
                Indicator=stop_point.Indicator,
                LocalityName=stop_point.LocalityName,
                LocalityQualifier=stop_point.LocalityQualifier,
            )
        if (
            isinstance(stop_point, TXCStopPoint)
            and stop_point.StopPointRef == stop_point_ref
        ):
            return StopPointDetails(
                type="Custom",
                StopPointRef=stop_point.StopPointRef,
                CommonName=stop_point.Descriptor.CommonName,
                Indicator=stop_point.Descriptor.Indicator,
                LocalityName=stop_point.Place.LocalityName,
                LocalityQualifier=None,
            )
    return None


def get_all_stop_point_details(
    stop_points: list[AnnotatedStopPointRef | TXCStopPoint],
) -> list[StopPointDetails]:
    """
    Function to get stop point details for all stop points
    """
    all_stop_point_details = []
    for stop_point in stop_points:
        if isinstance(stop_point, AnnotatedStopPointRef):
            all_stop_point_details.append(
                StopPointDetails(
                    type="Naptan",
                    StopPointRef=stop_point.StopPointRef,
                    CommonName=stop_point.CommonName,
                    Indicator=stop_point.Indicator,
                    LocalityName=stop_point.LocalityName,
                    LocalityQualifier=stop_point.LocalityQualifier,
                )
            )
        elif isinstance(stop_point, TXCStopPoint):
            all_stop_point_details.append(
                StopPointDetails(
                    type="Custom",
                    StopPointRef=stop_point.StopPointRef,
                    CommonName=stop_point.Descriptor.CommonName,
                    Indicator=stop_point.Descriptor.Indicator,
                    LocalityName=stop_point.Place.LocalityName,
                    LocalityQualifier=None,
                )
            )
    return all_stop_point_details
