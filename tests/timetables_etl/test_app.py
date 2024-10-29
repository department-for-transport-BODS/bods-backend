from timetables_etl.app import lambda_handler


def test_app():
    val = lambda_handler({}, None)
    assert val is None