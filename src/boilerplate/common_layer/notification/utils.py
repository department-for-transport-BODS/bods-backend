"""Email content for the emails being sent as part of the ETL process"""

import os
from datetime import datetime
from os import environ
from pathlib import Path
from typing import Any, cast


def data_end_point_error_publishing(
    published_time: str, user_type: str, kwargs: Any
) -> str:
    """Prepares the content of email

    Returns:
        str: Email prepared content
    """
    dataset_type: int = cast(int, kwargs.get("dataset_type", 0))
    content = "Hello, \n\n "
    content += (
        "The following data set has failed to upload on the Bus Open Data "
        "Service due to validation errors"
    )
    if dataset_type == 1:
        content += " supplied in the Validation report"
    content += "\n\n"

    if user_type == "agent":
        content += f"Operator: { kwargs['organisation'] } \n"
        content += f"Data set/ feed: {kwargs['feed_name']} \n"
        content += f"Data set/ feed id: {kwargs['feed_id']}\n"
    else:
        content += f"Data set: {kwargs['feed_name']} \n"
        content += f"Data set ID: {kwargs['feed_id']}\n"

    content += f"Short Description: {kwargs['feed_short_description']}\n"
    content += f"Published: {published_time} \n"
    content += f"Comments: {kwargs['comments']} \n"
    content += f"Link to data set: {kwargs['feed_detail_link']} \n"
    content += f"\nThe validation report is available here: {kwargs['report_link']}"
    content += (
        "\n\nAction required: \n"
        "\t 1) Share or forward this email to your supplier so "
        "that they can help you with the issues being encountered. \n"
        "\t 2) Complete all actions the supplier requests in response to the validation report. \n"
        "\t 3) Update the dataset on BODS and review the updated validation response. \n\n"
    )

    support_email = environ.get("SUPPORT_EMAIL")
    support_phone = environ.get("SUPPORT_PHONE")

    content += "Important: \n"
    content += (
        "You are legally obliged to supply data according to "
        " the standards, and you must resolve all issues listed immediately.\n"
    )
    content += (
        f"For support, please contact us on {support_phone}, "
        f"or by email at {support_email}.\n\n"
    )

    content += "Kind Regards,\n"
    content += "The Bus Open Data Team\n"

    return content


def get_email_body_from_text_file(template_path: str, args: Any) -> str:
    """Common method which will read content from the email text file

    Args:
        template_path (str): Path of the text file
        args (Any): Args to be replaced

    Returns:
        str: string body for email
    """
    file_path = Path(f"{os.path.dirname(os.path.realpath(__file__))}/{template_path}")

    with open(file_path, "r", encoding="utf-8") as file:
        content = file.read()

    for key, value in args.items():
        placeholder = f"{{{{ {key} }}}}"
        content = content.replace(placeholder, str(value))

    pti_enforce_date = datetime.strptime(
        environ.get("PTI_START_DATE", "2021-08-02"), "%Y-%m-%d"
    )
    pti_enforce_date = pti_enforce_date.strftime("%d %B, %Y")
    content = content.replace("{{ pti_enforced_date }}", pti_enforce_date)

    support_email = environ.get("SUPPORT_EMAIL")
    support_phone = environ.get("SUPPORT_PHONE")
    content = content.replace("{{ SUPPORT_EMAIL }}", support_email)
    content = content.replace("{{ SUPPORT_PHONE }}", support_phone)

    return content
