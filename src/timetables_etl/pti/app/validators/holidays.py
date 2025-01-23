"""
Validators related to holidays
"""

from common_layer.database.client import SqlDB
from common_layer.dynamodb.client import DynamoDB
from structlog.stdlib import get_logger

from ..utils.utils_scotland import is_service_in_scotland

log = get_logger()


BANK_HOLIDAYS_COMMON = [
    "ChristmasEve",
    "ChristmasDay",
    "ChristmasDayHoliday",
    "BoxingDay",
    "BoxingDayHoliday",
    "NewYearsDay",
    "NewYearsDayHoliday",
    "GoodFriday",
    "EasterMonday",
    "SpringBank",
    "MayDay",
]

BANK_HOLIDAYS_ONLY_ENGLISH = [
    "NewYearsEve",
    "LateSummerBankHolidayNotScotland",
]
BANK_HOLIDAYS_ONLY_SCOTTISH = [
    "StAndrewsDayHoliday",
    "Jan2ndScotland",
    "Jan2ndScotlandHoliday",
]
OLD_HOLIDAYS_ALREADY_REMOVED = [
    "StAndrewsDay",
    "AugustBankHolidayScotland",
]
OTHER_PUBLIC_HOLIDAYS = ["OtherPublicHoliday"]
OPERATION_DAYS = ("DaysOfOperation", "DaysOfNonOperation")

BANK_HOLIDAYS = BANK_HOLIDAYS_COMMON + BANK_HOLIDAYS_ONLY_ENGLISH
SCOTTISH_BANK_HOLIDAYS = BANK_HOLIDAYS_COMMON + BANK_HOLIDAYS_ONLY_SCOTTISH


def get_service_ref_from_element(element, ns):
    """
    Find and return the ServiceRef of the given element
    """
    vj = element.xpath("ancestor::x:VehicleJourney", namespaces=ns)
    service_ref = None
    if vj:
        service_ref = vj[0].xpath("string(x:ServiceRef)", namespaces=ns)
    else:
        service = element.xpath("ancestor::x:Service", namespaces=ns)
        if service:
            service_ref = service[0].xpath("string(x:ServiceCode)", namespaces=ns)

    return service_ref


def get_validate_bank_holidays(dynamo: DynamoDB, db: SqlDB):
    """
    Setup and return validator function for bank holidays
    """

    def validate_bank_holidays(_context, bank_holidays):
        """
        Validate bank holidays
        """
        bank_holiday = bank_holidays[0]
        ns = {"x": bank_holiday.nsmap.get(None)}
        children = bank_holiday.getchildren()
        local_name = "local-name()"

        holidays = []
        element = None
        for element in children:
            if element.xpath(local_name, namespaces=ns) in OPERATION_DAYS:
                days = [
                    el.xpath(local_name, namespaces=ns) for el in element.getchildren()
                ]
                holidays += days

        # .getchildren() will return comments: this filters out the comments.
        # It also removes occurrences of OTHER_PUBLIC_HOLIDAYS and OLD_HOLIDAYS_ALREADY_REMOVED
        # of which there may be many or none.
        holidays = [
            h
            for h in holidays
            if h and h not in OTHER_PUBLIC_HOLIDAYS + OLD_HOLIDAYS_ALREADY_REMOVED
        ]

        # duplicate check
        if sorted(list(set(holidays))) != sorted(holidays):
            log.info(
                "Duplicate Bank Holidays Found",
                observation_id=43,
                holidays=holidays,
            )
            return False

        service_ref = get_service_ref_from_element(element, ns)
        if service_ref and is_service_in_scotland(service_ref, dynamo, db):
            english_removed = list(set(holidays) - set(BANK_HOLIDAYS_ONLY_ENGLISH))
            if sorted(SCOTTISH_BANK_HOLIDAYS) != sorted(english_removed):
                log.info(
                    "Invalid Scottish Bank Holidays",
                    observation_id=43,
                    service_ref=service_ref,
                    holidays=holidays,
                    expected=SCOTTISH_BANK_HOLIDAYS,
                    actual=english_removed,
                )
                return False
            return True

        # optional Scottish holiday check
        scottish_removed = list(set(holidays) - set(BANK_HOLIDAYS_ONLY_SCOTTISH))
        if sorted(BANK_HOLIDAYS) != sorted(scottish_removed):
            log.info(
                "Invalid English Bank Holidays",
                observation_id=43,
                service_ref=service_ref,
                holidays=holidays,
                expected=BANK_HOLIDAYS,
                actual=scottish_removed,
            )
            return False
        return True

    return validate_bank_holidays
