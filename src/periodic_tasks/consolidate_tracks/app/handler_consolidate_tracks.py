"""
Lambda handler for consolidating duplicated Tracks data
"""

import json
import time
from typing import Any

import psutil
from aws_lambda_powertools import Tracer
from aws_lambda_powertools.utilities.typing import LambdaContext
from common_layer.database import SqlDB
from common_layer.database.repos import (
    TransmodelServicePatternTracksRepo,
    TransmodelTrackRepo,
)
from common_layer.json_logging import configure_logging
from pydantic import BaseModel, ValidationError
from structlog.stdlib import get_logger

from .utils import build_duplicate_groups

tracer = Tracer()
log = get_logger()


# pylint: disable=too-many-locals
def consolidate_tracks(
    track_repo: TransmodelTrackRepo,
    sp_track_repo: TransmodelServicePatternTracksRepo,
    threshold: float,
    start_time: int,
    dry_run: bool = False,
) -> dict[str, int]:
    """
    Find and consolidate duplicated Tracks data
    """
    if dry_run:
        log.info("Dry run mode enabled — no changes will be written to the database.")

    stats = {
        "total_pairs_checked": 0,
        "pairs_with_duplicates": 0,
        "tracks_to_delete": 0,
        "tracks_deleted": 0,
        "fks_updated": 0,
    }

    batch_size = 10000
    for batch_idx, stop_point_pairs in enumerate(
        track_repo.stream_distinct_stop_points_with_multiple_rows(batch_size=batch_size)
    ):
        log.info(
            "Streaming similar track pairs",
            batch_number=batch_idx,
            batch_size=batch_size,
            stats=stats,
        )
        for (
            from_code,
            to_code,
        ), similar_pairs in track_repo.stream_similar_track_pairs_by_stop_points(
            stop_point_pairs=stop_point_pairs, threshold=threshold
        ):
            log.debug(
                "Checking stop point pair",
                from_atco_code=from_code,
                to_atco_code=to_code,
            )
            if stats["total_pairs_checked"] % 1000 == 0:
                log.info(
                    "Pairs checked",
                    count=stats["total_pairs_checked"],
                    duration={int(time.perf_counter() - start_time)},
                )

            stats["total_pairs_checked"] += 1

            if not similar_pairs:
                continue

            # Build groups of similar tracks
            duplicate_groups = build_duplicate_groups(similar_pairs)

            for group in duplicate_groups:
                if len(group) <= 1:
                    continue

                stats["pairs_with_duplicates"] += 1
                # Select track with lowest ID (first created) as the canonical track
                canonical_id = min(group)

                tracks_to_consolidate = [
                    track_id for track_id in group if track_id != canonical_id
                ]

                if not dry_run:
                    fk_updated_count = (
                        sp_track_repo.bulk_replace_service_pattern_tracks(
                            tracks_to_consolidate, canonical_id
                        )
                    )
                    deleted_count = track_repo.bulk_delete_by_ids(tracks_to_consolidate)

                    stats["fks_updated"] += fk_updated_count if fk_updated_count else 0
                    stats["tracks_deleted"] += deleted_count if deleted_count else 0

                stats["tracks_to_delete"] += len(tracks_to_consolidate)

    return stats


class ConsolidateTracksInput(BaseModel):
    """Input schema for Consolidate Tracks Lambda."""

    dry_run: bool
    threshold_meters: float = 20.0


@tracer.capture_lambda_handler
def lambda_handler(event: dict[str, Any], context: LambdaContext) -> dict[str, Any]:
    """
    Lambda handler for consolidating Tracks data in Bods DB.
    Compares tracks between the same from/to atco codes and removes duplicates
    """
    configure_logging(event, context)

    try:
        input_data = ConsolidateTracksInput.model_validate(event)
    except ValidationError as e:
        log.error("Invalid input data", error=str(e))
        return {
            "statusCode": 400,
            "body": json.dumps({"message": "Invalid input data", "errors": e.errors()}),
        }

    db = SqlDB()
    track_repo = TransmodelTrackRepo(db)
    sp_track_repo = TransmodelServicePatternTracksRepo(db)
    process = psutil.Process()
    start = time.perf_counter()
    mem_before = process.memory_info().rss

    stats = consolidate_tracks(
        track_repo,
        sp_track_repo,
        threshold=input_data.threshold_meters,
        dry_run=input_data.dry_run,
        start_time=int(start),
    )

    mem_after = process.memory_info().rss
    duration = int(time.perf_counter() - start)

    stats["duration"] = duration
    stats["memory_mb_before"] = round(mem_before / 1024 / 1024, 2)
    stats["memory_mb_after"] = round(mem_after / 1024 / 1024, 2)
    stats["memory_mb_used"] = round((mem_after - mem_before) / 1024 / 1024, 2)

    log.info("Stats", **stats)
    return stats
