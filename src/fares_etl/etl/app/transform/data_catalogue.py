"""
Create fares data catalogue
"""

from common_layer.database.models import FaresDataCatalogueMetadata
from common_layer.xml.netex.helpers.helpers_composite_frame import (
    get_composite_frame_valid_from,
    get_composite_frame_valid_to,
)
from common_layer.xml.netex.helpers.helpers_counts import sort_frames
from common_layer.xml.netex.helpers.helpers_fare_frame_fare_products import (
    get_fare_products,
    get_product_names,
    get_product_types,
)
from common_layer.xml.netex.helpers.helpers_fare_frame_tariff import (
    get_tariff_basis,
    get_tariffs_from_fare_frames,
    get_user_types,
)
from common_layer.xml.netex.helpers.helpers_resource_frame import (
    get_national_operator_codes,
)
from common_layer.xml.netex.helpers.helpers_service_frame import (
    get_atco_area_codes_from_service_frames,
    get_line_ids_from_service_frames,
    get_line_public_codes_from_service_frames,
)
from common_layer.xml.netex.models.netex_publication_delivery import (
    PublicationDeliveryStructure,
)


def create_data_catalogue(
    netex: PublicationDeliveryStructure,
    file_name: str,
):
    """
    Create FaresDataCatalogueMetadata
    """
    sorted_frames = sort_frames(netex.dataObjects)

    tariffs = get_tariffs_from_fare_frames(sorted_frames.fare_frames)
    fare_products = get_fare_products(sorted_frames.fare_frames)
    valid_from = get_composite_frame_valid_from(sorted_frames.composite_frames)
    valid_to = get_composite_frame_valid_to(sorted_frames.composite_frames)

    return FaresDataCatalogueMetadata(
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
