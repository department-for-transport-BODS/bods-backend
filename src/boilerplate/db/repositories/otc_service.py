import logging
from typing import Any, Dict, List

from common import BodsDB
from exceptions.pipeline_exceptions import PipelineException

logger = logging.getLogger(__name__)


from sqlalchemy.sql import func, case, text

class OtcServiceRepository:
    def __init__(self, db: BodsDB):
        self._db = db

    def get_service_with_traveline_region(self, service_ref: str):
        with self._db.session as session:
            OtcService = self._db.classes.otc_service

            # Classes for related tables
            NaptanAdminArea = self._db.classes.naptan_adminarea
            OtcLocalAuthorityRegistrationNumbers = self._db.classes.otc_localauthority_registration_numbers
            OtcLocalAuthority = self._db.classes.otc_localauthority
            UILta = self._db.classes.ui_lta

            # Base service query
            service_query = session.query(OtcService).filter(
                OtcService.registration_number == service_ref.replace(":", "/")
            )

            # Query for traveline_region_weca
            traveline_region_weca_subquery = (
                session.query(
                    func.string_agg(NaptanAdminArea.traveline_region_id.distinct(), text("'|'")).label(
                        "traveline_region_weca"
                    ),
                    NaptanAdminArea.atco_code,
                ).group_by(NaptanAdminArea.atco_code)
                .subquery()
            )

            # Add traveline_region_weca column to base query
            service_query = service_query.outerjoin(
                traveline_region_weca_subquery, traveline_region_weca_subquery.c.atco_code == OtcService.atco_code
            ).add_columns(traveline_region_weca_subquery.c.traveline_region_weca)

            # Query for traveline_region_otc
            traveline_region_otc_subquery = (
                session.query(
                    func.string_agg(NaptanAdminArea.traveline_region_id.distinct(), text("'|'")).label(
                        "traveline_region_otc"
                    ),
                    OtcService.id,
                )
                .join(
                    OtcLocalAuthorityRegistrationNumbers,
                    OtcLocalAuthorityRegistrationNumbers.service_id == OtcService.id,
                )
                .join(
                    OtcLocalAuthority, OtcLocalAuthority.id == OtcLocalAuthorityRegistrationNumbers.localauthority_id
                )
                .join(UILta, UILta.id == OtcLocalAuthority.ui_lta_id)
                .join(NaptanAdminArea, NaptanAdminArea.ui_lta_id == UILta.id)
                .group_by(OtcService.id)
                .subquery()
            )

            service_query = service_query.outerjoin(
                traveline_region_otc_subquery, traveline_region_otc_subquery.c.id == OtcService.id
            ).add_columns(traveline_region_otc_subquery.c.traveline_region_otc)

            # Add traveline_region details based on api type
            service_query = service_query.add_columns(
                case(
                    (OtcService.api_type.in_(["WECA", "EP"]), traveline_region_weca_subquery.c.traveline_region_weca),
                    else_=traveline_region_otc_subquery.c.traveline_region_otc,
                ).label("traveline_region")
            )

            # import sqlparse
            # query = str(service_query.statement.compile(compile_kwargs={"literal_binds": True}))
            # print(sqlparse.format(query, reindent=True, keyword_case="upper"))
            # print("====")
            result = service_query.first()
            if result:
                service = result[0]
                traveline_region = result[3]
                return service, traveline_region
            return None, None
