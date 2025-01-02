"""
Timing Stats for the operations
"""

from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

from structlog.stdlib import get_logger

log = get_logger()


@dataclass
class TimingStats:
    """Store timing statistics for file processing"""

    file_path: Path
    parse_time: float = 0
    transform_time: float = 0
    total_time: float = 0
    status: str = "success"
    error: str = ""

    def __str__(self):
        log_dict = {
            "file_name": self.file_path.name,
            "parse_time_seconds": round(self.parse_time, 2),
            "transform_time_seconds": round(self.transform_time, 2),
            "total_time_seconds": round(self.total_time, 2),
            "status": self.status,
        }
        if self.error:
            log_dict["error"] = self.error

        return str(log_dict)


def print_timing_report(timing_stats: list[TimingStats], total_time: float) -> None:
    """Generate a structured timing report using structlog"""
    log.info(
        "Files",
        timestamp=datetime.now().isoformat(),
        total_files=len(timing_stats),
        total_time_seconds=round(total_time, 2),
    )

    # Log individual file statistics
    for stats in timing_stats:
        log.info(
            "File Processing Stats",
            file_name=stats.file_path.name,
            parse_time_seconds=round(stats.parse_time, 2),
            transform_time_seconds=round(stats.transform_time, 2),
            total_time_seconds=round(stats.total_time, 2),
            status=stats.status,
            error=stats.error if stats.error else None,
        )

    # Calculate and log averages for successful files
    successful_stats = [s for s in timing_stats if s.status == "success"]
    if successful_stats:
        avg_parse = sum(s.parse_time for s in successful_stats) / len(successful_stats)
        avg_transform = sum(s.transform_time for s in successful_stats) / len(
            successful_stats
        )
        avg_total = sum(s.total_time for s in successful_stats) / len(successful_stats)

        log.info(
            "Processing Timing Averages",
            successful_files_count=len(successful_stats),
            avg_parse_time_seconds=round(avg_parse, 2),
            avg_transform_time_seconds=round(avg_transform, 2),
            avg_total_time_seconds=round(avg_total, 2),
        )

    # Log error summary
    error_stats = [s for s in timing_stats if s.status == "error"]
    if error_stats:
        log.error(
            "File Processing Errors",
            error_count=len(error_stats),
            errors=[
                {"file_name": stat.file_path.name, "error": stat.error}
                for stat in error_stats
            ],
        )

    # Log final summary
    log.info(
        "Local DB ETL Test Script Complete",
        total_files=len(timing_stats),
        successful_files=len(successful_stats),
        failed_files=len(error_stats),
        total_time_seconds=round(total_time, 2),
    )
