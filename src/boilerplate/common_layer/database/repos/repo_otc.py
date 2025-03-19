"""
OTC Data

Note: There's a lot of Any types here that could be narrowed
"""

from dataclasses import dataclass
from typing import Any

from common_layer.exceptions.pipeline_exceptions import PipelineException
from sqlalchemy.orm import Query, Session
from sqlalchemy.sql import case, func, text
from sqlalchemy.sql.elements import KeyedColumnElement
from structlog.stdlib import get_logger

from ..client import SqlDB
from ..models import (
    NaptanAdminArea,
    OtcLocalAuthority,
    OtcLocalAuthorityRegistrationNumbers,
    OtcService,
    UiLta,
)

log = get_logger()


@dataclass
class ServiceWithRegion:
    """
    Service and Traveline Region Map for PTI
    """

    service: OtcService
    traveline_region: str


class OtcServiceRepo:
    """
    Traveline OTC Service Repo
    """

    def __init__(self, db: SqlDB) -> None:
        self._db = db

    def _add_traveline_region_weca(
        self, session: Session, query: Query[OtcService]
    ) -> tuple[Query[Any], KeyedColumnElement[Any]]:
        """
        Traveline Region that the UI LTA maps to via the admin area table
        by joining atco code. If Traveline Region value is multiple in the row
        for this service code it should sperated with |.

        Returns: Tuple of (query with traveline_region_weca column, column label)
        """

        traveline_region_weca_subquery = (
            session.query(
                func.string_agg(
                    NaptanAdminArea.traveline_region_id.distinct(), text("'|'")
                ).label("traveline_region_weca"),
                NaptanAdminArea.atco_code,
            )
            .group_by(NaptanAdminArea.atco_code)
            .subquery()
        )
        column_label = traveline_region_weca_subquery.c.traveline_region_weca

        query_with_weca = query.outerjoin(
            traveline_region_weca_subquery,
            traveline_region_weca_subquery.c.atco_code == OtcService.atco_code,
        ).add_columns(column_label)

        return query_with_weca, column_label

    def _add_traveline_region_otc(
        self, session: Session, query: Query[OtcService]
    ) -> tuple[Query[Any], KeyedColumnElement[Any]]:
        """
        Traveline Region that the UI LTA maps to via LocalAuthority table
        by joining ui lta table and then admin area table via ui lta and
        get the traveline_region_id.If Traveline Region value is multiple
        in the row for this service code it should sperated with |.

        Returns: Tuple of (query with traveline_region_otc column, column label)
        """

        traveline_region_otc_subquery = (
            session.query(
                func.string_agg(
                    NaptanAdminArea.traveline_region_id.distinct(), text("'|'")
                ).label("traveline_region_otc"),
                OtcService.id,
            )
            .join(
                OtcLocalAuthorityRegistrationNumbers,
                OtcLocalAuthorityRegistrationNumbers.service_id == OtcService.id,
            )
            .join(
                OtcLocalAuthority,
                OtcLocalAuthority.id
                == OtcLocalAuthorityRegistrationNumbers.localauthority_id,
            )
            .join(UiLta, UiLta.id == OtcLocalAuthority.ui_lta_id)
            .join(NaptanAdminArea, NaptanAdminArea.ui_lta_id == UiLta.id)
            .group_by(OtcService.id)
            .subquery()
        )
        column_label = traveline_region_otc_subquery.c.traveline_region_otc

        query_with_traveline_region_otc = query.outerjoin(
            traveline_region_otc_subquery,
            traveline_region_otc_subquery.c.id == OtcService.id,
        ).add_columns(column_label)

        return query_with_traveline_region_otc, column_label

    def get_service_with_traveline_region(
        self, registration_number: str
    ) -> ServiceWithRegion | None:
        """
        Return ServiceWithRegion Dataclass as used by PTI implementation
        """
        try:
            with self._db.session_scope() as session:
                # Base service query
                base_query = session.query(OtcService).filter(
                    OtcService.registration_number
                    == registration_number.replace(":", "/")
                )

                # Add traveline_region_weca and traveline_region_otc columns
                query_with_traveline_region_weca, weca_column_label = (
                    self._add_traveline_region_weca(session, base_query)
                )
                query_with_traveline_region_otc, otc_column_label = (
                    self._add_traveline_region_otc(
                        session, query_with_traveline_region_weca
                    )
                )

                # Add traveline_region details based on api type
                query_with_traveline_region = (
                    query_with_traveline_region_otc.add_columns(
                        case(
                            (
                                OtcService.api_type.in_(["WECA", "EP"]),
                                weca_column_label,
                            ),
                            else_=otc_column_label,
                        ).label("traveline_region")
                    )
                )

                # Result row:
                # [service_obj, traveline_region_weca, travelin_region_otc, traveline_region]
                result = query_with_traveline_region.first()
                if result:
                    service = result[0]
                    session.expunge(service)
                    traveline_region = result[3]
                    return ServiceWithRegion(service, traveline_region)
                return None
        except Exception as exc:
            message = (
                "Error retrieving service with traveline region"
                f" with registration number {registration_number}."
            )
            log.exception(message, exc_info=True)
            raise PipelineException(message) from exc
