"""
AWS Cloudwatch Metrics Configuration
"""

import os

from aws_lambda_powertools import Metrics
from common_layer.db.constants import StepName


def configure_metrics(step_name: StepName) -> Metrics:
    """
    Configure AWS Metrics setup
    """

    metrics = Metrics()
    metrics.set_default_dimensions(environment=os.getenv("PROJECT_ENV", "unknown"))  # type: ignore
    metrics.add_metadata(key="step_name", value=step_name)
    return metrics


def get_metric_name(metric: str) -> str:
    """
    Get metric name in standard format.
    """
    return f"timetables.etl.{metric}"
