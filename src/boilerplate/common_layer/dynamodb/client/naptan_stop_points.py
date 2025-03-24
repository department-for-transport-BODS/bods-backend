"""
DynamoDB NAPTAN StopPoint Client
"""

from typing import Iterator, Set

from common_layer.xml.txc.models import TXCStopPoint
from pydantic import ValidationError
from structlog.stdlib import get_logger

from .base import DynamoDB
from .models import AttributeValueTypeDef
from .settings import DynamoDBSettings, NaptanDynamoDBSettings

log = get_logger()


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
                PROJECT_ENV=naptan_settings.PROJECT_ENV,
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
        found_atco_codes: Set[str] = set()

        # Limit for BatchGetItem is 100
        batch_size: int = 100
        for batch in self._batch_queries(atco_codes, batch_size=batch_size):
            raw_items = self._batch_get_items(batch)
            for item in raw_items:
                atco_code = item.get("AtcoCode", {}).get("S")
                stop_point = self._deserialize_stop_point(item, atco_code=atco_code)
                if stop_point:
                    stop_points.append(stop_point)
                    found_atco_codes.add(stop_point.AtcoCode)

        missing_atco_codes: list[str] = [
            code for code in atco_codes if code not in found_atco_codes
        ]

        log.info(
            "Completed fetching and parsing TxcStopPoints from DynamoDB",
            total_fetched=len(stop_points),
            total_missing=len(missing_atco_codes),
        )
        return stop_points, missing_atco_codes

    def get_by_atco_code(self, atco_code: str) -> TXCStopPoint | None:
        """
        Get a single StopPoint from DynamoDB by AtcoCode.
        """
        log.info("Fetching single StopPoint from DynamoDB", atco_code=atco_code)

        try:
            response = self._client.get_item(
                TableName=self._settings.DYNAMODB_TABLE_NAME,
                Key={"AtcoCode": {"S": atco_code}},
            )

            item: dict[str, AttributeValueTypeDef] | None = response.get("Item")
            if not item:
                log.info("No StopPoint found for AtcoCode", atco_code=atco_code)
                return None

            return self._deserialize_stop_point(item, atco_code=atco_code)

        except Exception:
            log.error("Failed to fetch StopPoint", atco_code=atco_code, exc_info=True)
            raise

    def get_by_naptan_codes(
        self, naptan_codes: list[str]
    ) -> tuple[list[TXCStopPoint], list[str]]:
        """
        Get all StopPoints from DynamoDB by the given list of NaptanCodes.

        Returns:
            Tuple of (found TXCStopPoints, list of missing NaptanCodes).
        """
        log.info("Fetching StopPoints from DynamoDB by NaptanCodes")

        if not naptan_codes:
            log.warning("No NaptanCodes provided for fetching StopPoints")
            return [], []

        stop_points: list[TXCStopPoint] = []
        found_naptan_codes: Set[str] = set()

        # Batch get item can't be used on a GSI so we need to query for each NaptanCode
        for naptan_code in naptan_codes:
            raw_items = self._client.query(
                TableName=self._settings.DYNAMODB_TABLE_NAME,
                IndexName="NaptanCodeIndex",
                KeyConditionExpression="NaptanCode = :NaptanCode",
                ExpressionAttributeValues={":NaptanCode": {"S": naptan_code}},
            ).get("Items", [])

            if len(raw_items) == 0:
                log.info("No StopPoint found for NaptanCode", naptan_code=naptan_code)
                continue

            if len(raw_items) > 1:
                log.info(
                    "Multiple StopPoints found for NaptanCode", naptan_code=naptan_code
                )
                continue

            item = raw_items[0]

            naptan_code = item.get("NaptanCode", {}).get("S")
            stop_point = self._deserialize_stop_point(item, naptan_code=naptan_code)
            if stop_point and stop_point.NaptanCode:
                stop_points.append(stop_point)
                found_naptan_codes.add(stop_point.NaptanCode)

        missing_naptan_codes = [
            code for code in naptan_codes if code not in found_naptan_codes
        ]

        log.info(
            "Completed fetching and parsing TxcStopPoints from DynamoDB",
            total_fetched=len(stop_points),
            total_missing=len(missing_naptan_codes),
        )
        return stop_points, missing_naptan_codes

    def get_stop_area_map(self, atco_codes: list[str]) -> dict[str, list[str]]:
        """
        Build a stop area map from list of AtcoCodes.

        Returns:
            Dict of {AtcoCode: StopAreas}
        """
        stop_points, _ = self.get_by_atco_codes(atco_codes)
        return {
            stop_point.AtcoCode: (stop_point.StopAreas or [])
            for stop_point in stop_points
        }

    def _deserialize_stop_point(
        self,
        raw_item: dict[str, AttributeValueTypeDef],
        atco_code: str | None = None,
        naptan_code: str | None = None,
    ) -> TXCStopPoint | None:
        """
        Deserialize a DynamoDB item into a TXCStopPoint.
        """
        try:
            deserialized_item = {
                key: self._deserializer.deserialize(value)
                for key, value in raw_item.items()
            }
            return TXCStopPoint(**deserialized_item)
        except (ValueError, ValidationError):
            log.error(
                "Failed to parse StopPoint",
                atco_code=atco_code,
                naptan_code=naptan_code,
                item=raw_item,
                exc_info=True,
            )
            return None

    def _batch_queries(self, items: list[str], batch_size: int) -> Iterator[list[str]]:
        """
        Split list into batch of a specified size.
        """
        for i in range(0, len(items), batch_size):
            yield items[i : i + batch_size]

    def _batch_get_items(
        self, atco_codes: list[str]
    ) -> list[dict[str, AttributeValueTypeDef]]:
        """
        Use DynamoDB BatchGetItem to fetch items for a list of AtcoCodes.
        """
        try:
            request_keys: list[dict[str, dict[str, str]]] = [
                {"AtcoCode": {"S": atco_code}} for atco_code in atco_codes
            ]
            response = self._client.batch_get_item(
                RequestItems={
                    self._settings.DYNAMODB_TABLE_NAME: {"Keys": request_keys}
                }
            )
            # Extract items for the specific table
            raw_items: list[dict[str, AttributeValueTypeDef]] = response.get(
                "Responses", {}
            ).get(self._settings.DYNAMODB_TABLE_NAME, [])

            log.info(
                "BatchGetItem completed",
                fetched=len(raw_items),
                requested=len(atco_codes),
            )
            return raw_items
        except Exception:
            log.error(
                "Failed to execute BatchGetItem", exc_info=True, settings=self._settings
            )

            raise
