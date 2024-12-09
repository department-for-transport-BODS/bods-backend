import logging

from common_layer.db.manager import DbManager
from common_layer.db.repositories.otc_service import OtcServiceRepository
from common_layer.dynamodb.client import DynamoDB
from pti.constants import SCOTLAND_TRAVELINE_REGIONS


logger = logging.getLogger(__name__)

def is_service_in_scotland(service_ref: str) -> bool:
    cache_key = f"{service_ref.replace(':', '-')}-is-scottish-region"
    value_in_cache = DynamoDB.get(cache_key)
    if value_in_cache is not None:
        logger.info(f"{cache_key} for PTI Validation found in cache")
        return value_in_cache

    is_in_scotland = get_service_in_scotland_from_db(service_ref)

    DynamoDB.put(cache_key, is_in_scotland, ttl=7200)

    return is_in_scotland


def get_service_in_scotland_from_db(service_ref: str) -> bool:
    """
    Check whether a service is from the scotland region or not
    If any of the english regions are present the service will be considered english
    If only scottish region is present then service will be considered scottish

    Args:
        service_ref (str): service registration number

    Returns:
        bool: True/False if service is in scotland
    """
    logger.info(f"{service_ref} PTI validation For region checking in database")
    db = DbManager.get_db()
    repo = OtcServiceRepository(db)
    service_with_region = repo.get_service_with_traveline_region(service_ref)

    is_scottish = False
    if service_with_region and service_with_region.traveline_region:
        regions = service_with_region.traveline_region.split("|")
        if sorted(SCOTLAND_TRAVELINE_REGIONS) == sorted(regions):
            is_scottish = True

    return is_scottish