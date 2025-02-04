"""
Test Time Helpers
"""

from unittest.mock import Mock

from dateutil import parser
from freezegun import freeze_time
from pti.app.utils.utils_time import today


@freeze_time("2020-02-02")
def test_today():
    context = Mock()
    actual = today(context)
    assert actual == parser.parse("2020-02-02").timestamp()
