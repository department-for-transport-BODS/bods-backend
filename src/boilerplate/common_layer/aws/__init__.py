"""
Functions which are AWS Environment Specific
Like Logging Setups, AWS Metrics etc 

Allows importing as:

    `from common_layer.aws import configure_metrics`
"""

from .metrics import configure_metrics

__all__ = ["configure_metrics"]
