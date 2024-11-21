OPERATION_DAYS = ("DaysOfOperation", "DaysOfNonOperation")

# holidays common for english and scottish regions

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

# holidays only for english regions
BANK_HOLIDAYS_ONLY_ENGLISH = [
    "NewYearsEve",
    "LateSummerBankHolidayNotScotland",
]

# holidays only for scottish regions
BANK_HOLIDAYS_ONLY_SCOTTISH = [
    "StAndrewsDayHoliday",
    "Jan2ndScotland",
    "Jan2ndScotlandHoliday",
]

BANK_HOLIDAYS = BANK_HOLIDAYS_COMMON + BANK_HOLIDAYS_ONLY_ENGLISH
SCOTTISH_BANK_HOLIDAYS = BANK_HOLIDAYS_COMMON + BANK_HOLIDAYS_ONLY_SCOTTISH
OTHER_PUBLIC_HOLIDAYS = ["OtherPublicHoliday"]

# old holidays, which may not come now
OLD_HOLIDAYS_ALREADY_REMOVED = [
    "StAndrewsDay",
    "AugustBankHolidayScotland",
]

REF_URL = "http://pti_pdf_url.com/"  # TODO: was coming from settings.PTI_PDF_URL. Hardcode or get from env var?
REF_PREFIX = "Please refer to section "
REF_SUFFIX = " in the BODS PTI profile v1.1 document: "
NO_REF = "Please refer to the BODS PTI profile v1.1 document: "

MODE_COACH = "coach"
