
from timetables_etl.exception_handler import lambda_handler


def test_app():
    val = lambda_handler({}, None)
    assert val == {
        'statusCode': 200,
        'body': ""
    }