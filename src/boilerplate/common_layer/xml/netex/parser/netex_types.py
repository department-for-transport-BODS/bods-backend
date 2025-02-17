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
    ProofOfIdentityT,
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
