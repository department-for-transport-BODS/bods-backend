import logging


logger = logging.getLogger(__name__)

def is_service_in_scotland(service_ref: str) -> bool:
    # TODO: Do we need the caching here? How to implement in lambda environment?

    # service_name_in_cache = f"{service_ref.replace(':', '-')}-scottish-region"
    # value_in_cache = cache.get(service_name_in_cache, None)

    # if value_in_cache is not None:
    #     logger.info(f"{service_ref} PTI validation For region found in cache")
    #     return value_in_cache

    return get_service_in_scotland_from_db(service_ref)


def get_service_in_scotland_from_db(service_ref: str) -> bool:
    """Check weather a service is from the scotland region or not
    If any of the english regions is present service will be considered as english
    If only scottish is present then service will be considered as scottish

    Args:
        service_ref (str): service registration number

    Returns:
        bool: True/False if service is in scotland
    """
    logger.info(f"{service_ref} PTI validation For region checking in database")
    service_obj = (
        Service.objects.filter(registration_number=service_ref.replace(":", "/"))
        .add_traveline_region_weca()
        .add_traveline_region_otc()
        .add_traveline_region_details()
        .first()
    )
    is_scottish = False
    if service_obj and service_obj.traveline_region:
        regions = service_obj.traveline_region.split("|")
        if sorted(SCOTLAND_TRAVELINE_REGIONS) == sorted(regions):
            is_scottish = True

    service_name_in_cache = f"{service_ref.replace(':', '-')}-scottish-region"
    # cache.set(service_name_in_cache, is_scottish, timeout=7200)
    return is_scottish