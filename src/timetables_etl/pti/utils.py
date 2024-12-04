import logging

from common import DbManager
from db.repositories.otc_service import OtcServiceRepository
from pti.constants import SCOTLAND_TRAVELINE_REGIONS


logger = logging.getLogger(__name__)

def is_service_in_scotland(service_ref: str) -> bool:
    # TODO: How should we implement caching in lambda environment?

    # service_name_in_cache = f"{service_ref.replace(':', '-')}-scottish-region"
    # value_in_cache = cache.get(service_name_in_cache, None)
    # if value_in_cache is not None:
    #     logger.info(f"{service_ref} PTI validation For region found in cache")
    #     return value_in_cache

    is_in_scotland = get_service_in_scotland_from_db(service_ref)

    # service_name_in_cache = f"{service_ref.replace(':', '-')}-scottish-region"
    # cache.set(service_name_in_cache, is_scottish, timeout=7200)

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