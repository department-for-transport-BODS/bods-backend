import time
from typing import Any

import psutil
from aws_lambda_powertools import Tracer
from aws_lambda_powertools.utilities.typing import LambdaContext
from common_layer.database import SqlDB
from common_layer.database.repos import TransmodelTrackRepo
from common_layer.json_logging import configure_logging
from structlog.stdlib import get_logger

from .utils import build_duplicate_groups

tracer = Tracer()
log = get_logger()


def consolidate_tracks(
    track_repo: TransmodelTrackRepo,
    start_time: int,
    dry_run: bool = False,
) -> dict[str, int]:
    if dry_run:
        print("Dry run mode enabled — no changes will be written to the database.")

    stats = {
        "total_pairs_checked": 0,
        "pairs_with_duplicates": 0,
        "tracks_deleted": 0,
        "vehicle_journey_fks_updated": 0,
    }

    log.info("Streaming similar track pairs")
    for (
        from_code,
        to_code,
    ), similar_pairs in track_repo.stream_similar_track_pairs_json(threshold=20.0):
        stats["total_pairs_checked"] += 1

        if stats["total_pairs_checked"] % 100 == 0:
            log.info(
                f"Pairs checked: {stats['total_pairs_checked']}, duration: {int(time.perf_counter() - start_time)}"
            )

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
            for track_id in group:
                if track_id == canonical_id:
                    continue

                stats["vehicle_journey_fks_updated"] += 1
                stats["tracks_deleted"] += 1

                if not dry_run:
                    # TODO: Implement once we have the service pattern track junction table
                    # replace_vehicle_journey_track(track_id, canonical_id)
                    track_repo.delete_by_id(track_id)

    return stats


@tracer.capture_lambda_handler
def lambda_handler(event: dict[str, Any], context: LambdaContext) -> dict[str, Any]:
    """
    Lambda handler for consolidating Tracks data in Bods DB.
    Compares tracks between the same from/to atco codes and removes duplicates
    """
    configure_logging(event, context)
    db = SqlDB()
    track_repo = TransmodelTrackRepo(db)
    process = psutil.Process()
    start = time.perf_counter()
    mem_before = process.memory_info().rss

    stats = consolidate_tracks(track_repo, dry_run=True, start_time=int(start))

    mem_after = process.memory_info().rss
    duration = int(time.perf_counter() - start)

    stats["duration"] = duration
    stats["memory_mb_before"] = round(mem_before / 1024 / 1024, 2)
    stats["memory_mb_after"] = round(mem_after / 1024 / 1024, 2)
    stats["memory_mb_used"] = round((mem_after - mem_before) / 1024 / 1024, 2)

    log.info("Stats", **stats)
    return {}


if __name__ == "__main__":
    lambda_handler({}, {})
