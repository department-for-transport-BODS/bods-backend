"""Email helper class for methods requred for time conversion"""

from zoneinfo import ZoneInfo


def localize_datetime_and_convert_to_string(
    datetime_object, datetime_string_format: str = "%d-%m-%Y %H:%M"
):
    """Convert datetime object to a given format

    Args:
        datetime_object (datetime): datetime object for conversion
        datetime_string_format (string, optional): string format. Defaults to "%d-%m-%Y %H:%M".

    Returns:
        string: datetime string
    """
    # convert datetime using uktimezone
    uk_timezone = ZoneInfo("Europe/London")
    localized_datetime = datetime_object.replace(tzinfo=uk_timezone)
    return localized_datetime.strftime(datetime_string_format)
