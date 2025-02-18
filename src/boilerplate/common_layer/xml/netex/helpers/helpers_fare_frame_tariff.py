"""
Helper Functions for working with Tariffs in FareFrames
"""

from datetime import datetime

from ..models import FareFrame, Tariff, TariffBasisT


def get_tariffs_from_fare_frames(frames: list[FareFrame]) -> list[Tariff]:
    """
    Get a list of tariffs from a list of fare frames
    """
    return [
        tariff
        for frame in frames
        if frame.tariffs is not None
        for tariff in frame.tariffs
    ]


def get_tariff_basis(tariffs: list[Tariff]) -> list[TariffBasisT]:
    """
    Get Tariff Basis
    """
    tariff_basis_list: list[TariffBasisT] = []
    for tariff in tariffs:
        if tariff.TariffBasis is not None:
            tariff_basis_list.append(tariff.TariffBasis)
    return tariff_basis_list


def earliest_tariff_from_date(tariffs: list[Tariff]) -> datetime | None:
    """
    Look through a list of Tariffs and find the earlest Validity (if any)
    """
    from_dates: list[datetime] = []

    for tariff in tariffs:
        if tariff.validityConditions is None:
            continue

        for validity_condition in tariff.validityConditions:
            if validity_condition.FromDate is not None:
                from_dates.append(validity_condition.FromDate)

    if not from_dates:
        return None

    return min(from_dates)


def latest_tariff_to_date(tariffs: list[Tariff]) -> datetime | None:
    """
    Look through a list of Tariffs and find the latest Validity date (if any)
    """
    to_dates: list[datetime] = []

    for tariff in tariffs:
        if tariff.validityConditions is None:
            continue

        for validity_condition in tariff.validityConditions:
            if validity_condition.ToDate is not None:
                to_dates.append(validity_condition.ToDate)

    if not to_dates:
        return None

    return max(to_dates)
