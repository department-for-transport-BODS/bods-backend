import ZoneInfo


def localize_datetime_and_convert_to_string(
    datetime_object, datetime_string_format: str = "%d-%m-%Y %H:%M"
):
    # convert datetime using uktimezone
    uk_timezone = ZoneInfo("Europe/London")
    localized_datetime = datetime_object.replace(tzinfo=uk_timezone)
    return localized_datetime.strftime(datetime_string_format)
