"""Email content for the emails being sent as part of the ETL process"""

from typing import Any, cast


def data_end_point_error_publishing(
    published_time: str, user_type: str, kwargs: Any
) -> str:
    """Prepares the content of email

    Returns:
        str: Email prepared content
    """
    dataset_type: int = cast(int, kwargs.get("dataset_type", 0))
    content = "Hello, \n\n"
    content += (
        "The following data set has failed to upload on the Bus Open Data "
        "Service due to validation errors"
    )
    if dataset_type == 1:
        content += " supplied in the Validation report"
    content += "\n\n"

    if user_type == "5":
        content += f"Operator: { kwargs['organisation'] } \n"
        content += f"Data set/ feed: {kwargs['feed_name']} \n"
        content += f"Data set/ feed id: {kwargs['feed_id']}\n"
    else:
        content += f"Data set: {kwargs['feed_name']} \n"
        content += f"Data set ID: {kwargs['feed_id']}\n"

    content += f"Short Description: {kwargs['feed_short_description']} \n"
    content += f"Published: {published_time} \n"
    content += f"Comments: {kwargs['comments']} \n"
    content += f"Link to data set: {kwargs['feed_detail_link']} \n"
    if dataset_type == 1:
        content += f"The validation report is available here: {kwargs['report_link']}"
    content += (
        "Action required: \n"
        "\t 1) Share or forward this email to your supplier so "
        "that they can help you with the issues being encountered. \n"
        "\t 2) Complete all actions the supplier requests in response to the validation report. \n"
        "\t 3) Update the dataset on BODS and review the updated validation response. \n\n\n"
    )

    content += "Important: \n"
    content += (
        "You are legally obliged to supply data according to "
        " the standards, and you must resolve all issues listed immediately.\n"
    )
    content += (
        "For support, please contact us on 0800 028 8531, "
        " or by email at bodshelpdesk@kpmg.co.uk.\n\n"
    )

    content += "Kind Regards,\n"
    content += "The Bus Open Data Team\n"

    return content
