"""
Checkers for Netex Types
"""

from typing import cast, get_args

from lxml.etree import _Element  # type: ignore
from structlog.stdlib import get_logger

from ..models import DiscountBasisT, LineTypeT, ProofOfIdentityT
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
