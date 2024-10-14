from pytest import fixture
from unittest.mock import MagicMock


@fixture
def mocked_context():
    context = MagicMock()
    context.get_remaining_time_in_millis.return_value = 120000
    return context
