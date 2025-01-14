from common_layer.database.client import SqlDB
from common_layer.dynamodb.client import DynamoDB
from common_layer.pti.constants import (
    BANK_HOLIDAYS,
    BANK_HOLIDAYS_ONLY_ENGLISH,
    BANK_HOLIDAYS_ONLY_SCOTTISH,
    OLD_HOLIDAYS_ALREADY_REMOVED,
    OPERATION_DAYS,
    OTHER_PUBLIC_HOLIDAYS,
    SCOTTISH_BANK_HOLIDAYS,
)

from ..utils import is_service_in_scotland


def get_service_ref_from_element(element, ns):
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

    def validate_bank_holidays(context, bank_holidays):
        bank_holiday = bank_holidays[0]
        ns = {"x": bank_holiday.nsmap.get(None)}
        children = bank_holiday.getchildren()
        local_name = "local-name()"

        holidays = []
        for element in children:
            if element.xpath(local_name, namespaces=ns) in OPERATION_DAYS:
                days = [
                    el.xpath(local_name, namespaces=ns) for el in element.getchildren()
                ]
                holidays += days

        # .getchildren() will return comments: this filters out the comments.
        # It also removes occurrences of OTHER_PUBLIC_HOLIDAYS and OLD_HOLIDAYS_ALREADY_REMOVED of which there may be many or
        # none.
        holidays = [
            h
            for h in holidays
            if h and h not in OTHER_PUBLIC_HOLIDAYS + OLD_HOLIDAYS_ALREADY_REMOVED
        ]

        # duplicate check
        if sorted(list(set(holidays))) != sorted(holidays):
            return False

        service_ref = get_service_ref_from_element(element, ns)
        if service_ref and is_service_in_scotland(service_ref, dynamo, db):
            english_removed = list(set(holidays) - set(BANK_HOLIDAYS_ONLY_ENGLISH))
            return sorted(SCOTTISH_BANK_HOLIDAYS) == sorted(english_removed)

        # optional Scottish holiday check
        scottish_removed = list(set(holidays) - set(BANK_HOLIDAYS_ONLY_SCOTTISH))
        return sorted(BANK_HOLIDAYS) == sorted(scottish_removed)

    return validate_bank_holidays
