"""
PTI Helper Utils
"""

from functools import lru_cache

from common_layer.database.client import SqlDB
from common_layer.database.repos import OtcServiceRepo
from common_layer.dynamodb.client import DynamoDB
from common_layer.pti.constants import SCOTLAND_TRAVELINE_REGIONS
from structlog.stdlib import get_logger

log = get_logger()


@lru_cache()
def is_service_in_scotland(service_ref: str, dynamo: DynamoDB, db: SqlDB) -> bool:
    """
    Checks if a Service Ref is in Scotland
    """
    cache_key = f"{service_ref.replace(':', '-')}-is-scottish-region"
    return dynamo.get_or_compute(
        key=cache_key,
        compute_fn=lambda: get_service_in_scotland_from_db(service_ref, db),
        ttl=7200,
    )


def get_service_in_scotland_from_db(service_ref: str, db: SqlDB) -> bool:
    """
    Check whether a service is from the scotland region or not
    If any of the english regions are present the service will be considered english
    If only scottish region is present then service will be considered scottish

    Args:
        service_ref (str): service registration number

    Returns:
        bool: True/False if service is in scotland
    """
    log.info(
        "Checking if Service is in Scotland",
        service_ref=service_ref,
    )
    repo = OtcServiceRepo(db)
    service_with_region = repo.get_service_with_traveline_region(service_ref)

    is_scottish = False
    if service_with_region and service_with_region.traveline_region:
        regions = service_with_region.traveline_region.split("|")
        if sorted(SCOTLAND_TRAVELINE_REGIONS) == sorted(regions):
            is_scottish = True

    return is_scottish
