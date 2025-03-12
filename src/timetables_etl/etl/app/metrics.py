"""
Datadog Metrics for Serverless ETL
"""

from aws_lambda_powertools.metrics.provider.datadog import DatadogMetrics
from common_layer.aws.metrics import get_metric_name

from .models import ETLProcessStats


def create_datadog_metrics(metrics: DatadogMetrics, stats: ETLProcessStats) -> None:
    """
    Send metrics for ETL processing statistics
    """
    metrics.add_metric(name=get_metric_name("services"), value=stats.services)
    metrics.add_metric(
        name=get_metric_name("booking_arrangements"), value=stats.booking_arrangements
    )
    metrics.add_metric(
        name=get_metric_name("service_patterns"), value=stats.service_patterns
    )

    metrics.add_metric(
        name=get_metric_name("localities"), value=stats.pattern_stats.localities
    )
    metrics.add_metric(
        name=get_metric_name("admin_areas"), value=stats.pattern_stats.admin_areas
    )
    metrics.add_metric(
        name=get_metric_name("vehicle_journeys"),
        value=stats.pattern_stats.vehicle_journeys,
    )
    metrics.add_metric(
        name=get_metric_name("stops"), value=stats.pattern_stats.pattern_stops
    )
    metrics.add_metric(name=get_metric_name("tracks"), value=stats.pattern_stats.tracks)
