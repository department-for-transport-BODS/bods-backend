"""
Days of Week Section
"""

import pytest
from common_layer.txc.models import TXCDaysOfWeek
from common_layer.txc.parser.operating_profile import parse_regular_days
from lxml import etree


@pytest.mark.parametrize(
    "xml_string, expected_result",
    [
        pytest.param(
            """
            <RegularDayType>
                <DaysOfWeek>
                    <Monday/>
                    <Tuesday/>
                    <Wednesday/>
                    <Thursday/>
                </DaysOfWeek>
            </RegularDayType>
            """,
            TXCDaysOfWeek(
                Monday=True,
                Tuesday=True,
                Wednesday=True,
                Thursday=True,
                Friday=False,
                Saturday=False,
                Sunday=False,
                HolidaysOnly=False,
            ),
            id="Individual Days: Weekdays",
        ),
        pytest.param(
            """
            <RegularDayType>
                <DaysOfWeek>
                    <Saturday/>
                    <Sunday/>
                </DaysOfWeek>
            </RegularDayType>
            """,
            TXCDaysOfWeek(
                Monday=False,
                Tuesday=False,
                Wednesday=False,
                Thursday=False,
                Friday=False,
                Saturday=True,
                Sunday=True,
                HolidaysOnly=False,
            ),
            id="Individual Days: Weekend",
        ),
        pytest.param(
            """
            <RegularDayType>
                <HolidaysOnly/>
            </RegularDayType>
            """,
            TXCDaysOfWeek(
                Monday=False,
                Tuesday=False,
                Wednesday=False,
                Thursday=False,
                Friday=False,
                Saturday=False,
                Sunday=False,
                HolidaysOnly=True,
            ),
            id="Holidays only",
        ),
        pytest.param(
            """
            <RegularDayType>
                <DaysOfWeek>
                    <MondayToFriday/>
                </DaysOfWeek>
            </RegularDayType>
            """,
            TXCDaysOfWeek(
                Monday=True,
                Tuesday=True,
                Wednesday=True,
                Thursday=True,
                Friday=True,
                Saturday=False,
                Sunday=False,
                HolidaysOnly=False,
            ),
            id="MondayToFriday",
        ),
        pytest.param(
            """
            <RegularDayType>
                <DaysOfWeek>
                    <MondayToSunday/>
                </DaysOfWeek>
            </RegularDayType>
            """,
            TXCDaysOfWeek(
                Monday=True,
                Tuesday=True,
                Wednesday=True,
                Thursday=True,
                Friday=True,
                Saturday=True,
                Sunday=True,
                HolidaysOnly=False,
            ),
            id="MondayToSunday",
        ),
        pytest.param(
            """
            <RegularDayType>
                <DaysOfWeek>
                    <Weekend/>
                </DaysOfWeek>
            </RegularDayType>
            """,
            TXCDaysOfWeek(
                Monday=False,
                Tuesday=False,
                Wednesday=False,
                Thursday=False,
                Friday=False,
                Saturday=True,
                Sunday=True,
                HolidaysOnly=False,
            ),
            id="Weekend",
        ),
        pytest.param(
            """
            <RegularDayType>
                <DaysOfWeek />
            </RegularDayType>
            """,
            TXCDaysOfWeek(
                Monday=False,
                Tuesday=False,
                Wednesday=False,
                Thursday=False,
                Friday=False,
                Saturday=False,
                Sunday=False,
                HolidaysOnly=False,
            ),
            id="Empty DaysOfWeek - Current incorrect behavior",
        ),
        pytest.param(
            """
            <RegularDayType>
                <DaysOfWeek />
            </RegularDayType>
            """,
            TXCDaysOfWeek(
                Monday=True,
                Tuesday=True,
                Wednesday=True,
                Thursday=True,
                Friday=True,
                Saturday=True,
                Sunday=True,
                HolidaysOnly=False,
            ),
            id="Empty DaysOfWeek - Correct spec behavior",
            marks=pytest.mark.xfail(
                reason="TXC 2.1 spec states empty DaysOfWeek should default to all days, "
                "but current implementation defaults to no days "
                "due to BODS Timetable Tool Generating Incorrect data"
            ),
        ),
    ],
)
def test_parse_regular_days(xml_string: str, expected_result: TXCDaysOfWeek):
    """
    Regular Days
    """
    xml_element = etree.fromstring(xml_string)

    result = parse_regular_days(xml_element)
    assert result == expected_result
