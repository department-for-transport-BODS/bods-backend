"""
Datadog Metrics for Serverless ETL
"""

from aws_lambda_powertools import Metrics
from aws_lambda_powertools.metrics import MetricUnit
from common_layer.aws.metrics import get_metric_name

from .models import ETLProcessStats


def create_datadog_metrics(metrics: Metrics, stats: ETLProcessStats) -> None:
    """
    Send metrics for ETL processing statistics
    """
    metrics.add_metric(
        name=get_metric_name("services"), unit=MetricUnit.Count, value=stats.services
    )
    metrics.add_metric(
        name=get_metric_name("booking_arrangements"),
        unit=MetricUnit.Count,
        value=stats.booking_arrangements,
    )
    metrics.add_metric(
        name=get_metric_name("service_patterns"),
        unit=MetricUnit.Count,
        value=stats.service_patterns,
    )

    metrics.add_metric(
        name=get_metric_name("localities"),
        unit=MetricUnit.Count,
        value=stats.pattern_stats.localities,
    )
    metrics.add_metric(
        name=get_metric_name("admin_areas"),
        unit=MetricUnit.Count,
        value=stats.pattern_stats.admin_areas,
    )
    metrics.add_metric(
        name=get_metric_name("vehicle_journeys"),
        unit=MetricUnit.Count,
        value=stats.pattern_stats.vehicle_journeys,
    )
    metrics.add_metric(
        name=get_metric_name("stops"),
        unit=MetricUnit.Count,
        value=stats.pattern_stats.pattern_stops,
    )
    metrics.add_metric(
        name=get_metric_name("tracks"),
        unit=MetricUnit.Count,
        value=stats.pattern_stats.tracks,
    )
    metrics.add_metric(
        name=get_metric_name("superseded_timetables"),
        unit=MetricUnit.Count,
        value=stats.superseded_timetables,
    )
