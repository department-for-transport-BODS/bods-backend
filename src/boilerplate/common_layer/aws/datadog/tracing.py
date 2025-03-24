"""
Tracing init
# Automatically patch all supported libraries when this module is imported
"""

from ddtrace import patch

patch(sqlalchemy=True, structlog=True, requests=True, psycopg=True, botocore=True)
