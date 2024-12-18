"""
Helper Functions to Query the TXCOperator Pydantic Models
"""

from structlog.stdlib import get_logger

from ..models.txc_operator import TXCOperator

log = get_logger()


def get_national_operator_code(operators: list[TXCOperator]) -> str | None:
    """
    Get the National Operator Code from list of operators. Returns first NOC if multiple found.
    """
    nocs: list[str] = [op.NationalOperatorCode for op in operators]

    if not nocs:
        log.warning("No National Operator Codes found")
        return None

    if len(nocs) > 1:
        log.warning(
            "More than one national operator code found, returning first noc", nocs=nocs
        )

    return nocs[0]


def get_licence_number(operators: list[TXCOperator]) -> str | None:
    """Get the Licence Number from a TXC File. Returns first if multiple found."""
    licence_numbers = [op.LicenceNumber for op in operators]

    if not licence_numbers:
        log.warning("No Licence Numbers found")
        return None

    if len(licence_numbers) > 1:
        log.warning(
            "More than one licence number found, returning first",
            numbers=licence_numbers,
        )

    return licence_numbers[0]
