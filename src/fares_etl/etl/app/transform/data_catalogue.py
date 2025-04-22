"""
Create fares data catalogue
"""

from common_layer.database.models import FaresDataCatalogueMetadata
from common_layer.xml.netex.helpers import (
    get_atco_area_codes_from_service_frames,
    get_composite_frame_valid_from,
    get_composite_frame_valid_to,
    get_fare_products,
    get_line_ids_from_service_frames,
    get_line_public_codes_from_service_frames,
    get_national_operator_codes,
    get_product_names,
    get_product_types,
    get_tariff_basis,
    get_tariffs_from_fare_frames,
    get_user_types,
    sort_frames,
)
from common_layer.xml.netex.models import PublicationDeliveryStructure
from structlog.stdlib import get_logger

log = get_logger()


def create_data_catalogue(
    netex: PublicationDeliveryStructure,
    file_name: str,
) -> FaresDataCatalogueMetadata:
    """
    Create FaresDataCatalogueMetadata
    """
    sorted_frames = sort_frames(netex.dataObjects)

    tariffs = get_tariffs_from_fare_frames(sorted_frames.fare_frames)
    fare_products = get_fare_products(sorted_frames.fare_frames)
    valid_from = get_composite_frame_valid_from(sorted_frames.composite_frames)
    valid_to = get_composite_frame_valid_to(sorted_frames.composite_frames)

    data_catalogue = FaresDataCatalogueMetadata(
        valid_from=valid_from.date() if valid_from else None,
        valid_to=valid_to.date() if valid_to else None,
        atco_area=get_atco_area_codes_from_service_frames(sorted_frames.service_frames),
        line_id=get_line_ids_from_service_frames(sorted_frames.service_frames),
        line_name=get_line_public_codes_from_service_frames(
            sorted_frames.service_frames
        ),
        national_operator_code=get_national_operator_codes(
            sorted_frames.resource_frames
        ),
        product_name=get_product_names(fare_products),
        product_type=get_product_types(fare_products),
        tariff_basis=get_tariff_basis(tariffs),
        user_type=get_user_types(tariffs),
        xml_file_name=file_name,
    )
    log.info("Generated FearesDataCatalogueMetadata", **data_catalogue.as_dict())
    return data_catalogue
