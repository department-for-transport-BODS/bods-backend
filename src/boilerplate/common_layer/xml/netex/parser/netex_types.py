"""
Checkers for Netex Types
"""

from typing import cast, get_args

from lxml.etree import _Element  # type: ignore
from structlog.stdlib import get_logger

from ..models import (
    ActivationMeansT,
    DiscountBasisT,
    LineTypeT,
    PreassignedFareProductTypeT,
    ProofOfIdentityT,
    TariffBasisT,
    UsageEndT,
    UsageTriggerT,
)
from .netex_utility import get_netex_text

log = get_logger()


def parse_line_type(elem: _Element) -> LineTypeT | None:
    """
    Parse a Netex LineType
    """
    text = get_netex_text(elem, "LineType")
    if text in get_args(LineTypeT):
        return cast(LineTypeT, text)
    log.warning("Unknown Line Type", text=text)
    return None


def parse_proof_of_identity_type(
    elem: _Element, element_name: str
) -> ProofOfIdentityT | None:
    """
    Parse a Netex LineType
    """
    text = get_netex_text(elem, element_name)
    if text in get_args(ProofOfIdentityT):
        return cast(ProofOfIdentityT, text)
    log.warning("Unknown Proof of Identity", text=text)
    return None


def parse_discount_basis_type(elem: _Element) -> DiscountBasisT | None:
    """
    Parse a DiscountBasis as the type
    """
    text = get_netex_text(elem, "DiscountBasis")
    if text in get_args(DiscountBasisT):
        return cast(DiscountBasisT, text)
    log.warning("Unknown Discount Basis", text=text)
    return None


def parse_usage_trigger_type(elem: _Element) -> UsageTriggerT | None:
    """
    Parse a UsageTrigger as the type
    """
    text = get_netex_text(elem, "UsageTrigger")
    if text in get_args(UsageTriggerT):
        return cast(UsageTriggerT, text)
    log.warning("Unknown Usage Trigger", text=text)
    return None


def parse_activation_means_type(elem: _Element) -> ActivationMeansT | None:
    """
    Parse an ActivationMeans as the type
    """
    text = get_netex_text(elem, "ActivationMeans")
    if text in get_args(ActivationMeansT):
        return cast(ActivationMeansT, text)
    log.warning("Unknown Activation Means", text=text)
    return None


def parse_usage_end_type(elem: _Element) -> UsageEndT | None:
    """
    Parse a UsageEnd as the type
    """
    text = get_netex_text(elem, "UsageEnd")
    if text in get_args(UsageEndT):
        return cast(UsageEndT, text)
    log.warning("Unknown Usage End", text=text)
    return None


def parse_tariff_basis_type(elem: _Element) -> TariffBasisT | None:
    """
    Parse a TariffBasis from a NeTEx XML element
    """
    text = get_netex_text(elem, "TariffBasis")
    if text in get_args(TariffBasisT):
        return cast(TariffBasisT, text)
    log.warning("Unknown Tariff Basis", text=text)
    return None


def parse_preassigned_fare_product_type(
    elem: _Element,
) -> PreassignedFareProductTypeT | None:
    """
    Parse a PreassignedFareProduct type from a NeTEx XML element
    """
    text = get_netex_text(elem, "PreassignedFareProduct")
    if text in get_args(PreassignedFareProductTypeT):
        return cast(PreassignedFareProductTypeT, text)
    log.warning("Unknown Preassigned Fare Product type", text=text)
    return None
