"""
AWS Cloudwatch Metrics Configuration
"""

import os

from aws_lambda_powertools import Metrics


def configure_metrics() -> Metrics:
    """
    Configure AWS Metrics setup
    """

    metrics = Metrics()
    metrics.set_default_dimensions(environment=os.getenv("PROJECT_ENV", "unknown"))
    return metrics
