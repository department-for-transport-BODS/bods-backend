"""
GovUkNotifyEmail constants to map template
"""

from typing import Dict

TEMPLATE_LOOKUP: Dict[str, str] = {
    "DEVELOPER_DATA_CHANGED": "emails/data_end_point_changed_developer.txt",
    "OPERATOR_PUBLISH_LIVE": "emails/data_end_point_published.txt",
    "OPERATOR_PUBLISH_LIVE_WITH_PTI_VIOLATIONS": (
        "emails/data_end_point_published_with_pti_violations.txt"
    ),
    "AGENT_PUBLISH_LIVE": "emails/data_end_point_published_agent.txt",
    "AGENT_PUBLISH_LIVE_WITH_PTI_VIOLATIONS": (
        "emails/data_end_point_published_with_pti_violations_agent.txt"
    ),
}
