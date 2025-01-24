"""
DynamoDB NAPTAN StopPoint Client
"""

from typing import Any, Iterator

from common_layer.txc.models.txc_stoppoint import TXCStopPoint
from pydantic import Field
from structlog.stdlib import get_logger

from .base import DynamoDB
from .settings import DynamoBaseSettings, DynamoDBSettings

log = get_logger()


class NaptanDynamoDBSettings(DynamoBaseSettings):
    """
    Settings for DynamoDBCache client
    """

    DYNAMODB_NAPTAN_STOP_POINT_TABLE_NAME: str = Field(
        default="",
        description="Table Name for NAPTAN StopPoint table",
    )


class NaptanStopPointDynamoDBClient(DynamoDB):
    """
    DynamoDB client specialized for fetching Naptan StopPoints.
    """

    def __init__(self, settings: NaptanDynamoDBSettings | None = None):
        naptan_settings = settings if settings else NaptanDynamoDBSettings()
        super().__init__(
            DynamoDBSettings(
                DYNAMODB_ENDPOINT_URL=naptan_settings.DYNAMODB_ENDPOINT_URL,
                AWS_REGION=naptan_settings.AWS_REGION,
                DYNAMODB_TABLE_NAME=naptan_settings.DYNAMODB_NAPTAN_STOP_POINT_TABLE_NAME,
            )
        )

    def get_by_atco_codes(
        self, atco_codes: list[str]
    ) -> tuple[list[TXCStopPoint], list[str]]:
        """
        Get all StopPoints from DynamoDB by the given list of AtcoCodes.

        Returns:
            Tuple of (found TXCStopPoints, list of missing AtcoCodes).
        """
        log.info("Fetching StopPoints from DynamoDB by AtcoCodes")

        if not atco_codes:
            log.warning("No AtcoCodes provided for fetching StopPoints")
            return [], []

        stop_points: list[TXCStopPoint] = []
        found_atco_codes = set()

        # Limit for BatchGetItem is 100
        batch_size = 100
        for batch in self._batch_queries(atco_codes, batch_size=batch_size):
            raw_items = self._batch_get_items(batch)
            for item in raw_items:
                try:
                    stop_point = TXCStopPoint(**item)
                    stop_points.append(stop_point)
                    found_atco_codes.add(stop_point.AtcoCode)
                except ValueError as e:
                    log.error("Failed to parse StopPoint", item=item, error=str(e))

        missing_atco_codes = [
            code for code in atco_codes if code not in found_atco_codes
        ]

        log.info(
            "Completed fetching and parsing TxcStopPoints from DynamoDB",
            total_fetched=len(stop_points),
            total_missing=len(missing_atco_codes),
        )
        return stop_points, missing_atco_codes

    def get_stop_area_map(self, atco_codes: list[str]) -> dict[str, list[str] | None]:
        """
        Build a stop area map from list of AtcoCodes.

        Returns:
            Dict of {AtcoCode: StopAreas}
        """
        stop_points, _ = self.get_by_atco_codes(atco_codes)
        return {stop_point.AtcoCode: stop_point.StopAreas for stop_point in stop_points}

    def _batch_queries(self, items: list[Any], batch_size: int) -> Iterator[list[Any]]:
        """
        Split list into batch of a specified size.
        """
        for i in range(0, len(items), batch_size):
            yield items[i : i + batch_size]

    def _batch_get_items(self, atco_codes: list[str]) -> list[dict[str, Any]]:
        """
        Use DynamoDB BatchGetItem to fetch items for a list of AtcoCodes.
        """
        try:
            request_keys = [{"AtcoCode": {"S": atco_code}} for atco_code in atco_codes]
            response = self._client.batch_get_item(
                RequestItems={
                    self._settings.DYNAMODB_TABLE_NAME: {"Keys": request_keys}
                }
            )
            # Extract items for the specific table
            raw_items = response.get("Responses", {}).get(
                self._settings.DYNAMODB_TABLE_NAME, []
            )

            # Deserialize each item correctly
            deserialized_items = []
            for raw_item in raw_items:
                deserialized_item = {
                    key: self._deserializer.deserialize(value)
                    for key, value in raw_item.items()
                }
                deserialized_items.append(deserialized_item)

            log.info(
                "BatchGetItem completed",
                fetched=len(deserialized_items),
                requested=len(atco_codes),
            )
            return deserialized_items
        except Exception as e:
            log.error("Failed to execute BatchGetItem", error=str(e))
            raise
